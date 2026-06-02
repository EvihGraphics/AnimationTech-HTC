from __future__ import annotations

from pathlib import Path
from typing import Any

from evih_reproductions import common


CASE_SLUG = 'character_usd'
CONTRACT: dict[str, Any] = {'contract_name': 'character_usd_evih_contract', 'source_case': 'character_usd', 'source_contract': 'character hierarchy demo', 'artifact_schema': ['case', 'metrics', 'bone_names', 'parents', 'frames', 'trajectory', 'curve', 'markers', 'field_points', 'face_frames', 'face_controls', 'comparison_frames'], 'expected': {'slug': 'character_usd', 'family': 'character', 'visual_contract': 'character hierarchy demo'}, 'minimums': {'frame_count': 1, 'bone_count': 1, 'curve_samples': 16, 'marker_count': 1}, 'allowed_differences': 'Reduced deterministic Evih/Raylib reproduction; preserves concept metrics and visual evidence rather than notebook cell parity.'}


def run_pipeline(repo_root: Path | None = None, strict_baseline: bool = True, **_: Any) -> dict[str, Any]:
    payload = common.build_case_payload(CASE_SLUG, CONTRACT)
    if strict_baseline:
        validate_metrics(payload["metrics"])
    return payload


def validate_metrics(metrics: dict[str, Any]) -> None:
    common.validate_case_metrics(metrics, CONTRACT)


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

