# 素材清单

本目录存放 `animation_format` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Animation Format.ipynb` 的学习卡片序列 | The video links character viewing, tensor output, skeleton mapping, and root projection. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_character_bind_pose.png` | Cell 11 | `viewer` | Run render(frame), convert BVH channels to character bone matrices, then draw the character, ground, skeleton lines, and local axes. | This confirms that the animation data can drive the live viewer; later format, mapping, and root-motion discussions use this visual baseline. |
| `02_raw_bvh_skeleton.png` | Cell 12 | `viewer` | Run render_skeleton(frame) and draw only BVH skeleton lines and joint axes. | Separating the mesh from the skeleton lets the reader inspect the joint hierarchy directly. |
| `03_tensor_shape_output.png` | Cell 9 | `log` | Print the position and quaternion tensor shapes after importing BVH data. | The log shows that an animation is represented as frame x bone x channel arrays. |
| `04_raw_vs_mapped_compare.png` | Cell 19 | `viewer` | Render the raw BVH skeleton beside the AnimMapper result on the target character. | This shows that mapping adapts hierarchy and pose to the character while preserving the time structure. |
| `05_skeleton_tree_output.png` | Cell 21 | `log` | Print the raw and mapped skeleton parent trees. | The textual tree turns the viewer difference into an inspectable parent-child hierarchy. |
| `06_root_projection_motion.png` | Cell 24 | `timeline_viewer` | Use static_position/static_rotation controls to inspect root motion and local pelvis motion. | The result explains how global displacement and local body pose are stored separately. |
| `07_static_root_toggles.png` | Cell 24 | `timeline_viewer` | Enable a Root toggle and observe which motion remains in the local skeleton. | This makes the role of Root translation and rotation visible in the animated result. |
