---
name: reproduce-animationtech-with-evih
description: Guidance for reproducing AnimationTech cases as EvihAnimation/Raylib implementations. Use when adding, reviewing, or debugging *_evih reproductions for AnimationTech notebooks, AnimationPapers cases, ipyanimlab demos, Motion Graph parity work, Raylib viewer artifacts, EvihAnimation BVH/runtime integration, screenshot validation, or full-case reproduction planning.
---

# Reproduce AnimationTech With Evih

## Overview

Create EvihAnimation/Raylib reproductions as new cases, not replacements for the existing notebooks. Treat the original AnimationTech case as the behavioral contract, then build a Motion Graph style reproduction: a case-local deterministic `core.py`, a thin Raylib `viewer.py`, an explicit artifact schema, `validate_metrics()`, and an unattended screenshot path. A shared family-level smoke renderer is useful only as a temporary scaffold; it is not a completed reproduction.

## Workflow

1. Read `tools/cases.yaml` and the source case before designing the reproduction. Use the manifest as the case inventory, but coordinate before editing it because the repository is commonly shared by several agents.
2. Create a new reproduction shape: slug `<original_slug>_evih`, env prefix `.envs/<original_slug>_evih`, shared entry `labs/evih_reproductions/runner.py --case <original_slug>`, case-local package `labs/evih_reproductions/<original_slug>/`, artifact `labs/evih_reproductions/<original_slug>/generated.dat`, and screenshot `.reports/visual-checks/<original_slug>_evih/final.png`.
3. Preserve the original algorithm contract. Extract frame counts, graph sizes, loss values, contact statistics, generated artifact schemas, visible debug overlays, and any screenshots or logs that prove parity.
4. Use EvihAnimation for motion import/runtime data and Raylib as the main visual entrypoint. Do not translate Jupyter widgets or ipyanimlab APIs cell by cell; reproduce the same concept and outputs as an executable Raylib demo.
5. Split implementation into a pure computation layer and a viewer layer. `core.py` must expose `run_pipeline(...)`, `save_generated(...)`, `load_generated(...)`, and `validate_metrics(...)`. `viewer.py` must accept `--artifact`, `--screenshot`, `--frame`, `--max-frames`, `--width`, and `--height`, then close cleanly after screenshot capture. The shared runner should only dispatch to the case-local modules.
6. Validate with metrics, dynamic GIF sequence evidence, and baseline comparison. A reproduction is not done until the artifact exists, the screenshot smoke is nonempty and plausible, `comparison.json` passes, and the important numerical contract is documented or checked. Static screenshots are never sufficient for animation parity; each comparison directory must contain `evih.gif` and `animationtech_source.gif`.

## Case Strategy

- **Theory cases**: Put sampled curves, point clouds, fields, matrices, or graph debug data in the artifact. Validate sampled counts, shapes, and representative values in `core.py`.
- **ipyanimlab scene cases**: Build equivalent Raylib primitives, meshes, materials, lights, time-of-day changes, or skeleton displays. Preserve the learning objective instead of the widget API, and record that equivalence in the contract.
- **BVH and motion editing cases**: Load with EvihAnimation, normalize motion data into shared matrices, and draw skeletons, root paths, contacts, warp targets, and before/after comparisons. Validate frame, bone, trajectory, and contact/warp counts.
- **Algorithm-heavy paper cases**: Keep the original data flow and baseline metrics, but move playback/export to the Evih/Raylib runtime. Use reduced validation profiles for expensive precompute work and record intentional differences in metrics.
- **Special non-BVH cases**: Use synthetic fallback data when the original external tool is unavailable, but keep the output schema, metrics, and visual evidence strong enough to verify behavior.

## References

- Read `references/motion-graph-contract.md` when using the existing Motion Graph Evih case as the template or when checking baseline graph metrics.
- Read `references/evih-runtime-patterns.md` before adding shared runtime helpers, viewer CLIs, artifact schemas, or Raylib drawing code.
- Read `references/validation.md` before running checks, adding status notes, or deciding whether a reproduction is complete.
- Read `references/failure-modes.md` when Evih imports, Raylib screenshots, metrics, paths, or concurrent edits behave strangely.

## Script

Use the bundled read-only checker for structural validation. Strict mode expects Motion Graph style case-local packages:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root .
```

Useful modes:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --case motion_graph
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --require-artifacts --require-screenshots
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --validate-metrics
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons
```

The checker reads manifests, entries, artifacts, screenshots, GIF visual evidence, comparison reports, and viewer source text. It does not modify `tools/cases.yaml`, `labs/`, `.reports/`, or generated artifacts.
