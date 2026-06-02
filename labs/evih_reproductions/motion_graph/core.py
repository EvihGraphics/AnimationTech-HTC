from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from evih_reproductions import common
from evih_reproductions.cases import get_case


CASE_SLUG = "motion_graph"
BASELINE_LOCAL_MINIMA = 955
BASELINE_FINAL_NODES = 546
BASELINE_FINAL_EDGES = 1416
BASELINE_PATH_FOUND = True
BASELINE_PATH_FRAMES = 53

ARTIFACT_SCHEMA = [
    "case",
    "metrics",
    "bone_names",
    "parents",
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
]

CONTRACT: dict[str, Any] = {
    "contract_name": "motion_graph_evih_contract",
    "source_case": "motion_graph",
    "source_contract": "Motion Graph EvihAnimation canonical pipeline",
    "artifact_schema": ARTIFACT_SCHEMA,
    "expected": {
        "slug": CASE_SLUG,
        "family": "motion_graph",
        "path_found": BASELINE_PATH_FOUND,
        "path_frame_count": BASELINE_PATH_FRAMES,
        "final_nodes": BASELINE_FINAL_NODES,
        "final_edges": BASELINE_FINAL_EDGES,
    },
    "minimums": {
        "frame_count": 1,
        "bone_count": 1,
        "trajectory_frames": 1,
        "trajectory_length": 1,
    },
    "allowed_differences": "Runtime device may be CPU or CUDA; local minima may drift by +/-2 from the canonical Motion Graph baseline.",
}


def _animation_papers_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "AnimationPapers"


def _canonical_artifact() -> Path:
    return _animation_papers_dir() / "motion_graph_evih_generated.dat"


def _load_or_build_canonical(repo_root: Path | None = None) -> dict[str, Any]:
    from AnimationPapers.evih_motion_graph import core as canonical

    artifact = _canonical_artifact()
    if artifact.exists():
        return canonical.load_generated(artifact)
    result = canonical.run_pipeline(repo_root=repo_root, strict_baseline=True)
    canonical.save_generated(result, artifact)
    return canonical.load_generated(artifact)


def _standardize_payload(canonical_payload: dict[str, Any]) -> dict[str, Any]:
    case = get_case(CASE_SLUG)
    matrices = np.asarray(canonical_payload["trajectory_matrices"], dtype=np.float32)
    frames = matrices[..., :3, 3].astype(np.float32)
    parents = np.asarray(canonical_payload["parents"], dtype=np.int32)
    names = list(canonical_payload.get("bone_names", [f"bone_{i}" for i in range(frames.shape[1])]))
    trajectory_2d = np.asarray(canonical_payload.get("trajectory"), dtype=np.float32)
    if trajectory_2d.ndim == 2 and trajectory_2d.shape[1] == 2:
        curve = np.column_stack(
            [trajectory_2d[:, 0], np.ones(len(trajectory_2d), dtype=np.float32) * 4.0, trajectory_2d[:, 1]]
        ).astype(np.float32)
    else:
        curve = frames[:, 0]

    metrics = dict(canonical_payload.get("metrics", {}))
    metrics.update(
        {
            "slug": CASE_SLUG,
            "title": case["title"],
            "family": case["family"],
            "metric": case["metric"],
            "contract_name": CONTRACT["contract_name"],
            "source_case": CONTRACT["source_case"],
            "source_contract": CONTRACT["source_contract"],
            "artifact_schema": CONTRACT["artifact_schema"],
            "allowed_differences": CONTRACT["allowed_differences"],
            "frame_count": int(frames.shape[0]),
            "bone_count": int(frames.shape[1]),
            "used_evih_bvh": True,
            "visual_contract": case["metric"],
        }
    )
    return {
        "case": case,
        "metrics": metrics,
        "bone_names": names,
        "parents": parents,
        "frames": frames,
        "trajectory": frames[:, 0, [0, 2]].astype(np.float32),
        "curve": curve,
        "markers": curve[:: max(1, len(curve) // 6)][:6],
        "field_points": np.zeros((0, 4), dtype=np.float32),
        "face_frames": np.zeros((0, 0, 3), dtype=np.float32),
        "face_controls": np.zeros((0, 3), dtype=np.float32),
        "comparison_frames": frames[:: max(1, frames.shape[0] // 4)][:4],
        "trajectory_matrices": matrices,
        "trajectory_check": np.asarray(canonical_payload["trajectory_check"], dtype=np.float32),
    }


def run_pipeline(repo_root: Path | None = None, strict_baseline: bool = True, **_: Any) -> dict[str, Any]:
    payload = _standardize_payload(_load_or_build_canonical(repo_root))
    if strict_baseline:
        validate_metrics(payload["metrics"])
    return payload


def validate_metrics(metrics: dict[str, Any]) -> None:
    errors: list[str] = []
    local_count = int(metrics.get("local_minima_count", -1))
    if abs(local_count - BASELINE_LOCAL_MINIMA) > 2:
        errors.append(f"local_minima_count expected {BASELINE_LOCAL_MINIMA} +/- 2, got {local_count}")
    for key, expected in CONTRACT["expected"].items():
        actual = metrics.get(key)
        if actual != expected:
            errors.append(f"{key} expected {expected!r}, got {actual!r}")
    for key, minimum in CONTRACT["minimums"].items():
        actual = metrics.get(key)
        if actual is None or float(actual) < float(minimum):
            errors.append(f"{key} expected >= {minimum!r}, got {actual!r}")
    if errors:
        raise AssertionError("; ".join(errors))


def save_generated(result: dict[str, Any], output_path: Path | None = None) -> Path:
    return common.save_payload(result, output_path or common.default_artifact_path(__file__))


def load_generated(path: Path | None = None) -> dict[str, Any]:
    return common.load_payload(path or common.default_artifact_path(__file__))

def load_or_bake_baseline(repo_root: Path | None = None, baseline_path: Path | None = None, evih_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = evih_payload if evih_payload is not None else run_pipeline(repo_root=repo_root, strict_baseline=True)
    return common.load_or_bake_baseline(CASE_SLUG, payload, CONTRACT, baseline_path=baseline_path, repo_root=repo_root)


def compare_to_baseline(evih_payload: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return common.compare_payload_to_baseline(CASE_SLUG, evih_payload, baseline, CONTRACT)


def validate_comparison(comparison: dict[str, Any]) -> None:
    common.validate_comparison(comparison)

