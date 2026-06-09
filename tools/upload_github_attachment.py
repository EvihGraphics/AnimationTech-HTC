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
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ATTACHMENT_RE = re.compile(
    r"https://(?:github\.com/user-attachments/assets/[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
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


def write_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def insert_url_after_preview(readme_path: Path, preview_gif: str, url: str) -> None:
    text = readme_path.read_text(encoding="utf-8-sig")
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
        if line.strip().startswith("![") and preview_ref in line:
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


def missing_key_animation_targets(manifest: dict, root: Path) -> list[dict]:
    targets: list[dict] = []
    for case in manifest.get("cases", []):
        readme_path = root / case["blog_readme"]
        assets_dir = readme_path.parent / "assets"
        for step in case.get("steps", []):
            if step.get("media_role") != "key_animation" or step.get("github_video_url"):
                continue
            missing = [field for field in ("preview_gif", "video_mp4", "video_webm") if not step.get(field)]
            if missing:
                raise SystemExit(f"Key animation {case.get('slug')}:{step.get('id')} missing fields: {', '.join(missing)}")
            mp4_path = assets_dir / step["video_mp4"]
            gif_path = assets_dir / step["preview_gif"]
            webm_path = assets_dir / step["video_webm"]
            for path in (mp4_path, gif_path, webm_path):
                if not path.exists():
                    raise SystemExit(f"Expected media file does not exist: {path}")
            targets.append(
                {
                    "case_slug": case["slug"],
                    "step_id": step["id"],
                    "readme_path": readme_path,
                    "preview_gif": step["preview_gif"],
                    "video_mp4": step["video_mp4"],
                    "file_path": mp4_path,
                }
            )
    return targets


def backfill_many_docs(manifest_path: Path, targets: list[dict], urls: list[str], dry_run: bool) -> None:
    if len(targets) != len(urls):
        raise SystemExit(f"Target/URL count mismatch: {len(targets)} targets, {len(urls)} URLs")
    manifest = load_manifest(manifest_path)
    url_by_key = {(target["case_slug"], target["step_id"]): url for target, url in zip(targets, urls)}

    if dry_run:
        for target in targets:
            print(
                f"Would set github_video_url for {target['case_slug']}:{target['step_id']} "
                f"and insert after assets/{target['preview_gif']}"
            )
        return

    for target, url in zip(targets, urls):
        insert_url_after_preview(target["readme_path"], target["preview_gif"], url)

    for case in manifest.get("cases", []):
        for step in case.get("steps", []):
            key = (case.get("slug"), step.get("id"))
            if key in url_by_key:
                step["github_video_url"] = url_by_key[key]
    write_manifest(manifest_path, manifest)


def has_visible_textarea(page) -> bool:
    return page.locator("textarea:visible").count() > 0


def needs_login(page) -> bool:
    if "github.com/login" in page.url:
        return True
    if has_visible_textarea(page):
        return False
    try:
        if "page not found" in page.title().lower():
            return True
    except Exception:
        pass
    return page.locator("a[href*='/login']").count() > 0


def wait_for_login_if_needed(page, repo: str, headless: bool, timeout_seconds: int) -> None:
    if not needs_login(page):
        return
    if headless:
        raise SystemExit("GitHub login is required; rerun without --headless.")

    print("GitHub login is required. Complete login in the opened browser window.")
    page.goto(
        f"https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2F{repo}%2Fissues%2Fnew",
        wait_until="domcontentloaded",
        timeout=60_000,
    )
    page.wait_for_function(
        "() => !location.href.includes('/login') && !document.querySelector(\"a[href*='/login']\")",
        timeout=timeout_seconds * 1000,
    )


def current_git_branch(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    branch = result.stdout.strip()
    if not branch or branch == "HEAD":
        return None
    return branch


def markdown_editor_urls(repo: str, branch: str | None, base_branch: str, editor_url: str | None) -> list[str]:
    urls = []
    if editor_url:
        urls.append(editor_url)
    urls.append(f"https://github.com/{repo}/issues/new")
    if branch and branch != base_branch:
        urls.append(f"https://github.com/{repo}/compare/{base_branch}...{branch}?expand=1")
    return urls


def compare_url(repo: str, branch: str, base_branch: str) -> str:
    return f"https://github.com/{repo}/compare/{base_branch}...{branch}?expand=1"


def open_markdown_editor(
    page,
    repo: str,
    branch: str | None,
    base_branch: str,
    editor_url: str | None,
) -> None:
    """Open a GitHub Markdown editor without submitting anything."""

    for url in markdown_editor_urls(repo, branch, base_branch, editor_url):
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        if has_visible_textarea(page) or needs_login(page):
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
                    if has_visible_textarea(page) or needs_login(page):
                        return
            except Exception:
                continue


def public_attachment_available(url: str) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": "AnimationTech-HTC-docs-bot"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get("content-type", "")
            return response.status == 200 and content_type.lower().startswith("video/")
    except (urllib.error.URLError, TimeoutError):
        return False


def publish_attachment_in_pr(
    page,
    repo: str,
    branch: str | None,
    base_branch: str,
    url: str,
    title: str,
) -> str:
    if not branch or branch == base_branch:
        raise SystemExit("--publish-pr requires running from a pushed feature branch.")

    page.goto(compare_url(repo, branch, base_branch), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1000)
    if "/pull/" in page.url:
        return page.url

    title_input = page.locator("input[name='pull_request[title]']:visible").first
    body_input = page.locator("textarea[name='pull_request[body]']:visible").first
    title_input.wait_for(state="visible", timeout=30_000)
    body_input.wait_for(state="visible", timeout=30_000)
    title_input.fill(title)
    body_input.fill(
        "Attachment host for docs/blog video verification.\n\n"
        "This PR body intentionally publishes the GitHub attachment URL used by the README, "
        "so GitHub can render it as an inline video player.\n\n"
        f"{url}\n"
    )
    page.get_by_role("button", name="Create pull request").first.click(timeout=30_000)
    page.wait_for_url("**/pull/**", timeout=60_000)
    return page.url


def publish_attachment_urls_in_pr(
    page,
    repo: str,
    branch: str | None,
    base_branch: str,
    urls: list[str],
    title: str,
) -> str:
    if not branch or branch == base_branch:
        raise SystemExit("--publish-pr requires running from a pushed feature branch.")

    body_lines = [
        "Attachment host for docs/blog key animation video verification.",
        "",
        "This PR body/comment intentionally publishes the GitHub attachment URLs used by README key animations, so GitHub can render them as inline video players.",
        "",
    ]
    body_lines.extend(urls)
    body = "\n".join(body_lines) + "\n"

    if "/pull/" in page.url:
        comment_input = page.locator("textarea[name='comment[body]']:visible").first
        comment_input.wait_for(state="visible", timeout=30_000)
        comment_input.fill(body)
        page.get_by_role("button", name=re.compile(r"^Comment$", re.I)).first.click(timeout=30_000)
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        return page.url

    page.goto(compare_url(repo, branch, base_branch), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1000)
    if "/pull/" in page.url:
        comment_input = page.locator("textarea[name='comment[body]']:visible").first
        comment_input.wait_for(state="visible", timeout=30_000)
        comment_input.fill(body)
        page.get_by_role("button", name=re.compile(r"^Comment$", re.I)).first.click(timeout=30_000)
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        return page.url

    title_input = page.locator("input[name='pull_request[title]']:visible").first
    body_input = page.locator("textarea[name='pull_request[body]']:visible").first
    title_input.wait_for(state="visible", timeout=30_000)
    body_input.wait_for(state="visible", timeout=30_000)
    title_input.fill(title)
    body_input.fill(body)
    page.get_by_role("button", name="Create pull request").first.click(timeout=30_000)
    page.wait_for_url("**/pull/**", timeout=60_000)
    return page.url


def upload_with_playwright(
    repo: str,
    file_path: Path,
    profile_dir: Path,
    headless: bool,
    timeout_seconds: int,
    branch: str | None,
    base_branch: str,
    editor_url: str | None,
    publish_pr: bool,
    pr_title: str,
) -> str:
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
            open_markdown_editor(page, repo, branch, base_branch, editor_url)
            if needs_login(page):
                wait_for_login_if_needed(page, repo, headless, timeout_seconds)
                open_markdown_editor(page, repo, branch, base_branch, editor_url)

            editor_timeout_ms = max(30_000, timeout_seconds * 1000)
            textarea = page.locator("textarea:visible").first
            textarea.wait_for(state="visible", timeout=editor_timeout_ms)
            textarea.click()

            file_inputs = page.locator("input[type='file']")
            try:
                file_inputs.first.wait_for(state="attached", timeout=editor_timeout_ms)
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
                    url = match.group(0)
                    if publish_pr and not public_attachment_available(url):
                        pr_url = publish_attachment_in_pr(page, repo, branch, base_branch, url, pr_title)
                        print(f"Published attachment through PR: {pr_url}")
                        for _ in range(12):
                            if public_attachment_available(url):
                                break
                            page.wait_for_timeout(1000)
                        if not public_attachment_available(url):
                            raise SystemExit(f"Attachment URL is still not public after PR publish: {url}")
                    return url
                page.wait_for_timeout(1000)
            raise SystemExit("Timed out waiting for GitHub to insert the attachment URL.")
        finally:
            context.close()


def attachment_urls_in_text(page) -> list[str]:
    values = page.locator("textarea").evaluate_all("(nodes) => nodes.map((node) => node.value).join('\\n')")
    return ATTACHMENT_RE.findall(values)


def wait_for_new_attachment_url(page, known_urls: set[str], timeout_seconds: int) -> str:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        urls = attachment_urls_in_text(page)
        for url in urls:
            if url not in known_urls:
                return url
        page.wait_for_timeout(1000)
    raise SystemExit("Timed out waiting for GitHub to insert the attachment URL.")


def upload_many_with_playwright(
    repo: str,
    targets: list[dict],
    profile_dir: Path,
    headless: bool,
    timeout_seconds: int,
    branch: str | None,
    base_branch: str,
    editor_url: str | None,
    publish_pr: bool,
    pr_title: str,
) -> list[str]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - depends on local env
        raise SystemExit("Python Playwright is required. Install with: pip install playwright") from exc

    browser_executable = find_browser_executable()
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
            open_markdown_editor(page, repo, branch, base_branch, editor_url)
            if needs_login(page):
                wait_for_login_if_needed(page, repo, headless, timeout_seconds)
                open_markdown_editor(page, repo, branch, base_branch, editor_url)

            editor_timeout_ms = max(30_000, timeout_seconds * 1000)
            textarea = page.locator("textarea:visible").first
            textarea.wait_for(state="visible", timeout=editor_timeout_ms)
            file_inputs = page.locator("input[type='file']")
            try:
                file_inputs.first.wait_for(state="attached", timeout=editor_timeout_ms)
            except PlaywrightTimeoutError as exc:
                raise SystemExit(
                    "Could not find GitHub Markdown attachment file input. "
                    "Make sure the Markdown editor loaded."
                ) from exc

            known_urls = set(attachment_urls_in_text(page))
            uploaded_urls: list[str] = []
            for index, target in enumerate(targets, start=1):
                print(f"[{index}/{len(targets)}] Uploading {target['case_slug']}:{target['step_id']} -> {target['file_path'].name}")
                textarea.click()
                file_inputs.first.set_input_files(str(target["file_path"]))
                url = wait_for_new_attachment_url(page, known_urls, timeout_seconds)
                known_urls.add(url)
                uploaded_urls.append(url)
                print(url)

            if publish_pr and any(not public_attachment_available(url) for url in uploaded_urls):
                pr_url = publish_attachment_urls_in_pr(page, repo, branch, base_branch, uploaded_urls, pr_title)
                print(f"Published attachments through PR: {pr_url}")
                for url in uploaded_urls:
                    for _ in range(12):
                        if public_attachment_available(url):
                            break
                        page.wait_for_timeout(1000)
                    if not public_attachment_available(url):
                        raise SystemExit(f"Attachment URL is still not public after PR publish: {url}")
            return uploaded_urls
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
    parser.add_argument(
        "--all-missing-key-animations",
        action="store_true",
        help="Upload and backfill every key_animation step missing github_video_url.",
    )
    parser.add_argument(
        "--editor-url",
        help="Optional GitHub page with a Markdown attachment editor; useful when Issues are disabled.",
    )
    parser.add_argument("--base-branch", default="main", help="Base branch for compare-page upload fallback.")
    parser.add_argument(
        "--publish-pr",
        action="store_true",
        help="Create a PR body to publish draft-only attachment URLs when needed.",
    )
    parser.add_argument(
        "--pr-title",
        default="Footskate GitHub attachment video validation",
        help="Title to use when --publish-pr creates the attachment-host PR.",
    )
    parser.add_argument("--no-backfill", action="store_true", help="Only print the generated URL.")
    parser.add_argument("--dry-run", action="store_true", help="Validate targets without writing files.")
    parser.add_argument("--headless", action="store_true", help="Run browser headlessly. Only works if already logged in.")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--profile-dir", default=str(default_profile_dir()), help="Persistent browser profile directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    manifest_path = (root / args.manifest).resolve()
    if not manifest_path.exists():
        raise SystemExit(f"Manifest does not exist: {manifest_path}")

    if args.all_missing_key_animations:
        manifest = load_manifest(manifest_path)
        targets = missing_key_animation_targets(manifest, root)
        if not targets:
            print("No missing key_animation github_video_url entries.")
            return 0
        print(f"Missing key_animation github_video_url entries: {len(targets)}")
        for target in targets:
            print(f"- {target['case_slug']}:{target['step_id']} {target['file_path'].relative_to(root)}")
        if args.dry_run:
            backfill_many_docs(manifest_path, targets, ["https://github.com/user-attachments/assets/dry-run"] * len(targets), True)
            return 0
        branch = current_git_branch(root)
        urls = upload_many_with_playwright(
            args.repo,
            targets,
            Path(args.profile_dir).expanduser().resolve(),
            args.headless,
            args.timeout_seconds,
            branch,
            args.base_branch,
            args.editor_url,
            args.publish_pr,
            args.pr_title,
        )
        urls = [validate_attachment_url(url) for url in urls]
        backfill_many_docs(manifest_path, targets, urls, False)
        print(f"Backfilled {len(urls)} key_animation GitHub attachment URLs.")
        return 0

    file_path = (root / args.file).resolve()
    if not file_path.exists():
        raise SystemExit(f"Video file does not exist: {file_path}")

    if args.github_video_url:
        url = validate_attachment_url(args.github_video_url)
    elif args.dry_run:
        url = "https://github.com/user-attachments/assets/dry-run"
    else:
        branch = current_git_branch(root)
        url = upload_with_playwright(
            args.repo,
            file_path,
            Path(args.profile_dir).expanduser().resolve(),
            args.headless,
            args.timeout_seconds,
            branch,
            args.base_branch,
            args.editor_url,
            args.publish_pr,
            args.pr_title,
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
