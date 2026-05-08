# 素材清单

本目录存放 `animation_format` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_character_bind_pose_result.png` | Cell 11 | `result_png` | `key_visual` | Character bind pose and skeleton viewer：This confirms that the animation data can drive the live viewer; later format, mapping, and root-motion discussions use this visual baseline. |
| `01_character_bind_pose.png` | Cell 11 | `learning_card` | `key_visual` | Character bind pose and skeleton viewer：This confirms that the animation data can drive the live viewer; later format, mapping, and root-motion discussions use this visual baseline. |
| `02_raw_bvh_skeleton_result.png` | Cell 12 | `result_png` | `key_visual` | Raw BVH skeleton-only view：Separating the mesh from the skeleton lets the reader inspect the joint hierarchy directly. |
| `02_raw_bvh_skeleton.png` | Cell 12 | `learning_card` | `key_visual` | Raw BVH skeleton-only view：Separating the mesh from the skeleton lets the reader inspect the joint hierarchy directly. |
| `03_tensor_shape_output_result.png` | Cell 9 | `result_png` | `supporting_evidence` | pos/quats tensor shape output：The log shows that an animation is represented as frame x bone x channel arrays. |
| `03_tensor_shape_output.png` | Cell 9 | `learning_card` | `supporting_evidence` | pos/quats tensor shape output：The log shows that an animation is represented as frame x bone x channel arrays. |
| `04_raw_vs_mapped_compare_result.png` | Cell 19 | `result_png` | `key_visual` | Raw skeleton versus mapped skeleton：This shows that mapping adapts hierarchy and pose to the character while preserving the time structure. |
| `04_raw_vs_mapped_compare.png` | Cell 19 | `learning_card` | `key_visual` | Raw skeleton versus mapped skeleton：This shows that mapping adapts hierarchy and pose to the character while preserving the time structure. |
| `05_skeleton_tree_output_result.png` | Cell 21 | `result_png` | `supporting_evidence` | Skeleton parent tree output：The textual tree turns the viewer difference into an inspectable parent-child hierarchy. |
| `05_skeleton_tree_output.png` | Cell 21 | `learning_card` | `supporting_evidence` | Skeleton parent tree output：The textual tree turns the viewer difference into an inspectable parent-child hierarchy. |
| `06_root_projection_motion_result.png` | Cell 24 | `result_png` | `key_animation` | Root projection and Root/Hips split：The result explains how global displacement and local body pose are stored separately. |
| `06_root_projection_motion_preview.gif` | Cell 24 | `preview_gif` | `key_animation` | Root projection and Root/Hips split：The result explains how global displacement and local body pose are stored separately. |
| `06_root_projection_motion_preview.mp4` | Cell 24 | `video_mp4` | `key_animation` | Root projection and Root/Hips split：The result explains how global displacement and local body pose are stored separately. |
| `06_root_projection_motion_preview.webm` | Cell 24 | `video_webm` | `key_animation` | Root projection and Root/Hips split：The result explains how global displacement and local body pose are stored separately. |
| `06_root_projection_motion.png` | Cell 24 | `learning_card` | `key_animation` | Root projection and Root/Hips split：The result explains how global displacement and local body pose are stored separately. |
| `07_static_root_toggles_result.png` | Cell 24 | `result_png` | `key_animation` | Static Root toggle comparison：This makes the role of Root translation and rotation visible in the animated result. |
| `07_static_root_toggles_preview.gif` | Cell 24 | `preview_gif` | `key_animation` | Static Root toggle comparison：This makes the role of Root translation and rotation visible in the animated result. |
| `07_static_root_toggles_preview.mp4` | Cell 24 | `video_mp4` | `key_animation` | Static Root toggle comparison：This makes the role of Root translation and rotation visible in the animated result. |
| `07_static_root_toggles_preview.webm` | Cell 24 | `video_webm` | `key_animation` | Static Root toggle comparison：This makes the role of Root translation and rotation visible in the animated result. |
| `07_static_root_toggles.png` | Cell 24 | `learning_card` | `key_animation` | Static Root toggle comparison：This makes the role of Root translation and rotation visible in the animated result. |
