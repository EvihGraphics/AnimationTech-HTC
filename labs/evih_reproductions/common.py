from __future__ import annotations

import hashlib
import json
import math
import pickle
import re
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from .cases import get_case


REPO_ROOT = Path(__file__).resolve().parents[2]
LAFAN_BVH = REPO_ROOT / "resources" / "lafan1" / "bvh" / "walk1_subject5.bvh"
ANIMATION_BASELINES_DIR = REPO_ROOT / ".reports" / "animation-baselines"
ANIMATION_COMPARISONS_DIR = REPO_ROOT / ".reports" / "animation-comparisons"
BLOG_DIR = REPO_ROOT / "docs" / "blog"
COMPARISON_SCHEMA_VERSION = 1
SOURCE_SKELETON_SCHEMA_VERSION = 1
CHARACTER_MESH_SCHEMA_VERSION = 1
CHARACTER_MESH_CHANNEL = "animationtech_skinned_character_mesh"
CHARACTER_MESH_ASSET_NAME = "AnimLabSimpleMale.usd"
EVIHANIMATION_STYLE_MESH_RENDERER = "evihanimation_style_raylib"
EVIHANIMATION_RENDERER_REFERENCE = {
    "repo": "https://github.com/EvihGraphics/EvihAnimation",
    "commit": "c8c96e6ed0416c2a517a8207d0985417acff3edf",
    "fallback_reference_repo": "https://github.com/facebookresearch/ai4animationpy",
    "fallback_reference_commit": "63d9a48f338f2492996dbc913bc8c2c8bf035e4a",
    "reference_cache": ".reports/external/EvihAnimation_ref_src",
    "key_files": [
        "ai4animation/Standalone/RenderPipeline.py",
        "ai4animation/Standalone/SkinnedMesh.py",
        "ai4animation/Standalone/Grid.py",
        "ai4animation/Standalone/Camera.py",
    ],
    "style_notes": [
        "Raylib 3D skinned mesh scene",
        "perspective camera aimed at the actor",
        "cool sky background and ground grid",
        "warm directional sun with ambient sky/ground shading",
        "root trajectory overlay for motion cases",
    ],
}
GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
SKELETON_SOURCE_CASES = {
    "motion_graph",
    "laplacian_deformation",
    "animation",
    "character_usd",
    "multiple_characters",
    "animation_format",
    "footskate_cleanup_for_motion_capture_editing",
    "knowing_when_to_put_your_foot_down",
    "motion_fields_for_interactive_character_animation",
    "motion_matching",
    "motion_warping",
    "near_optimal_character_animation_with_continuous_control",
    "precomputing_avatar_behavior",
    "real_time_planning_for_parameterized_human_motion",
    "verbs_and_adverbs",
}
COMPARISON_ARRAY_KEYS = (
    "frames",
    "trajectory",
    "curve",
    "markers",
    "field_points",
    "face_frames",
    "face_controls",
    "comparison_frames",
    "trajectory_matrices",
    "trajectory_check",
)
DEFAULT_ARRAY_THRESHOLDS = {
    "rmse": 1e-5,
    "max_abs": 1e-4,
}
CORE_VISUAL_ROLES = {"key_animation", "key_visual", "final", "result"}
REJECT_SOURCE_TOKENS = {
    "walkthrough",
    "supporting_evidence",
    "code_evidence",
    "learning_card",
    "debug",
    "log",
    "input",
    "dataset",
}
CORE_SOURCE_TOKENS = {
    "animation",
    "compare",
    "control",
    "deform",
    "field",
    "final",
    "follow",
    "graph",
    "matching",
    "motion",
    "path",
    "policy",
    "preview",
    "query",
    "reconstruction",
    "result",
    "search",
    "solved",
    "style",
    "trajectory",
    "viewer",
    "warp",
}
_CHARACTER_MESH_ASSET_CACHE: dict[str, Any] | None = None


def default_artifact_path(module_file: str | Path) -> Path:
    return Path(module_file).resolve().with_name("generated.dat")


def evih_slug(slug: str) -> str:
    return slug if slug.endswith("_evih") else f"{slug}_evih"


def baseline_path_for(slug: str, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / ".reports" / "animation-baselines" / evih_slug(slug) / "baseline.dat"


def comparison_report_path_for(slug: str, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / ".reports" / "animation-comparisons" / evih_slug(slug) / "comparison.json"


def source_skeleton_path_for(slug: str, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / ".reports" / "animation-comparisons" / evih_slug(slug) / "animationtech_source.dat"


def save_payload(payload: dict[str, Any], output_path: Path | None) -> Path:
    path = output_path if output_path is not None else Path("generated.dat")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(payload, handle)
    return path


def load_payload(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"Expected artifact payload dict, got {type(payload).__name__}")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return {
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "sha256": sha256_bytes(np.ascontiguousarray(value).tobytes()),
        }
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _json_digest(value: Any) -> str:
    text = json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"))
    return sha256_bytes(text.encode("utf-8"))


def _array_signature(array: np.ndarray) -> dict[str, Any]:
    normalized = np.ascontiguousarray(array)
    return {
        "shape": list(normalized.shape),
        "dtype": str(normalized.dtype),
        "sha256": sha256_bytes(normalized.tobytes()),
    }


def _source_files_for_payload(slug: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = dict(payload.get("metrics", {}))
    files: list[Path] = []
    if metrics.get("used_evih_bvh") and LAFAN_BVH.exists():
        files.append(LAFAN_BVH)
    if metrics.get("family") == "halo":
        face_asset = REPO_ROOT / "labs" / "AnimationPapers" / "animated_face.dat"
        if face_asset.exists():
            files.append(face_asset)
    source_files = []
    for path in files:
        source_files.append(
            {
                "path": str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return source_files


def make_input_signature(slug: str, payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(payload.get("metrics", {}))
    array_shapes = {}
    for key in COMPARISON_ARRAY_KEYS:
        if key in payload:
            array_shapes[key] = _array_signature(np.asarray(payload[key]))
    signature = {
        "slug": slug,
        "evih_slug": evih_slug(slug),
        "source_case": contract.get("source_case", slug),
        "contract_name": contract.get("contract_name"),
        "source_contract": contract.get("source_contract"),
        "input_kind": "evih_bvh" if metrics.get("used_evih_bvh") else "reduced_deterministic",
        "source_note": metrics.get("source_note"),
        "source_files": _source_files_for_payload(slug, payload),
        "metric_keys": sorted(str(key) for key in metrics.keys()),
        "array_signatures": array_shapes,
        "contract_digest": _json_digest(contract),
    }
    signature["digest"] = _json_digest(signature)
    return signature


def payload_output_summary(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(payload.get("metrics", {}))
    arrays = {}
    for key in COMPARISON_ARRAY_KEYS:
        if key in payload:
            arrays[key] = _array_signature(np.asarray(payload[key]))
    return {
        "metrics": json_safe(metrics),
        "arrays": arrays,
    }


def _baseline_payload_from(slug: str, payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    input_signature = make_input_signature(slug, payload, contract)
    output = {
        "metrics": dict(payload.get("metrics", {})),
        "arrays": {
            key: np.asarray(payload[key]).copy()
            for key in COMPARISON_ARRAY_KEYS
            if key in payload
        },
    }
    baseline_signature = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "slug": slug,
        "evih_slug": evih_slug(slug),
        "source_case": contract.get("source_case", slug),
        "baseline_kind": "baked_from_current_contract_payload",
        "input_digest": input_signature["digest"],
        "output_digest": _json_digest(payload_output_summary(payload)),
    }
    baseline_signature["digest"] = _json_digest(baseline_signature)
    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "slug": slug,
        "input_signature": input_signature,
        "baseline_signature": baseline_signature,
        "output": output,
        "contract": json_safe(contract),
    }


def load_or_bake_baseline(
    slug: str,
    payload: dict[str, Any],
    contract: dict[str, Any],
    baseline_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    path = baseline_path or baseline_path_for(slug, repo_root)
    if path.exists():
        baseline = load_payload(path)
        if "baseline_signature" not in baseline or "output" not in baseline:
            raise TypeError(f"Baseline payload has an unsupported schema: {path}")
        return baseline
    baseline = _baseline_payload_from(slug, payload, contract)
    save_payload(baseline, path)
    return baseline


def _metric_comparison(evih_metrics: dict[str, Any], baseline_metrics: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    comparisons = []
    failures = []
    ignored = {"runtime_device"}
    for key, expected in baseline_metrics.items():
        if key in ignored:
            continue
        actual = evih_metrics.get(key)
        if isinstance(expected, (str, int, float, bool)) or expected is None:
            passed = actual == expected
            comparisons.append({"key": key, "expected": json_safe(expected), "actual": json_safe(actual), "pass": passed})
            if not passed:
                failures.append(f"metric {key} expected {expected!r}, got {actual!r}")
    return comparisons, failures


def array_error(actual: np.ndarray, expected: np.ndarray) -> dict[str, Any]:
    actual_arr = np.asarray(actual)
    expected_arr = np.asarray(expected)
    if actual_arr.shape != expected_arr.shape:
        return {
            "shape_match": False,
            "actual_shape": list(actual_arr.shape),
            "expected_shape": list(expected_arr.shape),
            "rmse": None,
            "max_abs": None,
        }
    if actual_arr.size == 0:
        return {
            "shape_match": True,
            "actual_shape": list(actual_arr.shape),
            "expected_shape": list(expected_arr.shape),
            "rmse": 0.0,
            "max_abs": 0.0,
        }
    diff = actual_arr.astype(np.float64) - expected_arr.astype(np.float64)
    return {
        "shape_match": True,
        "actual_shape": list(actual_arr.shape),
        "expected_shape": list(expected_arr.shape),
        "rmse": float(np.sqrt(np.mean(diff * diff))),
        "max_abs": float(np.max(np.abs(diff))),
    }


def contact_f1(actual: np.ndarray, expected: np.ndarray) -> dict[str, float]:
    actual_bool = np.asarray(actual).astype(bool)
    expected_bool = np.asarray(expected).astype(bool)
    true_positive = float(np.logical_and(actual_bool, expected_bool).sum())
    false_positive = float(np.logical_and(actual_bool, np.logical_not(expected_bool)).sum())
    false_negative = float(np.logical_and(np.logical_not(actual_bool), expected_bool).sum())
    precision = true_positive / (true_positive + false_positive + 1e-8)
    recall = true_positive / (true_positive + false_negative + 1e-8)
    f1 = 2.0 * precision * recall / (precision + recall + 1e-8)
    return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}


def compare_payload_to_baseline(
    slug: str,
    evih_payload: dict[str, Any],
    baseline: dict[str, Any],
    contract: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = dict(DEFAULT_ARRAY_THRESHOLDS | (thresholds or {}))
    input_signature = make_input_signature(slug, evih_payload, contract)
    baseline_input = dict(baseline.get("input_signature", {}))
    baseline_signature = dict(baseline.get("baseline_signature", {}))
    failures: list[str] = []
    if baseline_input.get("digest") != input_signature.get("digest"):
        failures.append(
            f"input signature changed: baseline {baseline_input.get('digest')} current {input_signature.get('digest')}"
        )

    baseline_output = dict(baseline.get("output", {}))
    metric_comparisons, metric_failures = _metric_comparison(
        dict(evih_payload.get("metrics", {})),
        dict(baseline_output.get("metrics", {})),
    )
    failures.extend(metric_failures)

    array_comparisons = []
    for key, expected in dict(baseline_output.get("arrays", {})).items():
        if key not in evih_payload:
            failures.append(f"array {key} missing from Evih payload")
            array_comparisons.append({"key": key, "pass": False, "missing": True})
            continue
        error = array_error(np.asarray(evih_payload[key]), np.asarray(expected))
        passed = bool(
            error["shape_match"]
            and float(error["rmse"] or 0.0) <= thresholds["rmse"]
            and float(error["max_abs"] or 0.0) <= thresholds["max_abs"]
        )
        if not passed:
            failures.append(
                f"array {key} mismatch: shape_match={error['shape_match']} rmse={error['rmse']} max_abs={error['max_abs']}"
            )
        array_comparisons.append({"key": key, "pass": passed, **error})

    comparison = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "slug": slug,
        "evih_slug": evih_slug(slug),
        "source_case": contract.get("source_case", slug),
        "pass": not failures,
        "status": "passed" if not failures else "failed",
        "visual_evidence": {
            "kind": "dynamic_sequence",
            "policy": "Static screenshots are smoke evidence only; animation parity is judged from time-series arrays and optional overlay/contact-sheet sequence artifacts.",
            "sequence_arrays": [key for key in ("frames", "trajectory", "face_frames", "trajectory_matrices", "trajectory_check") if key in evih_payload],
        },
        "input_signature": input_signature,
        "baseline_signature": baseline_signature,
        "metrics": {
            "metric_comparisons": metric_comparisons,
            "array_comparisons": array_comparisons,
        },
        "thresholds": thresholds,
        "failures": failures,
        "artifact": payload_output_summary(evih_payload),
    }
    return comparison


def validate_comparison(comparison: dict[str, Any]) -> None:
    if not comparison.get("pass"):
        failures = comparison.get("failures") or ["comparison pass flag is false"]
        raise AssertionError("; ".join(str(item) for item in failures))


def attach_comparison_payload(
    payload: dict[str, Any],
    baseline: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    payload["input_signature"] = comparison["input_signature"]
    payload["baseline_signature"] = comparison["baseline_signature"]
    payload["evih_output"] = payload_output_summary(payload)
    payload["comparison"] = comparison
    return payload


def write_comparison_report(comparison: dict[str, Any], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(json_safe(comparison), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def read_comparison_report(report_path: Path) -> dict[str, Any]:
    return json.loads(report_path.read_text(encoding="utf-8"))


def repo_relative(path: Path, repo_root: Path | None = None) -> str:
    root = (repo_root or REPO_ROOT).resolve()
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def original_slug(slug: str) -> str:
    return slug[:-5] if slug.endswith("_evih") else slug


def is_skeleton_source_case(slug: str, payload: dict[str, Any] | None = None) -> bool:
    base_slug = original_slug(slug)
    if base_slug in SKELETON_SOURCE_CASES:
        return True
    case = dict(payload.get("case", {})) if payload else {}
    if not case:
        try:
            case = get_case(base_slug)
        except Exception:
            case = {}
    return bool(case.get("uses_bvh", False))


def _clean_markdown(value: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    return text.replace("`", "").replace("*", "").strip()


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _cell_number(value: str) -> int:
    match = re.search(r"cell\s+(\d+)", value, flags=re.IGNORECASE)
    return int(match.group(1)) if match else -1


def _gif_reference(value: str) -> str | None:
    for pattern in (r"`([^`]+\.gif)`", r"\(([^)]+\.gif)\)", r"([A-Za-z0-9_./\\-]+\.gif)"):
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _resolve_blog_media(readme_path: Path, reference: str) -> Path:
    ref = Path(reference.replace("\\", "/"))
    candidates = [
        readme_path.parent / ref,
        readme_path.parent.parent / ref,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def visual_subject_policy(slug: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    base_slug = original_slug(slug)
    case = dict(payload.get("case", {})) if payload else {}
    if not case:
        try:
            case = get_case(base_slug)
        except Exception:
            case = {}
    family = str(case.get("family", ""))
    subject = "final algorithm result sequence"
    positive = {"final", "result", "viewer", "preview"}
    negative = {"walkthrough", "debug", "log", "input", "dataset"}
    allows_no_character = family in {"theory_curve", "field", "pointcloud", "material", "lighting", "rigid", "primitive"}

    if base_slug == "motion_graph":
        subject = "final follow-path / graph-search result viewer with character motion and target path"
        positive |= {"follow", "path", "search", "graph"}
        negative |= {"raw", "point", "cloud", "distance", "matrix", "overview"}
    elif base_slug == "animation_format":
        subject = "final root projection or static-root motion format comparison result"
        positive |= {"root", "projection", "static", "format", "compare", "motion"}
    elif base_slug == "footskate_cleanup_for_motion_capture_editing":
        subject = "final cleanup / IK-solved foot contact processing result"
        positive |= {"final", "processing", "cleanup", "solved", "ik", "contact", "compare"}
        negative |= {"raw"}
    elif family == "halo":
        subject = "final facial reconstruction / control stream result"
        positive |= {"reconstruction", "control", "pca", "shader", "export"}
        negative |= {"raw", "vertex", "smoke"}
    elif family in {"contacts", "warping", "style", "deformation", "bvh_motion", "character", "multi_character"}:
        subject = "algorithm-processed motion result, not the raw input clip"
        positive |= {"cleanup", "final", "processed", "retime", "style", "warping", "warp", "mapped", "compare", "motion", "solved"}
        negative |= {"raw", "input"}
    elif family in {"planning", "matching", "graph"}:
        subject = "policy, query, search, graph, or final trajectory/control result"
        positive |= {"policy", "query", "search", "trajectory", "control", "planning", "matching", "graph", "path", "value"}
        negative |= {"dataset", "preview"}
    elif family in {"theory_curve", "field", "pointcloud"}:
        subject = "final curve, field, matrix, or point-cloud derivation result"
        positive |= {"curve", "field", "matrix", "point", "cloud", "basis", "rbf", "interpolation", "derivation"}
    elif family in {"material", "lighting", "rigid", "primitive"}:
        subject = "final scene, material, light, transform, or primitive state change"
        positive |= {"material", "light", "time", "transform", "scene", "sphere", "result"}

    return {
        "slug": base_slug,
        "family": family,
        "expected_subject": subject,
        "positive_tokens": sorted(positive),
        "negative_tokens": sorted(negative),
        "allows_no_character": allows_no_character,
        "requires_dynamic_sequence": True,
    }


def _candidate_algorithm_match(candidate: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    text = " ".join(
        str(candidate.get(key, ""))
        for key in ("file", "role", "media_type", "description", "source_cell")
    ).lower()
    role = str(candidate.get("role", "")).lower()
    media_type = str(candidate.get("media_type", "")).lower()
    positive = set(policy.get("positive_tokens", []))
    negative = set(policy.get("negative_tokens", []))
    token_set = _tokens(text)
    hits = sorted(token for token in positive if token in token_set or token in text)
    negative_hits = sorted(token for token in negative if token in token_set or token in text)
    bad_role = any(token in role or token in media_type for token in REJECT_SOURCE_TOKENS)
    core_role = role in CORE_VISUAL_ROLES or any(token in role for token in CORE_VISUAL_ROLES)

    if policy.get("slug") == "motion_graph":
        required = {"follow", "path"}
        matched = bool(required & token_set) and ("graph" in token_set or "viewer" in token_set or "search" in token_set)
        return matched and not bad_role, hits, negative_hits
    if policy.get("family") == "halo" and "raw" in negative_hits and not {"reconstruction", "control", "pca", "shader"} & set(hits):
        return False, hits, negative_hits
    if bad_role:
        return False, hits, negative_hits
    if hits:
        return True, hits, negative_hits
    return bool(core_role and not negative_hits), hits, negative_hits


def _score_source_candidate(candidate: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    matched, hits, negative_hits = _candidate_algorithm_match(candidate, policy)
    role = str(candidate.get("role", "")).lower()
    media_type = str(candidate.get("media_type", "")).lower()
    text_tokens = _tokens(" ".join(str(candidate.get(key, "")) for key in ("file", "description", "role")))
    score = int(candidate.get("cell_number", -1))
    if "key_animation" in role:
        score += 600
    elif "key_visual" in role:
        score += 300
    if "preview_gif" in media_type:
        score += 75
    score += len(hits) * 30
    score += len(text_tokens & CORE_SOURCE_TOKENS) * 6
    score -= len(negative_hits) * 90
    if not matched:
        score -= 1000
    scored = dict(candidate)
    scored.update(
        {
            "algorithm_feature_match": bool(matched),
            "feature_hits": hits,
            "negative_hits": negative_hits,
            "score": score,
            "expected_subject": policy["expected_subject"],
        }
    )
    return scored


def _parse_asset_readme(readme_path: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if not readme_path.exists():
        return candidates
    for line in readme_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ".gif" not in line.lower() or not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or set(cells[0]) <= {"-", " "}:
            continue
        gif_ref = _gif_reference(cells[0]) or _gif_reference(line)
        if not gif_ref:
            continue
        source_cell = _clean_markdown(cells[1]) if len(cells) > 1 else ""
        media_type = _clean_markdown(cells[2]) if len(cells) > 2 else ""
        role = _clean_markdown(cells[3]) if len(cells) > 3 else ""
        description = _clean_markdown(cells[-1]) if len(cells) > 4 else ""
        candidates.append(
            {
                "path": _resolve_blog_media(readme_path, gif_ref),
                "file": gif_ref.replace("\\", "/"),
                "source_cell": source_cell,
                "cell_number": _cell_number(source_cell),
                "source_cell_role": role,
                "role": role,
                "media_type": media_type,
                "description": description,
                "readme": repo_relative(readme_path),
            }
        )
    return candidates


def _blog_case_dirs(slug: str) -> list[Path]:
    base_slug = original_slug(slug)
    return [path for path in (BLOG_DIR / "AnimationPapers", BLOG_DIR / "Theory") if path.exists() for path in [path / base_slug] if path.exists()]


def select_algorithm_source_gif(slug: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = visual_subject_policy(slug, payload)
    candidates: list[dict[str, Any]] = []
    for case_dir in _blog_case_dirs(slug):
        candidates.extend(_parse_asset_readme(case_dir / "assets" / "README.md"))
        candidates.extend(_parse_asset_readme(case_dir / "README.md"))
        if not any(candidate.get("path", Path()).exists() for candidate in candidates):
            for gif_path in sorted((case_dir / "assets").glob("*.gif")):
                candidates.append(
                    {
                        "path": gif_path.resolve(),
                        "file": gif_path.name,
                        "source_cell": "",
                        "cell_number": -1,
                        "source_cell_role": "unclassified_blog_asset",
                        "role": "unclassified_blog_asset",
                        "media_type": "preview_gif",
                        "description": gif_path.stem.replace("_", " "),
                        "readme": "",
                    }
                )
    scored = [_score_source_candidate(candidate, policy) for candidate in candidates if Path(candidate["path"]).exists()]
    scored.sort(key=lambda item: (int(item.get("score", -9999)), int(item.get("cell_number", -1))), reverse=True)
    if scored:
        selected = scored[0]
        selected["origin"] = "blog_asset"
        return selected
    return {
        "path": None,
        "file": None,
        "source_cell": "baseline_payload",
        "cell_number": -1,
        "source_cell_role": "baseline_render",
        "role": "baseline_render",
        "media_type": "generated_gif",
        "description": "No qualifying blog GIF was available; source evidence must be rendered from the baseline payload.",
        "origin": "missing_blog_asset",
        "algorithm_feature_match": False,
        "feature_hits": [],
        "negative_hits": [],
        "expected_subject": policy["expected_subject"],
        "score": -9999,
    }


def validate_gif_sequence(
    gif_path: Path,
    expected_subject: str,
    min_frames: int = 6,
    min_temporal_delta: float = 0.0005,
    min_bbox_area_ratio: float = 0.0005,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "pass": False,
        "path": repo_relative(gif_path),
        "expected_subject": expected_subject,
        "frame_count": 0,
        "temporal_delta": 0.0,
        "motion_bbox_area_ratio": 0.0,
        "foreground_occupancy_mean": 0.0,
        "foreground_occupancy_min": 0.0,
        "foreground_occupancy_max": 0.0,
        "reason": "",
    }
    if not gif_path.exists():
        result["reason"] = "gif_missing"
        return result
    result["bytes"] = gif_path.stat().st_size
    if gif_path.stat().st_size < 128:
        result["reason"] = "gif_too_small"
        return result
    with gif_path.open("rb") as handle:
        if handle.read(6) not in GIF_SIGNATURES:
            result["reason"] = "not_a_gif"
            return result
    try:
        from PIL import Image, ImageSequence
    except Exception as exc:
        result["reason"] = f"pillow_unavailable:{type(exc).__name__}"
        return result
    try:
        with Image.open(gif_path) as image:
            result["frame_count"] = int(getattr(image, "n_frames", 1))
            samples = []
            step = max(1, int(result["frame_count"]) // 48)
            for index, frame in enumerate(ImageSequence.Iterator(image)):
                if index % step:
                    continue
                thumb = frame.convert("RGB").resize((96, 64))
                samples.append(np.asarray(thumb, dtype=np.float32))
                if len(samples) >= 48:
                    break
    except Exception as exc:
        result["reason"] = f"gif_decode_failed:{type(exc).__name__}:{exc}"
        return result
    if int(result["frame_count"]) < min_frames or len(samples) < 2:
        result["reason"] = "too_few_frames"
        return result
    stack = np.stack(samples, axis=0)
    deltas = np.mean(np.abs(stack[1:] - stack[:-1]), axis=(1, 2, 3)) / 255.0
    temporal_delta = float(np.mean(deltas)) if deltas.size else 0.0
    motion = np.std(stack, axis=0).mean(axis=2)
    mask = motion > 2.0
    if np.any(mask):
        ys, xs = np.where(mask)
        bbox_area_ratio = float(((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)) / (mask.shape[0] * mask.shape[1]))
    else:
        bbox_area_ratio = 0.0
    foreground_occupancy = []
    for sample in stack:
        corners = np.concatenate(
            [
                sample[:6, :6].reshape(-1, 3),
                sample[:6, -6:].reshape(-1, 3),
                sample[-6:, :6].reshape(-1, 3),
                sample[-6:, -6:].reshape(-1, 3),
            ],
            axis=0,
        )
        background = np.median(corners, axis=0)
        diff = np.linalg.norm(sample - background, axis=2)
        foreground_occupancy.append(float(np.mean(diff > 35.0)))
    result["temporal_delta"] = temporal_delta
    result["motion_bbox_area_ratio"] = bbox_area_ratio
    result["foreground_occupancy_mean"] = float(np.mean(foreground_occupancy)) if foreground_occupancy else 0.0
    result["foreground_occupancy_min"] = float(np.min(foreground_occupancy)) if foreground_occupancy else 0.0
    result["foreground_occupancy_max"] = float(np.max(foreground_occupancy)) if foreground_occupancy else 0.0
    reasons = []
    if temporal_delta < min_temporal_delta:
        reasons.append("near_static_sequence")
    if bbox_area_ratio < min_bbox_area_ratio:
        reasons.append("subject_bbox_degenerate")
    result["pass"] = not reasons
    result["reason"] = ";".join(reasons)
    return result


def validate_algorithm_subject_gif(
    slug: str,
    gif_path: Path,
    policy: dict[str, Any],
    sequence_quality: dict[str, Any],
    candidate: dict[str, Any],
    baseline_rendered: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    base_slug = original_slug(slug)
    metadata_match = bool(candidate.get("algorithm_feature_match")) or baseline_rendered
    if not metadata_match:
        reasons.append("metadata_algorithm_subject_mismatch")
    if not sequence_quality.get("pass"):
        reasons.append("sequence_quality_failed")

    foreground_mean = float(sequence_quality.get("foreground_occupancy_mean") or 0.0)
    motion_bbox = float(sequence_quality.get("motion_bbox_area_ratio") or 0.0)
    temporal_delta = float(sequence_quality.get("temporal_delta") or 0.0)

    if base_slug == "motion_graph":
        if foreground_mean < 0.01:
            reasons.append("character_or_path_not_visible")
        if foreground_mean > 0.70:
            reasons.append("ui_or_background_dominates_frame")
        if motion_bbox > 0.88:
            reasons.append("motion_area_too_broad_for_readable_character_path")
        if temporal_delta < 0.003:
            reasons.append("follow_path_motion_too_weak")

    return {
        "pass": not reasons,
        "expected_subject": policy["expected_subject"],
        "path": repo_relative(gif_path),
        "source_description": candidate.get("description"),
        "source_role": "baseline_render" if baseline_rendered else candidate.get("role"),
        "feature_hits": candidate.get("feature_hits", []),
        "negative_hits": candidate.get("negative_hits", []),
        "content_metrics": {
            "foreground_occupancy_mean": foreground_mean,
            "motion_bbox_area_ratio": motion_bbox,
            "temporal_delta": temporal_delta,
        },
        "reason": ";".join(reasons),
    }


def _gif_file_metadata(path: Path) -> dict[str, Any]:
    return {
        "path": repo_relative(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
    }


def _procedural_skeleton(frame_count: int = 150) -> tuple[list[str], np.ndarray, np.ndarray]:
    names = [
        "Root",
        "Spine",
        "Chest",
        "Head",
        "LeftArm",
        "LeftHand",
        "RightArm",
        "RightHand",
        "LeftLeg",
        "LeftFoot",
        "RightLeg",
        "RightFoot",
    ]
    parents = np.asarray([-1, 0, 1, 2, 2, 4, 2, 6, 0, 8, 0, 10], dtype=np.int32)
    base = np.asarray(
        [
            [0, 36, 0],
            [0, 72, 0],
            [0, 98, 0],
            [0, 132, 0],
            [-34, 96, 0],
            [-58, 76, 4],
            [34, 96, 0],
            [58, 76, -4],
            [-16, 26, 0],
            [-20, 4, 16],
            [16, 26, 0],
            [20, 4, -16],
        ],
        dtype=np.float32,
    )
    frames = np.zeros((frame_count, len(names), 3), dtype=np.float32)
    for i in range(frame_count):
        t = i / max(1, frame_count - 1)
        stride = math.sin(t * math.tau * 2.0)
        lift = abs(stride)
        frames[i] = base
        frames[i, :, 0] += (t - 0.5) * 230.0
        frames[i, :, 2] += math.sin(t * math.tau * 0.6) * 45.0
        frames[i, 4:8, 2] += np.asarray([stride * 24.0, stride * 32.0, -stride * 24.0, -stride * 32.0])
        frames[i, 8:12, 2] += np.asarray([-stride * 22.0, -stride * 32.0, stride * 22.0, stride * 32.0])
        frames[i, 9, 1] += lift * 12.0
        frames[i, 11, 1] += (1.0 - lift) * 12.0
    return names, parents, frames


def _load_bvh_skeleton(max_frames: int = 180) -> tuple[list[str], np.ndarray, np.ndarray, float, bool, str]:
    if not LAFAN_BVH.exists():
        names, parents, frames = _procedural_skeleton(max_frames)
        return names, parents, frames, 30.0, False, "procedural fallback; lafan1 BVH missing"
    try:
        from ai4animation.Import.BVHImporter import BVH

        motion = BVH(str(LAFAN_BVH)).LoadMotion()
        matrices = np.asarray(motion.Frames, dtype=np.float32)
        step = max(1, matrices.shape[0] // max_frames)
        chosen = matrices[::step][:max_frames]
        positions = chosen[:, :, :3, 3].astype(np.float32)
        root = positions[:, :1].copy()
        positions = positions - root
        positions[:, :, 1] -= positions[:, :, 1].min()
        return (
            list(motion.Hierarchy.BoneNames),
            np.asarray(motion.Hierarchy.ParentIndices, dtype=np.int32),
            positions,
            float(motion.Framerate),
            True,
            str(LAFAN_BVH),
        )
    except Exception as exc:
        names, parents, frames = _procedural_skeleton(max_frames)
        return names, parents, frames, 30.0, False, f"procedural fallback; Evih BVH import failed: {exc}"


def _curve_points(kind: str, count: int = 128) -> np.ndarray:
    t = np.linspace(0.0, 1.0, count, dtype=np.float32)
    if kind == "theory_curve":
        p0 = np.asarray([-260, 24, -120], dtype=np.float32)
        p1 = np.asarray([-160, 170, 100], dtype=np.float32)
        p2 = np.asarray([120, -40, -80], dtype=np.float32)
        p3 = np.asarray([260, 120, 130], dtype=np.float32)
        u = t[:, None]
        return ((1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u**2 * p2 + u**3 * p3).astype(np.float32)
    if kind == "pointcloud":
        theta = t * math.tau * 1.25
        radius = 70.0 + 150.0 * t
        return np.column_stack([np.cos(theta) * radius, 22.0 + t * 115.0, np.sin(theta) * radius]).astype(np.float32)
    if kind in {"field", "material", "lighting", "rigid", "primitive", "halo"}:
        x = (t - 0.5) * 520.0
        z = np.sin(t * math.tau * 2.0) * 135.0
        y = 10.0 + np.exp(-((t - 0.48) ** 2) * 24.0) * 125.0
        return np.column_stack([x, y, z]).astype(np.float32)
    if kind in {"planning", "matching", "graph", "motion_graph"}:
        theta = t * math.tau
        return np.column_stack([np.cos(theta) * 210.0, np.ones_like(t) * 5.0, np.sin(theta) * 125.0]).astype(np.float32)
    if kind in {"warping", "contacts", "style", "deformation"}:
        x = (t - 0.5) * 480.0
        z = np.sin(t * math.tau * 1.5) * 95.0
        y = 5.0 + np.cos(t * math.tau) * 18.0
        return np.column_stack([x, y, z]).astype(np.float32)
    x = (t - 0.5) * 500.0
    z = np.sin(t * math.tau) * 135.0
    y = 20.0 + np.sin(t * math.pi) * 80.0
    return np.column_stack([x, y, z]).astype(np.float32)


def _field_grid() -> np.ndarray:
    xs = np.linspace(-240.0, 240.0, 25, dtype=np.float32)
    zs = np.linspace(-180.0, 180.0, 19, dtype=np.float32)
    centers = np.asarray([[-150.0, -90.0], [10.0, 55.0], [165.0, -20.0]], dtype=np.float32)
    rows = []
    for x in xs:
        for z in zs:
            p = np.asarray([x, z], dtype=np.float32)
            weights = np.exp(-np.sum((centers - p) ** 2, axis=1) / 22000.0)
            y = 8.0 + float(np.dot(weights, [28.0, 80.0, 45.0]))
            rows.append([x, y, z, float(np.max(weights))])
    return np.asarray(rows, dtype=np.float32)


def _face_points(frame_count: int = 90) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0.0, math.tau, 72, endpoint=False, dtype=np.float32)
    base = np.column_stack([np.cos(theta) * 90.0, np.sin(theta) * 120.0 + 88.0, np.zeros_like(theta)])
    frames = np.zeros((frame_count, base.shape[0], 3), dtype=np.float32)
    for i in range(frame_count):
        t = i / max(1, frame_count - 1)
        smile = math.sin(t * math.tau) * 12.0
        frames[i] = base
        frames[i, :, 2] = np.cos(theta * 2.0) * 12.0
        lower = frames[i, :, 1] < 65.0
        frames[i, lower, 1] -= smile
        frames[i, ~lower, 0] += np.sin(theta[~lower] * 3.0) * smile * 0.25
    controls = np.asarray([[-45, 65, 18], [45, 65, 18], [0, 110, 22], [-30, 135, 20], [30, 135, 20]], dtype=np.float32)
    return frames, controls


def case_markers(family: str) -> np.ndarray:
    if family in {"planning", "matching", "graph", "motion_graph"}:
        return np.asarray([[-220, 4, -120], [-80, 4, 95], [90, 4, -80], [230, 4, 130]], dtype=np.float32)
    if family in {"contacts", "warping"}:
        return np.asarray([[-180, 3, -80], [-40, 3, 120], [110, 3, -95], [210, 3, 90]], dtype=np.float32)
    if family == "pointcloud":
        return np.asarray([[-120, 40, -80], [0, 75, 0], [120, 110, 80]], dtype=np.float32)
    return np.asarray([[-180, 4, -120], [-80, 4, 100], [60, 4, -80], [180, 4, 120]], dtype=np.float32)


def build_case_payload(slug: str, contract: dict[str, Any]) -> dict[str, Any]:
    case = get_case(slug)
    family = str(case["family"])
    uses_bvh = bool(case.get("uses_bvh", False))
    names, parents, frames, framerate, used_bvh, source_note = _load_bvh_skeleton()
    if not uses_bvh:
        names, parents, frames = _procedural_skeleton()
        framerate = 30.0
        used_bvh = False
        source_note = "procedural deterministic case data"

    curve = _curve_points(family)
    field_points = _field_grid() if family in {"field", "planning", "matching", "graph"} else np.zeros((0, 4), dtype=np.float32)
    face_frames = np.zeros((0, 0, 3), dtype=np.float32)
    face_controls = np.zeros((0, 3), dtype=np.float32)
    if family == "halo":
        face_frames, face_controls = _face_points()
        frames = face_frames
        parents = np.asarray([-1] + [0 for _ in range(face_frames.shape[1] - 1)], dtype=np.int32)
        names = [f"face_{i:02d}" for i in range(face_frames.shape[1])]

    if family == "deformation":
        offset = np.linspace(-1.0, 1.0, frames.shape[1], dtype=np.float32)
        frames = frames.copy()
        frames[:, :, 2] += offset[None, :] * 45.0
    if family == "warping":
        frames = frames.copy()
        frames[:, :, 0] *= np.linspace(0.7, 1.25, frames.shape[0], dtype=np.float32)[:, None]
    if family == "style":
        frames = frames.copy()
        frames[:, :, 2] += np.sin(np.linspace(0.0, math.tau * 2.0, frames.shape[0], dtype=np.float32))[:, None] * 35.0

    trajectory = frames[:, 0, [0, 2]].astype(np.float32)
    if family == "halo":
        trajectory = np.column_stack(
            [np.linspace(-80.0, 80.0, frames.shape[0]), np.sin(np.linspace(0, math.tau, frames.shape[0])) * 20.0]
        ).astype(np.float32)
    comparison_indices = np.linspace(0, frames.shape[0] - 1, 4, dtype=np.int32)
    markers = case_markers(family)

    metrics = {
        "slug": slug,
        "title": case["title"],
        "family": family,
        "metric": case["metric"],
        "contract_name": contract["contract_name"],
        "source_case": contract["source_case"],
        "source_contract": contract["source_contract"],
        "artifact_schema": contract["artifact_schema"],
        "allowed_differences": contract["allowed_differences"],
        "frame_count": int(frames.shape[0]),
        "bone_count": int(frames.shape[1]),
        "framerate": float(framerate),
        "used_evih_bvh": bool(used_bvh),
        "source_note": source_note,
        "curve_samples": int(curve.shape[0]),
        "field_samples": int(field_points.shape[0]),
        "marker_count": int(markers.shape[0]),
        "trajectory_length": float(np.sum(np.linalg.norm(trajectory[1:] - trajectory[:-1], axis=-1))),
        "visual_contract": str(case["metric"]),
    }
    if family == "contacts":
        foot_height = np.minimum(frames[:, min(9, frames.shape[1] - 1), 1], frames[:, min(11, frames.shape[1] - 1), 1])
        metrics["contact_frames"] = int(np.sum(foot_height < np.percentile(foot_height, 35)))
    if family == "planning":
        metrics["policy_waypoints"] = int(markers.shape[0])
        metrics["reduced_validation_profile"] = True
    if family == "matching":
        metrics["query_samples"] = int(curve.shape[0])
    if family == "field":
        metrics["rbf_centers"] = 3
    if family == "halo":
        metrics["face_points"] = int(frames.shape[1])
        metrics["control_points"] = int(face_controls.shape[0])

    return {
        "case": case,
        "metrics": metrics,
        "bone_names": names,
        "parents": parents,
        "frames": frames.astype(np.float32),
        "trajectory": trajectory.astype(np.float32),
        "curve": curve.astype(np.float32),
        "markers": markers.astype(np.float32),
        "field_points": field_points.astype(np.float32),
        "face_frames": face_frames.astype(np.float32),
        "face_controls": face_controls.astype(np.float32),
        "comparison_frames": frames[comparison_indices].astype(np.float32),
    }


def validate_case_metrics(metrics: dict[str, Any], contract: dict[str, Any]) -> None:
    errors: list[str] = []
    for key, expected in contract["expected"].items():
        actual = metrics.get(key)
        if actual != expected:
            errors.append(f"{key} expected {expected!r}, got {actual!r}")
    for key, minimum in contract["minimums"].items():
        actual = metrics.get(key)
        if actual is None or float(actual) < float(minimum):
            errors.append(f"{key} expected >= {minimum!r}, got {actual!r}")
    if errors:
        raise AssertionError("; ".join(errors))


def _baseline_output_payload(baseline: dict[str, Any], fallback_payload: dict[str, Any]) -> dict[str, Any]:
    output = dict(baseline.get("output", {}))
    arrays = dict(output.get("arrays", {}))
    payload = {
        "metrics": dict(output.get("metrics", fallback_payload.get("metrics", {}))),
        "case": fallback_payload.get("case", {}),
        "bone_names": fallback_payload.get("bone_names", []),
    }
    for key, value in arrays.items():
        payload[key] = np.asarray(value)
    if "frames" not in payload and "face_frames" in payload:
        payload["frames"] = np.asarray(payload["face_frames"])
    if "parents" in fallback_payload:
        payload["parents"] = np.asarray(fallback_payload["parents"])
    else:
        frames = np.asarray(payload.get("frames", np.zeros((1, 1, 3), dtype=np.float32)))
        payload["parents"] = np.asarray([-1] + [0 for _ in range(max(0, frames.shape[1] - 1))], dtype=np.int32)
    return payload


def _source_skeleton_signature(
    slug: str,
    source_payload: dict[str, Any],
    baseline: dict[str, Any],
    source_cell: str,
    source_role: str,
) -> dict[str, Any]:
    frames = np.asarray(source_payload["global_positions"], dtype=np.float32)
    parents = np.asarray(source_payload["parents"], dtype=np.int32)
    root_trajectory = np.asarray(source_payload["root_trajectory"], dtype=np.float32)
    signature = {
        "schema_version": SOURCE_SKELETON_SCHEMA_VERSION,
        "slug": original_slug(slug),
        "evih_slug": evih_slug(slug),
        "source_channel": "animationtech_skeleton_trajectory",
        "source_cell": source_cell,
        "source_role": source_role,
        "source_files": _source_files_for_payload(slug, source_payload),
        "baseline_digest": dict(baseline.get("baseline_signature", {})).get("digest"),
        "array_signatures": {
            "global_positions": _array_signature(frames),
            "parents": _array_signature(parents),
            "root_trajectory": _array_signature(root_trajectory),
        },
    }
    signature["digest"] = _json_digest(signature)
    return signature


def _contract_from_payload(slug: str, evih_payload: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(evih_payload.get("metrics", {}))
    return {
        "contract_name": metrics.get("contract_name", f"{slug}_evih_contract"),
        "source_case": metrics.get("source_case", slug),
        "source_contract": metrics.get("source_contract", "Reduced AnimationTech source skeleton contract"),
        "artifact_schema": metrics.get("artifact_schema", []),
        "expected": {},
        "minimums": {},
        "allowed_differences": metrics.get("allowed_differences", ""),
    }


def build_animationtech_source_skeleton_payload(
    slug: str,
    evih_payload: dict[str, Any],
    baseline: dict[str, Any],
    selected_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_slug = original_slug(slug)
    if not is_skeleton_source_case(base_slug, evih_payload):
        raise ValueError(f"{base_slug} is not configured for AnimationTech source skeleton comparison")

    if base_slug == "motion_graph":
        source = _baseline_output_payload(baseline, evih_payload)
        source_extractor = "motion_graph_canonical_baseline_payload"
    else:
        source = build_case_payload(base_slug, _contract_from_payload(base_slug, evih_payload))
        source_extractor = "reduced_animationtech_case_source_builder"
    frames = _payload_frames(source).astype(np.float32)
    parents = np.asarray(source.get("parents", evih_payload.get("parents")), dtype=np.int32)
    if parents.ndim != 1 or parents.shape[0] != frames.shape[1]:
        parents = np.asarray([-1] + [0 for _ in range(max(0, frames.shape[1] - 1))], dtype=np.int32)
    root_trajectory = frames[:, 0, :3].astype(np.float32)
    trajectory_2d = np.asarray(source.get("trajectory", root_trajectory[:, [0, 2]]), dtype=np.float32)
    if trajectory_2d.ndim != 2 or trajectory_2d.shape[0] != frames.shape[0]:
        trajectory_2d = root_trajectory[:, [0, 2]].astype(np.float32)

    selected = selected_source or {}
    source_cell = str(selected.get("source_cell") or "animationtech_source_skeleton_payload")
    source_role = str(selected.get("source_cell_role") or selected.get("role") or "animationtech_skeleton_trajectory")
    metrics = dict(source.get("metrics", evih_payload.get("metrics", {})))
    metrics.update(
        {
            "slug": base_slug,
            "source_channel": "animationtech_skeleton_trajectory",
            "source_data_kind": "animationtech_source_payload",
            "frame_count": int(frames.shape[0]),
            "bone_count": int(frames.shape[1]),
            "fps": float(metrics.get("fps", metrics.get("framerate", 30.0))),
        }
    )
    payload = {
        "schema_version": SOURCE_SKELETON_SCHEMA_VERSION,
        "slug": base_slug,
        "evih_slug": evih_slug(base_slug),
        "source_channel": "animationtech_skeleton_trajectory",
        "source_kind": "animationtech_source_payload",
        "source_extractor": source_extractor,
        "source_cell": source_cell,
        "source_role": source_role,
        "source_cell_role": source_role,
        "case": evih_payload.get("case", {}),
        "metrics": metrics,
        "bone_names": list(source.get("bone_names") or evih_payload.get("bone_names") or [f"bone_{i}" for i in range(frames.shape[1])]),
        "parents": parents,
        "frames": frames,
        "global_positions": frames.copy(),
        "root_trajectory": root_trajectory,
        "trajectory": trajectory_2d.astype(np.float32),
        "frame_count": int(frames.shape[0]),
        "fps": float(metrics.get("fps", metrics.get("framerate", 30.0))),
    }
    for key in ("curve", "markers", "field_points", "face_controls", "comparison_frames", "trajectory_matrices", "trajectory_check"):
        if key in source:
            payload[key] = np.asarray(source[key]).copy()
    payload["source_signature"] = _source_skeleton_signature(base_slug, payload, baseline, source_cell, source_role)
    return payload


def source_skeleton_data_metadata(path: Path, source_payload: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "path": repo_relative(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
        "schema_version": source_payload.get("schema_version"),
        "source_channel": source_payload.get("source_channel"),
        "frame_count": int(source_payload.get("frame_count", 0)),
        "fps": float(source_payload.get("fps", 0.0)),
        "source_cell": source_payload.get("source_cell"),
        "source_role": source_payload.get("source_role"),
        "signature": source_payload.get("source_signature"),
    }
    return metadata


def _compare_array_entry(key: str, source_array: np.ndarray, evih_array: np.ndarray, thresholds: dict[str, float]) -> tuple[dict[str, Any], str | None]:
    error = array_error(evih_array, source_array)
    passed = bool(
        error["shape_match"]
        and float(error["rmse"] or 0.0) <= thresholds["rmse"]
        and float(error["max_abs"] or 0.0) <= thresholds["max_abs"]
    )
    failure = None
    if not passed:
        failure = f"{key} mismatch: shape_match={error['shape_match']} rmse={error['rmse']} max_abs={error['max_abs']}"
    return {"key": key, "pass": passed, **error}, failure


def compare_source_skeleton_to_evih(
    source_payload: dict[str, Any],
    evih_payload: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = dict(DEFAULT_ARRAY_THRESHOLDS | (thresholds or {}))
    failures: list[str] = []
    comparisons: list[dict[str, Any]] = []

    source_frames = np.asarray(source_payload.get("global_positions", source_payload.get("frames")), dtype=np.float32)
    evih_frames = _payload_frames(evih_payload).astype(np.float32)
    source_root = np.asarray(source_payload.get("root_trajectory"), dtype=np.float32)
    if source_root.ndim != 2 or source_root.shape[-1] < 3:
        source_root = source_frames[:, 0, :3]
    evih_root = evih_frames[:, 0, :3]

    scalar_checks = [
        ("frame_count", int(source_payload.get("frame_count", source_frames.shape[0])), int(evih_frames.shape[0])),
        ("bone_count", int(source_frames.shape[1]), int(evih_frames.shape[1])),
    ]
    for key, expected, actual in scalar_checks:
        passed = expected == actual
        comparisons.append({"key": key, "pass": passed, "expected": expected, "actual": actual})
        if not passed:
            failures.append(f"{key} expected {expected}, got {actual}")

    source_fps = float(source_payload.get("fps", dict(source_payload.get("metrics", {})).get("framerate", 30.0)))
    evih_fps = float(dict(evih_payload.get("metrics", {})).get("fps", dict(evih_payload.get("metrics", {})).get("framerate", 30.0)))
    fps_pass = abs(source_fps - evih_fps) <= 1e-4
    comparisons.append({"key": "fps", "pass": fps_pass, "expected": source_fps, "actual": evih_fps})
    if not fps_pass:
        failures.append(f"fps expected {source_fps}, got {evih_fps}")

    source_parents = np.asarray(source_payload.get("parents"), dtype=np.int32)
    evih_parents = np.asarray(evih_payload.get("parents"), dtype=np.int32)
    parents_match = bool(source_parents.shape == evih_parents.shape and np.array_equal(source_parents, evih_parents))
    comparisons.append(
        {
            "key": "parents",
            "pass": parents_match,
            "expected_shape": list(source_parents.shape),
            "actual_shape": list(evih_parents.shape),
        }
    )
    if not parents_match:
        failures.append("parents hierarchy mismatch")

    for key, source_array, evih_array in (
        ("global_positions", source_frames, evih_frames),
        ("root_trajectory", source_root[:, :3], evih_root[:, :3]),
    ):
        entry, failure = _compare_array_entry(key, source_array, evih_array, thresholds)
        comparisons.append(entry)
        if failure:
            failures.append(failure)

    if "trajectory" in source_payload and "trajectory" in evih_payload:
        entry, failure = _compare_array_entry(
            "trajectory",
            np.asarray(source_payload["trajectory"], dtype=np.float32),
            np.asarray(evih_payload["trajectory"], dtype=np.float32),
            thresholds,
        )
        comparisons.append(entry)
        if failure:
            failures.append(failure)
    if "contacts" in source_payload and "contacts" in evih_payload:
        f1 = contact_f1(np.asarray(evih_payload["contacts"]), np.asarray(source_payload["contacts"]))
        passed = f1["f1"] >= 0.999
        comparisons.append({"key": "contacts", "pass": passed, **f1})
        if not passed:
            failures.append(f"contacts F1 below threshold: {f1['f1']}")
    if "markers" in source_payload and "markers" in evih_payload:
        entry, failure = _compare_array_entry(
            "targets",
            np.asarray(source_payload["markers"], dtype=np.float32),
            np.asarray(evih_payload["markers"], dtype=np.float32),
            thresholds,
        )
        comparisons.append(entry)
        if failure:
            failures.append(failure)

    return {
        "source_channel": "animationtech_skeleton_trajectory",
        "pass": not failures,
        "status": "passed" if not failures else "failed",
        "thresholds": thresholds,
        "comparisons": comparisons,
        "failures": failures,
    }


def _load_character_mesh_asset() -> dict[str, Any]:
    global _CHARACTER_MESH_ASSET_CACHE
    if _CHARACTER_MESH_ASSET_CACHE is not None:
        return _CHARACTER_MESH_ASSET_CACHE
    try:
        import ipyanimlab.assets as ipyanimlab_assets
        from pxr import Usd
        from ipyanimlab.usd.import_asset import read_usd_asset
    except Exception as exc:
        raise RuntimeError("ipyanimlab with pxr/USD support is required for character mesh strict comparison") from exc

    asset_path = Path(ipyanimlab_assets.get_asset_path(CHARACTER_MESH_ASSET_NAME)).resolve()
    if not asset_path.exists():
        raise FileNotFoundError(f"Character mesh asset missing: {asset_path}")
    stage = Usd.Stage.Open(str(asset_path))
    if stage is None:
        raise RuntimeError(f"Could not open character mesh USD: {asset_path}")
    vbuffer, ibuffer, materials, sibuffer, swbuffer, bindpose, initialpose, bone_names, parents, mesh_name = read_usd_asset(stage)
    vertices = np.asarray(vbuffer, dtype=np.float32).reshape(-1, 10)
    indices = np.asarray(ibuffer, dtype=np.int32).reshape(-1)
    if sibuffer is None or swbuffer is None or bindpose is None or initialpose is None:
        raise RuntimeError(f"{CHARACTER_MESH_ASSET_NAME} did not expose skinned mesh buffers")
    influence_count = int(np.asarray(sibuffer).size // max(1, vertices.shape[0]))
    if influence_count not in (4, 8):
        raise RuntimeError(f"Unsupported character mesh influence count: {influence_count}")
    bone_ids = np.asarray(sibuffer, dtype=np.int32).reshape(vertices.shape[0], influence_count)
    weights = np.asarray(swbuffer, dtype=np.float32).reshape(vertices.shape[0], influence_count)
    weight_sums = np.sum(weights, axis=1, keepdims=True)
    weights = np.divide(weights, np.where(weight_sums > 1e-8, weight_sums, 1.0)).astype(np.float32)
    material_metadata = [
        {
            "name": str(getattr(material, "name", f"material_{index}")),
            "first_index": int(getattr(material, "first_index", 0)),
            "index_count": int(getattr(material, "index_count", 0)),
        }
        for index, material in enumerate(materials or [])
    ]
    mesh_asset = {
        "asset_name": CHARACTER_MESH_ASSET_NAME,
        "path": repo_relative(asset_path) if asset_path.is_relative_to(REPO_ROOT) else str(asset_path),
        "sha256": sha256_file(asset_path),
        "bytes": asset_path.stat().st_size,
        "mesh_name": str(mesh_name),
        "vertex_count": int(vertices.shape[0]),
        "index_count": int(indices.shape[0]),
        "triangle_count": int(indices.shape[0] // 3),
        "material_count": int(len(material_metadata)),
        "bone_count": int(len(bone_names or [])),
        "influence_count": influence_count,
        "materials": material_metadata,
    }
    _CHARACTER_MESH_ASSET_CACHE = {
        "mesh_asset": mesh_asset,
        "vertices": vertices,
        "indices": indices,
        "bone_ids": bone_ids,
        "weights": weights,
        "bindpose": np.asarray(bindpose, dtype=np.float32),
        "initialpose": np.asarray(initialpose, dtype=np.float32),
        "bone_names": list(bone_names or []),
        "parents": np.asarray(parents, dtype=np.int32),
    }
    return _CHARACTER_MESH_ASSET_CACHE


def _global_matrices_from_local(local_matrices: np.ndarray, parents: np.ndarray) -> np.ndarray:
    local = np.asarray(local_matrices, dtype=np.float32)
    result = local.copy()
    for index, parent in enumerate(np.asarray(parents, dtype=np.int32)):
        if parent >= 0:
            result[index] = result[parent] @ result[index]
    return result


def _payload_positions_for_mesh(payload: dict[str, Any], mesh_bone_names: list[str], rest_global: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    frames = _payload_frames(payload).astype(np.float32)
    payload_names = [str(name) for name in payload.get("bone_names", [])]
    name_to_index = {name: index for index, name in enumerate(payload_names)}
    positions = np.repeat(rest_global[None, :, :3, 3], frames.shape[0], axis=0).astype(np.float32)
    mapping: dict[str, Any] = {"mapped": {}, "missing": [], "root_source": None}
    hips_index = name_to_index.get("Hips")
    for mesh_index, name in enumerate(mesh_bone_names):
        if name in name_to_index:
            source_index = name_to_index[name]
            positions[:, mesh_index, :] = frames[:, source_index, :3]
            mapping["mapped"][name] = source_index
        elif name == "Root" and hips_index is not None:
            positions[:, mesh_index, :] = frames[:, hips_index, :3]
            positions[:, mesh_index, 1] = 0.0
            mapping["mapped"][name] = hips_index
            mapping["root_source"] = "Hips projected to ground plane"
        else:
            mapping["missing"].append(name)
    if mapping["missing"]:
        raise RuntimeError(f"Payload cannot be mapped to {CHARACTER_MESH_ASSET_NAME}; missing bones: {mapping['missing']}")
    return positions, mapping


def _payload_global_matrices_for_character_mesh(payload: dict[str, Any], mesh_asset: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    parents = np.asarray(mesh_asset["parents"], dtype=np.int32)
    rest_global = _global_matrices_from_local(np.asarray(mesh_asset["initialpose"], dtype=np.float32), parents)
    positions, mapping = _payload_positions_for_mesh(payload, list(mesh_asset["bone_names"]), rest_global)
    global_matrices = np.repeat(rest_global[None, :, :, :], positions.shape[0], axis=0).astype(np.float32)
    global_matrices[:, :, :3, 3] = positions
    return global_matrices, mapping


def _skin_vertices(
    vertices: np.ndarray,
    bone_ids: np.ndarray,
    weights: np.ndarray,
    skin_matrices: np.ndarray,
    vertex_indices: np.ndarray | None = None,
) -> np.ndarray:
    if vertex_indices is not None:
        base = np.asarray(vertices, dtype=np.float32)[vertex_indices, :3]
        ids = np.asarray(bone_ids, dtype=np.int32)[vertex_indices]
        w = np.asarray(weights, dtype=np.float32)[vertex_indices]
    else:
        base = np.asarray(vertices, dtype=np.float32)[:, :3]
        ids = np.asarray(bone_ids, dtype=np.int32)
        w = np.asarray(weights, dtype=np.float32)
    ids = np.clip(ids, 0, skin_matrices.shape[0] - 1)
    matrices = skin_matrices[ids]
    hom = np.ones((base.shape[0], 4), dtype=np.float32)
    hom[:, :3] = base
    transformed = np.einsum("vijk,vk->vij", matrices, hom, optimize=True)[:, :, :3]
    return np.sum(transformed * w[:, :, None], axis=1).astype(np.float32)


def _mesh_sample_indices(vertex_count: int, sample_count: int = 2048) -> np.ndarray:
    count = min(vertex_count, sample_count)
    if count <= 0:
        return np.zeros((0,), dtype=np.int32)
    return np.unique(np.linspace(0, vertex_count - 1, count, dtype=np.int32))


def _mesh_frame_indices(frame_total: int, sample_count: int) -> np.ndarray:
    count = max(6, min(int(frame_total), int(sample_count)))
    return np.unique(np.linspace(0, max(0, frame_total - 1), count, dtype=np.int32))


def _render_face_indices(indices: np.ndarray, max_triangles: int = 2200) -> np.ndarray:
    faces = np.asarray(indices, dtype=np.int32).reshape(-1, 3)
    if faces.shape[0] <= max_triangles:
        return faces
    stride = max(1, faces.shape[0] // max_triangles)
    return faces[::stride][:max_triangles]


def _character_mesh_signature(mesh_payload: dict[str, Any], role: str) -> dict[str, Any]:
    signature = {
        "schema_version": CHARACTER_MESH_SCHEMA_VERSION,
        "role": role,
        "mesh_channel": CHARACTER_MESH_CHANNEL,
        "slug": mesh_payload.get("slug"),
        "evih_slug": mesh_payload.get("evih_slug"),
        "mesh_asset_sha256": dict(mesh_payload.get("mesh_asset", {})).get("sha256"),
        "array_signatures": {
            "vertices": _array_signature(np.asarray(mesh_payload["vertices"])),
            "indices": _array_signature(np.asarray(mesh_payload["indices"])),
            "bone_ids": _array_signature(np.asarray(mesh_payload["bone_ids"])),
            "weights": _array_signature(np.asarray(mesh_payload["weights"])),
            "global_matrices": _array_signature(np.asarray(mesh_payload["global_matrices"])),
            "skinned_vertices": _array_signature(np.asarray(mesh_payload["skinned_vertices"])),
            "skinned_bbox_min": _array_signature(np.asarray(mesh_payload["skinned_bbox_min"])),
            "skinned_bbox_max": _array_signature(np.asarray(mesh_payload["skinned_bbox_max"])),
        },
    }
    signature["digest"] = _json_digest(signature)
    return signature


def build_character_mesh_payload(
    slug: str,
    motion_payload: dict[str, Any],
    role: str,
    frame_count: int = 48,
) -> dict[str, Any]:
    if not is_skeleton_source_case(slug, motion_payload):
        raise ValueError(f"{slug} is not configured for character mesh comparison")
    mesh_asset = _load_character_mesh_asset()
    global_matrices, joint_mapping = _payload_global_matrices_for_character_mesh(motion_payload, mesh_asset)
    bindpose = np.asarray(mesh_asset["bindpose"], dtype=np.float32)
    frame_indices = _mesh_frame_indices(global_matrices.shape[0], frame_count)
    vertex_indices = _mesh_sample_indices(np.asarray(mesh_asset["vertices"]).shape[0])
    sampled_vertices = []
    bbox_min = []
    bbox_max = []
    for frame_index in frame_indices:
        skin_matrices = global_matrices[int(frame_index)] @ bindpose
        all_vertices = _skin_vertices(
            mesh_asset["vertices"],
            mesh_asset["bone_ids"],
            mesh_asset["weights"],
            skin_matrices,
        )
        sampled_vertices.append(all_vertices[vertex_indices])
        bbox_min.append(np.min(all_vertices, axis=0))
        bbox_max.append(np.max(all_vertices, axis=0))
    frames = _payload_frames(motion_payload)
    root_trajectory = frames[:, 0, :3].astype(np.float32)
    metrics = dict(motion_payload.get("metrics", {}))
    payload = {
        "schema_version": CHARACTER_MESH_SCHEMA_VERSION,
        "slug": original_slug(slug),
        "evih_slug": evih_slug(slug),
        "role": role,
        "mesh_channel": CHARACTER_MESH_CHANNEL,
        "origin": "animationtech_source_mesh_payload" if role == "source" else "evih_mesh_payload",
        "mesh_asset": mesh_asset["mesh_asset"],
        "bone_names": list(mesh_asset["bone_names"]),
        "parents": np.asarray(mesh_asset["parents"], dtype=np.int32),
        "vertices": np.asarray(mesh_asset["vertices"], dtype=np.float32),
        "indices": np.asarray(mesh_asset["indices"], dtype=np.int32),
        "bone_ids": np.asarray(mesh_asset["bone_ids"], dtype=np.int32),
        "weights": np.asarray(mesh_asset["weights"], dtype=np.float32),
        "bindpose": bindpose,
        "initialpose": np.asarray(mesh_asset["initialpose"], dtype=np.float32),
        "global_matrices": global_matrices.astype(np.float32),
        "root_trajectory": root_trajectory,
        "fps": float(metrics.get("fps", metrics.get("framerate", 30.0))),
        "frame_count": int(global_matrices.shape[0]),
        "sample_frame_indices": frame_indices.astype(np.int32),
        "sample_vertex_indices": vertex_indices.astype(np.int32),
        "skinned_vertices": np.asarray(sampled_vertices, dtype=np.float32),
        "skinned_bbox_min": np.asarray(bbox_min, dtype=np.float32),
        "skinned_bbox_max": np.asarray(bbox_max, dtype=np.float32),
        "joint_mapping": json_safe(joint_mapping),
    }
    signature_key = "source_signature" if role == "source" else "evih_signature"
    payload[signature_key] = _character_mesh_signature(payload, role)
    return payload


def character_mesh_data_metadata(path: Path, mesh_payload: dict[str, Any]) -> dict[str, Any]:
    signature = mesh_payload.get("source_signature") or mesh_payload.get("evih_signature")
    return {
        "path": repo_relative(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() else None,
        "schema_version": mesh_payload.get("schema_version"),
        "mesh_channel": mesh_payload.get("mesh_channel"),
        "origin": mesh_payload.get("origin"),
        "mesh_asset": mesh_payload.get("mesh_asset"),
        "frame_count": int(mesh_payload.get("frame_count", 0)),
        "fps": float(mesh_payload.get("fps", 0.0)),
        "signature": signature,
    }


def compare_character_mesh_payloads(
    source_mesh: dict[str, Any],
    evih_mesh: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    thresholds = dict({"rmse": 2e-4, "max_abs": 2e-3} | (thresholds or {}))
    failures: list[str] = []
    comparisons: list[dict[str, Any]] = []
    scalar_checks = [
        ("mesh_asset_sha256", dict(source_mesh.get("mesh_asset", {})).get("sha256"), dict(evih_mesh.get("mesh_asset", {})).get("sha256")),
        ("vertex_count", int(np.asarray(source_mesh["vertices"]).shape[0]), int(np.asarray(evih_mesh["vertices"]).shape[0])),
        ("index_count", int(np.asarray(source_mesh["indices"]).shape[0]), int(np.asarray(evih_mesh["indices"]).shape[0])),
        ("bone_count", int(np.asarray(source_mesh["parents"]).shape[0]), int(np.asarray(evih_mesh["parents"]).shape[0])),
        ("frame_count", int(source_mesh.get("frame_count", 0)), int(evih_mesh.get("frame_count", 0))),
    ]
    for key, expected, actual in scalar_checks:
        passed = expected == actual
        comparisons.append({"key": key, "pass": passed, "expected": json_safe(expected), "actual": json_safe(actual)})
        if not passed:
            failures.append(f"{key} expected {expected!r}, got {actual!r}")
    source_fps = float(source_mesh.get("fps", 0.0))
    evih_fps = float(evih_mesh.get("fps", 0.0))
    fps_pass = abs(source_fps - evih_fps) <= 1e-4
    comparisons.append({"key": "fps", "pass": fps_pass, "expected": source_fps, "actual": evih_fps})
    if not fps_pass:
        failures.append(f"fps expected {source_fps}, got {evih_fps}")
    for key in ("parents", "vertices", "indices", "bone_ids", "weights", "bindpose", "initialpose", "sample_frame_indices", "sample_vertex_indices", "skinned_vertices", "skinned_bbox_min", "skinned_bbox_max", "root_trajectory"):
        entry, failure = _compare_array_entry(
            key,
            np.asarray(source_mesh[key]),
            np.asarray(evih_mesh[key]),
            thresholds,
        )
        comparisons.append(entry)
        if failure:
            failures.append(failure)
    return {
        "mesh_channel": CHARACTER_MESH_CHANNEL,
        "pass": not failures,
        "status": "passed" if not failures else "failed",
        "thresholds": thresholds,
        "comparisons": comparisons,
        "failures": failures,
    }


def _payload_array(payload: dict[str, Any], key: str, width: int = 3) -> np.ndarray:
    value = payload.get(key)
    if value is None:
        return np.zeros((0, width), dtype=np.float32)
    array = np.asarray(value, dtype=np.float32)
    if array.size == 0:
        return np.zeros((0, width), dtype=np.float32)
    return array


def _payload_frames(payload: dict[str, Any]) -> np.ndarray:
    frames = payload.get("frames", payload.get("face_frames"))
    array = np.asarray(frames, dtype=np.float32) if frames is not None else np.zeros((1, 1, 3), dtype=np.float32)
    if array.ndim != 3 or array.shape[-1] < 3:
        return np.zeros((1, 1, 3), dtype=np.float32)
    return array[:, :, :3]


def _render_projection(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    return np.column_stack([pts[:, 0] * 0.9 + pts[:, 2] * 0.35, -pts[:, 1] + pts[:, 2] * 0.18])


def _render_bounds(payload: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    frames = _payload_frames(payload)
    arrays = [frames[:: max(1, frames.shape[0] // 24)].reshape(-1, 3)]
    for key in ("curve", "markers", "face_controls"):
        array = _payload_array(payload, key)
        if array.ndim == 2 and array.shape[1] >= 3 and array.size:
            arrays.append(array[:, :3])
    field_points = _payload_array(payload, "field_points", 4)
    if field_points.ndim == 2 and field_points.shape[1] >= 3 and field_points.size:
        arrays.append(field_points[:, :3])
    all_points = np.concatenate([array for array in arrays if array.size], axis=0)
    projected = _render_projection(all_points)
    lo = projected.min(axis=0)
    hi = projected.max(axis=0)
    span = np.maximum(hi - lo, np.asarray([1.0, 1.0], dtype=np.float32))
    pad = span * 0.12
    return lo - pad, hi + pad


def _project_to_canvas(points: np.ndarray, lo: np.ndarray, hi: np.ndarray, width: int, height: int, margin: int = 38) -> list[tuple[int, int]]:
    projected = _render_projection(points)
    span = np.maximum(hi - lo, np.asarray([1.0, 1.0], dtype=np.float32))
    scale = min((width - margin * 2) / span[0], (height - margin * 2) / span[1])
    centered = (projected - (lo + hi) * 0.5) * scale
    screen = np.column_stack([width * 0.5 + centered[:, 0], height * 0.54 + centered[:, 1]])
    return [(int(x), int(y)) for x, y in screen]


def _draw_polyline(draw: Any, points: list[tuple[int, int]], fill: tuple[int, int, int], width: int = 2) -> None:
    if len(points) >= 2:
        draw.line(points, fill=fill, width=width, joint="curve")


def _draw_payload_frame(
    draw: Any,
    payload: dict[str, Any],
    frame_index: int,
    phase: float,
    lo: np.ndarray,
    hi: np.ndarray,
    width: int,
    height: int,
    label: str,
) -> None:
    frames = _payload_frames(payload)
    metrics = dict(payload.get("metrics", {}))
    family = str(metrics.get("family", ""))
    curve = _payload_array(payload, "curve")
    markers = _payload_array(payload, "markers")
    field_points = _payload_array(payload, "field_points", 4)
    face_controls = _payload_array(payload, "face_controls")
    parents = np.asarray(payload.get("parents", np.asarray([-1] + [0 for _ in range(max(0, frames.shape[1] - 1))])), dtype=np.int32)

    for x in range(0, width, 48):
        draw.line([(x, height - 42), (x + 24, height - 30)], fill=(210, 218, 226), width=1)
    draw.rectangle((0, 0, width, 48), fill=(245, 247, 250))
    title = str(metrics.get("title", metrics.get("slug", "")))[:68]
    draw.text((14, 9), f"{label}: {title}", fill=(22, 28, 38))
    draw.text((14, 27), f"{family} | frame {frame_index}/{frames.shape[0] - 1}", fill=(82, 91, 105))

    if field_points.ndim == 2 and field_points.shape[1] >= 4 and field_points.size:
        values = field_points[:, 3]
        for point, value in zip(field_points[::2, :3], values[::2]):
            sx, sy = _project_to_canvas(point[None, :], lo, hi, width, height)[0]
            value = float(np.clip(value, 0.0, 1.0))
            color = (int(45 + 155 * value), int(105 + 95 * value), int(215 - 110 * value))
            draw.ellipse((sx - 2, sy - 2, sx + 2, sy + 2), fill=color)
        scan_x = int(42 + phase * max(1, width - 84))
        draw.line((scan_x, 58, scan_x, height - 48), fill=(245, 130, 70), width=5)

    if curve.ndim == 2 and curve.shape[1] >= 3 and curve.size:
        curve_points = _project_to_canvas(curve[:, :3], lo, hi, width, height)
        _draw_polyline(draw, curve_points, (28, 33, 42), width=3)
        cursor = int(np.clip(round(phase * (len(curve_points) - 1)), 0, len(curve_points) - 1))
        _draw_polyline(draw, curve_points[: max(2, cursor + 1)], (226, 83, 55), width=4)
        cx, cy = curve_points[cursor]
        draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(230, 82, 55), outline=(255, 255, 255), width=2)
    if family in {"theory_curve", "pointcloud"}:
        scan_x = int(42 + phase * max(1, width - 84))
        draw.line((scan_x, 58, scan_x, height - 48), fill=(245, 130, 70), width=5)

    if markers.ndim == 2 and markers.shape[1] >= 3 and markers.size:
        for index, (sx, sy) in enumerate(_project_to_canvas(markers[:, :3], lo, hi, width, height)):
            color = (220, max(60, 160 - index * 18), min(245, 70 + index * 35))
            draw.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=color, outline=(35, 40, 52))

    if family in {"material", "lighting", "rigid", "primitive"}:
        cx = int(width * (0.48 + math.sin(phase * math.tau) * 0.08))
        cy = int(height * 0.54)
        hue = int(90 + 80 * math.sin(phase * math.tau))
        draw.rounded_rectangle((cx - 58, cy - 48, cx + 58, cy + 48), radius=8, fill=(42, 130 + hue // 6, 210 - hue // 4), outline=(30, 35, 45), width=3)
        lx = int(width * (0.22 + 0.56 * phase))
        draw.line((lx, 76, cx, cy - 18), fill=(245, 204, 75), width=4)
        draw.ellipse((lx - 15, 61, lx + 15, 91), fill=(255, 222, 96), outline=(75, 62, 20))
        return

    points = frames[int(np.clip(frame_index, 0, frames.shape[0] - 1))]
    if family == "halo":
        for sx, sy in _project_to_canvas(points, lo, hi, width, height):
            draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=(235, 188, 164), outline=(125, 75, 68))
        if face_controls.ndim == 2 and face_controls.shape[1] >= 3 and face_controls.size:
            for sx, sy in _project_to_canvas(face_controls[:, :3], lo, hi, width, height):
                draw.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=(220, 52, 55), outline=(80, 20, 28))
        return

    draw_skeleton = family not in {"theory_curve", "field"}
    if draw_skeleton:
        offsets = [-165.0, 0.0, 165.0] if family == "multi_character" else [0.0]
        for offset in offsets:
            shifted = points.copy()
            shifted[:, 0] += offset
            projected = _project_to_canvas(shifted, lo, hi, width, height)
            for i, parent in enumerate(parents):
                if parent >= 0 and parent < len(projected):
                    draw.line((projected[parent], projected[i]), fill=(250, 252, 255), width=4)
                    draw.line((projected[parent], projected[i]), fill=(88, 104, 127), width=1)
            for sx, sy in projected:
                draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=(22, 28, 44))


def render_payload_gif(
    payload: dict[str, Any],
    gif_path: Path,
    frame_count: int = 48,
    fps: int = 12,
    width: int = 640,
    height: int = 360,
    label: str = "Evih",
) -> Path:
    from PIL import Image, ImageDraw

    gif_path.parent.mkdir(parents=True, exist_ok=True)
    frames = _payload_frames(payload)
    lo, hi = _render_bounds(payload)
    count = max(6, int(frame_count))
    indices = np.linspace(0, max(0, frames.shape[0] - 1), count, dtype=np.int32)
    images = []
    for order, frame_index in enumerate(indices):
        phase = order / max(1, count - 1)
        image = Image.new("RGB", (width, height), (229, 235, 241))
        draw = ImageDraw.Draw(image)
        _draw_payload_frame(draw, payload, int(frame_index), phase, lo, hi, width, height, label)
        images.append(image)
    duration_ms = max(20, int(1000 / max(1, fps)))
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, optimize=False)
    return gif_path


def _mesh_render_bounds(mesh_payload: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    lo = np.min(np.asarray(mesh_payload["skinned_bbox_min"], dtype=np.float32), axis=0)
    hi = np.max(np.asarray(mesh_payload["skinned_bbox_max"], dtype=np.float32), axis=0)
    for key in ("root_trajectory",):
        array = np.asarray(mesh_payload.get(key, np.zeros((0, 3), dtype=np.float32)), dtype=np.float32)
        if array.ndim == 2 and array.shape[1] >= 3 and array.size:
            lo = np.minimum(lo, np.min(array[:, :3], axis=0))
            hi = np.maximum(hi, np.max(array[:, :3], axis=0))
    projected = _render_projection(np.stack([lo, hi], axis=0))
    p_lo = projected.min(axis=0)
    p_hi = projected.max(axis=0)
    span = np.maximum(p_hi - p_lo, np.asarray([1.0, 1.0], dtype=np.float32))
    pad = span * 0.18
    return p_lo - pad, p_hi + pad


def _draw_mesh_header(draw: Any, mesh_payload: dict[str, Any], label: str, frame_index: int, width: int) -> None:
    draw.rectangle((0, 0, width, 52), fill=(245, 247, 250))
    asset = dict(mesh_payload.get("mesh_asset", {}))
    title = f"{label}: {mesh_payload.get('slug', '')}"[:72]
    draw.text((14, 9), title, fill=(22, 28, 38))
    draw.text(
        (14, 29),
        f"{mesh_payload.get('mesh_channel')} | frame {frame_index}/{int(mesh_payload.get('frame_count', 1)) - 1} | vertices {asset.get('vertex_count')}",
        fill=(82, 91, 105),
    )


def _mesh_world_bounds(mesh_payload: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    lo = np.min(np.asarray(mesh_payload["skinned_bbox_min"], dtype=np.float32), axis=0)
    hi = np.max(np.asarray(mesh_payload["skinned_bbox_max"], dtype=np.float32), axis=0)
    root = np.asarray(mesh_payload.get("root_trajectory", np.zeros((0, 3), dtype=np.float32)), dtype=np.float32)
    if root.ndim == 2 and root.shape[1] >= 3 and root.size:
        lo = np.minimum(lo, np.min(root[:, :3], axis=0))
        hi = np.maximum(hi, np.max(root[:, :3], axis=0))
    span = np.maximum(hi - lo, np.asarray([1.0, 1.0, 1.0], dtype=np.float32))
    pad = np.asarray([span[0] * 0.12, span[1] * 0.08, span[2] * 0.12], dtype=np.float32)
    return lo - pad, hi + pad


def _normalize_vec(vector: np.ndarray, fallback: tuple[float, float, float]) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(value))
    if norm <= 1e-8:
        return np.asarray(fallback, dtype=np.float32)
    return value / norm


def _mesh_face_color(rl: Any, normal: np.ndarray) -> Any:
    light_dir = _normalize_vec(np.asarray([0.35, -1.0, -0.35], dtype=np.float32), (0.35, -1.0, -0.35))
    n = _normalize_vec(normal, (0.0, 1.0, 0.0))
    sun = max(0.0, float(np.dot(n, -light_dir)))
    sky = max(0.0, float(n[1]))
    ground = max(0.0, float(-n[1]))
    base = np.asarray([198.0, 199.0, 190.0], dtype=np.float32)
    sun_color = np.asarray([253.0, 255.0, 232.0], dtype=np.float32)
    sky_color = np.asarray([174.0, 183.0, 190.0], dtype=np.float32)
    ground_color = np.asarray([132.0, 124.0, 112.0], dtype=np.float32)
    lit = base * 0.54 + sun_color * (0.30 * sun) + sky_color * (0.14 * sky) + ground_color * (0.10 * ground)
    lit = np.clip(lit, 72.0, 238.0)
    return rl.Color(int(lit[0]), int(lit[1]), int(lit[2]), 255)


def _evihanimation_mesh_camera(rl: Any, mesh_payload: dict[str, Any], width: int, height: int, frame_index: int) -> Any:
    lo, hi = _mesh_world_bounds(mesh_payload)
    center = (lo + hi) * 0.5
    span = np.maximum(hi - lo, np.asarray([80.0, 120.0, 80.0], dtype=np.float32))
    body_spans = np.asarray(mesh_payload["skinned_bbox_max"], dtype=np.float32) - np.asarray(mesh_payload["skinned_bbox_min"], dtype=np.float32)
    body_span = np.maximum(np.max(body_spans, axis=0), np.asarray([70.0, 135.0, 70.0], dtype=np.float32))
    root = np.asarray(mesh_payload.get("root_trajectory", np.zeros((0, 3), dtype=np.float32)), dtype=np.float32)
    if root.ndim == 2 and root.shape[1] >= 3 and root.size:
        actor_index = int(np.clip(frame_index, 0, root.shape[0] - 1))
        actor = root[actor_index, :3]
    else:
        actor = center
    radius = float(max(body_span[0] * 1.15, body_span[2] * 1.20, body_span[1] * 0.82, 118.0))
    target = np.asarray([actor[0], max(64.0, actor[1] + body_span[1] * 0.46), actor[2]], dtype=np.float32)
    if span[0] < 180.0 and span[2] < 180.0:
        target = np.asarray([center[0], max(65.0, center[1] + span[1] * 0.08), center[2]], dtype=np.float32)
    position = target + np.asarray([-1.06 * radius, 0.66 * radius, 1.18 * radius], dtype=np.float32)
    fovy = 35.0 if width >= height else 42.0
    return rl.Camera3D(_v3(rl, position), _v3(rl, target), rl.Vector3(0.0, 1.0, 0.0), fovy, rl.CAMERA_PERSPECTIVE)


def _draw_evihanimation_mesh_scene(
    rl: Any,
    mesh_payload: dict[str, Any],
    frame_index: int,
    frame_order: int,
    frame_total: int,
    width: int,
    height: int,
    label: str,
    faces: np.ndarray,
) -> None:
    vertices = np.asarray(mesh_payload["vertices"], dtype=np.float32)
    bone_ids = np.asarray(mesh_payload["bone_ids"], dtype=np.int32)
    weights = np.asarray(mesh_payload["weights"], dtype=np.float32)
    bindpose = np.asarray(mesh_payload["bindpose"], dtype=np.float32)
    global_matrices = np.asarray(mesh_payload["global_matrices"], dtype=np.float32)
    root_trajectory = np.asarray(mesh_payload.get("root_trajectory", np.zeros((0, 3), dtype=np.float32)), dtype=np.float32)
    parents = np.asarray(mesh_payload.get("parents", np.zeros((0,), dtype=np.int32)), dtype=np.int32)
    skin_matrices = global_matrices[int(frame_index)] @ bindpose
    skinned = _skin_vertices(vertices, bone_ids, weights, skin_matrices)
    camera = _evihanimation_mesh_camera(rl, mesh_payload, width, height, int(frame_index))

    rl.begin_drawing()
    rl.clear_background(rl.Color(174, 183, 190, 255))
    rl.begin_mode_3d(camera)
    rl.draw_grid(32, 25.0)
    if root_trajectory.ndim == 2 and root_trajectory.shape[1] >= 3 and root_trajectory.size:
        cursor = int(np.clip((frame_order / max(1, frame_total - 1)) * (root_trajectory.shape[0] - 1), 0, root_trajectory.shape[0] - 1))
        for index, (a, b) in enumerate(zip(root_trajectory[:-1:2], root_trajectory[1::2])):
            color = rl.Color(230, 58, 42, 255) if index * 2 <= cursor else rl.Color(102, 54, 48, 210)
            rl.draw_line_3d(rl.Vector3(float(a[0]), 4.0, float(a[2])), rl.Vector3(float(b[0]), 4.0, float(b[2])), color)
        p = root_trajectory[cursor]
        rl.draw_sphere(rl.Vector3(float(p[0]), 7.5, float(p[2])), 8.5, rl.Color(245, 63, 45, 255))

    for face in faces:
        p0 = skinned[int(face[0])]
        p1 = skinned[int(face[1])]
        p2 = skinned[int(face[2])]
        normal = np.cross(p1 - p0, p2 - p0)
        rl.draw_triangle_3d(_v3(rl, p0), _v3(rl, p1), _v3(rl, p2), _mesh_face_color(rl, normal))

    joint_positions = global_matrices[int(frame_index), :, :3, 3]
    for joint, parent in enumerate(parents):
        if parent >= 0 and parent < joint_positions.shape[0]:
            rl.draw_line_3d(_v3(rl, joint_positions[int(parent)]), _v3(rl, joint_positions[int(joint)]), rl.Color(32, 38, 46, 210))
    for joint in joint_positions[::2]:
        rl.draw_sphere(_v3(rl, joint), 1.9, rl.Color(245, 248, 250, 235))

    rl.end_mode_3d()
    rl.draw_rectangle(0, 0, width, 52, rl.Color(20, 25, 31, 178))
    rl.draw_text(label, 16, 11, 20, rl.RAYWHITE)
    rl.draw_text(
        f"{mesh_payload.get('slug', '')} | {EVIHANIMATION_STYLE_MESH_RENDERER} | frame {int(frame_index)}/{int(mesh_payload.get('frame_count', 1)) - 1}",
        16,
        32,
        13,
        rl.Color(226, 232, 238, 255),
    )
    rl.end_drawing()


def _normalized_raylib_capture(image: Any, width: int, height: int) -> Any:
    rgb = image.convert("RGB")
    array = np.asarray(rgb, dtype=np.uint8)
    visible = np.mean(array, axis=2) > 8
    if np.any(visible):
        ys, xs = np.where(visible)
        top = int(ys.min())
        bottom = int(ys.max()) + 1
        left = int(xs.min())
        right = int(xs.max()) + 1
        if top > 0 or left > 0 or bottom < array.shape[0] or right < array.shape[1]:
            rgb = rgb.crop((left, top, right, bottom)).resize((width, height))
    return rgb


def render_character_mesh_gif(
    mesh_payload: dict[str, Any],
    gif_path: Path,
    frame_count: int = 48,
    fps: int = 12,
    width: int = 640,
    height: int = 360,
    label: str = "Mesh",
) -> Path:
    import pyray as rl
    from PIL import Image

    gif_path.parent.mkdir(parents=True, exist_ok=True)
    indices = np.asarray(mesh_payload["indices"], dtype=np.int32)
    global_matrices = np.asarray(mesh_payload["global_matrices"], dtype=np.float32)
    count = max(6, int(frame_count))
    frame_indices = np.linspace(0, max(0, global_matrices.shape[0] - 1), count, dtype=np.int32)
    render_faces = _render_face_indices(indices, max_triangles=18000)
    frame_dir = gif_path.parent / f"_{gif_path.stem}_raylib_frames"
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    images = []
    capture_name = f"_{gif_path.stem}_raylib_capture.png"
    capture_path = Path.cwd() / capture_name
    try:
        flags = getattr(rl, "FLAG_MSAA_4X_HINT", 0)
        if flags:
            rl.set_config_flags(flags)
        rl.init_window(width, height, f"{label} - {mesh_payload.get('slug', '')}")
        rl.set_target_fps(max(1, int(fps)))
        for order, frame_index in enumerate(frame_indices):
            _draw_evihanimation_mesh_scene(rl, mesh_payload, int(frame_index), order, len(frame_indices), width, height, label, render_faces)
            if capture_path.exists():
                capture_path.unlink()
            rl.take_screenshot(capture_name)
            target_png = frame_dir / f"frame_{order:03d}.png"
            if capture_path.exists():
                capture_path.replace(target_png)
            else:
                raise RuntimeError(f"Raylib did not write screenshot frame {order} for {gif_path}")
            with Image.open(target_png) as image:
                images.append(_normalized_raylib_capture(image, width, height))
    finally:
        try:
            rl.close_window()
        except Exception:
            pass
        if capture_path.exists():
            capture_path.unlink()
    if not images:
        raise RuntimeError(f"No Raylib mesh frames rendered for {gif_path}")
    duration_ms = max(20, int(1000 / max(1, fps)))
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0, optimize=False)
    shutil.rmtree(frame_dir, ignore_errors=True)
    return gif_path


def ensure_character_mesh_evidence(
    slug: str,
    evih_payload: dict[str, Any],
    baseline: dict[str, Any],
    comparison_dir: Path,
    source_mesh_path: Path | None = None,
    evih_mesh_path: Path | None = None,
    source_mesh_gif_path: Path | None = None,
    evih_mesh_gif_path: Path | None = None,
    frame_count: int = 48,
    fps: int = 12,
    width: int = 640,
    height: int = 360,
) -> dict[str, Any]:
    if not is_skeleton_source_case(slug, evih_payload):
        raise ValueError(f"{slug} is not configured for character mesh strict comparison")
    comparison_dir.mkdir(parents=True, exist_ok=True)
    selected = select_algorithm_source_gif(slug, evih_payload)
    source_motion = build_animationtech_source_skeleton_payload(slug, evih_payload, baseline, selected)
    source_mesh = build_character_mesh_payload(slug, source_motion, role="source", frame_count=frame_count)
    evih_mesh = build_character_mesh_payload(slug, evih_payload, role="evih", frame_count=frame_count)
    source_mesh_dat = source_mesh_path or (comparison_dir / "animationtech_source_mesh.dat")
    evih_mesh_dat = evih_mesh_path or (comparison_dir / "evih_mesh.dat")
    source_gif = source_mesh_gif_path or (comparison_dir / "animationtech_source_mesh.gif")
    evih_gif = evih_mesh_gif_path or (comparison_dir / "evih_mesh.gif")
    save_payload(source_mesh, source_mesh_dat)
    save_payload(evih_mesh, evih_mesh_dat)
    render_character_mesh_gif(source_mesh, source_gif, frame_count=frame_count, fps=fps, width=width, height=height, label="AnimationTech Source Mesh")
    render_character_mesh_gif(evih_mesh, evih_gif, frame_count=frame_count, fps=fps, width=width, height=height, label="Evih Mesh")
    policy = visual_subject_policy(slug, evih_payload)
    source_quality = validate_gif_sequence(source_gif, policy["expected_subject"])
    evih_quality = validate_gif_sequence(evih_gif, policy["expected_subject"])
    mesh_comparison = compare_character_mesh_payloads(source_mesh, evih_mesh)
    return {
        "mesh_channel": CHARACTER_MESH_CHANNEL,
        "source_mesh_data": character_mesh_data_metadata(source_mesh_dat, source_mesh),
        "evih_mesh_data": character_mesh_data_metadata(evih_mesh_dat, evih_mesh),
        "mesh_visual_evidence": {
            "kind": "character_mesh_gif_sequence_pair",
            "renderer": EVIHANIMATION_STYLE_MESH_RENDERER,
            "renderer_reference": EVIHANIMATION_RENDERER_REFERENCE,
            "policy": "Strict mesh visual comparison uses real AnimLabSimpleMale.usd skinned mesh buffers rendered through the same EvihAnimation-style Raylib renderer.",
            "comparison_dir": repo_relative(comparison_dir),
            "source_mesh_gif": {
                **_gif_file_metadata(source_gif),
                "origin": "animationtech_source_mesh_payload",
                "renderer": EVIHANIMATION_STYLE_MESH_RENDERER,
                "expected_subject": policy["expected_subject"],
                "sequence_quality": source_quality,
            },
            "evih_mesh_gif": {
                **_gif_file_metadata(evih_gif),
                "origin": "evih_mesh_payload",
                "renderer": EVIHANIMATION_STYLE_MESH_RENDERER,
                "expected_subject": policy["expected_subject"],
                "sequence_quality": evih_quality,
            },
        },
        "mesh_comparison": mesh_comparison,
    }


def ensure_visual_gifs(
    slug: str,
    evih_payload: dict[str, Any],
    baseline: dict[str, Any],
    comparison_dir: Path,
    evih_gif_path: Path | None = None,
    source_gif_path: Path | None = None,
    source_skeleton_path: Path | None = None,
    frame_count: int = 48,
    fps: int = 12,
    width: int = 640,
    height: int = 360,
) -> dict[str, Any]:
    comparison_dir.mkdir(parents=True, exist_ok=True)
    evih_path = evih_gif_path or (comparison_dir / "evih.gif")
    source_path = source_gif_path or (comparison_dir / "animationtech_source.gif")
    policy = visual_subject_policy(slug, evih_payload)

    render_payload_gif(evih_payload, evih_path, frame_count=frame_count, fps=fps, width=width, height=height, label="Evih")
    evih_quality = validate_gif_sequence(evih_path, policy["expected_subject"])

    selected = select_algorithm_source_gif(slug, evih_payload)
    selected_path = Path(selected["path"]) if selected.get("path") else None
    replaced_reason: str | None = None
    source_origin = "blog_asset"
    source_cell = str(selected.get("source_cell") or "")
    source_cell_role = str(selected.get("source_cell_role") or selected.get("role") or "")
    algorithm_match = bool(selected.get("algorithm_feature_match"))
    source_quality: dict[str, Any] | None = None
    source_subject_quality: dict[str, Any] | None = None
    rejected_blog_subject_quality: dict[str, Any] | None = None
    source_data: dict[str, Any] | None = None
    source_skeleton_comparison: dict[str, Any] | None = None
    supplemental_blog_gif: dict[str, Any] | None = None

    if is_skeleton_source_case(slug, evih_payload):
        source_origin = "animationtech_source_payload"
        source_data_path = source_skeleton_path or (comparison_dir / "animationtech_source.dat")
        source_payload = build_animationtech_source_skeleton_payload(slug, evih_payload, baseline, selected)
        save_payload(source_payload, source_data_path)
        render_payload_gif(source_payload, source_path, frame_count=frame_count, fps=fps, width=width, height=height, label="AnimationTech Source")
        source_quality = validate_gif_sequence(source_path, policy["expected_subject"])
        source_cell = str(source_payload.get("source_cell") or "animationtech_source_skeleton_payload")
        source_cell_role = str(source_payload.get("source_role") or "animationtech_skeleton_trajectory")
        algorithm_match = True
        source_subject_quality = validate_algorithm_subject_gif(
            slug,
            source_path,
            policy,
            source_quality,
            {
                **selected,
                "role": source_cell_role,
                "source_cell_role": source_cell_role,
                "source_cell": source_cell,
                "algorithm_feature_match": True,
            },
            baseline_rendered=True,
        )
        source_data = source_skeleton_data_metadata(source_data_path, source_payload)
        source_skeleton_comparison = compare_source_skeleton_to_evih(source_payload, evih_payload)
        if selected_path:
            supplemental_blog_gif = {
                "path": repo_relative(selected_path),
                "origin": selected.get("origin", "blog_asset"),
                "source_cell": selected.get("source_cell"),
                "source_cell_role": selected.get("source_cell_role") or selected.get("role"),
                "algorithm_feature_match": bool(selected.get("algorithm_feature_match")),
                "feature_hits": selected.get("feature_hits", []),
                "negative_hits": selected.get("negative_hits", []),
                "strict_control": False,
            }
    else:
        if selected_path and algorithm_match:
            source_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(selected_path, source_path)
            source_quality = validate_gif_sequence(source_path, policy["expected_subject"])
            if not source_quality.get("pass"):
                replaced_reason = "invalid_blog_asset"
            else:
                source_subject_quality = validate_algorithm_subject_gif(
                    slug,
                    source_path,
                    policy,
                    source_quality,
                    selected,
                    baseline_rendered=False,
                )
                if not source_subject_quality.get("pass"):
                    replaced_reason = "algorithm_subject_unreadable"
                    rejected_blog_subject_quality = source_subject_quality
        elif selected_path:
            replaced_reason = "algorithm_subject_mismatch"
        else:
            replaced_reason = "missing_blog_asset"

        if replaced_reason:
            source_origin = f"baseline_render_{replaced_reason}"
            source_payload = _baseline_output_payload(baseline, evih_payload)
            render_payload_gif(source_payload, source_path, frame_count=frame_count, fps=fps, width=width, height=height, label="AnimationTech Source")
            source_quality = validate_gif_sequence(source_path, policy["expected_subject"])
            source_cell = "baseline_payload"
            source_cell_role = "baseline_render"
            algorithm_match = True
            source_subject_quality = validate_algorithm_subject_gif(
                slug,
                source_path,
                policy,
                source_quality,
                selected,
                baseline_rendered=True,
            )

    source_quality = source_quality or validate_gif_sequence(source_path, policy["expected_subject"])
    source_subject_quality = source_subject_quality or validate_algorithm_subject_gif(
        slug,
        source_path,
        policy,
        source_quality,
        selected,
        baseline_rendered=str(source_origin).startswith("baseline_render_"),
    )
    selected_blog_asset = repo_relative(selected_path) if selected_path else None
    source_metadata = {
        **_gif_file_metadata(source_path),
        "origin": source_origin,
        "expected_subject": policy["expected_subject"],
        "source_cell": source_cell,
        "source_cell_role": source_cell_role,
        "algorithm_feature_match": bool(algorithm_match),
        "replaced_reason": replaced_reason,
        "selected_blog_asset": selected_blog_asset,
        "feature_hits": selected.get("feature_hits", []),
        "negative_hits": selected.get("negative_hits", []),
        "sequence_quality": source_quality,
        "algorithm_subject_quality": source_subject_quality,
    }
    if rejected_blog_subject_quality is not None:
        source_metadata["rejected_blog_subject_quality"] = rejected_blog_subject_quality
    if source_data is not None:
        source_metadata["source_data"] = source_data
    if supplemental_blog_gif is not None:
        source_metadata["supplemental_blog_gif"] = supplemental_blog_gif
    evih_metadata = {
        **_gif_file_metadata(evih_path),
        "origin": "evih_render",
        "expected_subject": policy["expected_subject"],
        "sequence_quality": evih_quality,
    }
    return {
        "kind": "gif_sequence_pair",
        "policy": "Visual comparison uses dynamic GIF sequences. Static screenshots remain smoke evidence only.",
        "comparison_dir": repo_relative(comparison_dir),
        "evih_gif": evih_metadata,
        "source_gif": source_metadata,
        **({"source_channel": "animationtech_skeleton_trajectory"} if source_data is not None else {}),
        **({"source_data": source_data} if source_data is not None else {}),
        **({"source_skeleton_comparison": source_skeleton_comparison} if source_skeleton_comparison is not None else {}),
    }


def validate_visual_evidence(visual_evidence: dict[str, Any]) -> None:
    failures: list[str] = []
    if visual_evidence.get("kind") != "gif_sequence_pair":
        failures.append("visual evidence kind must be gif_sequence_pair")
    evih = dict(visual_evidence.get("evih_gif", {}))
    source = dict(visual_evidence.get("source_gif", {}))
    for label, payload in (("evih_gif", evih), ("source_gif", source)):
        quality = dict(payload.get("sequence_quality", {}))
        if not payload.get("path"):
            failures.append(f"{label} path is missing")
        if not quality.get("pass"):
            failures.append(f"{label} sequence quality failed: {quality.get('reason')}")
    if source.get("algorithm_feature_match") is not True:
        failures.append("source_gif algorithm_feature_match must be true")
    subject_quality = dict(source.get("algorithm_subject_quality", {}))
    if subject_quality.get("pass") is not True:
        failures.append(f"source_gif algorithm subject quality failed: {subject_quality.get('reason')}")
    role = str(source.get("source_cell_role", "")).lower()
    if source.get("origin") == "blog_asset" and any(token in role for token in REJECT_SOURCE_TOKENS):
        failures.append(f"source_gif blog role is not acceptable: {role}")
    if str(source.get("origin", "")).startswith("baseline_render_") and not source.get("replaced_reason"):
        failures.append("baseline-rendered source_gif must record replaced_reason")
    if failures:
        raise AssertionError("; ".join(failures))


def _v3(rl: Any, point: np.ndarray) -> Any:
    return rl.Vector3(float(point[0]), float(point[1]), float(point[2]))


def _color_for_value(rl: Any, value: float) -> Any:
    value = float(np.clip(value, 0.0, 1.0))
    return rl.Color(int(35 + value * 220), int(90 + value * 90), int(210 - value * 150), 230)


def _draw_skeleton(rl: Any, points: np.ndarray, parents: np.ndarray, color: Any, joint_color: Any, offset_x: float = 0.0) -> None:
    shifted = points.copy()
    shifted[:, 0] += offset_x
    for i, parent in enumerate(parents):
        if parent < 0 or parent >= shifted.shape[0]:
            continue
        rl.draw_line_3d(_v3(rl, shifted[parent]), _v3(rl, shifted[i]), color)
        rl.draw_sphere(_v3(rl, shifted[i]), 2.8, joint_color)


def render_raylib(payload: dict[str, Any], screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> None:
    import pyray as rl

    frames = np.asarray(payload["frames"], dtype=np.float32)
    parents = np.asarray(payload["parents"], dtype=np.int32)
    curve = np.asarray(payload["curve"], dtype=np.float32)
    markers = np.asarray(payload["markers"], dtype=np.float32)
    field_points = np.asarray(payload["field_points"], dtype=np.float32)
    face_controls = np.asarray(payload["face_controls"], dtype=np.float32)
    metrics = dict(payload["metrics"])
    family = str(metrics["family"])
    current = int(np.clip(frame, 0, frames.shape[0] - 1))

    rl.set_config_flags(rl.FLAG_MSAA_4X_HINT)
    rl.init_window(width, height, str(metrics["title"]))
    rl.set_target_fps(30)
    camera = rl.Camera3D(
        rl.Vector3(-430.0, 275.0, 440.0),
        rl.Vector3(0.0, 76.0, 0.0),
        rl.Vector3(0.0, 1.0, 0.0),
        45.0,
        rl.CAMERA_PERSPECTIVE,
    )
    captured = False
    ticks = 0
    while not rl.window_should_close():
        if max_frames > 0:
            current = (frame + ticks) % frames.shape[0]
        points = frames[current]
        rl.begin_drawing()
        rl.clear_background(rl.Color(132, 174, 219, 255))
        rl.begin_mode_3d(camera)
        rl.draw_grid(32, 25.0)
        if field_points.size:
            for p in field_points[::3]:
                rl.draw_cube(_v3(rl, p[:3]), 8.0, 2.0 + float(p[3]) * 16.0, 8.0, _color_for_value(rl, p[3]))
        for a, b in zip(curve[:-1], curve[1:]):
            rl.draw_line_3d(_v3(rl, a), _v3(rl, b), rl.BLACK)
        for index, p in enumerate(markers):
            color = rl.Color(220, max(60, 160 - index * 18), min(245, 70 + index * 35), 255)
            rl.draw_sphere(_v3(rl, p), 7.5, color)
        offsets = [-165.0, 0.0, 165.0] if family == "multi_character" else [0.0]
        for offset in offsets:
            _draw_skeleton(rl, points, parents, rl.RAYWHITE, rl.Color(20, 28, 44, 255), offset)
        if family in {"primitive", "rigid", "material", "lighting"}:
            rl.draw_cube(rl.Vector3(0.0, 38.0, 0.0), 52.0, 52.0, 52.0, rl.Color(42, 118, 210, 255))
            rl.draw_cube_wires(rl.Vector3(0.0, 38.0, 0.0), 52.0, 52.0, 52.0, rl.BLACK)
            rl.draw_sphere(rl.Vector3(94.0, 44.0, -70.0), 30.0, rl.Color(255, 205, 80, 255))
            if family == "lighting":
                rl.draw_line_3d(rl.Vector3(-120.0, 160.0, -80.0), rl.Vector3(0.0, 35.0, 0.0), rl.YELLOW)
        if family == "halo":
            for p in points:
                rl.draw_sphere(_v3(rl, p), 3.0, rl.Color(246, 212, 188, 255))
            for c in face_controls:
                rl.draw_sphere(_v3(rl, c), 6.5, rl.RED)
        if family in {"contacts", "warping", "planning", "matching", "graph", "style"}:
            trajectory = np.asarray(payload["trajectory"], dtype=np.float32)
            for a, b in zip(trajectory[:-1:3], trajectory[1::3]):
                rl.draw_line_3d(rl.Vector3(float(a[0]), 3.0, float(a[1])), rl.Vector3(float(b[0]), 3.0, float(b[1])), rl.RED)
        rl.end_mode_3d()
        rl.draw_rectangle(0, 0, width, 92, rl.Color(245, 247, 250, 228))
        rl.draw_text(str(metrics["title"]), 22, 16, 24, rl.BLACK)
        rl.draw_text(f"{family} | frame {current}/{frames.shape[0] - 1} | bones {metrics['bone_count']}", 22, 49, 18, rl.DARKGRAY)
        rl.draw_text(str(metrics["metric"])[:90], 22, 71, 14, rl.DARKGRAY)
        rl.end_drawing()
        if screenshot and not captured:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            capture_name = f"_evih_capture_{metrics['slug']}.png"
            capture_path = Path.cwd() / capture_name
            if capture_path.exists():
                capture_path.unlink()
            rl.take_screenshot(capture_name)
            if capture_path.exists():
                capture_path.replace(screenshot)
            elif not screenshot.exists():
                cwd_screenshot = Path.cwd() / screenshot.name
                if cwd_screenshot.exists():
                    cwd_screenshot.replace(screenshot)
            captured = True
            if max_frames <= 0:
                break
        ticks += 1
        if max_frames > 0 and ticks >= max_frames:
            break
    rl.close_window()


def render_matplotlib(payload: dict[str, Any], screenshot: Path, frame: int) -> None:
    import matplotlib.pyplot as plt

    frames = np.asarray(payload["frames"], dtype=np.float32)
    parents = np.asarray(payload["parents"], dtype=np.int32)
    curve = np.asarray(payload["curve"], dtype=np.float32)
    markers = np.asarray(payload["markers"], dtype=np.float32)
    field_points = np.asarray(payload["field_points"], dtype=np.float32)
    face_controls = np.asarray(payload["face_controls"], dtype=np.float32)
    metrics = dict(payload["metrics"])
    family = str(metrics["family"])
    points = frames[int(np.clip(frame, 0, frames.shape[0] - 1))]

    fig = plt.figure(figsize=(12, 7), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#84aedb")
    if field_points.size:
        ax.scatter(field_points[:, 0], field_points[:, 2], field_points[:, 1], c=field_points[:, 3], cmap="viridis", s=16, alpha=0.65)
    ax.plot(curve[:, 0], curve[:, 2], curve[:, 1], color="black", linewidth=2.2)
    if markers.size:
        ax.scatter(markers[:, 0], markers[:, 2], markers[:, 1], color="#e6512f", s=55)
    offsets = [-165.0, 0.0, 165.0] if family == "multi_character" else [0.0]
    for offset in offsets:
        shifted = points.copy()
        shifted[:, 0] += offset
        for i, parent in enumerate(parents):
            if parent >= 0 and parent < shifted.shape[0]:
                ax.plot(
                    [shifted[parent, 0], shifted[i, 0]],
                    [shifted[parent, 2], shifted[i, 2]],
                    [shifted[parent, 1], shifted[i, 1]],
                    color="white",
                    linewidth=2.4,
                )
        ax.scatter(shifted[:, 0], shifted[:, 2], shifted[:, 1], color="#141c2c", s=15)
    if family == "halo" and face_controls.size:
        ax.scatter(face_controls[:, 0], face_controls[:, 2], face_controls[:, 1], color="red", s=65)
    ax.set_title(f"{metrics['title']} - {metrics['metric']}")
    ax.set_xlim(-330, 330)
    ax.set_ylim(-260, 260)
    ax.set_zlim(0, 230)
    ax.view_init(elev=18, azim=-55)
    ax.set_axis_off()
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(screenshot, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def render_payload(payload: dict[str, Any], screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> None:
    try:
        render_raylib(payload, screenshot, frame, width, height, max_frames)
    except Exception:
        if screenshot is None:
            raise
        render_matplotlib(payload, screenshot, frame)
