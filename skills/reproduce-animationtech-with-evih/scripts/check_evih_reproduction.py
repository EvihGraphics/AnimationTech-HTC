#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DEFAULT_CLI_FLAGS = ("--artifact", "--screenshot", "--frame", "--max-frames", "--width", "--height")


@dataclass
class Finding:
    level: str
    code: str
    message: str


def load_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except Exception as exc:
            raise SystemExit(f"Manifest is not JSON and PyYAML is unavailable: {path}") from exc
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise SystemExit(f"Manifest did not parse to an object: {path}")
        return data


def is_evih_slug(slug: str) -> bool:
    return slug.endswith("_evih")


def original_slug(slug: str) -> str:
    return slug[:-5] if is_evih_slug(slug) else slug


def evih_slug(slug: str) -> str:
    return slug if is_evih_slug(slug) else f"{slug}_evih"


def case_slug(case: dict[str, Any]) -> str:
    return str(case.get("slug", ""))


def path_value(item: Any) -> str | None:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("path"), str):
        return item["path"]
    return None


def find_case(cases: list[dict[str, Any]], query: str) -> dict[str, Any] | None:
    candidates = {query, evih_slug(query)}
    if is_evih_slug(query):
        candidates.add(original_slug(query))
    for case in cases:
        if case_slug(case) in candidates:
            if is_evih_slug(case_slug(case)) or is_evih_slug(query):
                return case
    for case in cases:
        if case_slug(case) == query:
            return case
    return None


def get_cases(data: dict[str, Any]) -> list[dict[str, Any]]:
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise SystemExit("Manifest does not contain a cases list.")
    result: list[dict[str, Any]] = []
    for item in cases:
        if isinstance(item, dict):
            result.append(item)
    return result


def viewer_candidates(repo_root: Path, case: dict[str, Any]) -> list[Path]:
    slug = case_slug(case)
    base = original_slug(slug)
    paths: list[Path] = []
    entry = case.get("entry")
    if isinstance(entry, str) and entry.endswith(".py"):
        paths.append(repo_root / entry)
    paths.append(repo_root / "labs" / "evih_reproductions" / "runner.py")
    paths.append(repo_root / "labs" / "evih_reproductions" / base / "viewer.py")
    if slug == "motion_graph_evih":
        paths.append(repo_root / "labs" / "AnimationPapers" / "evih_motion_graph" / "viewer.py")
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def check_png(path: Path, min_bytes: int) -> Finding | None:
    if not path.exists():
        return Finding("error", "screenshot-missing", f"Screenshot missing: {path}")
    if path.stat().st_size < min_bytes:
        return Finding("error", "screenshot-small", f"Screenshot too small: {path} ({path.stat().st_size} bytes)")
    with path.open("rb") as handle:
        if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            return Finding("error", "screenshot-not-png", f"Screenshot is not a PNG: {path}")
    return None


def check_artifact(path: Path, min_bytes: int) -> Finding | None:
    if not path.exists():
        return Finding("error", "artifact-missing", f"Artifact missing: {path}")
    if path.stat().st_size < min_bytes:
        return Finding("error", "artifact-small", f"Artifact too small: {path} ({path.stat().st_size} bytes)")
    return None


def add(finding_list: list[Finding], level: str, code: str, message: str) -> None:
    finding_list.append(Finding(level, code, message))


def check_viewer_source(path: Path, findings: list[Finding], strict: bool) -> None:
    if not path.exists():
        add(findings, "error" if strict else "warning", "viewer-missing", f"Viewer script not found: {path}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    contract_text = text
    for parent in path.parents:
        runner = parent / "runner.py"
        runtime = parent / "runtime.py"
        if runner.exists():
            contract_text += "\n" + runner.read_text(encoding="utf-8", errors="replace")
        if runtime.exists():
            contract_text += "\n" + runtime.read_text(encoding="utf-8", errors="replace")
    missing = [flag for flag in DEFAULT_CLI_FLAGS if flag not in contract_text]
    if missing:
        add(findings, "error" if strict else "warning", "viewer-cli", f"{path} missing CLI flags: {', '.join(missing)}")
    if "pyray" not in contract_text and "raylib" not in contract_text.lower():
        add(findings, "error" if strict else "warning", "viewer-raylib", f"{path} does not appear to use Raylib/pyray")


def check_case(
    repo_root: Path,
    case: dict[str, Any],
    require_artifacts: bool,
    require_screenshots: bool,
    strict: bool,
    allow_legacy_motion_graph: bool,
    min_artifact_bytes: int,
    min_screenshot_bytes: int,
) -> list[Finding]:
    findings: list[Finding] = []
    slug = case_slug(case)
    if not is_evih_slug(slug):
        add(findings, "error", "not-evih", f"Case is not an Evih reproduction slug: {slug}")
        return findings

    entry = case.get("entry")
    if not isinstance(entry, str) or not entry:
        add(findings, "error", "entry-missing", f"{slug}: missing entry")
    else:
        entry_path = repo_root / entry
        if not entry_path.exists():
            add(findings, "error", "entry-not-found", f"{slug}: entry not found: {entry_path}")

    template = str(case.get("template", ""))
    if template != "papers-evih":
        add(findings, "error" if strict else "warning", "template", f"{slug}: expected template papers-evih, got {template!r}")

    python_version = str(case.get("python_version", ""))
    if python_version and python_version != "3.12":
        add(findings, "warning", "python-version", f"{slug}: expected Python 3.12, got {python_version}")
    if strict and not python_version:
        add(findings, "error", "python-version-missing", f"{slug}: python_version should be 3.12")

    kind = str(case.get("kind", ""))
    if kind != "python_script":
        legacy_motion_graph = allow_legacy_motion_graph and slug == "motion_graph_evih" and kind == "notebook"
        if legacy_motion_graph:
            add(findings, "warning", "kind", f"{slug}: legacy template uses notebook wrapper; newer cases should prefer python_script")
        else:
            add(findings, "error" if strict else "warning", "kind", f"{slug}: preferred kind is python_script, got {kind!r}")

    artifacts = case.get("generated_artifacts") or []
    artifact_paths: list[Path] = []
    if isinstance(artifacts, list):
        for item in artifacts:
            value = path_value(item)
            if value:
                artifact_paths.append(repo_root / value)
    if not artifact_paths:
        add(findings, "warning", "artifact-declared", f"{slug}: no generated_artifacts declared")
    if require_artifacts:
        for artifact in artifact_paths:
            finding = check_artifact(artifact, min_artifact_bytes)
            if finding:
                findings.append(finding)

    viewers = viewer_candidates(repo_root, case)
    existing_viewer = next((path for path in viewers if path.exists()), viewers[0])
    check_viewer_source(existing_viewer, findings, strict)

    if require_screenshots:
        visual_dir = repo_root / ".reports" / "visual-checks" / slug
        pngs = sorted(visual_dir.glob("*.png")) if visual_dir.exists() else []
        if not pngs:
            add(findings, "error", "screenshot-missing", f"{slug}: no PNG screenshots found under {visual_dir}")
        for png in pngs:
            finding = check_png(png, min_screenshot_bytes)
            if finding:
                findings.append(finding)

    return findings


def matrix_findings(cases: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    slugs = {case_slug(case) for case in cases}
    originals = sorted(slug for slug in slugs if slug and not is_evih_slug(slug))
    missing = [slug for slug in originals if evih_slug(slug) not in slugs]
    for slug in missing:
        add(findings, "error", "matrix-missing", f"Missing Evih reproduction case: {evih_slug(slug)}")
    return findings


def print_text(targets: list[dict[str, Any]], findings_by_slug: dict[str, list[Finding]], matrix: list[Finding]) -> None:
    if targets:
        print("Checked Evih cases:")
        for case in targets:
            slug = case_slug(case)
            errors = sum(1 for item in findings_by_slug[slug] if item.level == "error")
            warnings = sum(1 for item in findings_by_slug[slug] if item.level == "warning")
            print(f"  {slug}: {errors} error(s), {warnings} warning(s)")
    if matrix:
        print("Matrix findings:")
        for finding in matrix:
            print(f"  [{finding.level}] {finding.code}: {finding.message}")
    for slug, findings in findings_by_slug.items():
        for finding in findings:
            print(f"[{finding.level}] {slug} {finding.code}: {finding.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only checker for AnimationTech Evih/Raylib reproductions.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--manifest", default="tools/cases.yaml", help="Manifest path relative to repo root.")
    parser.add_argument("--case", action="append", default=[], help="Original or Evih slug to check. Repeatable.")
    parser.add_argument("--list", action="store_true", help="List original and Evih cases, then exit.")
    parser.add_argument("--expect-full-matrix", action="store_true", help="Require every original case to have a *_evih case.")
    parser.add_argument("--strict", action="store_true", help="Require the standard python_script + conventional viewer shape.")
    parser.add_argument("--disallow-legacy-motion-graph", action="store_true", help="Treat the existing motion_graph_evih notebook wrapper as an error in strict mode.")
    parser.add_argument("--require-artifacts", action="store_true", help="Require declared generated artifacts to exist.")
    parser.add_argument("--require-screenshots", action="store_true", help="Require PNG screenshots under .reports/visual-checks/<slug>.")
    parser.add_argument("--min-artifact-bytes", type=int, default=128)
    parser.add_argument("--min-screenshot-bytes", type=int, default=1024)
    parser.add_argument("--warnings-as-errors", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    data = load_manifest(manifest_path)
    cases = get_cases(data)
    evih_cases = [case for case in cases if is_evih_slug(case_slug(case))]

    if args.list:
        originals = sorted(case_slug(case) for case in cases if case_slug(case) and not is_evih_slug(case_slug(case)))
        evihs = sorted(case_slug(case) for case in evih_cases)
        payload = {"original_cases": originals, "evih_cases": evihs}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("Original cases:")
            for slug in originals:
                print(f"  {slug}")
            print("Evih cases:")
            for slug in evihs:
                print(f"  {slug}")
        return 0

    if args.case:
        targets: list[dict[str, Any]] = []
        for query in args.case:
            found = find_case(cases, query)
            if found is None or not is_evih_slug(case_slug(found)):
                targets.append({"slug": evih_slug(query), "_missing": True})
            else:
                targets.append(found)
    else:
        targets = evih_cases

    findings_by_slug: dict[str, list[Finding]] = {}
    for case in targets:
        slug = case_slug(case)
        if case.get("_missing"):
            findings_by_slug[slug] = [Finding("error", "case-missing", f"Evih case not found in manifest: {slug}")]
            continue
        findings_by_slug[slug] = check_case(
            repo_root=repo_root,
            case=case,
            require_artifacts=args.require_artifacts,
            require_screenshots=args.require_screenshots,
            strict=args.strict,
            allow_legacy_motion_graph=not args.disallow_legacy_motion_graph,
            min_artifact_bytes=args.min_artifact_bytes,
            min_screenshot_bytes=args.min_screenshot_bytes,
        )

    matrix = matrix_findings(cases) if args.expect_full_matrix else []
    all_findings = matrix + [finding for findings in findings_by_slug.values() for finding in findings]
    has_errors = any(finding.level == "error" for finding in all_findings)
    has_warnings = any(finding.level == "warning" for finding in all_findings)

    if args.json:
        payload = {
            "repo_root": str(repo_root),
            "manifest": str(manifest_path),
            "checked": [
                {
                    "slug": slug,
                    "findings": [finding.__dict__ for finding in findings],
                }
                for slug, findings in findings_by_slug.items()
            ],
            "matrix_findings": [finding.__dict__ for finding in matrix],
            "ok": not has_errors and not (args.warnings_as_errors and has_warnings),
        }
        print(json.dumps(payload, indent=2))
    else:
        print_text(targets, findings_by_slug, matrix)
        if not all_findings:
            print("No findings.")

    if has_errors or (args.warnings_as_errors and has_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
