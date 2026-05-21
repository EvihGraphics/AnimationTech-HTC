# 素材清单

本目录存放 `real_time_planning_for_parameterized_human_motion` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

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
| `09_reach_goal_policy_playback_result.png` | Cell 47 | `result_png` | `key_animation` | Source notebook `Player(motion_clips)` viewer：character target tracking from the original render function. |
| `09_reach_goal_policy_playback_preview.gif` | Cell 47 | `gif_preview` | `key_animation` | Animated preview captured from the source notebook clip-policy viewer. |
| `09_reach_goal_policy_playback_preview.mp4` | Cell 47 | `video_mp4` | `key_animation` | H.264 local preview; GitHub attachment waits for human media approval. |
| `09_reach_goal_policy_playback_preview.webm` | Cell 47 | `video_webm` | `key_animation` | VP9 local evidence copy. |
| `09_reach_goal_policy_playback.png` | Cell 47 | `learning_card` | `key_animation` | Learning card kept for reproducibility; not used as the正文 key media. |
| `10_motiongroup_reach_goal_playback_result.png` | Cell 74 | `result_png` | `key_animation` | Source notebook `Player(motion_groups)` viewer：parameterized MotionGroup target tracking from the original render function. |
| `10_motiongroup_reach_goal_playback_preview.gif` | Cell 74 | `gif_preview` | `key_animation` | Animated preview captured from the source notebook MotionGroup viewer. |
| `10_motiongroup_reach_goal_playback_preview.mp4` | Cell 74 | `video_mp4` | `key_animation` | H.264 local preview; GitHub attachment waits for human media approval. |
| `10_motiongroup_reach_goal_playback_preview.webm` | Cell 74 | `video_webm` | `key_animation` | VP9 local evidence copy. |
| `10_motiongroup_reach_goal_playback.png` | Cell 74 | `learning_card` | `key_animation` | Learning card kept for reproducibility; not used as the正文 key media. |
