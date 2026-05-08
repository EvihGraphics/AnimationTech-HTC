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

gold_slugs = {
    "animation_format",
    "footskate_cleanup_for_motion_capture_editing",
    "motion_matching",
    "motion_graph",
    "real_time_planning_for_parameterized_human_motion",
    "curve_and_spline",
}

def read_text(path):
    return Path(path).read_text(encoding="utf-8-sig")

def fmt_bytes(value):
    value = float(value)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024

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
    if case["slug"] in gold_slugs:
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
png_bytes = 0
webm_bytes = 0
output_types = Counter()
unreferenced_assets = []
extra_assets = []

asset_link_pattern = re.compile(r"(?:!\[[^\]]*\]|\[[^\]]+\])\((assets/[^)]+)\)")

for case in media_cases:
    slug = case.get("slug", "<unknown>")
    readme = repo_root / case.get("blog_readme", "")
    assets_dir = repo_root / case.get("assets_dir", "")
    asset_readme = assets_dir / "README.md"
    video_file = media_manifest.get("video", {}).get("file", "00-walkthrough.webm")
    expected_files = {step.get("file") for step in case.get("steps", []) if step.get("file")}
    expected_files.add(video_file)

    step_count += len(case.get("steps", []))
    output_types.update(step.get("output_type", "<missing>") for step in case.get("steps", []))

    readme_text = read_text(readme) if readme.exists() else ""
    asset_text = read_text(asset_readme) if asset_readme.exists() else ""
    linked_assets = {
        Path(match.group(1)).name
        for match in asset_link_pattern.finditer(readme_text)
    }

    for file_name in expected_files:
        media_path = assets_dir / file_name
        if not media_path.exists():
            issues.append(f"Missing media for {slug}: {media_path}")
            continue
        if file_name not in linked_assets:
            issues.append(f"README for {slug} does not link assets/{file_name}")
        if file_name not in asset_text:
            issues.append(f"assets README for {slug} does not list {file_name}")
        if file_name.lower().endswith(".png"):
            png_count += 1
            png_bytes += media_path.stat().st_size
        elif file_name.lower().endswith(".webm"):
            webm_count += 1
            webm_bytes += media_path.stat().st_size

    if assets_dir.exists():
        for media_path in sorted(assets_dir.iterdir()):
            if media_path.suffix.lower() not in {".png", ".webm"}:
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
        "webm_count": webm_count,
        "webm_bytes": webm_bytes,
        "output_types": dict(output_types),
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
print(f"PNG cards: {png_count} ({fmt_bytes(png_bytes)})")
print(f"WebM walkthroughs: {webm_count} ({fmt_bytes(webm_bytes)})")
print("Output types:")
for key, value in sorted(output_types.items()):
    print(f" - {key}: {value}")

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
