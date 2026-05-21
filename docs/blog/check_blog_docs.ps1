param(
    [switch]$Strict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Error "python was not found on PATH; docs/blog checks require Python."
    exit 1
}

$pythonScript = @'
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

blog_root = Path(sys.argv[1]).resolve()
repo_root = blog_root.parents[1]
strict = len(sys.argv) > 2 and sys.argv[2].lower() == "true"

cases_path = repo_root / "tools" / "cases.yaml"
media_manifest_path = blog_root / "media_manifest.json"
deep_slugs = {
    "animation_format",
    "footskate_cleanup_for_motion_capture_editing",
    "motion_matching",
    "motion_graph",
    "real_time_planning_for_parameterized_human_motion",
    "curve_and_spline",
    "laplacian_deformation",
    "motion_warping",
    "verbs_and_adverbs",
    "precomputing_avatar_behavior",
    "near_optimal_character_animation_with_continuous_control",
    "motion_fields_for_interactive_character_animation",
}

required_sections = [
    "## \u6a21\u5757\u62c6\u89e3",
    "## \u6267\u884c\u7ed3\u679c\u7684\u610f\u4e49",
]
gold_sections = [
    "## \u9605\u8bfb\u524d\u7f6e\u77e5\u8bc6",
    "## \u4ee3\u7801\u6267\u884c\u8def\u5f84",
    "## \u5173\u952e cell / \u51fd\u6570\u6df1\u8bb2",
]
forbidden_tokens = [
    "\u5f85\u8865",
    "\u5360\u4f4d",
    "TO" + "DO",
    "?" * 3,
]
allowed_capture_kinds = {
    "canvas",
    "plot",
    "table",
    "formula",
    "widget_controls",
    "artifact_summary",
    "code_evidence",
}
key_media_roles = {"key_visual", "key_animation"}
forbidden_key_provenance = {
    "curated_algorithm_visual",
    "derived_card_crop",
    "generated_algorithm_animation",
    "learning_card",
    "scroll_capture",
    "whole_cell",
    "browser_page",
    "static_pan_zoom",
}
footskate_slug = "footskate_cleanup_for_motion_capture_editing"
footskate_key_provenance_allowlist = {"live_canvas", "executed_plot_image"}
forbidden_key_provenance_prefixes = ("curated", "derived", "static")
pollution_text_markers = [
    "Code cell",
    "Source excerpt",
    "Mode: Command",
    "Busy",
    "Markdown",
    "JupyterLab",
    "Jupyter Notebook",
    "Cell In",
    "Run",
]
label_artifact_patterns = [
    ("code-purpose label", re.compile(r"\u4ee3\u7801\u505a\u4ec0\u4e48\?")),
    ("output label", re.compile(r"\u8fd0\u884c\u540e\u770b\u5230\u4ec0\u4e48\?")),
    ("meaning label", re.compile(r"\u7ed3\u679c\u8bf4\u660e\u4ec0\u4e48\?")),
    ("generated output suffix", re.compile(r"(\u56fe\u8868\u8f93\u51fa|\u8fd0\u884c\u65e5\u5fd7\u6216\u6587\u672c\u8f93\u51fa|\u8868\u683c\u6216\u7ed3\u6784\u5316\u6570\u636e\u8f93\u51fa|\u77e9\u9635\u6216\u6570\u7ec4\u8f93\u51fa|\u53ef\u89c6\u5316 viewer \u89c6\u53e3|\u5e26 timeline \u7684\u53ef\u64ad\u653e viewer|\u4ea4\u4e92\u63a7\u4ef6\u72b6\u6001|\u4ee3\u7801\u903b\u8f91\u7247\u6bb5|\u6e90\u7801\u7247\u6bb5|\u547d\u4ee4\u65e5\u5fd7|\u4ea7\u7269\u6458\u8981|\u6a21\u5757\u6d41\u7a0b\u56fe)\?")),
]
stale_phase_phrases = [
    "\u91d1\u6807\u51c6\u6df1\u5199",
    "\u5148\u628a 6 \u4e2a\u4ee3\u8868\u6848\u4f8b\u6269\u5199",
    "\u91d1\u6807\u51c6\u6848\u4f8b",
    "\u7b2c\u4e8c\u9636\u6bb5",
    "\u7b2c\u4e09\u9636\u6bb5",
    "\u7b2c\u56db\u9636\u6bb5",
]

errors = []

def add_error(message):
    errors.append(message)

def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig")

def count_mermaid(text):
    return text.count("```mermaid")

def count_cell_mermaid(text):
    pattern = re.compile(r"^### (?:Cell|[A-Za-z0-9_-]+).*?(?=^### |\Z)", re.M | re.S)
    return sum(1 for block in pattern.findall(text) if "```mermaid" in block)

def resolve_blog_relative(base_file, relative_path):
    clean = relative_path.split("#", 1)[0].split("?", 1)[0].strip()
    if not clean:
        return None
    return (Path(base_file).parent / clean).resolve()

asset_ref_pattern = re.compile(
    r"!\[[^\]]*\]\((assets/[^)]+)\)"
    r"|\[[^\]]+\]\((assets/[^)]+)\)"
    r"|(?:src|poster)=[\"'](assets/[^\"']+)[\"']",
    re.I,
)
legacy_video_link_pattern = re.compile(
    r"\[(?:\u6253\u5f00|\u6253\u5f00/\u4e0b\u8f7d)[^\]]*(?:MP4|WebM)[^\]]*\]\(assets/[^)]+\.(?:mp4|webm)\)",
    re.I,
)
github_video_url_pattern = re.compile(
    r"^https://(?:github\.com/user-attachments/assets/[A-Za-z0-9_-]+|user-images\.githubusercontent\.com/[^\s<>)\"']+\.(?:mp4|webm|mov))$",
    re.I,
)

def asset_refs_in_text(text):
    for match in asset_ref_pattern.finditer(text):
        yield next(group for group in match.groups() if group)

def check_asset_links(file_path, text):
    for asset_rel in asset_refs_in_text(text):
        asset_path = resolve_blog_relative(file_path, asset_rel)
        if asset_path is not None and not asset_path.exists():
            add_error(f"Broken asset reference in {file_path}: {asset_rel}")

def check_text_artifacts(file_path, text):
    for label, pattern in label_artifact_patterns:
        match = pattern.search(text)
        if match:
            add_error(f"Generated label artifact in {file_path} ({label}): {match.group(0)}")

def png_size(path):
    with Path(path).open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height

def step_label(slug, step):
    return f"{slug}:{step.get('id', '<missing-id>')}"

def has_real_controls(step, expected_roles=None):
    controls = step.get("controls", [])
    if not isinstance(controls, list) or not controls:
        return False
    expected_roles = set(expected_roles or [])
    for control in controls:
        if not isinstance(control, dict):
            continue
        kind = control.get("kind")
        role = control.get("role")
        if kind not in {"slider", "range", "scrubber", "checkbox", "toggle", "select"}:
            continue
        if expected_roles and role not in expected_roles:
            continue
        if kind in {"slider", "range", "scrubber"}:
            if any(key in control for key in ("fraction", "value", "frame", "time")):
                return True
        elif any(key in control for key in ("checked", "value", "index")):
            return True
    return False

def is_forbidden_key_provenance(provenance):
    if provenance in (None, ""):
        return False
    value = str(provenance)
    return value in forbidden_key_provenance or value.startswith(forbidden_key_provenance_prefixes)

def png_has_embedded_pollution_text(path):
    try:
        raw = Path(path).read_bytes()
    except OSError:
        return []
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return []
    chunks = []
    pos = 8
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        chunk_type = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + length]
        if chunk_type in {b"tEXt", b"iTXt"}:
            chunks.append(data.decode("latin-1", errors="ignore"))
        elif chunk_type == b"zTXt":
            try:
                nul = data.index(b"\x00")
                chunks.append(data[:nul].decode("latin-1", errors="ignore"))
                chunks.append(zlib.decompress(data[nul + 2:]).decode("latin-1", errors="ignore"))
            except Exception:
                chunks.append(data.decode("latin-1", errors="ignore"))
        pos += 12 + length
    text = "\n".join(chunks)
    return [marker for marker in pollution_text_markers if marker in text]

def check_result_png_visual_pollution(slug, step, media_path, width, height):
    label = step_label(slug, step)
    found_markers = png_has_embedded_pollution_text(media_path)
    if found_markers:
        add_error(f"Result PNG for {label} contains notebook/chrome text marker(s): {', '.join(found_markers)}")

    role = step.get("media_role")
    provenance = step.get("media_provenance")
    if role in key_media_roles:
        if width <= 0 or height <= 0:
            add_error(f"Key result PNG has invalid dimensions for {label}: {media_path}")
            return
        ratio = width / height
        if height > width * 1.4:
            add_error(f"Key result PNG looks like a tall scroll capture for {label}: {media_path} ({width}x{height})")
        if ratio > 10:
            add_error(f"Key result PNG has an extreme wide ratio for {label}: {media_path} ({width}x{height})")
        if is_forbidden_key_provenance(provenance):
            add_error(f"Key result PNG uses forbidden provenance for {label}: {provenance}")

def section_between(text, heading, next_prefix="\n## "):
    start = text.find(heading)
    if start < 0:
        return ""
    end = text.find(next_prefix, start + 1)
    return text[start:] if end < 0 else text[start:end]

def html_video_blocks(text):
    return re.findall(r"<video\b[^>]*>.*?</video>", text, flags=re.I | re.S)

def has_video_preview(text, mp4_ref, webm_ref):
    for block in html_video_blocks(text):
        if mp4_ref in block:
            return True
        if webm_ref in block and mp4_ref in text:
            return True
    return False

def is_github_video_url(value):
    return isinstance(value, str) and bool(github_video_url_pattern.match(value.strip()))

def ffprobe_duration(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None

if not cases_path.exists():
    add_error(f"Missing manifest: {cases_path}")
    manifest = {"cases": []}
else:
    manifest = json.loads(read_text(cases_path))

if media_manifest_path.exists():
    media_manifest = json.loads(read_text(media_manifest_path))
else:
    media_manifest = None

target_cases = [
    case for case in manifest["cases"]
    if case["entry"].startswith("labs/AnimationPapers/")
    or case["entry"].startswith("labs/Theory/")
]
target_by_slug = {case["slug"]: case for case in target_cases}
target_slugs = set(target_by_slug)

if len(target_cases) != 19:
    add_error(f"Expected 19 AnimationPapers/Theory cases, found {len(target_cases)}.")

top_readme = blog_root / "README.md"
top_text = read_text(top_readme) if top_readme.exists() else ""
check_text_artifacts(top_readme, top_text)

for required in [
    "start_animationpapers_lab.ps1",
    "run_case.ps1",
    ".reports/study/AnimationPapers",
    "report_blog_docs.ps1",
]:
    if required not in top_text:
        add_error(f"Top README does not mention {required}.")

for stale_phrase in stale_phase_phrases:
    if stale_phrase in top_text:
        add_error(f"Top README contains stale phase wording: {stale_phrase}")

report_script = blog_root / "report_blog_docs.ps1"
if not report_script.exists():
    add_error(f"Missing blog report helper: {report_script}")

for case in target_cases:
    group = "AnimationPapers" if case["entry"].startswith("labs/AnimationPapers/") else "Theory"
    slug = case["slug"]
    case_dir = blog_root / group / slug
    readme = case_dir / "README.md"
    assets_dir = case_dir / "assets"
    source_path = repo_root / case["entry"]
    group_readme = blog_root / group / "README.md"

    if not case_dir.exists():
        add_error(f"Missing case directory: {group}/{slug}")
        continue

    if not readme.exists():
        add_error(f"Missing README: {group}/{slug}")
        continue

    if not assets_dir.exists():
        add_error(f"Missing assets directory: {group}/{slug}")

    if not source_path.exists():
        add_error(f"Manifest source does not exist for {slug}: {case['entry']}")

    text = read_text(readme)
    check_text_artifacts(readme, text)

    if case["entry"] not in text:
        add_error(f"README for {slug} does not mention manifest source path {case['entry']}.")

    if count_mermaid(text) < 1:
        add_error(f"README for {slug} needs at least one Mermaid block.")

    for section in required_sections:
        if section not in text:
            add_error(f"README for {slug} is missing {section}.")

    if forbidden_tokens[-1] in text:
        add_error(f"README for {slug} contains mojibake marker.")

    check_asset_links(readme, text)

    if group_readme.exists():
        group_text = read_text(group_readme)
        check_text_artifacts(group_readme, group_text)
        for stale_phrase in stale_phase_phrases:
            if stale_phrase in group_text:
                add_error(f"Group README contains stale phase wording: {group_readme}: {stale_phrase}")
        if f"{slug}/README.md" not in group_text:
            add_error(f"Group README does not link {slug}.")

    if f"{group}/{slug}/README.md" not in top_text:
        add_error(f"Top README does not link {group}/{slug}.")

    if slug in deep_slugs:
        for token in forbidden_tokens:
            if token in text:
                add_error(f"Deep README for {slug} contains forbidden token.")

        if count_mermaid(text) < 2:
            add_error(f"Deep README for {slug} needs at least two Mermaid blocks.")
        if slug not in {
            "animation_format",
            "footskate_cleanup_for_motion_capture_editing",
            "motion_matching",
            "motion_graph",
            "real_time_planning_for_parameterized_human_motion",
            "curve_and_spline",
        } and count_cell_mermaid(text) < 3:
            add_error(f"Deep README for {slug} needs at least three cell-level Mermaid blocks.")

        for section in gold_sections:
            if section not in text:
                add_error(f"Deep README for {slug} is missing {section}.")

        asset_readme = assets_dir / "README.md"
        if not asset_readme.exists():
            add_error(f"Deep case {slug} is missing assets/README.md.")
        else:
            asset_text = read_text(asset_readme)
            for token in forbidden_tokens:
                if token in asset_text:
                    add_error(f"Deep assets README for {slug} contains forbidden token.")
            check_asset_links(asset_readme, asset_text)

unmanaged_dir = blog_root / "AnimationPapers" / "animation_format_inv"
if unmanaged_dir.exists():
    add_error(f"Unmanaged Animation Format_inv case directory should not exist: {unmanaged_dir}")

if media_manifest is not None:
    if int(media_manifest.get("version", 0)) != 5:
        add_error("Media manifest must use version 5 key-result media schema.")
    if media_manifest.get("capture_mode") != "key_result_media":
        add_error("Media manifest capture_mode must be key_result_media.")
    media_cases = media_manifest.get("cases", [])
    media_slugs = {case.get("slug") for case in media_cases}
    if media_slugs != target_slugs:
        add_error(f"Media manifest slugs do not match managed blog slugs: {sorted(media_slugs)}")

    video_conf = media_manifest.get("video", {})
    animation_conf = media_manifest.get("animation", video_conf)
    video_file = video_conf.get("file", "00-walkthrough.webm")
    max_video_bytes = int(video_conf.get("max_bytes", 20 * 1024 * 1024))
    max_video_seconds = float(video_conf.get("max_seconds", 15))
    max_animation_bytes = int(animation_conf.get("max_bytes", 10 * 1024 * 1024))
    max_animation_seconds = float(animation_conf.get("max_seconds", 6))

    for case in media_cases:
        slug = case.get("slug")
        readme = repo_root / case.get("blog_readme", "")
        assets_dir = repo_root / case.get("assets_dir", "")
        asset_readme = assets_dir / "README.md"
        if not readme.exists():
            add_error(f"Media README missing for {slug}: {readme}")
            continue
        if not asset_readme.exists():
            add_error(f"Media assets README missing for {slug}: {asset_readme}")
            continue

        readme_text = read_text(readme)
        asset_text = read_text(asset_readme)
        key_media_section = section_between(readme_text, "## \u91cd\u70b9\u53ef\u89c6\u5316 / \u52a8\u753b")
        manifest_case = target_by_slug.get(slug, {})
        case_kind = case.get("kind") or manifest_case.get("kind", "notebook")
        if case_kind == "python_module":
            if "## \u6e90\u7801\u6a21\u5757\u4e0e\u6267\u884c\u8bc1\u636e" not in readme_text:
                add_error(f"README for {slug} is missing ## \u6e90\u7801\u6a21\u5757\u4e0e\u6267\u884c\u8bc1\u636e.")
        elif "## \u4ee3\u7801 Cell \u4e0e\u53ef\u89c6\u5316\u8bc1\u636e" not in readme_text:
            add_error(f"README for {slug} is missing ## \u4ee3\u7801 Cell \u4e0e\u53ef\u89c6\u5316\u8bc1\u636e.")
        steps = case.get("steps", [])
        if len(steps) < 5:
            add_error(f"Media case {slug} needs at least 5 learning steps.")
        media_entries = []
        for step in steps:
            for key in ("result_file", "card_file", "preview_gif", "video_mp4", "video_webm"):
                if step.get(key):
                    media_entries.append({"file": step.get(key), "output_type": step.get("output_type"), "key": key, "step": step})
        walkthrough_conf = case.get("walkthrough", {})
        walkthrough_webm = walkthrough_conf.get("webm") or video_file
        media_entries.append({"file": walkthrough_webm, "output_type": "video", "key": "walkthrough_webm"})
        if walkthrough_conf.get("mp4"):
            media_entries.append({"file": walkthrough_conf.get("mp4"), "output_type": "video", "key": "walkthrough_mp4"})
        declared_media_files = {entry.get("file") for entry in media_entries if entry.get("file")}
        optional_readme_media_files = {
            entry.get("file")
            for entry in media_entries
            if str(entry.get("key", "")).startswith("walkthrough_")
        }
        for media_entry in media_entries:
            media_file = media_entry.get("file")
            media_path = assets_dir / media_file
            media_ref = f"assets/{media_file}"
            if not media_path.exists():
                add_error(f"Media file missing for {slug}: {media_path}")
                continue
            if media_path.stat().st_size <= 0:
                add_error(f"Media file is empty for {slug}: {media_path}")
            if media_file not in optional_readme_media_files and media_ref not in readme_text:
                add_error(f"README for {slug} does not reference {media_ref}.")
            if media_file not in asset_text:
                add_error(f"assets README for {slug} does not list {media_file}.")

            if media_file.lower().endswith(".png"):
                size = png_size(media_path)
                if size is None:
                    add_error(f"PNG media is not readable for {slug}: {media_path}")
                else:
                    width, height = size
                    if media_entry.get("key") == "result_file":
                        if width < 320 or height < 160:
                            add_error(f"Result PNG media is too small for {slug}: {media_path} ({width}x{height})")
                        check_result_png_visual_pollution(slug, media_entry.get("step", {}), media_path, width, height)
                    elif width < 800 or height < 450:
                        add_error(f"Card PNG media is too small for {slug}: {media_path} ({width}x{height})")
                min_png_bytes = 4000 if media_entry.get("key") == "result_file" else 10000
                if media_path.stat().st_size < min_png_bytes:
                    add_error(f"PNG media is suspiciously tiny for {slug}: {media_path}")
            elif media_file.lower().endswith(".gif"):
                if media_path.stat().st_size > max_animation_bytes:
                    add_error(f"GIF media is too large for {slug}: {media_path}")
            elif media_file.lower().endswith((".webm", ".mp4")):
                limit_bytes = max_animation_bytes if media_entry.get("key") in {"video_mp4", "video_webm"} else max_video_bytes
                limit_seconds = max_animation_seconds if media_entry.get("key") in {"video_mp4", "video_webm"} else max_video_seconds
                if media_path.stat().st_size > limit_bytes:
                    add_error(f"Video media is too large for {slug}: {media_path}")
                duration = ffprobe_duration(media_path)
                if duration is not None and duration > limit_seconds + 0.75:
                    add_error(f"Video media is too long for {slug}: {media_path} ({duration:.2f}s)")

        if assets_dir.exists():
            for local_media in assets_dir.iterdir():
                if local_media.suffix.lower() not in {".png", ".gif", ".mp4", ".webm"}:
                    continue
                media_ref = f"assets/{local_media.name}"
                if local_media.name not in declared_media_files:
                    add_error(f"Media file for {slug} is not declared in media manifest: {local_media}")
                if local_media.name not in optional_readme_media_files and media_ref not in readme_text:
                    add_error(f"README for {slug} does not reference local media file {media_ref}.")
                if local_media.name not in asset_text:
                    add_error(f"assets README for {slug} does not list local media file {local_media.name}.")

        for step in steps:
            required_step_fields = ["output_type", "code_purpose", "result_meaning", "title"]
            if case_kind == "python_module":
                required_step_fields.append("source_path")
            else:
                required_step_fields.append("cell_index")
            required_step_fields.extend([
                "visual_subject",
                "capture_kind",
                "capture_selector",
                "publish_media_required",
            ])
            for field in required_step_fields:
                if field not in step:
                    add_error(f"Media step for {slug} is missing {field}.")
            for field in ("media_role", "result_file", "card_file"):
                if field not in step:
                    add_error(f"Media step for {slug} is missing {field}.")
            capture_kind = step.get("capture_kind")
            if capture_kind is not None and capture_kind not in allowed_capture_kinds:
                add_error(f"Media step for {slug} has unsupported capture_kind: {capture_kind}")
            if step.get("capture_selector") in (None, ""):
                add_error(f"Media step for {slug} needs a non-empty capture_selector: {step.get('id')}")
            if step.get("visual_subject") in (None, ""):
                add_error(f"Media step for {slug} needs a non-empty visual_subject: {step.get('id')}")
            if "publish_media_required" in step and not isinstance(step.get("publish_media_required"), bool):
                add_error(f"Media step for {slug} publish_media_required must be boolean: {step.get('id')}")
            if step.get("media_role") in {"key_visual", "key_animation"}:
                result_ref = f"assets/{step.get('result_file', '')}"
                if result_ref not in readme_text:
                    add_error(f"README for {slug} does not reference key result media {result_ref}.")
                if key_media_section and f"assets/{step.get('card_file', '')}" in key_media_section:
                    add_error(f"Key media section for {slug} must not reference learning card {step.get('card_file')}.")
                if capture_kind == "code_evidence":
                    add_error(f"Key media for {slug} cannot use capture_kind=code_evidence: {step.get('id')}")
                if step.get("publish_media_required") is not True:
                    add_error(f"Key media for {slug} must set publish_media_required=true: {step.get('id')}")
                provenance = step.get("media_provenance")
                if provenance in (None, ""):
                    add_error(f"Key media for {slug} is missing media_provenance: {step.get('id')}")
                elif is_forbidden_key_provenance(provenance):
                    add_error(f"Key media for {slug} uses forbidden media_provenance={provenance}: {step.get('id')}")
                if step.get("capture_selector") == "generated algorithm frame sequence":
                    add_error(f"Key media for {slug} cannot use generated algorithm frame sequence: {step.get('id')}")
                if slug == footskate_slug and provenance not in footskate_key_provenance_allowlist:
                    add_error(f"Footskate key media must use live_canvas or executed_plot_image provenance: {step.get('id')} has {provenance}")
                if provenance == "live_canvas" and capture_kind != "canvas":
                    add_error(f"live_canvas media for {slug} must use capture_kind=canvas: {step.get('id')}")
                if provenance in {"executed_plot_image", "executed_plot_output"} and capture_kind != "plot":
                    add_error(f"executed plot media for {slug} must use capture_kind=plot: {step.get('id')}")
            if step.get("media_role") == "key_animation":
                if not step.get("preview_gif"):
                    add_error(f"Key animation for {slug} missing preview_gif: {step.get('id')}")
                if not (step.get("video_mp4") and step.get("video_webm")):
                    add_error(f"Key animation for {slug} requires both video_mp4 and video_webm: {step.get('id')}")
                elif strict:
                    gif_ref = f"assets/{step.get('preview_gif')}"
                    mp4_ref = f"assets/{step.get('video_mp4')}"
                    webm_ref = f"assets/{step.get('video_webm')}"
                    if gif_ref not in readme_text:
                        add_error(f"Key animation for {slug} must reference GIF preview {gif_ref}: {step.get('id')}")
                    if not has_video_preview(readme_text, mp4_ref, webm_ref):
                        add_error(f"Key animation for {slug} must provide a local video preview for {mp4_ref}: {step.get('id')}")
                    github_video_url = step.get("github_video_url")
                    if not github_video_url:
                        if step.get("github_video_url_pending") is not True:
                            add_error(f"Key animation for {slug} missing github_video_url: {step.get('id')}")
                    else:
                        if not is_github_video_url(github_video_url):
                            add_error(f"Key animation for {slug} has invalid github_video_url: {step.get('id')}")
                        elif github_video_url not in readme_text:
                            add_error(f"Key animation for {slug} must reference github_video_url in README: {step.get('id')}")
                if step.get("media_provenance") == "static_pan_zoom":
                    add_error(f"Key animation for {slug} cannot use static_pan_zoom provenance: {step.get('id')}")
                if not has_real_controls(step, {"timeline", "parameter"}):
                    add_error(f"Key animation for {slug} needs real timeline/parameter controls: {step.get('id')}")
            if step.get("output_type") == "timeline_viewer" or any(control.get("role") == "parameter" for control in step.get("controls", [])):
                if not step.get("preview_gif"):
                    add_error(f"Timeline/parameter step for {slug} missing preview_gif: {step.get('id')}")
                if not (step.get("video_mp4") or step.get("video_webm")):
                    add_error(f"Timeline/parameter step for {slug} missing video_mp4/video_webm: {step.get('id')}")
                if not has_real_controls(step, {"timeline", "parameter"}):
                    add_error(f"Timeline/parameter step for {slug} needs real controls: {step.get('id')}")
            if step.get("media_role") not in {"key_visual", "key_animation", "supporting_evidence", "code_evidence"}:
                add_error(f"Media step for {slug} has unsupported media_role: {step.get('media_role')}")
            if step.get("output_type") not in {
                "log",
                "table",
                "plot",
                "viewer",
                "timeline_viewer",
                "widget_controls",
                "animation_viewer",
                "code_only",
                "latex",
                "formula",
                "matrix",
                "source_excerpt",
                "command_log",
                "artifact_summary",
                "diagram",
            }:
                add_error(f"Media step for {slug} has unsupported output_type: {step.get('output_type')}")
        if strict and key_media_section and legacy_video_link_pattern.search(key_media_section):
            add_error(f"Key media section for {slug} still uses link-only video open/download text.")

if errors:
    print("docs/blog check failed:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(f"docs/blog check passed for {len(target_cases)} managed AnimationPapers/Theory cases.")
if strict:
    print("Strict mode includes real-media provenance, capture-kind, and key visual/animation quality gates.")
'@

$pythonScript | python - "$PSScriptRoot" "$($Strict.IsPresent)"
exit $LASTEXITCODE
