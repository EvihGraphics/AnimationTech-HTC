# Case Env Mapping And Startup

This document records the environment mapping and the startup flow for every case in this repository.

## Scope

- Source of truth: `tools/cases.yaml`
- Env root: `.envs/`
- Local Jupyter root: `.jupyter/`
- Execution logs and outputs: `.reports/`

## Common Startup Flow

> **Note:** Before setting up a new environment, always check if the target Conda prefix environment already exists locally to avoid unnecessary reinstallations.

### 1. Prepare public assets

Run this once before the dataset-driven notebooks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_assets.ps1
```

### 2. Run one case through the managed entrypoint

This is the default path for all cases:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>
```

Examples:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_matching
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_fields_for_interactive_character_animation -TrainingProfile adaptive
```

### 3. Open the AnimationPapers study entry

For AnimationPapers learning, prefer the managed browser launcher instead of opening the raw notebooks directly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

The launcher reads `tools/cases.yaml`, checks the managed `labs/AnimationPapers/*` cases, prepares missing environments, kernels, and study notebooks through `run_case.ps1`, then opens `.reports/study/AnimationPapers` in JupyterLab.

The study directory contains stable prepared notebook copies with cleared outputs and matching `animationtech-*` kernels. Keep the raw `labs/AnimationPapers/*.ipynb` files as source references; use `run_case.ps1 <slug>` when validating or debugging one case.

Useful options:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -NoOpen
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -ForceVerify
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -NoReuseServer
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1 -Port 8891
```

### 4. Open another interactive notebook manually

For `manual_smoke` notebooks, first create the case env with `run_case.ps1`, then start JupyterLab from that case env:

```powershell
.\.envs\<env_name>\python.exe -m jupyter lab --notebook-dir .
```

Open the notebook and select the matching kernel:

```text
animationtech-<slug>
```

### 5. Run a Python-module case directly

The managed path is still preferred:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 real_time_planning_multiprocess_func
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 halo_4_exporter_from_maya
```

The Halo exporter also supports direct invocation:

```powershell
.\.envs\halo_4_exporter_from_maya\python.exe ".\labs\AnimationPapers\Halo 4 exporter from maya.py" --output ".\labs\AnimationPapers\animated_face.dat"
```

## Training Runtime Options

These options matter only for the training-heavy cases such as `motion_fields_for_interactive_character_animation` and `real_time_planning_for_parameterized_human_motion`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug> `
  -TrainingProfile validate|adaptive|quality `
  -TorchDevice auto|cpu|gpu `
  -MaxWorkers <N> `
  -GpuIndex <N>
```

Current measured guidance on the benchmark machine:

- `motion_fields_for_interactive_character_animation`: prefer `CPU`
- `real_time_planning_for_parameterized_human_motion`: prefer `CPU` with `-MaxWorkers 12`
- Dual GPUs are useful for running separate cases in parallel, not for speeding up one notebook end to end

## Template To Env Mapping

| Template | Requirement file | Typical use |
| --- | --- | --- |
| `theory-core` | `tools/templates/theory-core.txt` | theory notebooks without `ipyanimlab` |
| `theory-anim` | `tools/templates/theory-anim.txt` | theory notebooks with `ipyanimlab` |
| `ipyanimlab` | `tools/templates/ipyanimlab.txt` | viewer-focused `ipyanimlab` notebooks |
| `papers-core` | `tools/templates/papers-core.txt` | paper notebooks using `lafan1`, plotting, widgets |
| `papers-planning` | `tools/templates/papers-planning.txt` | planning notebooks and helper modules |
| `papers-torch` | `tools/templates/papers-torch.txt` | PyTorch-based paper notebooks |
| `papers-warp` | `tools/templates/papers-warp.txt` | `warp-lang` notebooks |
| `python-stdlib` | `tools/templates/python-stdlib.txt` | script-only case with no notebook stack |
| `blocked_external` | `tools/templates/blocked_external.txt` | reserved template, not used by current passing matrix |
| `maya-external` | `tools/templates/maya-external.txt` | reserved template, not used by current passing matrix |

## Template To Case Groups

| Template | Cases |
| --- | --- |
| `theory-core` | `curve_and_spline`, `motiongraph_pointcloud_derivation`, `radial_basis_function`, `radial_basis_function_verbs_and_adverbs` |
| `theory-anim` | `laplacian_deformation` |
| `ipyanimlab` | `animation`, `character_usd`, `edit_material`, `multiple_characters`, `rigid_usd`, `simple_sphere`, `time_of_day` |
| `papers-core` | `animation_format`, `footskate_cleanup_for_motion_capture_editing`, `halo_4_facial_animation`, `knowing_when_to_put_your_foot_down`, `motion_matching`, `motion_warping`, `verbs_and_adverbs` |
| `papers-planning` | `near_optimal_character_animation_with_continuous_control`, `real_time_planning_for_parameterized_human_motion`, `real_time_planning_multiprocess_func` |
| `papers-torch` | `motion_fields_for_interactive_character_animation` |
| `papers-warp` | `motion_graph`, `precomputing_avatar_behavior` |
| `python-stdlib` | `halo_4_exporter_from_maya` |

## Full Case Matrix

| Slug | Kind | Entry | Template | Env prefix | Kernel | Validation | Startup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `curve_and_spline` | `notebook` | `labs/Theory/curve_and_spline.ipynb` | `theory-core` | `.envs/curve_and_spline` | `animationtech-curve_and_spline` | `automated` | `run_case.ps1 curve_and_spline` |
| `laplacian_deformation` | `notebook` | `labs/Theory/laplacian_deformation.ipynb` | `theory-anim` | `.envs/laplacian_deformation` | `animationtech-laplacian_deformation` | `manual_smoke` | `run_case.ps1 laplacian_deformation` then open JupyterLab from `.envs/laplacian_deformation` |
| `motiongraph_pointcloud_derivation` | `notebook` | `labs/Theory/motiongraph_pointcloud_derivation.ipynb` | `theory-core` | `.envs/motiongraph_pointcloud_derivation` | `animationtech-motiongraph_pointcloud_derivation` | `automated` | `run_case.ps1 motiongraph_pointcloud_derivation` |
| `radial_basis_function` | `notebook` | `labs/Theory/radial_basis_function.ipynb` | `theory-core` | `.envs/radial_basis_function` | `animationtech-radial_basis_function` | `automated` | `run_case.ps1 radial_basis_function` |
| `radial_basis_function_verbs_and_adverbs` | `notebook` | `labs/Theory/radial_basis_function_verbs_and_adverbs.ipynb` | `theory-core` | `.envs/rbf_verbs_adv` | `animationtech-radial_basis_function_verbs_and_adverbs` | `automated` | `run_case.ps1 radial_basis_function_verbs_and_adverbs` |
| `animation` | `notebook` | `labs/ipyanimlab/animation.ipynb` | `ipyanimlab` | `.envs/animation` | `animationtech-animation` | `manual_smoke` | `run_case.ps1 animation` then open JupyterLab from `.envs/animation` |
| `character_usd` | `notebook` | `labs/ipyanimlab/character_usd.ipynb` | `ipyanimlab` | `.envs/character_usd` | `animationtech-character_usd` | `manual_smoke` | `run_case.ps1 character_usd` then open JupyterLab from `.envs/character_usd` |
| `edit_material` | `notebook` | `labs/ipyanimlab/edit_material.ipynb` | `ipyanimlab` | `.envs/edit_material` | `animationtech-edit_material` | `manual_smoke` | `run_case.ps1 edit_material` then open JupyterLab from `.envs/edit_material` |
| `multiple_characters` | `notebook` | `labs/ipyanimlab/multiple_characters.ipynb` | `ipyanimlab` | `.envs/multiple_characters` | `animationtech-multiple_characters` | `manual_smoke` | `run_case.ps1 multiple_characters` then open JupyterLab from `.envs/multiple_characters` |
| `rigid_usd` | `notebook` | `labs/ipyanimlab/rigid_usd.ipynb` | `ipyanimlab` | `.envs/rigid_usd` | `animationtech-rigid_usd` | `manual_smoke` | `run_case.ps1 rigid_usd` then open JupyterLab from `.envs/rigid_usd` |
| `simple_sphere` | `notebook` | `labs/ipyanimlab/simple_sphere.ipynb` | `ipyanimlab` | `.envs/simple_sphere` | `animationtech-simple_sphere` | `manual_smoke` | `run_case.ps1 simple_sphere` then open JupyterLab from `.envs/simple_sphere` |
| `time_of_day` | `notebook` | `labs/ipyanimlab/time_of_day.ipynb` | `ipyanimlab` | `.envs/time_of_day` | `animationtech-time_of_day` | `manual_smoke` | `run_case.ps1 time_of_day` then open JupyterLab from `.envs/time_of_day` |
| `animation_format` | `notebook` | `labs/AnimationPapers/Animation Format.ipynb` | `papers-core` | `.envs/animation_format` | `animationtech-animation_format` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 animation_format` for validation/debug |
| `footskate_cleanup_for_motion_capture_editing` | `notebook` | `labs/AnimationPapers/Footskate Cleanup for Motion Capture Editing.ipynb` | `papers-core` | `.envs/footskate_cleanup` | `animationtech-footskate_cleanup_for_motion_capture_editing` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 footskate_cleanup_for_motion_capture_editing` for validation/debug |
| `halo_4_facial_animation` | `notebook` | `labs/AnimationPapers/Halo 4 Facial Animation.ipynb` | `papers-core` | `.envs/halo_4_facial_animation` | `animationtech-halo_4_facial_animation` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 halo_4_facial_animation` for validation/debug |
| `knowing_when_to_put_your_foot_down` | `notebook` | `labs/AnimationPapers/Knowing When To Put Your Foot Down.ipynb` | `papers-core` | `.envs/foot_down` | `animationtech-knowing_when_to_put_your_foot_down` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 knowing_when_to_put_your_foot_down` for validation/debug |
| `motion_fields_for_interactive_character_animation` | `notebook` | `labs/AnimationPapers/Motion Fields For Interactive Character Animation.ipynb` | `papers-torch` | `.envs/motion_fields` | `animationtech-motion_fields_for_interactive_character_animation` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 motion_fields_for_interactive_character_animation` for validation/debug |
| `motion_graph` | `notebook` | `labs/AnimationPapers/Motion Graph.ipynb` | `papers-warp` | `.envs/motion_graph` | `animationtech-motion_graph` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 motion_graph` for validation/debug |
| `motion_matching` | `notebook` | `labs/AnimationPapers/Motion Matching.ipynb` | `papers-core` | `.envs/motion_matching` | `animationtech-motion_matching` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 motion_matching` for validation/debug |
| `motion_warping` | `notebook` | `labs/AnimationPapers/Motion Warping.ipynb` | `papers-core` | `.envs/motion_warping` | `animationtech-motion_warping` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 motion_warping` for validation/debug |
| `near_optimal_character_animation_with_continuous_control` | `notebook` | `labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb` | `papers-planning` | `.envs/near_opt_ctrl` | `animationtech-near_optimal_character_animation_with_continuous_control` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 near_optimal_character_animation_with_continuous_control` for validation/debug |
| `precomputing_avatar_behavior` | `notebook` | `labs/AnimationPapers/Precomputing Avatar Behavior.ipynb` | `papers-warp` | `.envs/avatar_behavior` | `animationtech-precomputing_avatar_behavior` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 precomputing_avatar_behavior` for validation/debug |
| `real_time_planning_for_parameterized_human_motion` | `notebook` | `labs/AnimationPapers/Real-Time Planning for Parameterized Human Motion.ipynb` | `papers-planning` | `.envs/rt_param_human` | `animationtech-real_time_planning_for_parameterized_human_motion` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 real_time_planning_for_parameterized_human_motion` for validation/debug |
| `verbs_and_adverbs` | `notebook` | `labs/AnimationPapers/Verbs and Adverbs.ipynb` | `papers-core` | `.envs/verbs_and_adverbs` | `animationtech-verbs_and_adverbs` | `manual_smoke` | `start_animationpapers_lab.ps1` for study; `run_case.ps1 verbs_and_adverbs` for validation/debug |
| `real_time_planning_multiprocess_func` | `python_module` | `labs/AnimationPapers/RealTimePlanning_MultiProcess_Func.py` | `papers-planning` | `.envs/rtp_mp` | `animationtech-real_time_planning_multiprocess_func` | `automated` | `run_case.ps1 real_time_planning_multiprocess_func` |
| `halo_4_exporter_from_maya` | `python_module` | `labs/AnimationPapers/Halo 4 exporter from maya.py` | `python-stdlib` | `.envs/halo_4_exporter_from_maya` | `animationtech-halo_4_exporter_from_maya` | `automated` | `run_case.ps1 halo_4_exporter_from_maya` or direct script execution |

## Output Locations

For every case run, automation writes:

- `.reports/logs/<slug>.log`
- `.reports/executed/<slug>/`
- `.reports/locks/<slug>.txt`
- `.reports/status/<slug>.json`

The manifest remains the source of truth for env routing and case metadata:

```text
tools/cases.yaml
```
