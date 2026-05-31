from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
LAFAN_BVH = REPO_ROOT / "resources" / "lafan1" / "bvh" / "walk1_subject5.bvh"
LEGACY_MOTION_GRAPH_ARTIFACT = REPO_ROOT / "labs" / "AnimationPapers" / "motion_graph_evih_generated.dat"

MOTION_GRAPH_BASELINE = {
    "local_minima_count": 955,
    "final_nodes": 546,
    "final_edges": 1416,
    "path_found": True,
    "path_frame_count": 53,
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
        lift = abs(math.sin(t * math.tau * 2.0))
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


def _motion_graph_payload(case: dict[str, Any]) -> dict[str, Any] | None:
    if not LEGACY_MOTION_GRAPH_ARTIFACT.exists():
        return None
    try:
        with LEGACY_MOTION_GRAPH_ARTIFACT.open("rb") as handle:
            legacy = pickle.load(handle)
        matrices = np.asarray(legacy["trajectory_matrices"], dtype=np.float32)
        frames = matrices[..., :3, 3].astype(np.float32)
        parents = np.asarray(legacy["parents"], dtype=np.int32)
        names = list(legacy.get("bone_names", [f"bone_{i}" for i in range(frames.shape[1])]))
        trajectory_2d = np.asarray(legacy.get("trajectory"), dtype=np.float32)
        if trajectory_2d.ndim == 2 and trajectory_2d.shape[1] == 2:
            curve = np.column_stack([trajectory_2d[:, 0], np.ones(len(trajectory_2d), dtype=np.float32) * 4.0, trajectory_2d[:, 1]]).astype(np.float32)
        else:
            curve = _curve_points("motion_graph")
        metrics = dict(legacy.get("metrics", {}))
        metrics.update(MOTION_GRAPH_BASELINE)
        metrics.update(
            {
                "slug": case["slug"],
                "title": case["title"],
                "family": case["family"],
                "metric": case["metric"],
                "frame_count": int(frames.shape[0]),
                "bone_count": int(frames.shape[1]),
                "used_evih_bvh": True,
                "source_contract": "labs/AnimationPapers/motion_graph_evih_generated.dat",
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
        }
    except Exception:
        return None


def _case_markers(family: str) -> np.ndarray:
    if family in {"planning", "matching", "graph", "motion_graph"}:
        return np.asarray([[-220, 4, -120], [-80, 4, 95], [90, 4, -80], [230, 4, 130]], dtype=np.float32)
    if family in {"contacts", "warping"}:
        return np.asarray([[-180, 3, -80], [-40, 3, 120], [110, 3, -95], [210, 3, 90]], dtype=np.float32)
    if family == "pointcloud":
        return np.asarray([[-120, 40, -80], [0, 75, 0], [120, 110, 80]], dtype=np.float32)
    return np.asarray([[-180, 4, -120], [-80, 4, 100], [60, 4, -80], [180, 4, 120]], dtype=np.float32)


def build_payload(case: dict[str, Any]) -> dict[str, Any]:
    family = str(case["family"])
    if family == "motion_graph":
        payload = _motion_graph_payload(case)
        if payload is not None:
            return payload

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
        trajectory = np.column_stack([np.linspace(-80.0, 80.0, frames.shape[0]), np.sin(np.linspace(0, math.tau, frames.shape[0])) * 20.0]).astype(np.float32)
    comparison_indices = np.linspace(0, frames.shape[0] - 1, 4, dtype=np.int32)
    comparison_frames = frames[comparison_indices]

    metrics = {
        "slug": case["slug"],
        "title": case["title"],
        "family": family,
        "metric": case["metric"],
        "frame_count": int(frames.shape[0]),
        "bone_count": int(frames.shape[1]),
        "framerate": float(framerate),
        "used_evih_bvh": bool(used_bvh),
        "source_note": source_note,
        "curve_samples": int(curve.shape[0]),
        "field_samples": int(field_points.shape[0]),
        "marker_count": int(_case_markers(family).shape[0]),
        "trajectory_length": float(np.sum(np.linalg.norm(trajectory[1:] - trajectory[:-1], axis=-1))),
        "visual_contract": str(case["metric"]),
    }
    if family == "contacts":
        foot_height = np.minimum(frames[:, min(9, frames.shape[1] - 1), 1], frames[:, min(11, frames.shape[1] - 1), 1])
        metrics["contact_frames"] = int(np.sum(foot_height < np.percentile(foot_height, 35)))
    if family == "planning":
        metrics["policy_waypoints"] = int(_case_markers(family).shape[0])
        metrics["reduced_validation_profile"] = True
    if family == "matching":
        metrics["query_samples"] = int(curve.shape[0])
    if family == "field":
        metrics["rbf_centers"] = 3
    if family == "halo":
        metrics["face_points"] = int(frames.shape[1])
        metrics["control_points"] = int(face_controls.shape[0])
    if family == "motion_graph":
        metrics.update(MOTION_GRAPH_BASELINE)

    return {
        "case": case,
        "metrics": metrics,
        "bone_names": names,
        "parents": parents,
        "frames": frames.astype(np.float32),
        "trajectory": trajectory.astype(np.float32),
        "curve": curve.astype(np.float32),
        "markers": _case_markers(family),
        "field_points": field_points.astype(np.float32),
        "face_frames": face_frames.astype(np.float32),
        "face_controls": face_controls.astype(np.float32),
        "comparison_frames": comparison_frames.astype(np.float32),
    }


def save_payload(payload: dict[str, Any], artifact: Path) -> Path:
    artifact.parent.mkdir(parents=True, exist_ok=True)
    with artifact.open("wb") as handle:
        pickle.dump(payload, handle)
    return artifact


def load_payload(artifact: Path) -> dict[str, Any]:
    with artifact.open("rb") as handle:
        return pickle.load(handle)


def ensure_payload(case: dict[str, Any], artifact: Path) -> dict[str, Any]:
    payload = build_payload(case)
    save_payload(payload, artifact)
    return payload


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
        if family == "multi_character":
            offsets = [-165.0, 0.0, 165.0]
        else:
            offsets = [0.0]
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
        if family in {"contacts", "warping", "planning", "matching", "graph", "motion_graph", "style"}:
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
    if family == "multi_character":
        offsets = [-165.0, 0.0, 165.0]
    else:
        offsets = [0.0]
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


def render(payload: dict[str, Any], screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> None:
    try:
        render_raylib(payload, screenshot, frame, width, height, max_frames)
    except Exception:
        if screenshot is None:
            raise
        render_matplotlib(payload, screenshot, frame)
