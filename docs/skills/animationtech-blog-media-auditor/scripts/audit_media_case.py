#!/usr/bin/env python3
"""Inventory AnimationTech blog media for review and repair.

This script is intentionally read-only. It reports manifest/media/link issues
and obvious image risks so an agent can focus manual inspection on the right
case assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

VIDEO_ROOT_DEFAULT = Path(
    r"D:\Users\hi\Documents\SCU\Chaos\knowledge_base\raw\video\JeromeEippers\_video_mp4\AnimationTech"
)

ASSET_REF_PATTERN = re.compile(
    r"!\[[^\]]*\]\((assets/[^)]+)\)"
    r"|\[[^\]]+\]\((assets/[^)]+)\)"
    r"|(?:src|poster)=[\"'](assets/[^\"']+)[\"']",
    re.I,
)

POLLUTION_MARKERS = [
    "JupyterLab",
    "Jupyter Notebook",
    "Code cell",
    "Source excerpt",
    "Run All Cells",
    "Python 3",
    "Widget Javascript not detected",
]


def repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "docs" / "blog" / "media_manifest.json").exists():
            return candidate
    raise RuntimeError("Cannot find repo root containing docs/blog/media_manifest.json")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:24]
    except OSError:
        return None
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    return struct.unpack(">II", header[16:24])


def asset_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for match in ASSET_REF_PATTERN.finditer(text):
        refs.add(next(group for group in match.groups() if group))
    return refs


def declared_files(step: dict) -> list[tuple[str, str]]:
    keys = ["result_file", "card_file", "preview_gif", "video_mp4", "video_webm"]
    return [(key, step[key]) for key in keys if step.get(key)]


def transcript_stems(case: dict) -> list[str]:
    stems = []
    for source in case.get("transcript_sources", []):
        stems.append(Path(source).stem)
    return stems


def matching_video_files(video_root: Path, stem: str) -> dict[str, Path | None]:
    return {
        ".mp4": next(iter(video_root.glob(stem + ".mp4")), None),
        ".srt": next(iter(video_root.glob(stem + ".srt")), None),
    }


def embedded_pollution(path: Path) -> list[str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    text = raw.decode("latin-1", errors="ignore")
    return [marker for marker in POLLUTION_MARKERS if marker in text]


def file_digest(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def summarize_case(repo: Path, case: dict, video_root: Path) -> list[str]:
    lines: list[str] = []
    slug = case.get("slug", "<missing>")
    readme = repo / case.get("blog_readme", "")
    assets_dir = repo / case.get("assets_dir", "")
    asset_readme = assets_dir / "README.md"

    lines.append(f"## {slug}")
    lines.append(f"- readme: {readme.relative_to(repo) if readme.exists() else 'MISSING'}")
    lines.append(f"- assets: {assets_dir.relative_to(repo) if assets_dir.exists() else 'MISSING'}")

    if readme.exists():
        readme_text = read_text(readme)
        refs = asset_refs(readme_text)
    else:
        readme_text = ""
        refs = set()
    asset_text = read_text(asset_readme) if asset_readme.exists() else ""

    stems = transcript_stems(case)
    if not stems:
        lines.append("- transcript: MISSING manifest transcript_sources")
    for stem in stems:
        found = matching_video_files(video_root, stem)
        mp4 = "yes" if found[".mp4"] else "no"
        srt = "yes" if found[".srt"] else "no"
        lines.append(f"- evidence: {stem} mp4={mp4} srt={srt}")

    warnings: list[str] = []
    key_result_digests: dict[str, list[str]] = {}
    for step in case.get("steps", []):
        label = f"{step.get('id', '<missing-id>')} cell={step.get('cell_index', '-')}"
        role = step.get("media_role", "")
        capture_kind = step.get("capture_kind", "")
        provenance = step.get("media_provenance", "")
        if role in {"key_visual", "key_animation"} and provenance in {
            "learning_card",
            "derived_card_crop",
            "static_pan_zoom",
            "scroll_capture",
            "whole_cell",
        }:
            warnings.append(f"{label}: key media has risky provenance={provenance}")
        for key, name in declared_files(step):
            path = assets_dir / name
            ref = f"assets/{name}"
            if not path.exists():
                warnings.append(f"{label}: missing {key} {name}")
                continue
            if ref not in refs and key != "card_file":
                warnings.append(f"{label}: README does not reference {ref}")
            if asset_text and name not in asset_text:
                warnings.append(f"{label}: assets/README does not list {name}")
            if name.lower().endswith(".png"):
                size = png_size(path)
                if not size:
                    warnings.append(f"{label}: unreadable PNG {name}")
                else:
                    width, height = size
                    if key == "result_file" and (width < 320 or height < 160):
                        warnings.append(f"{label}: tiny result PNG {name} {width}x{height}")
                    if (
                        key == "result_file"
                        and role in {"key_visual", "key_animation"}
                        and capture_kind == "canvas"
                        and height < 360
                    ):
                        warnings.append(f"{label}: short key canvas {name} {width}x{height}")
                    if key == "result_file" and role in {"key_visual", "key_animation"} and height > width * 1.4:
                        warnings.append(f"{label}: tall key image may be scroll capture {name} {width}x{height}")
                markers = embedded_pollution(path)
                if markers:
                    warnings.append(f"{label}: PNG text markers {name}: {', '.join(markers)}")
            if key == "result_file" and role in {"key_visual", "key_animation"}:
                digest = file_digest(path)
                if digest:
                    key_result_digests.setdefault(digest, []).append(f"{step.get('id', '<missing-id>')}={name}")

    for duplicates in key_result_digests.values():
        if len(duplicates) > 1:
            warnings.append(f"duplicate key result bytes: {', '.join(duplicates)}")

    if warnings:
        lines.append("- warnings:")
        lines.extend(f"  - {warning}" for warning in warnings)
    else:
        lines.append("- warnings: none from static inventory")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", action="append", default=[], help="Case slug to audit; repeatable.")
    parser.add_argument("--exclude", action="append", default=[], help="Case slug to skip; repeatable.")
    parser.add_argument("--video-root", default=str(VIDEO_ROOT_DEFAULT))
    args = parser.parse_args()

    repo = repo_root(Path.cwd())
    manifest = json.loads(read_text(repo / "docs" / "blog" / "media_manifest.json"))
    wanted = set(args.slug)
    excluded = set(args.exclude)
    video_root = Path(args.video_root)

    cases = []
    for case in manifest.get("cases", []):
        slug = case.get("slug")
        if wanted and slug not in wanted:
            continue
        if slug in excluded:
            continue
        cases.append(case)

    if not cases:
        raise SystemExit("No matching cases.")

    output: list[str] = []
    for case in cases:
        output.extend(summarize_case(repo, case, video_root))
        output.append("")
    print("\n".join(output).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
