# 素材清单

本目录存放 `near_optimal_character_animation_with_continuous_control` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_load_character_helpers.png` | Cell 5 | `log` | Load the character and add helper bones for foot constraints. | The helper indices are later used for contacts, costs, and debug drawing. |
| `02_source_clip_playback.png` | Cell 9 | `timeline_viewer` | Render source locomotion clips before planning. | The viewer establishes the motion vocabulary available to the planner. |
| `03_clip_count_table.png` | Cell 11 | `table` | Slice source motion into fixed-length clips and print the count. | The count determines the discrete action set used by the controller. |
| `04_contact_constraint_viewer.png` | Cell 16 | `timeline_viewer` | Render a selected clip with contact and constraint debug information. | The viewer shows how physical plausibility is represented before planning. |
| `05_random_transition_player.png` | Cell 19 | `timeline_viewer` | Play through clip transitions with the Player abstraction. | This validates that clips can be stitched into continuous playback. |
| `06_transition_cost_precompute.png` | Cell 21 | `log` | Compute transition costs between candidate clips. | The log shows the expensive planning data being prepared offline. |
| `07_learned_value_surface.png` | Cell 36 | `plot` | Plot a learned value function over position and orientation state. | The surface makes the optimal-control objective visible as future cost. |
| `08_optimal_policy_player.png` | Cell 38 | `timeline_viewer` | Run the final optimal-policy player with browser-safe default controller input. | The viewer checks that the policy callback advances without requiring a physical gamepad. |
