# 素材清单

本目录存放 `motion_warping` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Motion Warping.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_source_animation_playback.png` | Cell 5 | `timeline_viewer` | Render the source animation before time or pose warping. | This baseline lets later warped outputs be compared against the original motion. |
| `02_raw_quaternion_channel.png` | Cell 6 | `plot` | Plot a selected quaternion channel over time. | The graph shows that animation warping often starts as curve manipulation. |
| `03_timewarp_keypoints.png` | Cell 12 | `plot` | Build a cardinal/Hermite curve from time remapping keypoints. | The plot shows how sparse timing edits become a continuous time-warp curve. |
| `04_resampled_timewarp_curve.png` | Cell 15 | `plot` | Resample the time-warp curve at animation-frame resolution. | The output shows the actual per-frame time lookup used for animation sampling. |
| `05_timewarped_animation_compare.png` | Cell 20 | `timeline_viewer` | Render the original and time-warped animation together. | The viewer reveals the timing change without changing the underlying pose content. |
| `06_pose_warp_key_poses.png` | Cell 23 | `viewer` | Render key poses used to define a pose-space offset. | The key-pose viewer shows what spatial correction will be blended into the clip. |
| `07_offset_warp_curve.png` | Cell 27 | `plot` | Plot the computed warp offsets over time. | The curve explains how local pose edits are distributed smoothly. |
| `08_combined_warped_animation.png` | Cell 31 | `timeline_viewer` | Render the final animation after time and pose warping. | This final viewer checks whether timing and pose edits combine into a coherent motion. |
