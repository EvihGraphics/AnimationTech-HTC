# 素材清单

本目录存放 `motion_fields_for_interactive_character_animation` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Motion Fields For Interactive Character Animation.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_interactive_ui_skip_note.png` | Cell 7 | `log` | Record the prepared skip for the first interactive viewer cell. | The note separates browser-safe validation from the original exploratory UI. |
| `02_state_table_build.png` | Cell 11 | `table` | Allocate pose, velocity, and trajectory state arrays for the motion field. | The table-like log shows the scale and layout of the state database. |
| `03_umap_motion_field.png` | Cell 17 | `plot` | Project high-dimensional motion states to a two-dimensional field. | The plot makes the motion-field neighborhood structure visible. |
| `04_torch_knn_functions.png` | Cell 20 | `code_only` | Define vector-based nearest-neighbor queries for runtime motion lookup. | The source card explains how a controller state becomes candidate future motions. |
| `05_controller_widget_note.png` | Cell 25 | `log` | Create the browser gamepad/controller widget with safe defaults. | The log documents why browser capture uses default input rather than requiring physical hardware. |
| `06_transition_table_precompute.png` | Cell 32 | `log` | Run the precompute cell that fills transition/value tables. | Moving the expensive search offline is what makes runtime interaction feasible. |
| `07_value_learning_curve.png` | Cell 35 | `plot` | Plot the learning score over epochs. | The curve gives a quick read on whether the learned policy is stabilizing. |
