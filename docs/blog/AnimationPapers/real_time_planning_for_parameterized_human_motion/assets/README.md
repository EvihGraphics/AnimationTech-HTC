# 素材清单

本目录存放 `real_time_planning_for_parameterized_human_motion` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

媒体审计说明：`00-walkthrough.webm` 是补充卡片序列，不作为关键动态媒体；`learning_card` 行只记录源码上下文，正文关键媒体应使用对应的 `*_result.png` executed 输出。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_source_animation_viewer_result.png` | Cell 4 | `result_png` | `supporting_evidence` | Character and foot-helper bone loading：The planning system can reference the foot-contact helper bones later. |
| `01_source_animation_viewer.png` | Cell 4 | `learning_card` | `supporting_evidence` | Character and foot-helper bone loading：The planning system can reference the foot-contact helper bones later. |
| `02_motion_clip_contact_axes_result.png` | Cell 13 | `result_png` | `supporting_evidence` | MotionClip count output：The clip count determines the size of transition-cost and value-function tables. |
| `02_motion_clip_contact_axes.png` | Cell 13 | `learning_card` | `supporting_evidence` | MotionClip count output：The clip count determines the size of transition-cost and value-function tables. |
| `03_player_transition_blend_result.png` | Cell 25 | `result_png` | `supporting_evidence` | Transition-cost precompute output：The progress output shows that expensive transition work is moved offline. |
| `03_player_transition_blend.png` | Cell 25 | `learning_card` | `supporting_evidence` | Transition-cost precompute output：The progress output shows that expensive transition work is moved offline. |
| `04_orientation_policy_controller_result.png` | Cell 30 | `result_png` | `key_visual` | Orientation policy value-learning curve：A decreasing curve indicates that the policy is stabilizing in the current state space. |
| `04_orientation_policy_controller.png` | Cell 30 | `learning_card` | `key_visual` | Orientation policy value-learning curve：A decreasing curve indicates that the policy is stabilizing in the current state space. |
| `05_reach_goal_target_tracking_result.png` | Cell 35 | `result_png` | `supporting_evidence` | Reach-goal stopping positions：These endpoints define target states for the reach-goal policy. |
| `05_reach_goal_target_tracking.png` | Cell 35 | `learning_card` | `supporting_evidence` | Reach-goal stopping positions：These endpoints define target states for the reach-goal policy. |
| `06_value_surface_clip16_result.png` | Cell 45 | `result_png` | `key_visual` | clip 16 value surface：The surface shows the future cost of reaching different target positions from one clip. |
| `06_value_surface_clip16.png` | Cell 45 | `learning_card` | `key_visual` | clip 16 value surface：The surface shows the future cost of reaching different target positions from one clip. |
| `07_motion_group_weight_blend_result.png` | Cell 61 | `result_png` | `supporting_evidence` | MotionGroup count output：Motion groups turn multiple clips into a parameterized action space. |
| `07_motion_group_weight_blend.png` | Cell 61 | `learning_card` | `supporting_evidence` | MotionGroup count output：Motion groups turn multiple clips into a parameterized action space. |
| `08_group_reach_goal_result_result.png` | Cell 72 | `result_png` | `key_visual` | MotionGroup policy-learning curve：The plot verifies that a useful policy can still be learned after moving from clips to motion groups. |
| `08_group_reach_goal_result.png` | Cell 72 | `learning_card` | `key_visual` | MotionGroup policy-learning curve：The plot verifies that a useful policy can still be learned after moving from clips to motion groups. |
