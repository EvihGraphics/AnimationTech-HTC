# 素材清单

本目录存放 `footskate_cleanup_for_motion_capture_editing` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Footskate Cleanup for Motion Capture Editing.ipynb` 的学习卡片序列 | The video links contact detection, target construction, IK debugging, and final smoothing. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `07_keep_translation_compare.png` | Cell 12 | `viewer` | Display two sphere-joint characters for keep_translation=False and keep_translation=True. | The comparison clarifies the responsibility split between root translation and local joint offsets. |
| `03_contact_signal_timeline.png` | Cell 16 | `plot` | Plot LeftHeel, LeftBall, RightHeel, and RightBall contact booleans. | These signals decide which foot points should stay fixed in world space. |
| `02_contact_targets.png` | Cell 19 | `viewer` | Draw the heel and ball targets back into the viewer for contact spans. | Stable targets are the anchors that let IK remove foot sliding. |
| `05_ankle_root_axes.png` | Cell 22 | `viewer` | Render ankle and root helper axes while the contact constraints are active. | The axes help check whether cleanup preserves foot orientation and body orientation. |
| `04_constraint_buffer_debug.png` | Cell 28 | `plot` | Plot the damping polynomial used by the IK correction. | The curve explains how correction error is smoothly distributed through the leg chain. |
| `01_raw_vs_solved_overview.png` | Cell 29 | `viewer` | Toggle between the original animation and the solved animation. | The reader can inspect whether the foot is more stable without damaging the body motion. |
| `06_final_processing_compare.png` | Cell 34 | `timeline_viewer` | Compare the solved animation before and after final processing. | Final processing smooths entering and leaving contact spans instead of recomputing the whole IK solve. |
