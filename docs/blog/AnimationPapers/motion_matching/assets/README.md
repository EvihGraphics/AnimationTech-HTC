# 素材清单

本目录存放 `motion_matching` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Motion Matching.ipynb` 的学习卡片序列 | The video links prediction, database construction, feature layout, and the Player loop. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `spring_damper_prediction.png` | Cell 9 | `viewer` | Update root position, velocity, and orientation with a spring-damper model. | This is the source of the future trajectory target used in the motion-matching query. |
| `motion_matching_overview.png` | Cell 14 | `viewer` | Render the imported locomotion clips. | The database is built from real motion frames, not from generated poses. |
| `trajectory_query_runtime.png` | Cell 18 | `viewer` | Visualize filtered bone positions, root velocity, and facing direction. | Stable velocity and orientation estimates reduce noise in nearest-neighbor search. |
| `feature_vector_layout.png` | Cell 21 | `viewer` | Show hips, foot, and future-trajectory debug lines in the viewer. | The abstract feature vector becomes visible as body parts and trajectory targets. |
| `feature_database_debug.png` | Cell 23 | `code_only` | Compute features_mean, features_std, and the normalized database. | Different physical quantities must be normalized before Euclidean nearest-neighbor search. |
| `inertialization_transition.png` | Cell 26 | `timeline_viewer` | Build a query, find the best frame, jump playback, and smooth the transition with inertialization. | This is the closed loop that connects input prediction, feature search, and visual playback. |
| `fast_stop_turn_cases.png` | Cell 26 | `timeline_viewer` | Inspect another runtime frame in the Player cell. | Stop and sharp-turn cases are useful stress tests for matching quality. |
