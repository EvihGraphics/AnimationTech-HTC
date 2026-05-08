# 素材清单

本目录存放 `precomputing_avatar_behavior` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Precomputing Avatar Behavior.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_character_helper_indices.png` | Cell 5 | `log` | Load character and helper bones used by the behavior system. | The log identifies the bones later used for foot locking and rewards. |
| `02_source_motion_graph_playback.png` | Cell 9 | `timeline_viewer` | Render the source motion graph clips. | The viewer shows the action fragments from which avatar behavior is assembled. |
| `03_state_action_graph.png` | Cell 11 | `code_only` | Define dataclasses that hold graph states, actions, rewards, and transitions. | The source card explains the discrete MDP structure behind the behavior system. |
| `04_random_action_playback.png` | Cell 16 | `timeline_viewer` | Play random actions through the graph with FootLock correction. | The viewer validates that graph actions can produce continuous animated output. |
| `05_action_count_table.png` | Cell 18 | `table` | Compute action counts and maximum clip lengths. | These numbers define the dimensionality of policy and value tables. |
| `06_target_position_rings.png` | Cell 19 | `table` | Build target position samples around the avatar. | The target set converts continuous goals into discrete reward queries. |
| `07_reward_policy_viewer.png` | Cell 22 | `timeline_viewer` | Run the policy viewer with default controller input. | The viewer shows how local target rewards can choose graph actions. |
| `08_mdp_value_policy_viewer.png` | Cell 27 | `timeline_viewer` | Run the value-based behavior policy after offline learning. | The final viewer checks that the learned value function can drive action selection. |
