---
name: reproduce-animationtech-with-evih
description: Guidance for reproducing AnimationTech cases as EvihAnimation/Raylib implementations. Use when adding, reviewing, or debugging *_evih reproductions for AnimationTech notebooks, AnimationPapers cases, ipyanimlab demos, Motion Graph parity work, Raylib viewer artifacts, EvihAnimation BVH/runtime integration, screenshot validation, or full-case reproduction planning.
---

# Reproduce AnimationTech With Evih

## Overview

Create EvihAnimation/Raylib reproductions as new cases, not replacements for the existing notebooks. Treat the original AnimationTech case as the behavioral contract, then build a deterministic Python runtime plus a Raylib viewer that can save a screenshot without manual interaction.

## Workflow

1. Read `tools/cases.yaml` and the source case before designing the reproduction. Use the manifest as the case inventory, but coordinate before editing it because the repository is commonly shared by several agents.
2. Create a new reproduction shape: slug `<original_slug>_evih`, env prefix `.envs/<original_slug>_evih`, shared entry `labs/evih_reproductions/runner.py --case <original_slug>` or a case-local viewer when the repo already uses that pattern, artifact `labs/evih_reproductions/<original_slug>/generated.dat`, and screenshot `.reports/visual-checks/<original_slug>_evih/final.png`.
3. Preserve the original algorithm contract. Extract frame counts, graph sizes, loss values, contact statistics, generated artifact schemas, visible debug overlays, and any screenshots or logs that prove parity.
4. Use EvihAnimation for motion import/runtime data and Raylib as the main visual entrypoint. Do not translate Jupyter widgets or ipyanimlab APIs cell by cell; reproduce the same concept and outputs as an executable Raylib demo.
5. Split implementation into a pure computation layer and a viewer layer. The entrypoint must support `--case` when shared, plus `--artifact`, `--screenshot`, `--frame`, `--max-frames`, `--width`, and `--height`, then close cleanly after screenshot capture.
6. Validate with both metrics and visuals. A reproduction is not done until the artifact exists, the screenshot is nonempty and plausible, and the important numerical contract is documented or checked.

## Case Strategy

- **Theory cases**: Render curves, point clouds, fields, matrices, or graph debug views directly in Raylib. Validate sampled values and visual nonblank screenshots.
- **ipyanimlab scene cases**: Build equivalent Raylib primitives, meshes, materials, lights, time-of-day changes, or skeleton displays. Preserve the learning objective instead of the widget API.
- **BVH and motion editing cases**: Load with EvihAnimation, normalize motion data into shared matrices, and draw skeletons, root paths, contacts, warp targets, and before/after comparisons.
- **Algorithm-heavy paper cases**: Keep the original data flow and baseline metrics, but move playback/export to the Evih/Raylib runtime. Use reduced validation profiles for expensive precompute work.
- **Special non-BVH cases**: Use synthetic fallback data when the original external tool is unavailable, but keep the output schema and visual evidence strong enough to verify behavior.

## References

- Read `references/motion-graph-contract.md` when using the existing Motion Graph Evih case as the template or when checking baseline graph metrics.
- Read `references/evih-runtime-patterns.md` before adding shared runtime helpers, viewer CLIs, artifact schemas, or Raylib drawing code.
- Read `references/validation.md` before running checks, adding status notes, or deciding whether a reproduction is complete.
- Read `references/failure-modes.md` when Evih imports, Raylib screenshots, metrics, paths, or concurrent edits behave strangely.

## Script

Use the bundled read-only checker for structural validation:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root .
```

Useful modes:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --case motion_graph
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --require-artifacts --require-screenshots
```

The checker reads manifests, entries, artifacts, screenshots, and viewer source text. It does not modify `tools/cases.yaml`, `labs/`, `.reports/`, or generated artifacts.
