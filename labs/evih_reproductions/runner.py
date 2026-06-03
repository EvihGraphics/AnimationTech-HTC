from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evih_reproductions import common


def _module(case: str, name: str) -> ModuleType:
    return importlib.import_module(f"evih_reproductions.{case}.{name}")


def _load_or_bake_baseline(core: ModuleType, case: str, payload: dict, baseline_path: Path | None, repo_root: Path) -> dict:
    if hasattr(core, "load_or_bake_baseline"):
        try:
            return core.load_or_bake_baseline(repo_root=repo_root, baseline_path=baseline_path, evih_payload=payload)
        except TypeError:
            return core.load_or_bake_baseline(repo_root=repo_root, baseline_path=baseline_path)
    contract = getattr(core, "CONTRACT", {"source_case": case, "contract_name": f"{case}_evih_contract"})
    return common.load_or_bake_baseline(case, payload, contract, baseline_path=baseline_path, repo_root=repo_root)


def _compare_to_baseline(core: ModuleType, case: str, payload: dict, baseline: dict) -> dict:
    if hasattr(core, "compare_to_baseline"):
        return core.compare_to_baseline(payload, baseline)
    contract = getattr(core, "CONTRACT", {"source_case": case, "contract_name": f"{case}_evih_contract"})
    return common.compare_payload_to_baseline(case, payload, baseline, contract)


def _validate_comparison(core: ModuleType, comparison: dict) -> None:
    if hasattr(core, "validate_comparison"):
        core.validate_comparison(comparison)
        return
    common.validate_comparison(comparison)


def main(argv: list[str] | None = None, default_case: str | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an EvihAnimation/Raylib reproduction case.")
    parser.add_argument("--case", default=default_case, required=default_case is None)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--screenshot", default=None)
    parser.add_argument("--baseline", default=None)
    parser.add_argument("--comparison-report", default=None)
    parser.add_argument("--require-comparison", action="store_true")
    parser.add_argument("--evih-gif", default=None)
    parser.add_argument("--source-gif", default=None)
    parser.add_argument("--source-skeleton", default=None)
    parser.add_argument("--source-mesh", default=None)
    parser.add_argument("--evih-mesh", default=None)
    parser.add_argument("--source-mesh-gif", default=None)
    parser.add_argument("--evih-mesh-gif", default=None)
    parser.add_argument("--require-gifs", action="store_true")
    parser.add_argument("--require-source-skeleton-baseline", action="store_true")
    parser.add_argument("--require-character-mesh-comparison", action="store_true")
    parser.add_argument("--gif-frames", type=int, default=48)
    parser.add_argument("--gif-fps", type=int, default=12)
    parser.add_argument("--gif-width", type=int, default=640)
    parser.add_argument("--gif-height", type=int, default=360)
    parser.add_argument("--frame", type=int, default=32)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args(argv)

    core = _module(args.case, "core")
    viewer = _module(args.case, "viewer")
    artifact = Path(args.artifact)
    repo_root = Path(__file__).resolve().parents[2]
    payload = core.run_pipeline(strict_baseline=True)
    comparison = None
    comparison_enabled = bool(
        args.require_comparison
        or args.comparison_report
        or args.require_gifs
        or args.require_source_skeleton_baseline
        or args.require_character_mesh_comparison
        or args.evih_gif
        or args.source_gif
        or args.source_skeleton
        or args.source_mesh
        or args.evih_mesh
        or args.source_mesh_gif
        or args.evih_mesh_gif
    )
    if comparison_enabled:
        baseline_path = Path(args.baseline) if args.baseline else None
        baseline = _load_or_bake_baseline(core, args.case, payload, baseline_path, repo_root)
        comparison = _compare_to_baseline(core, args.case, payload, baseline)
        report_path = Path(args.comparison_report) if args.comparison_report else common.comparison_report_path_for(args.case, repo_root)
        visual_evidence = common.ensure_visual_gifs(
            args.case,
            payload,
            baseline,
            report_path.parent,
            evih_gif_path=Path(args.evih_gif) if args.evih_gif else None,
            source_gif_path=Path(args.source_gif) if args.source_gif else None,
            source_skeleton_path=Path(args.source_skeleton) if args.source_skeleton else None,
            frame_count=args.gif_frames,
            fps=args.gif_fps,
            width=args.gif_width,
            height=args.gif_height,
        )
        comparison["visual_evidence"] = visual_evidence
        for key in ("source_channel", "source_data", "source_skeleton_comparison"):
            if key in visual_evidence:
                comparison[key] = visual_evidence[key]
        if args.require_source_skeleton_baseline:
            source_skeleton_failures = []
            if not common.is_skeleton_source_case(args.case, payload):
                source_skeleton_failures.append(f"{args.case} is not a configured source skeleton comparison case")
            if comparison.get("source_channel") != "animationtech_skeleton_trajectory":
                source_skeleton_failures.append("comparison source_channel is not animationtech_skeleton_trajectory")
            if not isinstance(comparison.get("source_data"), dict):
                source_skeleton_failures.append("comparison source_data metadata missing")
            skeleton_comparison = comparison.get("source_skeleton_comparison")
            if not isinstance(skeleton_comparison, dict) or skeleton_comparison.get("pass") is not True:
                source_skeleton_failures.append(f"source skeleton comparison failed: {skeleton_comparison!r}")
            if source_skeleton_failures:
                comparison.setdefault("failures", []).extend(source_skeleton_failures)
                comparison["pass"] = False
                comparison["status"] = "failed"
        if args.require_character_mesh_comparison or args.source_mesh or args.evih_mesh or args.source_mesh_gif or args.evih_mesh_gif:
            try:
                mesh_evidence = common.ensure_character_mesh_evidence(
                    args.case,
                    payload,
                    baseline,
                    report_path.parent,
                    source_mesh_path=Path(args.source_mesh) if args.source_mesh else None,
                    evih_mesh_path=Path(args.evih_mesh) if args.evih_mesh else None,
                    source_mesh_gif_path=Path(args.source_mesh_gif) if args.source_mesh_gif else None,
                    evih_mesh_gif_path=Path(args.evih_mesh_gif) if args.evih_mesh_gif else None,
                    frame_count=args.gif_frames,
                    fps=args.gif_fps,
                    width=args.gif_width,
                    height=args.gif_height,
                )
                for key in ("mesh_channel", "source_mesh_data", "evih_mesh_data", "mesh_visual_evidence", "mesh_comparison"):
                    comparison[key] = mesh_evidence[key]
            except Exception as exc:
                comparison.setdefault("failures", []).append(f"character mesh evidence failed: {type(exc).__name__}: {exc}")
                comparison["pass"] = False
                comparison["status"] = "failed"
            if args.require_character_mesh_comparison:
                mesh_failures = []
                if comparison.get("mesh_channel") != common.CHARACTER_MESH_CHANNEL:
                    mesh_failures.append(f"mesh_channel is not {common.CHARACTER_MESH_CHANNEL}")
                for key in ("source_mesh_data", "evih_mesh_data", "mesh_visual_evidence", "mesh_comparison"):
                    if not isinstance(comparison.get(key), dict):
                        mesh_failures.append(f"{key} metadata missing")
                mesh_comparison = comparison.get("mesh_comparison")
                if not isinstance(mesh_comparison, dict) or mesh_comparison.get("pass") is not True:
                    mesh_failures.append(f"mesh comparison failed: {mesh_comparison!r}")
                mesh_visual = comparison.get("mesh_visual_evidence") if isinstance(comparison.get("mesh_visual_evidence"), dict) else {}
                if mesh_visual.get("renderer") != common.EVIHANIMATION_STYLE_MESH_RENDERER:
                    mesh_failures.append(f"mesh visual renderer is not {common.EVIHANIMATION_STYLE_MESH_RENDERER}: {mesh_visual.get('renderer')!r}")
                for key in ("source_mesh_gif", "evih_mesh_gif"):
                    gif_payload = mesh_visual.get(key) if isinstance(mesh_visual, dict) else None
                    if isinstance(gif_payload, dict) and gif_payload.get("renderer") != common.EVIHANIMATION_STYLE_MESH_RENDERER:
                        mesh_failures.append(f"{key} renderer is not {common.EVIHANIMATION_STYLE_MESH_RENDERER}: {gif_payload.get('renderer')!r}")
                    quality = gif_payload.get("sequence_quality") if isinstance(gif_payload, dict) else None
                    if not isinstance(quality, dict) or quality.get("pass") is not True:
                        mesh_failures.append(f"{key} sequence quality failed: {quality!r}")
                if mesh_failures:
                    comparison.setdefault("failures", []).extend(mesh_failures)
                    comparison["pass"] = False
                    comparison["status"] = "failed"
        try:
            if args.require_gifs:
                common.validate_visual_evidence(visual_evidence)
        except AssertionError as exc:
            comparison.setdefault("failures", []).append(f"visual evidence failed: {exc}")
            comparison["pass"] = False
            comparison["status"] = "failed"
        common.attach_comparison_payload(payload, baseline, comparison)
        common.write_comparison_report(comparison, report_path)
        if args.require_comparison:
            _validate_comparison(core, comparison)
        if args.require_gifs:
            common.validate_visual_evidence(visual_evidence)
    core.save_generated(payload, artifact)
    saved_payload = core.load_generated(artifact)
    core.validate_metrics(saved_payload["metrics"])
    if args.screenshot:
        viewer.render_artifact(artifact, Path(args.screenshot), args.frame, args.width, args.height, args.max_frames)
    if args.require_comparison and comparison is not None:
        print(json.dumps(common.json_safe({"metrics": saved_payload["metrics"], "comparison": comparison}), sort_keys=True))
    else:
        print(json.dumps(common.json_safe(saved_payload["metrics"]), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
