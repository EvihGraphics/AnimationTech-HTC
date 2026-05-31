# Evih Runtime Patterns

Use these patterns for new AnimationTech Evih/Raylib reproductions.

## Standard Layout

Current repository shape uses a shared runner. For original slug `<slug>`:

```text
labs/evih_reproductions/
  __init__.py
  cases.py
  runtime.py
  runner.py
  <slug>/
    generated.dat
```

Manifest entry, when integration is explicitly in scope:

```text
slug: <slug>_evih
kind: python_script
entry: labs/evih_reproductions/runner.py
template: papers-evih
python_version: 3.12
env_prefix: .envs/<slug>_evih
kernel_name: animationtech-<slug>_evih
generated_artifacts:
  - labs/evih_reproductions/<slug>/generated.dat
script_args:
  - --case
  - <slug>
```

Do not replace the original case or move original notebooks. Add Evih reproductions beside them. If a case needs a dedicated viewer, keep the same CLI and document why the shared runner is not enough.

## Runtime Split

Put deterministic computation in the shared runtime or a case module:

- Load source data and public assets.
- Convert EvihAnimation motions to a small local data model.
- Compute case-specific metrics and generated playback data.
- Save and load artifacts.
- Expose a `run_pipeline(...)` function or equivalent small API.

Put visualization in `runtime.py`, `runner.py`, or a case-local viewer:

- Parse CLI arguments, including `--case` for the shared runner.
- Generate the artifact if missing or if `--rebuild` is provided.
- Load the artifact.
- Draw with Raylib.
- Save a screenshot when requested.
- Exit after screenshot capture or after `--max-frames` frames.

Keep notebooks optional. The Raylib script is the primary case entrypoint.

## Common CLI

Every entrypoint should accept:

```text
--case <original_slug>   # required for shared runner
--artifact <path>
--screenshot <path>
--frame <int>
--max-frames <int>
--width <int>
--height <int>
```

Recommended behavior:

- `--max-frames 0` renders one selected frame, saves a screenshot if requested, and exits.
- `--max-frames N` advances playback and exits after `N` frames.
- `--artifact` may be required by the managed runner; otherwise default it to the case-local `generated.dat`.
- `--screenshot` creates parent directories.
- If Raylib writes the screenshot into the current working directory, move it to the requested path before exit.

## EvihAnimation Data Model

Prefer a small dataclass around EvihAnimation output:

```python
@dataclass
class MotionData:
    bone_names: list[str]
    parents: np.ndarray
    global_matrices: np.ndarray
    framerate: float
    source: str

    @property
    def positions(self) -> np.ndarray:
        return self.global_matrices[..., :3, 3]
```

For BVH:

```python
from ai4animation.Import.BVHImporter import BVH

motion = BVH(str(path)).LoadMotion()
bone_names = list(motion.Hierarchy.BoneNames)
parents = np.asarray(motion.Hierarchy.ParentIndices, dtype=np.int32)
global_matrices = np.asarray(motion.Frames, dtype=np.float32)
framerate = float(motion.Framerate)
```

If the source case uses ipyanimlab mapping for compatibility, keep that mapping in `core.py` and document why it remains part of the parity contract.

## Raylib Drawing

Use `pyray` from the `raylib` package:

- Initialize with MSAA when available.
- Set a fixed camera and target FPS.
- Clear to a readable background.
- Draw ground/reference grids for motion cases.
- Draw bones with `draw_line_3d` and joints with small spheres.
- Draw trajectories, targets, contacts, or debug overlays in distinct colors.
- Draw short title/frame text; avoid long instructions in the app.
- Always call `close_window()` before returning.

When Raylib cannot run in the environment, a matplotlib fallback is acceptable for screenshot validation, but the primary path should remain Raylib.

## Case Group Patterns

- Curves and spline cases: precompute sampled points and draw polylines, control points, tangents, and numeric error overlays.
- RBF cases: draw weighted points, interpolation fields, sampled curves, or heatmap grids.
- Point-cloud and graph theory cases: draw points, edges, selected minima, and graph diagnostics.
- Character and USD cases: use Evih/Raylib equivalent meshes or skeletons; keep visual theme and behavior rather than exact ipyanimlab API calls.
- Motion warping and editing cases: show source versus result skeleton/root paths with aligned frame counts and clear target markers.
- Motion matching/planning cases: preserve nearest-neighbor or value-function metrics, then draw selected motion, query vector/debug path, and policy output.
- Halo/facial cases: render synthetic or exported facial vertices/curves/control points with nonempty expression changes.

## Concurrency Rules

Multiple agents may work in the repository. Before writing:

- Check `git status --short`.
- Use non-overlapping case directories.
- Avoid shared manifest/template edits unless you are the integration owner.
- Do not rewrite generated artifacts from another agent's case unless asked.
