# Case Contract Template

Use this checklist before marking a reproduction complete.

## Source Contract

- Original slug and source file.
- Learning objective or algorithm behavior being reproduced.
- Source assets and fallback assets.
- Important cell outputs, array shapes, frame counts, graph counts, losses, contact counts, or controller states.
- Visual evidence expected in the screenshot and in dynamic GIF comparison.

## Core Module

`core.py` must define:

- `CONTRACT` with `contract_name`, `source_case`, `source_contract`, `artifact_schema`, `expected`, `minimums`, and `allowed_differences`.
- `run_pipeline(...)` that builds deterministic artifact payload data.
- `save_generated(...)` and `load_generated(...)` for the case-local `generated.dat`.
- `validate_metrics(...)` that asserts the contract.
- `load_or_bake_baseline(...)`, `compare_to_baseline(...)`, and `validate_comparison(...)` for baseline comparison.

## Artifact

The pickle payload should include:

- `metrics`
- source/case metadata
- sampled arrays or matrices
- viewer geometry such as trajectories, targets, contacts, fields, points, or control curves
- fallback provenance when original external tooling is unavailable
- `input_signature`, `baseline_signature`, `evih_output`, and `comparison` after managed execution

## Viewer

`viewer.py` must load the artifact, call `validate_metrics()`, draw the required visual evidence with Raylib, save `--screenshot`, and exit unattended with `--max-frames 0`.

## Acceptance

- `run_case.ps1 <slug>_evih` exits `0`.
- `check_evih_reproduction.py --strict --validate-metrics` reports no findings.
- `check_evih_reproduction.py --require-baseline-comparisons` reports no findings.
- Artifact exists and is nonempty.
- Screenshot exists, is a PNG, is nonblank, and shows the case-specific evidence.
- `.reports/animation-comparisons/<slug>_evih/comparison.json` exists with `pass == true`.
- `.reports/animation-comparisons/<slug>_evih/evih.gif` and `animationtech_source.gif` exist, are dynamic, and the source GIF metadata identifies the expected final/core algorithm subject.
- Visual parity is backed by dynamic sequence evidence, not by a single static screenshot.
