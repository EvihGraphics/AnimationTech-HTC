# Validation

Use both structural and behavioral validation. Passing only one side is not enough.

## Read-Only Structural Check

Run the bundled checker from the repository root:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root .
```

Focused checks:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --case motion_graph
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --case motion_graph_evih --json
```

Final matrix checks:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --require-artifacts --require-screenshots
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons
```

The checker is read-only. It should be safe when other agents are working.

## Case Execution

The managed repository entrypoint is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>_evih
```

Important: `run_case.ps1` updates status fields in `tools/cases.yaml`. If the current task forbids manifest edits, do not run it; use direct viewer invocation and the read-only checker instead.

Direct viewer smoke test:

```powershell
.\.envs\<slug>_evih\python.exe .\labs\evih_reproductions\runner.py `
  --case <slug> `
  --artifact .\labs\evih_reproductions\<slug>\generated.dat `
  --screenshot .\.reports\visual-checks\<slug>_evih\final.png `
  --max-frames 0
```

Baseline comparison execution:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>_evih
```

This writes `.reports/animation-baselines/<slug>_evih/baseline.dat`, `.reports/animation-comparisons/<slug>_evih/comparison.json`, `.reports/animation-comparisons/<slug>_evih/evih.gif`, and `.reports/animation-comparisons/<slug>_evih/animationtech_source.gif`. Use `-SmokeOnly` only when intentionally checking the screenshot path without treating the result as complete.

## Completion Criteria

For each Evih reproduction:

- Manifest entry exists when integration is in scope.
- Entry script exists and has the standard CLI.
- Generated artifact exists and is nonempty after execution.
- Screenshot exists, is a PNG, and is nonempty.
- Case-specific metrics match the original contract or document intentional differences.
- Baseline comparison report exists and has `pass == true`.
- `evih.gif` and `animationtech_source.gif` exist in the comparison directory, are dynamic, and `comparison.json.visual_evidence.source_gif.algorithm_feature_match == true`.
- Viewer exits unattended with `--screenshot --max-frames 0`.
- Original non-Evih case still runs or remains untouched.

For full matrix completion:

- Every original case in `tools/cases.yaml` has a matching `<slug>_evih` entry.
- Heavy training/precompute cases use validate/adaptive profiles instead of forcing GPU.
- Original cases remain behaviorally unchanged.

## Visual Review Checklist

Open the screenshot or inspect it with a pixel-aware tool when checking smoke evidence:

- The image is not blank or a single flat color.
- Main subject is visible and framed.
- Debug overlays are visible when they are part of the contract.
- Text does not hide the main subject.
- For motion cases, skeleton, root path, target path, or contacts are visible.
- For theory cases, sampled geometry or fields are visible.

Do not use a single static screenshot as visual parity proof. Visual comparison for animation cases must use dynamic sequence evidence. For `_evih` managed runs, this means the generated `evih.gif` and `animationtech_source.gif` plus frame arrays, root trajectories, contacts/control time series, or other sampled time-series checks. The source GIF must show the case's final/core algorithm subject; if a blog GIF is static, misses the character/subject, or shows raw input/debug content, regenerate it from the baseline/source payload and record `replaced_reason`.

## Metrics Review

Prefer explicit assertions in `core.py` or a local validation function:

- Shape checks for arrays and matrices.
- Count checks for frames, bones, points, graph nodes, or generated samples.
- Tolerance checks for floating-point values.
- Deterministic seed and reduced data profiles for stochastic or expensive cases.

Keep validation output short and actionable. Long notebooks are not a substitute for a clear pass/fail signal.
