#!/usr/bin/env python
"""Upload a blog video through GitHub's Markdown attachment flow.

GitHub renders videos in README pages when they use a GitHub attachment URL
(`https://github.com/user-attachments/assets/...`). Repository-relative
`<video src="assets/...">` is useful for local preview, but GitHub strips it
from rendered README HTML. This tool automates the browser upload path and can
also backfill an already-known attachment URL into the blog README and media
manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path


ATTACHMENT_RE = re.compile(
    r"https://(?:github\.com/user-attachments/assets/[A-Za-z0-9_-]+"
    r"|user-images\.githubusercontent\.com/[^\s<>)\"']+\.(?:mp4|webm|mov))",
    re.I,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_profile_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "AnimationTechHTC" / "github-attachment-profile"
    return Path.home() / ".cache" / "animationtech-htc" / "github-attachment-profile"


def find_browser_executable() -> str | None:
    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def validate_attachment_url(value: str) -> str:
    match = ATTACHMENT_RE.search(value.strip())
    if not match:
        raise ValueError(
            "Expected a GitHub attachment or user-images video URL, "
            "for example https://github.com/user-attachments/assets/<uuid>."
        )
    return match.group(0)


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_case_and_step(manifest: dict, case_slug: str, step_id: str | None, video_name: str | None) -> tuple[dict, dict]:
    for case in manifest.get("cases", []):
        if case.get("slug") != case_slug:
            continue
        if step_id:
            for step in case.get("steps", []):
                if step.get("id") == step_id:
                    return case, step
            raise SystemExit(f"Step id not found in media manifest for {case_slug}: {step_id}")
        if video_name:
            for step in case.get("steps", []):
                if step.get("video_mp4") == video_name or step.get("video_webm") == video_name:
                    return case, step
        key_animations = [step for step in case.get("steps", []) if step.get("media_role") == "key_animation"]
        if len(key_animations) == 1:
            return case, key_animations[0]
        raise SystemExit(
            f"Cannot infer step for {case_slug}; pass --step-id. "
            f"Found {len(key_animations)} key animations."
        )
    raise SystemExit(f"Case slug not found in media manifest: {case_slug}")


def update_manifest(path: Path, manifest: dict, case_slug: str, step_id: str, url: str) -> None:
    updated = False
    for case in manifest.get("cases", []):
        if case.get("slug") != case_slug:
            continue
        for step in case.get("steps", []):
            if step.get("id") == step_id:
                step["github_video_url"] = url
                updated = True
                break
    if not updated:
        raise SystemExit(f"Could not update manifest step {case_slug}:{step_id}")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def insert_url_after_preview(readme_path: Path, preview_gif: str, url: str) -> None:
    text = readme_path.read_text(encoding="utf-8-sig")
    if url in text:
        return
    preview_ref = f"assets/{preview_gif}"
    if preview_ref not in text:
        raise SystemExit(f"README does not reference preview GIF {preview_ref}: {readme_path}")

    lines = text.splitlines()
    output: list[str] = []
    inserted = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        output.append(line)
        if preview_ref in line:
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].strip() == "":
                output.append(lines[cursor])
                cursor += 1
            if cursor < len(lines) and ATTACHMENT_RE.fullmatch(lines[cursor].strip()):
                output.append(url)
                index = cursor + 1
                inserted += 1
                continue
            output.append("")
            output.append(url)
            inserted += 1
        index += 1

    if inserted == 0:
        raise SystemExit(f"Did not find a place to insert {url} in {readme_path}")
    readme_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def backfill_docs(manifest_path: Path, case_slug: str, step_id: str | None, file_path: Path, url: str, dry_run: bool) -> tuple[Path, str]:
    manifest = load_manifest(manifest_path)
    case, step = find_case_and_step(manifest, case_slug, step_id, file_path.name)
    resolved_step_id = step.get("id")
    if not resolved_step_id:
        raise SystemExit("Matched manifest step is missing id.")
    readme_path = repo_root() / case["blog_readme"]
    preview_gif = step.get("preview_gif")
    if not preview_gif:
        raise SystemExit(f"Matched step has no preview_gif: {case_slug}:{resolved_step_id}")

    if dry_run:
        print(f"Would set github_video_url for {case_slug}:{resolved_step_id}")
        print(f"Would insert URL after assets/{preview_gif} in {readme_path}")
        return readme_path, resolved_step_id

    insert_url_after_preview(readme_path, preview_gif, url)
    update_manifest(manifest_path, manifest, case_slug, resolved_step_id, url)
    return readme_path, resolved_step_id


def open_issue_markdown_editor(page, repo: str) -> None:
    """Open a GitHub Markdown editor without creating any issue."""

    page.goto(f"https://github.com/{repo}/issues/new", wait_until="domcontentloaded", timeout=60_000)
    if page.locator("textarea").count() > 0:
        return

    blank_issue_links = [
        page.get_by_role("link", name=re.compile(r"open a blank issue", re.I)),
        page.get_by_role("link", name=re.compile(r"blank issue", re.I)),
        page.get_by_role("link", name=re.compile(r"get started", re.I)).first,
    ]
    for link in blank_issue_links:
        try:
            if link.count() > 0:
                link.click(timeout=5_000)
                page.wait_for_load_state("domcontentloaded", timeout=30_000)
                if page.locator("textarea").count() > 0:
                    return
        except Exception:
            continue

    page.goto(f"https://github.com/{repo}/issues/new?body=", wait_until="domcontentloaded", timeout=60_000)


def upload_with_playwright(repo: str, file_path: Path, profile_dir: Path, headless: bool, timeout_seconds: int) -> str:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on local env
        raise SystemExit("Python Playwright is required. Install with: pip install playwright") from exc

    browser_executable = find_browser_executable()
    deadline = time.monotonic() + timeout_seconds
    with sync_playwright() as playwright:
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": headless,
            "accept_downloads": False,
        }
        if browser_executable:
            launch_kwargs["executable_path"] = browser_executable
        context = playwright.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            open_issue_markdown_editor(page, repo)
            if "login" in page.url:
                if headless:
                    raise SystemExit("GitHub login is required; rerun without --headless.")
                print("GitHub login is required. Complete login in the opened browser window.")
                page.wait_for_url(lambda url: "login" not in url, timeout=timeout_seconds * 1000)
                open_issue_markdown_editor(page, repo)

            textarea = page.locator("textarea").first
            textarea.wait_for(state="attached", timeout=30_000)
            textarea.click()

            file_inputs = page.locator("input[type='file']")
            try:
                file_inputs.first.wait_for(state="attached", timeout=15_000)
            except PlaywrightTimeoutError as exc:
                raise SystemExit(
                    "Could not find GitHub Markdown attachment file input. "
                    "Make sure Issues are enabled and the Markdown editor loaded."
                ) from exc
            file_inputs.first.set_input_files(str(file_path))

            while time.monotonic() < deadline:
                values = page.locator("textarea").evaluate_all("(nodes) => nodes.map((node) => node.value).join('\\n')")
                match = ATTACHMENT_RE.search(values)
                if match:
                    return match.group(0)
                page.wait_for_timeout(1000)
            raise SystemExit("Timed out waiting for GitHub to insert the attachment URL.")
        finally:
            context.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="EvihGraphics/AnimationTech-HTC", help="GitHub repo in owner/name form.")
    parser.add_argument(
        "--file",
        default="docs/blog/AnimationPapers/footskate_cleanup_for_motion_capture_editing/assets/06_final_processing_compare_preview.mp4",
        help="Video file to upload.",
    )
    parser.add_argument("--case-slug", default="footskate_cleanup_for_motion_capture_editing")
    parser.add_argument("--step-id", default="final-processing", help="media_manifest step id.")
    parser.add_argument("--manifest", default="docs/blog/media_manifest.json")
    parser.add_argument("--github-video-url", help="Skip upload and backfill this existing attachment URL.")
    parser.add_argument("--no-backfill", action="store_true", help="Only print the generated URL.")
    parser.add_argument("--dry-run", action="store_true", help="Validate targets without writing files.")
    parser.add_argument("--headless", action="store_true", help="Run browser headlessly. Only works if already logged in.")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--profile-dir", default=str(default_profile_dir()), help="Persistent browser profile directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    file_path = (root / args.file).resolve()
    manifest_path = (root / args.manifest).resolve()
    if not file_path.exists():
        raise SystemExit(f"Video file does not exist: {file_path}")
    if not manifest_path.exists():
        raise SystemExit(f"Manifest does not exist: {manifest_path}")

    if args.github_video_url:
        url = validate_attachment_url(args.github_video_url)
    elif args.dry_run:
        url = "https://github.com/user-attachments/assets/dry-run"
    else:
        url = upload_with_playwright(
            args.repo,
            file_path,
            Path(args.profile_dir).expanduser().resolve(),
            args.headless,
            args.timeout_seconds,
        )
        url = validate_attachment_url(url)

    print(url)
    if not args.no_backfill:
        readme_path, step_id = backfill_docs(manifest_path, args.case_slug, args.step_id, file_path, url, args.dry_run)
        action = "Validated backfill target" if args.dry_run else "Backfilled"
        print(f"{action} {args.case_slug}:{step_id}")
        print(readme_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
