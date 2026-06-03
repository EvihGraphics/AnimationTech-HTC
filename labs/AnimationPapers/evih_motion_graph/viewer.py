from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from evih_motion_graph.core import GENERATED_ARTIFACT, animation_papers_dir_from_here, load_generated
else:
    from .core import GENERATED_ARTIFACT, animation_papers_dir_from_here, load_generated


def _artifact_path(value: str | None) -> Path:
    if value:
        return Path(value)
    return animation_papers_dir_from_here() / GENERATED_ARTIFACT


def _project(points: np.ndarray, width: int, height: int) -> np.ndarray:
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    sx = width * 0.52 + (x - z) * 0.55
    sy = height * 0.70 - y * 0.75 + (x + z) * 0.12
    return np.column_stack([sx, sy])


def render_matplotlib(payload: dict[str, object], screenshot: Path, frame: int = 0) -> None:
    import matplotlib.pyplot as plt

    matrices = np.asarray(payload["trajectory_matrices"], dtype=np.float32)
    parents = np.asarray(payload["parents"], dtype=np.int32)
    trajectory = np.asarray(payload["trajectory"], dtype=np.float32)
    trajectory_check = np.asarray(payload["trajectory_check"], dtype=np.float32)
    frame = int(np.clip(frame, 0, matrices.shape[0] - 1))
    points = matrices[frame, :, :3, 3]

    fig = plt.figure(figsize=(12, 7), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#83aee0")
    grid = np.linspace(-350, 350, 15)
    for g in grid:
        ax.plot([-350, 350], [0, 0], [g, g], color="#555b66", linewidth=0.6)
        ax.plot([g, g], [0, 0], [-350, 350], color="#555b66", linewidth=0.6)
    for i, parent in enumerate(parents):
        if parent >= 0:
            xs = [points[parent, 0], points[i, 0]]
            ys = [points[parent, 1], points[i, 1]]
            zs = [points[parent, 2], points[i, 2]]
            ax.plot(xs, ys, zs, color="#f5f7fb", linewidth=3)
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], color="#162039", s=14)
    draw_traj = np.ones((trajectory.shape[0], 3), dtype=np.float32)
    draw_traj[:, [0, 2]] = trajectory
    ax.plot(draw_traj[:, 0], draw_traj[:, 1], draw_traj[:, 2], color="#101010", linestyle="--", linewidth=1.5)
    ax.plot(
        [trajectory_check[frame, 0], points[0, 0]],
        [trajectory_check[frame, 1], points[0, 1]],
        [trajectory_check[frame, 2], points[0, 2]],
        color="#ff4040",
        linewidth=2,
    )
    ax.set_xlim(-350, 350)
    ax.set_ylim(0, 230)
    ax.set_zlim(-350, 350)
    ax.view_init(elev=18, azim=-55)
    ax.set_axis_off()
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(screenshot, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def render_raylib(payload: dict[str, object], screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> None:
    import pyray as rl

    matrices = np.asarray(payload["trajectory_matrices"], dtype=np.float32)
    parents = np.asarray(payload["parents"], dtype=np.int32)
    trajectory = np.asarray(payload["trajectory"], dtype=np.float32)
    trajectory_check = np.asarray(payload["trajectory_check"], dtype=np.float32)
    current = int(np.clip(frame, 0, matrices.shape[0] - 1))

    rl.set_config_flags(rl.FLAG_MSAA_4X_HINT)
    rl.init_window(width, height, "Motion Graph EvihAnimation")
    rl.set_target_fps(30)
    camera = rl.Camera3D(
        rl.Vector3(-430.0, 280.0, 430.0),
        rl.Vector3(0.0, 85.0, 0.0),
        rl.Vector3(0.0, 1.0, 0.0),
        45.0,
        rl.CAMERA_PERSPECTIVE,
    )
    captured = False
    ticks = 0
    while not rl.window_should_close():
        if max_frames > 0:
            current = (frame + ticks) % matrices.shape[0]
        points = matrices[current, :, :3, 3]
        rl.begin_drawing()
        rl.clear_background(rl.Color(130, 174, 224, 255))
        rl.begin_mode_3d(camera)
        rl.draw_grid(30, 25.0)
        for i, parent in enumerate(parents):
            if parent < 0:
                continue
            a = rl.Vector3(float(points[parent, 0]), float(points[parent, 1]), float(points[parent, 2]))
            b = rl.Vector3(float(points[i, 0]), float(points[i, 1]), float(points[i, 2]))
            rl.draw_line_3d(a, b, rl.RAYWHITE)
            rl.draw_sphere(b, 2.8, rl.Color(25, 32, 48, 255))
        for a, b in zip(trajectory[:-1], trajectory[1:]):
            rl.draw_line_3d(
                rl.Vector3(float(a[0]), 1.0, float(a[1])),
                rl.Vector3(float(b[0]), 1.0, float(b[1])),
                rl.BLACK,
            )
        root = points[0]
        target = trajectory_check[current]
        rl.draw_line_3d(
            rl.Vector3(float(root[0]), float(root[1]), float(root[2])),
            rl.Vector3(float(target[0]), float(target[1]), float(target[2])),
            rl.RED,
        )
        rl.end_mode_3d()
        rl.draw_text("EvihAnimation Motion Graph", 24, 22, 22, rl.BLACK)
        rl.draw_text(f"frame {current}/{matrices.shape[0] - 1}", 24, 50, 18, rl.DARKGRAY)
        rl.end_drawing()
        if screenshot and not captured:
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            rl.take_screenshot(str(screenshot))
            cwd_screenshot = Path.cwd() / screenshot.name
            if not screenshot.exists() and cwd_screenshot.exists():
                cwd_screenshot.replace(screenshot)
            captured = True
            if max_frames <= 0:
                break
        ticks += 1
        if max_frames > 0 and ticks >= max_frames:
            break
    rl.close_window()


def main() -> int:
    parser = argparse.ArgumentParser(description="View generated Evih Motion Graph playback.")
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--screenshot", default=None)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--matplotlib-fallback", action="store_true")
    args = parser.parse_args()

    payload = load_generated(_artifact_path(args.artifact))
    screenshot = Path(args.screenshot) if args.screenshot else None
    if args.matplotlib_fallback:
        if screenshot is None:
            raise SystemExit("--matplotlib-fallback requires --screenshot")
        render_matplotlib(payload, screenshot, args.frame)
        return 0
    try:
        render_raylib(payload, screenshot, args.frame, args.width, args.height, args.max_frames)
    except Exception:
        if screenshot is None:
            raise
        render_matplotlib(payload, screenshot, args.frame)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
