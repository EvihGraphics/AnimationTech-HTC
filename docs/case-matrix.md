# Case Matrix

Current automated result on 2026-03-19:
- Total: 26
- Passed: 26
- Failed: 0
- Blocked external: 0

`manual_smoke` cases are counted as passed because their automated execution succeeds. A manual JupyterLab viewer check is still recommended when visual validation matters.

## Theory

| Slug | Entry | Template | Assets | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `curve_and_spline` | `labs/Theory/curve_and_spline.ipynb` | `theory-core` | none | `passed` | Pure theory notebook. |
| `laplacian_deformation` | `labs/Theory/laplacian_deformation.ipynb` | `theory-anim` | `lafan1`, `ipyanimlab` package assets | `passed` | Uses local `lafan1` cache. |
| `motiongraph_pointcloud_derivation` | `labs/Theory/motiongraph_pointcloud_derivation.ipynb` | `theory-core` | none | `passed` | Pure derivation notebook. |
| `radial_basis_function` | `labs/Theory/radial_basis_function.ipynb` | `theory-core` | none | `passed` | Automated plotting pass. |
| `radial_basis_function_verbs_and_adverbs` | `labs/Theory/radial_basis_function_verbs_and_adverbs.ipynb` | `theory-core` | none | `passed` | Automated plotting pass. |

## ipyanimlab

| Slug | Entry | Template | Assets | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `animation` | `labs/ipyanimlab/animation.ipynb` | `ipyanimlab` | local BVH, package USD assets | `passed` | Viewer notebook. |
| `character_usd` | `labs/ipyanimlab/character_usd.ipynb` | `ipyanimlab` | local USD, package USD assets | `passed` | Viewer notebook. |
| `edit_material` | `labs/ipyanimlab/edit_material.ipynb` | `ipyanimlab` | package `ShaderBall` asset | `passed` | Viewer notebook. |
| `multiple_characters` | `labs/ipyanimlab/multiple_characters.ipynb` | `ipyanimlab` | local BVH, package USD assets | `passed` | Viewer notebook. |
| `rigid_usd` | `labs/ipyanimlab/rigid_usd.ipynb` | `ipyanimlab` | package `ShaderBall.usd` asset | `passed` | Viewer notebook. |
| `simple_sphere` | `labs/ipyanimlab/simple_sphere.ipynb` | `ipyanimlab` | none | `passed` | Smallest viewer case. |
| `time_of_day` | `labs/ipyanimlab/time_of_day.ipynb` | `ipyanimlab` | package `ShaderBall` asset | `passed` | Viewer notebook. |

## Animation Papers

For interactive study, use `tools/start_animationpapers_lab.ps1`. It opens the browser-safe `.reports/study/AnimationPapers` directory containing prepared copies of the 12 notebook cases. The 2 Python-module cases remain managed validation cases through `run_case.ps1`.

| Slug | Entry | Template | Assets | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `animation_format` | `labs/AnimationPapers/Animation Format.ipynb` | `papers-core` | `lafan1`, package USD assets | `passed` | Automated execution succeeds with local dataset cache. |
| `footskate_cleanup_for_motion_capture_editing` | `labs/AnimationPapers/Footskate Cleanup for Motion Capture Editing.ipynb` | `papers-core` | `lafan1`, package USD assets | `passed` | Automated execution succeeds with local dataset cache. |
| `halo_4_facial_animation` | `labs/AnimationPapers/Halo 4 Facial Animation.ipynb` | `papers-core` | synthetic or Maya-exported `animated_face.dat` | `passed` | Synthetic asset generator removes external blocker. |
| `knowing_when_to_put_your_foot_down` | `labs/AnimationPapers/Knowing When To Put Your Foot Down.ipynb` | `papers-core` | `lafan1`, `foot_feature_vector.dat` | `passed` | Prepared copy trims dataset and skips purely interactive demo cells. |
| `motion_fields_for_interactive_character_animation` | `labs/AnimationPapers/Motion Fields For Interactive Character Animation.ipynb` | `papers-torch` | `lafan1`, `meshes/displacement.usd`, generated `.dat` | `passed` | Prepared copy enables precompute, replaces hardcoded CUDA with CPU fallback, and reduces workload. On the benchmark dual-4090 machine, CPU was still the fastest end-to-end path. |
| `motion_graph` | `labs/AnimationPapers/Motion Graph.ipynb` | `papers-warp` | `lafan1`, `motion_graph_walking_rawdata.dat` | `passed` | Uses `warp-lang` environment. |
| `motion_matching` | `labs/AnimationPapers/Motion Matching.ipynb` | `papers-core` | `lafan1`, `meshes/displacement.usd` | `passed` | Automated execution succeeds with local dataset cache. |
| `motion_warping` | `labs/AnimationPapers/Motion Warping.ipynb` | `papers-core` | `lafan1`, package USD assets | `passed` | Automated execution succeeds with local dataset cache. |
| `near_optimal_character_animation_with_continuous_control` | `labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb` | `papers-planning` | repo-shipped data | `passed` | Automated execution succeeds without extra asset work. |
| `precomputing_avatar_behavior` | `labs/AnimationPapers/Precomputing Avatar Behavior.ipynb` | `papers-warp` | `motion_graph_walking_rawdata.dat` | `passed` | Runs after `warp-lang` setup. |
| `real_time_planning_for_parameterized_human_motion` | `labs/AnimationPapers/Real-Time Planning for Parameterized Human Motion.ipynb` | `papers-planning` | generated planning `.dat` files | `passed` | Prepared copy enables and scales down hidden precompute stages. The best measured adaptive profile on `Ryzen 9 7950X` used `12` workers; higher worker counts regressed. |
| `real_time_planning_multiprocess_func` | `labs/AnimationPapers/RealTimePlanning_MultiProcess_Func.py` | `papers-planning` | none | `passed` | Import-level validation. |
| `verbs_and_adverbs` | `labs/AnimationPapers/Verbs and Adverbs.ipynb` | `papers-core` | `lafan1`, package USD assets | `passed` | Automated execution succeeds with local dataset cache. |
| `halo_4_exporter_from_maya` | `labs/AnimationPapers/Halo 4 exporter from maya.py` | `python-stdlib` | optional Maya scene, generated `animated_face.dat` | `passed` | Falls back to synthetic export when Maya is unavailable. |

## Validation Artifacts

For each case, the automation writes:
- `.reports/logs/<slug>.log`
- `.reports/executed/<slug>/`
- `.reports/locks/<slug>.txt`
- `.reports/status/<slug>.json`

The current status source of truth is `tools/cases.yaml`.
