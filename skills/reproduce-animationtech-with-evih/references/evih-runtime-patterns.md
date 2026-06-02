# Evih Runtime Patterns

Use `labs/AnimationPapers/evih_motion_graph` as the canonical shape. New reproductions should be case-local modules with a shared runner only for dispatch.

## Standard Layout

For original slug `<slug>`:

```text
labs/evih_reproductions/
  runner.py                 # lightweight dispatcher only
  common.py                 # small cross-case helpers only
  <slug>/
    __init__.py
    core.py                 # deterministic computation and validation contract
    viewer.py               # Raylib artifact viewer
    generated.dat
```

Manifest entry:

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

Do not replace original notebooks. Do not finish with a generic family smoke renderer as the only implementation.

## Core Contract

Every `core.py` exposes:

```python
CONTRACT: dict[str, Any]

def run_pipeline(repo_root: Path | None = None, strict_baseline: bool = True, **kwargs) -> dict[str, Any]: ...
def save_generated(result: dict[str, Any], output_path: Path | None = None) -> Path: ...
def load_generated(path: Path | None = None) -> dict[str, Any]: ...
def validate_metrics(metrics: dict[str, Any]) -> None: ...
def load_or_bake_baseline(repo_root: Path | None = None, baseline_path: Path | None = None, evih_payload: dict[str, Any] | None = None) -> dict[str, Any]: ...
def compare_to_baseline(evih_payload: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]: ...
def validate_comparison(comparison: dict[str, Any]) -> None: ...
```

The artifact must include `metrics`. Once baseline comparison is enabled it must also include `input_signature`, `baseline_signature`, `evih_output`, and `comparison`. For motion cases it should include matrix or position arrays, parents, bone names, trajectory/debug overlays, and any contact/target data needed by the viewer. For theory cases it should include sampled values and debug geometry. For fallback cases it must include the fallback source and allowed differences.

## Viewer Contract

Every `viewer.py` accepts:

```text
--artifact <path>
--screenshot <path>
--frame <int>
--max-frames <int>
--width <int>
--height <int>
```

The viewer loads an artifact, calls `validate_metrics()`, renders with Raylib, saves a screenshot when requested, and exits after screenshot capture or after `--max-frames` frames. Matplotlib fallback is acceptable only for screenshot validation.

The shared runner accepts `--baseline`, `--comparison-report`, `--require-comparison`, `--evih-gif`, `--source-gif`, and `--require-gifs`. Managed `_evih` runs should use these flags so `passed` means artifact, screenshot, metrics, baseline comparison, and dynamic GIF evidence all passed.

## Shared Code

Shared helpers may provide serialization, Evih BVH loading, drawing primitives, and reduced-profile utilities. Shared code must not hide a case’s behavioral contract. Case-specific constants, expected counts, allowed differences, and schema notes live in the case-local `core.py`.

## Motion Graph Adapter

`motion_graph_evih` may keep using `labs/AnimationPapers/evih_motion_graph` as the canonical implementation. The `labs/evih_reproductions/motion_graph` package should be a thin adapter that loads or builds the canonical artifact, standardizes it for the shared runner, and validates the Motion Graph baseline.
