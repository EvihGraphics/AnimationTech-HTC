param(
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    Write-Error "python was not found on PATH; docs/blog report requires Python."
    exit 1
}

$pythonScript = @'
import json
import re
import sys
from collections import Counter
from pathlib import Path

blog_root = Path(sys.argv[1]).resolve()
json_mode = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
repo_root = blog_root.parents[1]

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
key_media_roles = {"key_visual", "key_animation"}
forbidden_key_provenance = {
    "curated_algorithm_visual",
    "derived_card_crop",
    "learning_card",
    "scroll_capture",
    "whole_cell",
    "browser_page",
    "static_pan_zoom",
}
footskate_slug = "footskate_cleanup_for_motion_capture_editing"
footskate_key_provenance_allowlist = {"live_canvas", "executed_plot_image"}
forbidden_key_provenance_prefixes = ("curated", "derived", "static")

def is_forbidden_key_provenance(provenance):
    if provenance in (None, ""):
        return False
    value = str(provenance)
    return value in forbidden_key_provenance or value.startswith(forbidden_key_provenance_prefixes)

def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig")

def fmt_bytes(value):
    value = float(value)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024

def count_mermaid(text):
    return text.count("```mermaid")

def count_cell_mermaid(text):
    pattern = re.compile(r"^### (?:Cell|[A-Za-z0-9_-]+).*?(?=^### |\Z)", re.M | re.S)
    return sum(1 for block in pattern.findall(text) if "```mermaid" in block)

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

def asset_refs_in_text(text):
    for match in asset_ref_pattern.finditer(text):
        yield next(group for group in match.groups() if group)

def html_video_blocks(text):
    return re.findall(r"<video\b[^>]*>.*?</video>", text, flags=re.I | re.S)

def direct_src_video_blocks(text):
    return re.findall(r"<video\b[^>]*\bsrc=[\"'][^\"']+[\"'][^>]*>.*?</video>", text, flags=re.I | re.S)

def github_attachment_video_urls(text):
    pattern = re.compile(
        r"https://(?:github\.com/user-attachments/assets/[A-Za-z0-9_-]+|user-images\.githubusercontent\.com/[^\s<>)\"']+\.(?:mp4|webm|mov))",
        re.I,
    )
    return pattern.findall(text)

manifest = json.loads(read_text(cases_path))
media_manifest = json.loads(read_text(media_manifest_path))

target_cases = [
    case for case in manifest["cases"]
    if case["entry"].startswith("labs/AnimationPapers/")
    or case["entry"].startswith("labs/Theory/")
]
target_by_slug = {case["slug"]: case for case in target_cases}
media_cases = media_manifest.get("cases", [])

issues = []
top_readme = blog_root / "README.md"
top_text = read_text(top_readme) if top_readme.exists() else ""

group_counts = Counter()
kind_counts = Counter()
status_counts = Counter()
for case in target_cases:
    group = "AnimationPapers" if case["entry"].startswith("labs/AnimationPapers/") else "Theory"
    group_counts[group] += 1
    kind_counts[case.get("kind", "notebook")] += 1
    if case["slug"] in deep_slugs:
        status_counts["deep_written_media_complete"] += 1
    else:
        status_counts["media_complete_publish_base"] += 1

    top_ref = f"{group}/{case['slug']}/README.md"
    if top_ref not in top_text:
        issues.append(f"Top README does not link {top_ref}")

    group_readme = blog_root / group / "README.md"
    if group_readme.exists():
        group_text = read_text(group_readme)
        group_ref = f"{case['slug']}/README.md"
        if group_ref not in group_text:
            issues.append(f"{group}/README.md does not link {group_ref}")
    else:
        issues.append(f"Missing group README: {group_readme}")

step_count = 0
png_count = 0
webm_count = 0
gif_count = 0
mp4_count = 0
png_bytes = 0
webm_bytes = 0
gif_bytes = 0
mp4_bytes = 0
output_types = Counter()
media_roles = Counter()
capture_kinds = Counter()
media_provenance = Counter()
key_media_provenance = Counter()
footskate_key_media_provenance = Counter()
key_forbidden_fallback_count = 0
footskate_forbidden_fallback_count = 0
footskate_non_allowlisted_count = 0
key_missing_provenance_count = 0
key_missing_required_metadata_count = 0
mermaid_counts = {}
cell_mermaid_counts = {}
unreferenced_assets = []
extra_assets = []
embedded_video_count = 0
direct_src_video_count = 0
github_attachment_video_count = 0
legacy_link_only_video_count = 0
embedded_webm_without_mp4_companion_count = 0

for case in media_cases:
    slug = case.get("slug", "<unknown>")
    readme = repo_root / case.get("blog_readme", "")
    assets_dir = repo_root / case.get("assets_dir", "")
    asset_readme = assets_dir / "README.md"
    video_file = media_manifest.get("video", {}).get("file", "00-walkthrough.webm")
    expected_files = set()
    for step in case.get("steps", []):
        for key in ("result_file", "card_file", "preview_gif", "video_mp4", "video_webm"):
            if step.get(key):
                expected_files.add(step.get(key))
    walkthrough_conf = case.get("walkthrough", {})
    expected_files.add(walkthrough_conf.get("webm") or video_file)
    if walkthrough_conf.get("mp4"):
        expected_files.add(walkthrough_conf.get("mp4"))
    optional_readme_files = {walkthrough_conf.get("webm") or video_file}
    if walkthrough_conf.get("mp4"):
        optional_readme_files.add(walkthrough_conf.get("mp4"))

    step_count += len(case.get("steps", []))
    output_types.update(step.get("output_type", "<missing>") for step in case.get("steps", []))
    media_roles.update(step.get("media_role", "<missing>") for step in case.get("steps", []))
    capture_kinds.update(step.get("capture_kind", "<missing>") for step in case.get("steps", []))
    media_provenance.update(step.get("media_provenance", "<missing>") for step in case.get("steps", []))
    for step in case.get("steps", []):
        role = step.get("media_role")
        provenance = step.get("media_provenance", "<missing>")
        if role in key_media_roles:
            key_media_provenance[provenance] += 1
            if provenance == "<missing>":
                key_missing_provenance_count += 1
            if is_forbidden_key_provenance(provenance):
                key_forbidden_fallback_count += 1
            if slug == footskate_slug:
                footskate_key_media_provenance[provenance] += 1
                if is_forbidden_key_provenance(provenance):
                    footskate_forbidden_fallback_count += 1
                if provenance not in footskate_key_provenance_allowlist:
                    footskate_non_allowlisted_count += 1
            for field in ("visual_subject", "capture_kind", "capture_selector", "publish_media_required"):
                if field not in step:
                    key_missing_required_metadata_count += 1

    readme_text = read_text(readme) if readme.exists() else ""
    asset_text = read_text(asset_readme) if asset_readme.exists() else ""
    mermaid_counts[slug] = count_mermaid(readme_text)
    cell_mermaid_counts[slug] = count_cell_mermaid(readme_text)
    video_blocks = html_video_blocks(readme_text)
    embedded_video_count += len(video_blocks)
    direct_src_video_count += len(direct_src_video_blocks(readme_text))
    github_attachment_video_count += len(github_attachment_video_urls(readme_text))
    legacy_link_only_video_count += len(legacy_video_link_pattern.findall(readme_text))
    embedded_webm_without_mp4_companion_count += sum(
        1 for block in video_blocks if ".webm" in block.lower() and ".mp4" not in block.lower()
    )
    linked_assets = {
        Path(asset_ref).name
        for asset_ref in asset_refs_in_text(readme_text)
    }

    for file_name in expected_files:
        media_path = assets_dir / file_name
        if not media_path.exists():
            issues.append(f"Missing media for {slug}: {media_path}")
            continue
        if file_name not in optional_readme_files and file_name not in linked_assets:
            issues.append(f"README for {slug} does not link assets/{file_name}")
        if file_name not in asset_text:
            issues.append(f"assets README for {slug} does not list {file_name}")
        if file_name.lower().endswith(".png"):
            png_count += 1
            png_bytes += media_path.stat().st_size
        elif file_name.lower().endswith(".gif"):
            gif_count += 1
            gif_bytes += media_path.stat().st_size
        elif file_name.lower().endswith(".mp4"):
            mp4_count += 1
            mp4_bytes += media_path.stat().st_size
        elif file_name.lower().endswith(".webm"):
            webm_count += 1
            webm_bytes += media_path.stat().st_size

    if assets_dir.exists():
        for media_path in sorted(assets_dir.iterdir()):
            if media_path.suffix.lower() not in {".png", ".gif", ".mp4", ".webm"}:
                continue
            if media_path.name not in expected_files:
                extra_assets.append(str(media_path.relative_to(repo_root)))
            if media_path.name not in linked_assets and media_path.name not in asset_text:
                unreferenced_assets.append(str(media_path.relative_to(repo_root)))

report = {
    "managed_cases": len(target_cases),
    "groups": dict(group_counts),
    "kinds": dict(kind_counts),
    "publish_status": dict(status_counts),
    "media": {
        "learning_steps": step_count,
        "png_count": png_count,
        "png_bytes": png_bytes,
        "gif_count": gif_count,
        "gif_bytes": gif_bytes,
        "mp4_count": mp4_count,
        "mp4_bytes": mp4_bytes,
        "webm_count": webm_count,
        "webm_bytes": webm_bytes,
        "output_types": dict(output_types),
        "media_roles": dict(media_roles),
        "capture_kinds": dict(capture_kinds),
        "media_provenance": dict(media_provenance),
        "key_media_provenance": dict(key_media_provenance),
        "key_forbidden_fallback_count": key_forbidden_fallback_count,
        "footskate_key_media_provenance": dict(footskate_key_media_provenance),
        "footskate_forbidden_fallback_count": footskate_forbidden_fallback_count,
        "footskate_non_allowlisted_count": footskate_non_allowlisted_count,
        "key_missing_provenance_count": key_missing_provenance_count,
        "key_missing_required_metadata_count": key_missing_required_metadata_count,
        "embedded_video_count": embedded_video_count,
        "direct_src_video_count": direct_src_video_count,
        "github_attachment_video_count": github_attachment_video_count,
        "legacy_link_only_video_count": legacy_link_only_video_count,
        "embedded_webm_without_mp4_companion_count": embedded_webm_without_mp4_companion_count,
    },
    "mermaid": {
        "case_blocks": mermaid_counts,
        "cell_blocks": cell_mermaid_counts,
    },
    "issues": issues,
    "extra_assets": extra_assets,
    "unreferenced_assets": unreferenced_assets,
}

if json_mode:
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0)

print("docs/blog publish report")
print("========================")
print(f"Managed cases: {len(target_cases)}")
print("Groups: " + ", ".join(f"{key}={value}" for key, value in sorted(group_counts.items())))
print("Kinds: " + ", ".join(f"{key}={value}" for key, value in sorted(kind_counts.items())))
print("Publish status: " + ", ".join(f"{key}={value}" for key, value in sorted(status_counts.items())))
print(f"Learning steps: {step_count}")
print(f"PNG media: {png_count} ({fmt_bytes(png_bytes)})")
print(f"GIF previews: {gif_count} ({fmt_bytes(gif_bytes)})")
print(f"MP4 videos: {mp4_count} ({fmt_bytes(mp4_bytes)})")
print(f"WebM videos: {webm_count} ({fmt_bytes(webm_bytes)})")
print(f"Embedded video tags: {embedded_video_count}")
print(f"Direct-src local video tags: {direct_src_video_count}")
print(f"GitHub attachment video URLs: {github_attachment_video_count}")
print(f"Legacy link-only video opens: {legacy_link_only_video_count}")
print(f"Embedded WebM without MP4 companion: {embedded_webm_without_mp4_companion_count}")
print("Output types:")
for key, value in sorted(output_types.items()):
    print(f" - {key}: {value}")
print("Media roles:")
for key, value in sorted(media_roles.items()):
    print(f" - {key}: {value}")
print("Capture kinds:")
for key, value in sorted(capture_kinds.items()):
    print(f" - {key}: {value}")
print("Media provenance:")
for key, value in sorted(media_provenance.items()):
    print(f" - {key}: {value}")
print("Key visual/animation provenance:")
for key, value in sorted(key_media_provenance.items()):
    print(f" - {key}: {value}")
print(f"Key visual/animation forbidden fallback count: {key_forbidden_fallback_count} (target 0)")
print("Footskate key media provenance:")
for key, value in sorted(footskate_key_media_provenance.items()):
    print(f" - {key}: {value}")
print(f"Footskate forbidden fallback count: {footskate_forbidden_fallback_count} (target 0)")
print(f"Footskate non-allowlisted key media count: {footskate_non_allowlisted_count} (target 0)")
print(f"Key visual/animation missing provenance count: {key_missing_provenance_count} (target 0)")
print(f"Key visual/animation missing required metadata fields: {key_missing_required_metadata_count} (target 0)")
print("Mermaid coverage:")
print(f" - case-level blocks: {sum(mermaid_counts.values())}")
print(f" - cell-level blocks: {sum(cell_mermaid_counts.values())}")

if extra_assets:
    print("Extra media files not declared in media_manifest.json:")
    for item in extra_assets:
        print(f" - {item}")
else:
    print("Extra media files not declared in media_manifest.json: 0")

if unreferenced_assets:
    print("Unreferenced media files:")
    for item in unreferenced_assets:
        print(f" - {item}")
else:
    print("Unreferenced media files: 0")

if issues:
    print("Potential issues:")
    for issue in issues:
        print(f" - {issue}")
else:
    print("Potential issues: 0")
'@

$pythonScript | python - "$PSScriptRoot" "$($Json.IsPresent)"
exit $LASTEXITCODE
