# 素材清单

本目录存放 `real_time_planning_for_parameterized_human_motion` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Real-Time Planning for Parameterized Human Motion.ipynb` 的学习卡片序列 | The video links loading logs, clip states, value curves, and parameterized policy output. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_source_animation_viewer.png` | Cell 4 | `log` | Load the character and print added heel/ball bone indices. | The planning system can reference the foot-contact helper bones later. |
| `02_motion_clip_contact_axes.png` | Cell 13 | `table` | Build short motion clips and output the number of clips. | The clip count determines the size of transition-cost and value-function tables. |
| `03_player_transition_blend.png` | Cell 25 | `log` | Iterate over clip pairs and compute physical continuity costs and delta states. | The progress output shows that expensive transition work is moved offline. |
| `04_orientation_policy_controller.png` | Cell 30 | `plot` | Plot the mean/min/max value-learning curve. | A decreasing curve indicates that the policy is stabilizing in the current state space. |
| `05_reach_goal_target_tracking.png` | Cell 35 | `table` | Print local end positions for stopping clips. | These endpoints define target states for the reach-goal policy. |
| `06_value_surface_clip16.png` | Cell 45 | `plot` | Plot the value function over a two-dimensional target space. | The surface shows the future cost of reaching different target positions from one clip. |
| `07_motion_group_weight_blend.png` | Cell 61 | `table` | Build motion groups and output the group count. | Motion groups turn multiple clips into a parameterized action space. |
| `08_group_reach_goal_result.png` | Cell 72 | `plot` | Plot the parameterized MotionGroup policy-learning curve. | The plot verifies that a useful policy can still be learned after moving from clips to motion groups. |
