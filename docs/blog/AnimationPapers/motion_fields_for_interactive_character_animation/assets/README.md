# 素材清单

本目录存放 `motion_fields_for_interactive_character_animation` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

媒体审计说明：`00-walkthrough.webm` 是补充卡片序列，不作为关键动态媒体；`learning_card` 行只记录源码上下文，正文关键媒体应使用对应的 `*_result.png` executed 输出。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_interactive_ui_skip_note_result.png` | Cell 7 | `result_png` | `supporting_evidence` | Interactive UI stability note：The note separates browser-safe validation from the original exploratory UI. |
| `01_interactive_ui_skip_note.png` | Cell 7 | `learning_card` | `supporting_evidence` | Interactive UI stability note：The note separates browser-safe validation from the original exploratory UI. |
| `02_state_table_build_result.png` | Cell 11 | `result_png` | `supporting_evidence` | Motion-field state table allocation：The table-like log shows the scale and layout of the state database. |
| `02_state_table_build.png` | Cell 11 | `learning_card` | `supporting_evidence` | Motion-field state table allocation：The table-like log shows the scale and layout of the state database. |
| `03_umap_motion_field_result.png` | Cell 17 | `result_png` | `key_visual` | UMAP motion-field embedding：The plot makes the motion-field neighborhood structure visible. |
| `03_umap_motion_field.png` | Cell 17 | `learning_card` | `key_visual` | UMAP motion-field embedding：The plot makes the motion-field neighborhood structure visible. |
| `04_torch_knn_functions_result.png` | Cell 20 | `result_png` | `code_evidence` | Torch nearest-neighbor helper：The source card explains how a controller state becomes candidate future motions. |
| `04_torch_knn_functions.png` | Cell 20 | `learning_card` | `code_evidence` | Torch nearest-neighbor helper：The source card explains how a controller state becomes candidate future motions. |
| `05_controller_widget_note_result.png` | Cell 25 | `result_png` | `supporting_evidence` | Controller widget setup：The log documents why browser capture uses default input rather than requiring physical hardware. |
| `05_controller_widget_note.png` | Cell 25 | `learning_card` | `supporting_evidence` | Controller widget setup：The log documents why browser capture uses default input rather than requiring physical hardware. |
| `06_transition_table_precompute_result.png` | Cell 32 | `result_png` | `supporting_evidence` | Transition table precompute：Moving the expensive search offline is what makes runtime interaction feasible. |
| `06_transition_table_precompute.png` | Cell 32 | `learning_card` | `supporting_evidence` | Transition table precompute：Moving the expensive search offline is what makes runtime interaction feasible. |
| `07_value_learning_curve_result.png` | Cell 35 | `result_png` | `key_visual` | Value-learning score curve：The curve gives a quick read on whether the learned policy is stabilizing. |
| `07_value_learning_curve.png` | Cell 35 | `learning_card` | `key_visual` | Value-learning score curve：The curve gives a quick read on whether the learned policy is stabilizing. |
| `08_motion_field_neighbor_rollout_result.png` | Cell 23 | `result_png` | `key_animation` | Source notebook motion-field viewer：current pose and k-NN candidate strip from the original render function. |
| `08_motion_field_neighbor_rollout_preview.gif` | Cell 23 | `gif_preview` | `key_animation` | Animated preview captured from the source notebook viewer. |
| `08_motion_field_neighbor_rollout_preview.mp4` | Cell 23 | `video_mp4` | `key_animation` | H.264 local preview; GitHub attachment waits for human media approval. |
| `08_motion_field_neighbor_rollout_preview.webm` | Cell 23 | `video_webm` | `key_animation` | VP9 local evidence copy. |
| `08_motion_field_neighbor_rollout.png` | Cell 23 | `learning_card` | `key_animation` | Learning card kept for reproducibility; not used as the正文 key media. |
