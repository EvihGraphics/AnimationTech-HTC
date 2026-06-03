# AnimationTech Local Runbook

As of 2026-03-19, all 26 cases in this repository pass automated validation with repo-local environments.

Everything stays inside the repository:
- `.envs/` holds one Conda prefix environment per case.
- `.jupyter/` holds local kernels and Jupyter state.
- `.reports/` holds logs, executed notebooks, lock files, and status snapshots.
- `resources/` and `labs/AnimationPapers/animated_face.dat` hold downloaded or generated assets required by the cases.

## Quick Commands

Prepare public assets:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_assets.ps1
```

Run one case:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>
```

Open the browser-safe AnimationPapers study entry:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

Re-run the full matrix:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate_all.ps1
```

Run an Evih/Raylib reproduction with baseline comparison:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>_evih
```

Run only the Evih screenshot smoke path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>_evih -SmokeOnly
```

Check the Evih baseline comparison matrix:

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons --require-source-skeleton-baselines --require-character-mesh-comparisons
```

Read the latest summary:

```powershell
Get-Content .\.reports\summary.json -Raw
```

Case env mapping and startup reference:

```text
docs/cases/README.md
```

## Execution Model

- Before re-creating or reinstalling an environment, always check if the target environment already exists locally to avoid unnecessary reinstallations.
- Every case gets its own local Conda prefix environment.
- Notebook execution always runs from the notebook directory so relative paths resolve correctly.
- Source notebooks are never edited in place for automation. Execution-only changes are applied to prepared copies.
- Logs are written to `.reports/logs/<slug>.log`.
- Executed notebooks are written to `.reports/executed/<slug>/`.
- Resolved package versions are written to `.reports/locks/<slug>.txt`.
- Evih baseline caches are written to `.reports/animation-baselines/<slug>_evih/baseline.dat`.
- Evih comparison reports are written to `.reports/animation-comparisons/<slug>_evih/comparison.json`.
- Evih visual comparison GIFs are written next to the report as `.reports/animation-comparisons/<slug>_evih/evih.gif` and `.reports/animation-comparisons/<slug>_evih/animationtech_source.gif`.
- For skeletal/BVH `_evih` cases, the strict source channel also writes `.reports/animation-comparisons/<slug>_evih/animationtech_source.dat`. That DAT stores the AnimationTech source skeleton trajectory (`global_positions`, `parents`, `bone_names`, `root_trajectory`, `fps`, `frame_count`, and source signature), and `animationtech_source.gif` is rendered from that DAT with the same skeleton/trajectory renderer used for `evih.gif`.
- Skeletal/BVH `_evih` cases also write strict character mesh evidence: `animationtech_source_mesh.dat`, `evih_mesh.dat`, `animationtech_source_mesh.gif`, and `evih_mesh.gif`. These use the real `AnimLabSimpleMale.usd` skinned mesh buffers, deterministic CPU skinning for the numeric DAT channel, and an EvihAnimation-style Raylib renderer for the dynamic mesh GIF channel; blog GIFs, CPU/PIL polygon renders, and skeleton-only views cannot satisfy mesh strict comparison.

For `_evih` cases, `passed` means the artifact, screenshot, metrics, baseline comparison, and required dynamic GIF evidence all passed. `smoke_passed` is reserved for `-SmokeOnly`, where the Raylib screenshot path passed but baseline comparison and GIF visual comparison were intentionally skipped.

Static screenshots are only smoke evidence. Visual comparison for `_evih` work must inspect dynamic sequence evidence: every baseline comparison directory must contain `evih.gif` for the Evih result and `animationtech_source.gif` for the AnimationTech source result. For skeletal/BVH cases, blog GIFs are supplemental only; strict pass requires `source_channel == "animationtech_skeleton_trajectory"`, `mesh_channel == "animationtech_skinned_character_mesh"`, source/evih DATs, and same-renderer source/evih GIFs. The strict mesh GIF renderer must be `evihanimation_style_raylib`, which follows the EvihAnimation/AI4AnimationPy Raylib scene style with real skinned character mesh data, a perspective actor camera, ground grid, directional lighting, and trajectory overlay. For non-skeletal cases, the source GIF must show the case's final/core algorithm subject, normally the last key visualization cell in the blog/notebook assets. Blog GIFs are candidates only; if the selected asset is static, missing the subject, or represents raw input/debug content instead of the algorithm result, the runner regenerates `animationtech_source.gif` from the baseline/source payload and records `replaced_reason` in `comparison.json`.

## Special Handling

- `lafan1` is downloaded into `resources/lafan1/bvh` from a direct public archive URL instead of relying on the original Git LFS path.
- `Motion Fields For Interactive Character Animation.ipynb` runs from a prepared copy with CPU fallback, smaller state ranges, lighter UMAP settings, reduced training epochs, and precompute enabled when the `.dat` file is missing.
- `Real-Time Planning for Parameterized Human Motion.ipynb` runs from a prepared copy that turns on the hidden precompute path and scales down the workload for unattended validation.
- `Knowing When To Put Your Foot Down.ipynb` runs from a prepared copy that trims the dataset window and skips purely interactive demo cells.
- `Halo 4 Facial Animation.ipynb` is unblocked by a local synthetic `animated_face.dat` generator when Maya-exported data is unavailable.
- `Halo 4 exporter from maya.py` now exports from Maya when available and otherwise falls back to the same synthetic asset generator for unattended validation.

## Training Hardware Guidance

- The benchmark machine for the training-heavy cases was `Ryzen 9 7950X / 64 GB RAM / 2 x RTX 4090`.
- `Motion Fields For Interactive Character Animation.ipynb` is CPU-preferred on this implementation. Even with CUDA-enabled PyTorch available, the measured adaptive profile was faster on CPU than on either GPU.
- `Real-Time Planning for Parameterized Human Motion.ipynb` is CPU-only and benefits from capped parallelism. The best measured adaptive profile used `12` workers on the 7950X; pushing past that caused regressions.
- The dual-GPU setup is currently useful for running separate cases in parallel, not for accelerating a single notebook end to end.

## Manual Smoke

All viewer-heavy notebooks now pass automated execution. A manual JupyterLab smoke pass is still recommended for interactive `ipyanimlab` notebooks if visual validation is required.

For day-to-day interactive preview and visual debugging, use the browser JupyterLab entrypoint instead of the VSCode notebook renderer. This repository's `ipyanimlab` and `ipywebgl` cases are validated against browser JupyterLab.

For AnimationPapers study sessions, prefer the managed launcher:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

The launcher reads `tools/cases.yaml`, checks the managed AnimationPapers cases, prepares missing environments, kernels, and study notebooks with `run_case.ps1`, and opens `.reports/study/AnimationPapers`. That study directory contains stable prepared notebook copies; the raw `labs/AnimationPapers/*.ipynb` files remain source references, not the guaranteed one-click learning surface.

Useful launcher options:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -NoOpen
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -ForceVerify
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -NoReuseServer
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -Port 8891
```

To launch JupyterLab for a specific case environment, use the local python executable (do not rely on a globally installed `jupyter`):

```powershell
.\.envs\<slug>\python.exe -m jupyter lab
```
