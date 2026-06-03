# Failure Modes

Use this list when an Evih/Raylib reproduction fails or gives suspicious output.

## Concurrent Edits

Symptoms:

- `tools/cases.yaml` has unrelated status churn.
- Another agent's case directory changes while you work.
- Generated artifacts disappear or change size unexpectedly.

Actions:

- Check `git status --short` before writing.
- Keep work inside the assigned case directory.
- Leave shared manifest/template changes to the integration owner unless explicitly assigned.
- Never revert unrelated changes.

## EvihAnimation Import Fails

Symptoms:

- `ModuleNotFoundError: ai4animation`
- BVH load errors
- Missing `EvihAnimation` dependency after environment creation

Actions:

- Confirm the case uses `template: papers-evih` and `python_version: 3.12`.
- Confirm `tools/templates/papers-evih.txt` includes the pinned EvihAnimation Git dependency.
- Run the case env setup before direct viewer invocation.
- Keep a clear error message that tells the next agent which env setup command to run.

## Raylib Screenshot Problems

Symptoms:

- Window opens but no screenshot appears at the requested path.
- Screenshot appears in the current working directory.
- Headless or GPU display errors.

Actions:

- Create the screenshot parent directory before capture.
- After `take_screenshot`, check both the requested path and `Path.cwd() / screenshot.name`; move the latter if necessary.
- Exit immediately after the first screenshot when `--max-frames 0`.
- Provide a matplotlib fallback only for screenshot validation; keep Raylib as the primary path.

## Artifact Schema Drift

Symptoms:

- Viewer cannot load generated data.
- Skeleton lines connect wrong joints.
- Character explodes, appears flat, or disappears.

Actions:

- Check artifact keys and array shapes.
- Confirm parents use `-1` for root or match the local drawing code.
- Confirm matrices are global transforms shaped `[frame, bone, 4, 4]`.
- Confirm positions come from `matrix[:3, 3]`.
- Use `float32` for large arrays to avoid unexpected file size and numeric drift.

## Metric Drift

Symptoms:

- Local minima, node counts, path frames, or loss values differ from baseline.
- CPU and CUDA produce slightly different results.

Actions:

- Re-run with a deterministic seed and fixed validation profile.
- Compare array shapes before comparing values.
- Allow only documented tolerances.
- For Motion Graph, keep the known parity correction unless the distance algorithm is re-baselined.
- Record backend/device in `metrics`.

## Visual Looks Plausible But Is Wrong

Symptoms:

- Screenshot is nonblank but misses the required concept.
- Skeleton is visible but target path/contact/debug data is absent.
- Theory case draws decoration but not the sampled result.
- `animationtech_source.gif` is a blog asset but shows raw input, a debug/log cell, or a static/subjectless recording instead of the final algorithm result.

Actions:

- Re-read the original notebook outputs and generated blog assets.
- Identify the smallest visual evidence that proves the case concept.
- Add debug overlays before polishing colors or camera.
- Make the screenshot deterministic by fixing frame, camera, and seed.
- Select the last key animation/result cell for `animationtech_source.gif`; regenerate from the baseline/source payload when the blog GIF is static, missing the character/subject, or not algorithm-specific.

## Heavy Case Runtime

Symptoms:

- Validation takes too long.
- GPU memory spikes.
- Precompute artifacts are huge.

Actions:

- Use validate/adaptive profiles before quality profiles.
- Prefer CPU for cases already known to behave better on CPU.
- Cache generated artifacts only when the task requires it.
- Keep artifact generation resumable and fail with a clear note if external assets are missing.
