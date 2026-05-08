# 素材清单

本目录存放 `laplacian_deformation` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/blog_media_work/laplacian_deformation.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_strip_mesh_baseline.png` | Cell 5 | `viewer` | Generate and draw the initial 2D strip graph. | This baseline shows the graph vertices and edges before Laplacian reconstruction. |
| `02_unanchored_reconstruction.png` | Cell 7 | `viewer` | Reconstruct vertices from differential coordinates without enough anchors. | The result shows why Laplacian coordinates alone do not fix global placement. |
| `03_two_anchor_solve.png` | Cell 9 | `viewer` | Add endpoint anchors to stabilize the linear solve. | Anchors turn relative differential coordinates into a positioned shape. |
| `04_three_anchor_deformation.png` | Cell 10 | `viewer` | Move an extra control point and solve the constrained system. | The viewer shows local deformation propagating through the graph. |
| `05_vectorized_3d_solve.png` | Cell 19 | `viewer` | Use a Kronecker-product system for x/y/z coordinates. | The same linear machinery scales from 2D graph points to 3D animation vertices. |
| `06_rotation_invariance_controls.png` | Cell 29 | `widget_controls` | Compare edge-length, rotation-invariance, and hard-constraint options. | The controls reveal which constraints preserve shape while allowing deformation. |
| `07_animation_graph_deformation.png` | Cell 40 | `timeline_viewer` | Convert skeleton animation into a graph and reconstruct motion. | The timeline viewer shows Laplacian deformation applied to animated pose data. |
| `08_curved_locomotion_result.png` | Cell 46 | `timeline_viewer` | Bend the walk trajectory and reconstruct the animated character. | The final viewer checks whether graph deformation can redirect locomotion smoothly. |
