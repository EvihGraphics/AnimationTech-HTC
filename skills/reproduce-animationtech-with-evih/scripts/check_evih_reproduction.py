#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import pickle
import subprocess
import sys
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
DEFAULT_CLI_FLAGS = ("--artifact", "--screenshot", "--frame", "--max-frames", "--width", "--height")
REJECT_SOURCE_TOKENS = ("walkthrough", "supporting_evidence", "code_evidence", "learning_card", "debug", "log", "input", "dataset")
CHARACTER_MESH_CHANNEL = "animationtech_skinned_character_mesh"
EVIHANIMATION_STYLE_MESH_RENDERER = "evihanimation_style_raylib"
SKELETON_SOURCE_CASES = {
    "motion_graph_evih",
    "laplacian_deformation_evih",
    "animation_evih",
    "character_usd_evih",
    "multiple_characters_evih",
    "animation_format_evih",
    "footskate_cleanup_for_motion_capture_editing_evih",
    "knowing_when_to_put_your_foot_down_evih",
    "motion_fields_for_interactive_character_animation_evih",
    "motion_matching_evih",
    "motion_warping_evih",
    "near_optimal_character_animation_with_continuous_control_evih",
    "precomputing_avatar_behavior_evih",
    "real_time_planning_for_parameterized_human_motion_evih",
    "verbs_and_adverbs_evih",
}


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
    if is_evih_slug(query):
        for case in cases:
            if case_slug(case) == query:
                return case
        return None
    candidates = {query, evih_slug(query)}
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


def check_gif(path: Path, min_bytes: int) -> Finding | None:
    if not path.exists():
        return Finding("error", "gif-missing", f"GIF missing: {path}")
    if path.stat().st_size < min_bytes:
        return Finding("error", "gif-small", f"GIF too small: {path} ({path.stat().st_size} bytes)")
    with path.open("rb") as handle:
        if handle.read(6) not in GIF_SIGNATURES:
            return Finding("error", "gif-not-gif", f"File is not a GIF: {path}")
    return None


def check_artifact(path: Path, min_bytes: int) -> Finding | None:
    if not path.exists():
        return Finding("error", "artifact-missing", f"Artifact missing: {path}")
    if path.stat().st_size < min_bytes:
        return Finding("error", "artifact-small", f"Artifact too small: {path} ({path.stat().st_size} bytes)")
    return None


def _report_file_path(repo_root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", value.lower()))


def _source_skeleton_summary_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    frames = payload.get("global_positions", payload.get("frames"))
    return {
        "type": type(payload).__name__,
        "keys": sorted(str(key) for key in payload.keys()),
        "source_channel": payload.get("source_channel"),
        "frame_shape": list(getattr(frames, "shape", []) or []),
        "parents_shape": list(getattr(payload.get("parents"), "shape", []) or []),
        "root_shape": list(getattr(payload.get("root_trajectory"), "shape", []) or []),
        "frame_count": payload.get("frame_count"),
        "source_signature_digest": payload.get("source_signature", {}).get("digest") if isinstance(payload.get("source_signature"), dict) else None,
    }


def _load_source_skeleton_summary(path: Path, slug: str, repo_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        if not isinstance(payload, dict):
            return {"type": type(payload).__name__, "keys": []}, None
        return _source_skeleton_summary_from_payload(payload), None
    except ModuleNotFoundError as exc:
        env_python = repo_root / ".envs" / slug / "python.exe"
        if not env_python.exists():
            return None, f"{type(exc).__name__}: {exc}; case env python missing: {env_python}"
        script = (
            "import json,pickle,sys\n"
            "from pathlib import Path\n"
            "p=Path(sys.argv[1])\n"
            "with p.open('rb') as h: payload=pickle.load(h)\n"
            "frames=payload.get('global_positions', payload.get('frames')) if isinstance(payload, dict) else None\n"
            "summary={\n"
            " 'type': type(payload).__name__,\n"
            " 'keys': sorted([str(k) for k in payload.keys()]) if isinstance(payload, dict) else [],\n"
            " 'source_channel': payload.get('source_channel') if isinstance(payload, dict) else None,\n"
            " 'frame_shape': list(getattr(frames, 'shape', []) or []),\n"
            " 'parents_shape': list(getattr(payload.get('parents') if isinstance(payload, dict) else None, 'shape', []) or []),\n"
            " 'root_shape': list(getattr(payload.get('root_trajectory') if isinstance(payload, dict) else None, 'shape', []) or []),\n"
            " 'frame_count': payload.get('frame_count') if isinstance(payload, dict) else None,\n"
            " 'source_signature_digest': payload.get('source_signature', {}).get('digest') if isinstance(payload, dict) and isinstance(payload.get('source_signature'), dict) else None,\n"
            "}\n"
            "print(json.dumps(summary))\n"
        )
        result = subprocess.run([str(env_python), "-c", script, str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            return None, (result.stderr or result.stdout).strip()
        try:
            return json.loads(result.stdout), None
        except Exception as json_exc:
            return None, f"summary JSON parse failed: {type(json_exc).__name__}: {json_exc}"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def check_source_skeleton_payload(path: Path, slug: str, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("error", "source-skeleton-missing", f"{slug}: source skeleton DAT missing: {path}")]
    if path.stat().st_size < 128:
        findings.append(Finding("error", "source-skeleton-small", f"{slug}: source skeleton DAT too small: {path}"))
        return findings
    summary, error = _load_source_skeleton_summary(path, slug, repo_root)
    if error and summary is None:
        return [Finding("error", "source-skeleton-load", f"{slug}: source skeleton DAT cannot be loaded: {error}")]
    if summary is None:
        return [Finding("error", "source-skeleton-load", f"{slug}: source skeleton DAT cannot be loaded")]
    if summary.get("type") != "dict":
        return [Finding("error", "source-skeleton-schema", f"{slug}: source skeleton DAT is not a dict: {summary.get('type')}")]
    required = (
        "source_channel",
        "frames",
        "global_positions",
        "parents",
        "bone_names",
        "root_trajectory",
        "fps",
        "frame_count",
        "source_cell",
        "source_role",
        "source_signature",
    )
    keys = set(summary.get("keys") or [])
    for key in required:
        if key not in keys:
            findings.append(Finding("error", "source-skeleton-schema", f"{slug}: source skeleton DAT missing key {key!r}"))
    if summary.get("source_channel") != "animationtech_skeleton_trajectory":
        findings.append(Finding("error", "source-skeleton-channel", f"{slug}: source skeleton channel is {summary.get('source_channel')!r}"))
    frame_shape = summary.get("frame_shape") or []
    parents_shape = summary.get("parents_shape") or []
    root_shape = summary.get("root_shape") or []
    if not frame_shape or len(frame_shape) != 3 or int(frame_shape[-1]) < 3:
        findings.append(Finding("error", "source-skeleton-frames", f"{slug}: global_positions must be frame x bone x xyz, got shape={frame_shape!r}"))
    if frame_shape and int(summary.get("frame_count", -1)) != int(frame_shape[0]):
        findings.append(Finding("error", "source-skeleton-frame-count", f"{slug}: frame_count does not match global_positions shape"))
    if frame_shape and parents_shape and int(parents_shape[0]) != int(frame_shape[1]):
        findings.append(Finding("error", "source-skeleton-parents", f"{slug}: parents length does not match bone count"))
    if frame_shape and root_shape and int(root_shape[0]) != int(frame_shape[0]):
        findings.append(Finding("error", "source-skeleton-root", f"{slug}: root_trajectory length does not match frame count"))
    if not summary.get("source_signature_digest"):
        findings.append(Finding("error", "source-skeleton-signature", f"{slug}: source_signature missing digest"))
    return findings


def _load_character_mesh_summary(path: Path, slug: str, repo_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    script = (
        "import json,pickle,sys\n"
        "from pathlib import Path\n"
        "p=Path(sys.argv[1])\n"
        "with p.open('rb') as h: payload=pickle.load(h)\n"
        "def shape(key):\n"
        "    value = payload.get(key) if isinstance(payload, dict) else None\n"
        "    return list(getattr(value, 'shape', []) or [])\n"
        "summary={\n"
        " 'type': type(payload).__name__,\n"
        " 'keys': sorted([str(k) for k in payload.keys()]) if isinstance(payload, dict) else [],\n"
        " 'mesh_channel': payload.get('mesh_channel') if isinstance(payload, dict) else None,\n"
        " 'origin': payload.get('origin') if isinstance(payload, dict) else None,\n"
        " 'mesh_asset': payload.get('mesh_asset') if isinstance(payload, dict) else None,\n"
        " 'vertices_shape': shape('vertices'),\n"
        " 'indices_shape': shape('indices'),\n"
        " 'bone_ids_shape': shape('bone_ids'),\n"
        " 'weights_shape': shape('weights'),\n"
        " 'bindpose_shape': shape('bindpose'),\n"
        " 'initialpose_shape': shape('initialpose'),\n"
        " 'global_matrices_shape': shape('global_matrices'),\n"
        " 'skinned_vertices_shape': shape('skinned_vertices'),\n"
        " 'bbox_min_shape': shape('skinned_bbox_min'),\n"
        " 'bbox_max_shape': shape('skinned_bbox_max'),\n"
        " 'frame_count': payload.get('frame_count') if isinstance(payload, dict) else None,\n"
        " 'source_signature_digest': payload.get('source_signature', {}).get('digest') if isinstance(payload, dict) and isinstance(payload.get('source_signature'), dict) else None,\n"
        " 'evih_signature_digest': payload.get('evih_signature', {}).get('digest') if isinstance(payload, dict) and isinstance(payload.get('evih_signature'), dict) else None,\n"
        "}\n"
        "print(json.dumps(summary))\n"
    )
    env_python = repo_root / ".envs" / slug / "python.exe"
    python_exe = env_python if env_python.exists() else Path(sys.executable)
    result = subprocess.run([str(python_exe), "-c", script, str(path)], capture_output=True, text=True)
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()
    try:
        return json.loads(result.stdout), None
    except Exception as exc:
        return None, f"summary JSON parse failed: {type(exc).__name__}: {exc}"


def check_character_mesh_payload(path: Path, slug: str, repo_root: Path, expected_origin: str) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("error", "character-mesh-missing", f"{slug}: character mesh DAT missing: {path}")]
    if path.stat().st_size < 4096:
        findings.append(Finding("error", "character-mesh-small", f"{slug}: character mesh DAT too small: {path}"))
        return findings
    summary, error = _load_character_mesh_summary(path, slug, repo_root)
    if summary is None:
        return [Finding("error", "character-mesh-load", f"{slug}: character mesh DAT cannot be loaded: {error}")]
    if summary.get("type") != "dict":
        return [Finding("error", "character-mesh-schema", f"{slug}: character mesh DAT is not a dict: {summary.get('type')}")]
    required = (
        "mesh_channel",
        "mesh_asset",
        "bone_names",
        "parents",
        "global_matrices",
        "vertices",
        "indices",
        "bone_ids",
        "weights",
        "bindpose",
        "initialpose",
        "skinned_vertices",
        "skinned_bbox_min",
        "skinned_bbox_max",
        "root_trajectory",
        "fps",
        "frame_count",
    )
    keys = set(summary.get("keys") or [])
    for key in required:
        if key not in keys:
            findings.append(Finding("error", "character-mesh-schema", f"{slug}: character mesh DAT missing key {key!r}"))
    if summary.get("mesh_channel") != CHARACTER_MESH_CHANNEL:
        findings.append(Finding("error", "character-mesh-channel", f"{slug}: mesh_channel is {summary.get('mesh_channel')!r}"))
    origin = str(summary.get("origin", ""))
    if origin != expected_origin:
        findings.append(Finding("error", "character-mesh-origin", f"{slug}: mesh DAT origin expected {expected_origin!r}, got {origin!r}"))
    if origin in {"blog_asset", "proxy_only", "skeleton_only"}:
        findings.append(Finding("error", "character-mesh-proxy", f"{slug}: invalid strict mesh origin {origin!r}"))
    mesh_asset = summary.get("mesh_asset") if isinstance(summary.get("mesh_asset"), dict) else {}
    if mesh_asset.get("asset_name") != "AnimLabSimpleMale.usd":
        findings.append(Finding("error", "character-mesh-asset", f"{slug}: mesh asset is not AnimLabSimpleMale.usd: {mesh_asset!r}"))
    for key, minimum in (("vertex_count", 1000), ("index_count", 3000), ("bone_count", 20), ("material_count", 1)):
        try:
            if int(mesh_asset.get(key, 0)) < minimum:
                findings.append(Finding("error", "character-mesh-asset", f"{slug}: mesh asset {key} below minimum {minimum}: {mesh_asset.get(key)!r}"))
        except Exception:
            findings.append(Finding("error", "character-mesh-asset", f"{slug}: mesh asset {key} is invalid: {mesh_asset.get(key)!r}"))
    vertices_shape = summary.get("vertices_shape") or []
    indices_shape = summary.get("indices_shape") or []
    bone_ids_shape = summary.get("bone_ids_shape") or []
    weights_shape = summary.get("weights_shape") or []
    global_shape = summary.get("global_matrices_shape") or []
    skinned_shape = summary.get("skinned_vertices_shape") or []
    if len(vertices_shape) != 2 or int(vertices_shape[-1]) != 10:
        findings.append(Finding("error", "character-mesh-vertices", f"{slug}: vertices must be N x 10, got {vertices_shape!r}"))
    if len(indices_shape) != 1 or (indices_shape and int(indices_shape[0]) % 3 != 0):
        findings.append(Finding("error", "character-mesh-indices", f"{slug}: indices must be a flat triangle list, got {indices_shape!r}"))
    if len(bone_ids_shape) != 2 or len(weights_shape) != 2 or bone_ids_shape != weights_shape:
        findings.append(Finding("error", "character-mesh-skinning", f"{slug}: bone_ids/weights shape mismatch: {bone_ids_shape!r} vs {weights_shape!r}"))
    if vertices_shape and bone_ids_shape and int(vertices_shape[0]) != int(bone_ids_shape[0]):
        findings.append(Finding("error", "character-mesh-skinning", f"{slug}: skinning rows do not match vertex count"))
    if len(global_shape) != 4 or global_shape[-2:] != [4, 4]:
        findings.append(Finding("error", "character-mesh-matrices", f"{slug}: global_matrices must be F x B x 4 x 4, got {global_shape!r}"))
    if global_shape and int(summary.get("frame_count", -1)) != int(global_shape[0]):
        findings.append(Finding("error", "character-mesh-frame-count", f"{slug}: frame_count does not match global_matrices shape"))
    if len(skinned_shape) != 3 or int(skinned_shape[-1]) != 3:
        findings.append(Finding("error", "character-mesh-skinned", f"{slug}: skinned_vertices must be sampled frame x vertex x xyz, got {skinned_shape!r}"))
    if expected_origin.startswith("animationtech") and not summary.get("source_signature_digest"):
        findings.append(Finding("error", "character-mesh-signature", f"{slug}: source mesh signature missing digest"))
    if expected_origin.startswith("evih") and not summary.get("evih_signature_digest"):
        findings.append(Finding("error", "character-mesh-signature", f"{slug}: evih mesh signature missing digest"))
    return findings


def check_comparison_report(
    path: Path,
    slug: str,
    repo_root: Path,
    require_source_skeleton_baseline: bool = False,
    require_character_mesh_comparison: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    if not path.exists():
        return [Finding("error", "comparison-missing", f"{slug}: comparison report missing: {path}")]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [Finding("error", "comparison-json", f"{slug}: comparison report is not valid JSON: {type(exc).__name__}: {exc}")]
    if payload.get("evih_slug") not in (slug, None):
        findings.append(Finding("error", "comparison-slug", f"{slug}: comparison evih_slug is {payload.get('evih_slug')!r}"))
    if payload.get("pass") is not True:
        failures = payload.get("failures") or []
        findings.append(Finding("error", "comparison-failed", f"{slug}: comparison pass != true; failures={failures!r}"))
    for key in ("input_signature", "baseline_signature", "metrics", "thresholds", "artifact"):
        if key not in payload:
            findings.append(Finding("error", "comparison-schema", f"{slug}: comparison report missing key {key!r}"))
    visual = payload.get("visual_evidence")
    if not isinstance(visual, dict):
        findings.append(Finding("error", "comparison-visual-schema", f"{slug}: comparison report missing visual_evidence object"))
        return findings
    if visual.get("kind") != "gif_sequence_pair":
        findings.append(Finding("error", "comparison-visual-kind", f"{slug}: visual_evidence kind is {visual.get('kind')!r}"))
    for key in ("evih_gif", "source_gif"):
        gif_payload = visual.get(key)
        if not isinstance(gif_payload, dict):
            findings.append(Finding("error", "comparison-gif-schema", f"{slug}: visual_evidence missing {key} object"))
            continue
        gif_path = _report_file_path(repo_root, gif_payload.get("path"))
        if gif_path is None:
            findings.append(Finding("error", "comparison-gif-path", f"{slug}: {key} path is missing"))
        else:
            finding = check_gif(gif_path, 128)
            if finding:
                findings.append(Finding(finding.level, f"comparison-{finding.code}", f"{slug}: {finding.message}"))
        quality = gif_payload.get("sequence_quality")
        if not isinstance(quality, dict) or quality.get("pass") is not True:
            findings.append(Finding("error", "comparison-gif-quality", f"{slug}: {key} sequence_quality pass != true; quality={quality!r}"))
    source = visual.get("source_gif") if isinstance(visual.get("source_gif"), dict) else {}
    if source.get("algorithm_feature_match") is not True:
        findings.append(Finding("error", "comparison-source-subject", f"{slug}: source_gif algorithm_feature_match != true"))
    for key in ("expected_subject", "source_cell", "source_cell_role"):
        if not source.get(key):
            findings.append(Finding("error", "comparison-source-metadata", f"{slug}: source_gif missing {key}"))
    subject_quality = source.get("algorithm_subject_quality")
    if not isinstance(subject_quality, dict) or subject_quality.get("pass") is not True:
        findings.append(Finding("error", "comparison-source-quality", f"{slug}: source_gif algorithm_subject_quality pass != true; quality={subject_quality!r}"))
    origin = str(source.get("origin", ""))
    role_text = " ".join(str(source.get(key, "")) for key in ("source_cell_role", "source_cell")).lower()
    role_tokens = _tokens(role_text)
    if origin == "blog_asset" and any(token in role_tokens for token in REJECT_SOURCE_TOKENS):
        findings.append(Finding("error", "comparison-source-blog-role", f"{slug}: source_gif blog role/cell looks non-final: {role_text!r}"))
    if origin.startswith("baseline_render_") and not source.get("replaced_reason"):
        findings.append(Finding("error", "comparison-source-replacement", f"{slug}: baseline-rendered source_gif missing replaced_reason"))
    if require_source_skeleton_baseline and slug in SKELETON_SOURCE_CASES:
        if payload.get("source_channel") != "animationtech_skeleton_trajectory":
            findings.append(Finding("error", "comparison-source-channel", f"{slug}: source_channel is not animationtech_skeleton_trajectory"))
        if origin != "animationtech_source_payload":
            findings.append(Finding("error", "comparison-source-origin", f"{slug}: skeleton source_gif origin must be animationtech_source_payload, got {origin!r}"))
        source_data = payload.get("source_data")
        if not isinstance(source_data, dict):
            findings.append(Finding("error", "comparison-source-data", f"{slug}: comparison missing source_data metadata"))
        else:
            source_data_path = _report_file_path(repo_root, source_data.get("path"))
            if source_data_path is None:
                findings.append(Finding("error", "comparison-source-data-path", f"{slug}: source_data path missing"))
            else:
                findings.extend(check_source_skeleton_payload(source_data_path, slug, repo_root))
            if source_data.get("source_channel") != "animationtech_skeleton_trajectory":
                findings.append(Finding("error", "comparison-source-data-channel", f"{slug}: source_data channel is {source_data.get('source_channel')!r}"))
            if not isinstance(source_data.get("signature"), dict) or not source_data.get("signature", {}).get("digest"):
                findings.append(Finding("error", "comparison-source-data-signature", f"{slug}: source_data signature missing digest"))
        skeleton_comparison = payload.get("source_skeleton_comparison")
        if not isinstance(skeleton_comparison, dict) or skeleton_comparison.get("pass") is not True:
            findings.append(Finding("error", "comparison-source-skeleton", f"{slug}: source_skeleton_comparison pass != true; value={skeleton_comparison!r}"))
        if source.get("selected_blog_asset") and source.get("origin") == "blog_asset":
            findings.append(Finding("error", "comparison-source-blog-strict", f"{slug}: blog_asset cannot be the strict skeleton source control"))
    if require_character_mesh_comparison and slug in SKELETON_SOURCE_CASES:
        if payload.get("mesh_channel") != CHARACTER_MESH_CHANNEL:
            findings.append(Finding("error", "comparison-mesh-channel", f"{slug}: mesh_channel is not {CHARACTER_MESH_CHANNEL}"))
        for key, expected_origin in (
            ("source_mesh_data", "animationtech_source_mesh_payload"),
            ("evih_mesh_data", "evih_mesh_payload"),
        ):
            data = payload.get(key)
            if not isinstance(data, dict):
                findings.append(Finding("error", "comparison-mesh-data", f"{slug}: comparison missing {key} metadata"))
                continue
            if data.get("mesh_channel") != CHARACTER_MESH_CHANNEL:
                findings.append(Finding("error", "comparison-mesh-data-channel", f"{slug}: {key} mesh_channel is {data.get('mesh_channel')!r}"))
            origin_value = str(data.get("origin", ""))
            if origin_value != expected_origin:
                findings.append(Finding("error", "comparison-mesh-data-origin", f"{slug}: {key} origin expected {expected_origin!r}, got {origin_value!r}"))
            if origin_value in {"blog_asset", "proxy_only", "skeleton_only"}:
                findings.append(Finding("error", "comparison-mesh-proxy", f"{slug}: {key} cannot use strict origin {origin_value!r}"))
            mesh_path = _report_file_path(repo_root, data.get("path"))
            if mesh_path is None:
                findings.append(Finding("error", "comparison-mesh-data-path", f"{slug}: {key} path missing"))
            else:
                findings.extend(check_character_mesh_payload(mesh_path, slug, repo_root, expected_origin))
            if not isinstance(data.get("signature"), dict) or not data.get("signature", {}).get("digest"):
                findings.append(Finding("error", "comparison-mesh-data-signature", f"{slug}: {key} signature missing digest"))
        mesh_visual = payload.get("mesh_visual_evidence")
        if not isinstance(mesh_visual, dict):
            findings.append(Finding("error", "comparison-mesh-visual", f"{slug}: mesh_visual_evidence missing"))
        else:
            if mesh_visual.get("kind") != "character_mesh_gif_sequence_pair":
                findings.append(Finding("error", "comparison-mesh-visual-kind", f"{slug}: mesh visual kind is {mesh_visual.get('kind')!r}"))
            renderer = str(mesh_visual.get("renderer", ""))
            if renderer != EVIHANIMATION_STYLE_MESH_RENDERER:
                findings.append(Finding("error", "comparison-mesh-renderer", f"{slug}: mesh visual renderer expected {EVIHANIMATION_STYLE_MESH_RENDERER!r}, got {renderer!r}"))
            policy = str(mesh_visual.get("policy", "")).lower()
            if "cpu/pil" in policy or "deterministic_cpu_pil" in renderer:
                findings.append(Finding("error", "comparison-mesh-renderer", f"{slug}: CPU/PIL mesh renderer cannot satisfy strict EvihAnimation-style mesh visual comparison"))
            reference = mesh_visual.get("renderer_reference")
            if not isinstance(reference, dict) or not reference.get("repo") or not reference.get("commit"):
                findings.append(Finding("error", "comparison-mesh-renderer-reference", f"{slug}: mesh visual renderer_reference missing repo/commit"))
            for key, expected_origin in (
                ("source_mesh_gif", "animationtech_source_mesh_payload"),
                ("evih_mesh_gif", "evih_mesh_payload"),
            ):
                gif_payload = mesh_visual.get(key)
                if not isinstance(gif_payload, dict):
                    findings.append(Finding("error", "comparison-mesh-gif-schema", f"{slug}: mesh visual missing {key}"))
                    continue
                if gif_payload.get("origin") != expected_origin:
                    findings.append(Finding("error", "comparison-mesh-gif-origin", f"{slug}: {key} origin expected {expected_origin!r}, got {gif_payload.get('origin')!r}"))
                if gif_payload.get("renderer") != EVIHANIMATION_STYLE_MESH_RENDERER:
                    findings.append(Finding("error", "comparison-mesh-gif-renderer", f"{slug}: {key} renderer expected {EVIHANIMATION_STYLE_MESH_RENDERER!r}, got {gif_payload.get('renderer')!r}"))
                gif_path = _report_file_path(repo_root, gif_payload.get("path"))
                if gif_path is None:
                    findings.append(Finding("error", "comparison-mesh-gif-path", f"{slug}: {key} path missing"))
                else:
                    finding = check_gif(gif_path, 128)
                    if finding:
                        findings.append(Finding(finding.level, f"comparison-mesh-{finding.code}", f"{slug}: {finding.message}"))
                quality = gif_payload.get("sequence_quality")
                if not isinstance(quality, dict) or quality.get("pass") is not True:
                    findings.append(Finding("error", "comparison-mesh-gif-quality", f"{slug}: {key} sequence_quality pass != true; quality={quality!r}"))
        mesh_comparison = payload.get("mesh_comparison")
        if not isinstance(mesh_comparison, dict) or mesh_comparison.get("pass") is not True:
            findings.append(Finding("error", "comparison-mesh-failed", f"{slug}: mesh_comparison pass != true; value={mesh_comparison!r}"))
        elif mesh_comparison.get("mesh_channel") != CHARACTER_MESH_CHANNEL:
            findings.append(Finding("error", "comparison-mesh-comparison-channel", f"{slug}: mesh_comparison channel is {mesh_comparison.get('mesh_channel')!r}"))
    return findings


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
        common = parent / "common.py"
        if runner.exists():
            contract_text += "\n" + runner.read_text(encoding="utf-8", errors="replace")
        if runtime.exists():
            contract_text += "\n" + runtime.read_text(encoding="utf-8", errors="replace")
        if common.exists():
            contract_text += "\n" + common.read_text(encoding="utf-8", errors="replace")
    missing = [flag for flag in DEFAULT_CLI_FLAGS if flag not in contract_text]
    if missing:
        add(findings, "error" if strict else "warning", "viewer-cli", f"{path} missing CLI flags: {', '.join(missing)}")
    if "pyray" not in contract_text and "raylib" not in contract_text.lower():
        add(findings, "error" if strict else "warning", "viewer-raylib", f"{path} does not appear to use Raylib/pyray")


def check_case_local_shape(repo_root: Path, slug: str, findings: list[Finding], strict: bool) -> None:
    base = original_slug(slug)
    case_dir = repo_root / "labs" / "evih_reproductions" / base
    required = {
        "case-dir": case_dir,
        "core": case_dir / "core.py",
        "viewer": case_dir / "viewer.py",
        "package": case_dir / "__init__.py",
    }
    for code, path in required.items():
        if not path.exists():
            add(findings, "error" if strict else "warning", f"{code}-missing", f"{slug}: required case-local path missing: {path}")
    core_path = required["core"]
    if core_path.exists():
        text = core_path.read_text(encoding="utf-8", errors="replace")
        missing = [name for name in ("run_pipeline", "save_generated", "load_generated", "validate_metrics", "CONTRACT") if name not in text]
        if missing:
            add(findings, "error" if strict else "warning", "core-contract", f"{slug}: {core_path} missing: {', '.join(missing)}")
    viewer_path = required["viewer"]
    if viewer_path.exists():
        check_viewer_source(viewer_path, findings, strict)


def check_artifact_metrics(repo_root: Path, case: dict[str, Any], artifact_paths: list[Path], findings: list[Finding]) -> None:
    if not artifact_paths:
        return
    slug = case_slug(case)
    base = original_slug(slug)
    env_prefix = str(case.get("env_prefix", ""))
    env_python = repo_root / env_prefix / "python.exe" if env_prefix else Path()
    python_exe = env_python if env_python.exists() else Path(sys.executable)
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(repo_root / 'labs')!r})\n"
        f"from evih_reproductions.{base} import core\n"
        f"payload = core.load_generated(Path({str(artifact_paths[0])!r}))\n"
        "assert isinstance(payload, dict) and 'metrics' in payload, 'artifact payload does not contain metrics'\n"
        "core.validate_metrics(payload['metrics'])\n"
    )
    result = subprocess.run([str(python_exe), "-c", script], text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        add(findings, "error", "artifact-metrics", f"{slug}: validate_metrics failed for {artifact_paths[0]}: {detail}")


def check_case(
    repo_root: Path,
    case: dict[str, Any],
    require_artifacts: bool,
    require_screenshots: bool,
    strict: bool,
    allow_legacy_motion_graph: bool,
    min_artifact_bytes: int,
    min_screenshot_bytes: int,
    validate_metrics: bool,
    require_baseline_comparisons: bool,
    require_source_skeleton_baselines: bool,
    require_character_mesh_comparisons: bool,
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
    if strict:
        check_case_local_shape(repo_root, slug, findings, strict)
    if validate_metrics:
        check_artifact_metrics(repo_root, case, artifact_paths, findings)

    viewers = viewer_candidates(repo_root, case)
    existing_viewer = next((path for path in viewers if path.exists()), viewers[0])
    if not strict:
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

    if require_baseline_comparisons or (require_source_skeleton_baselines and slug in SKELETON_SOURCE_CASES) or (require_character_mesh_comparisons and slug in SKELETON_SOURCE_CASES):
        comparison_path = repo_root / ".reports" / "animation-comparisons" / slug / "comparison.json"
        findings.extend(check_comparison_report(comparison_path, slug, repo_root, require_source_skeleton_baselines, require_character_mesh_comparisons))

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
    parser.add_argument("--validate-metrics", action="store_true", help="Load generated artifacts and call each case-local core.validate_metrics(metrics).")
    parser.add_argument("--require-baseline-comparisons", action="store_true", help="Require comparison.json under .reports/animation-comparisons/<slug> with pass == true.")
    parser.add_argument("--require-source-skeleton-baselines", action="store_true", help="Require AnimationTech source skeleton DAT/GIF channel for skeletal Evih cases.")
    parser.add_argument("--require-character-mesh-comparisons", action="store_true", help="Require strict AnimLabSimpleMale skinned mesh DAT/GIF comparison for skeletal Evih cases.")
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
            validate_metrics=args.validate_metrics,
            require_baseline_comparisons=args.require_baseline_comparisons,
            require_source_skeleton_baselines=args.require_source_skeleton_baselines,
            require_character_mesh_comparisons=args.require_character_mesh_comparisons,
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
