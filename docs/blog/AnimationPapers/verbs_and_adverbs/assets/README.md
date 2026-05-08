# 素材清单

本目录存放 `verbs_and_adverbs` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Verbs and Adverbs.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_raw_sample_clips.png` | Cell 7 | `timeline_viewer` | Render the original sample actions for different verbs/adverbs. | The viewer establishes the motion examples that will be normalized and blended. |
| `02_canonical_timing_contacts.png` | Cell 10 | `timeline_viewer` | Inspect clip timing with optional on-spot playback. | Canonical timing aligns examples before interpolation. |
| `03_looping_animation_compare.png` | Cell 14 | `timeline_viewer` | Render looped versions of the sample clips. | Looping makes repeated motion comparable across clips. |
| `04_resampled_canonical_clips.png` | Cell 18 | `timeline_viewer` | Render resampled clips after time normalization. | The viewer checks that examples share a common timing domain. |
| `05_bspline_fit_plot.png` | Cell 22 | `plot` | Plot fitted B-spline curves over normalized samples. | The plot shows how sparse motion samples become smooth parameterized curves. |
| `06_bspline_reconstruction_viewer.png` | Cell 23 | `timeline_viewer` | Render the reconstructed animation from fitted curves. | The viewer validates the curve representation as playable motion. |
| `07_adverb_coordinate_table.png` | Cell 28 | `table` | Print the adverb-space coordinates used by the RBF interpolator. | The table connects semantic labels to numeric interpolation coordinates. |
| `08_final_interpolated_adverb_controls.png` | Cell 33 | `timeline_viewer` | Move final controls for angle/style and render the blended result. | The final viewer shows how verb and adverb coordinates produce a new animation. |
