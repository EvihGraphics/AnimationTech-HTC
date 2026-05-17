# Precomputing Avatar Behavior：把 Motion Graph 预计算成运行时策略

## 元数据

| 字段 | 内容 |
| --- | --- |
| slug | `precomputing_avatar_behavior` |
| source path | [`labs/AnimationPapers/Precomputing Avatar Behavior.ipynb`](../../../../labs/AnimationPapers/Precomputing Avatar Behavior.ipynb) |
| transcript sources | [`docs/transcripts/tv3ZwY1mvIw_Reinforcement Learning 01 _ Precomputing Avatar Behavior From Human Motion Data.txt`](../../../../docs/transcripts/tv3ZwY1mvIw_Reinforcement Learning 01 _ Precomputing Avatar Behavior From Human Motion Data.txt) |
| env prefix | `.envs/avatar_behavior` |
| kernel | `animationtech-precomputing_avatar_behavior` |
| validation status | `passed` (`manual_smoke`) |

## 问题背景

语音稿中的关键思想是：运行时不要在庞大的动作图上做昂贵搜索，而是把行为决策预计算成状态、动作、reward 和 value table。这个 notebook 从 motion graph 片段出发，构造离散 MDP，让 avatar 面对局部目标时可以通过查表选择动作。

## 阅读前置知识

- Motion Graph：动作片段、转移边和 loopable playback。
- MDP：state、action、reward、next state 和 Bellman backup。
- root motion 局部化：动作效果要在角色局部坐标中比较。
- FootLock：随机或策略动作播放时用于减少脚滑。

## 总模块图

```mermaid
flowchart TD
    A[Motion graph data] --> B[State / Action graph]
    B --> C[Action local trajectories]
    C --> D[Target position rings]
    D --> E[Immediate rewards / next states]
    E --> F[Bellman value iteration]
    F --> G[Static value policy]
    G --> H[Runtime viewer]
```

## 代码执行路径

```mermaid
flowchart LR
    C5[Cell 5: helpers] --> C9[Cell 9: source graph]
    C9 --> C11[Cell 11: State/Action]
    C11 --> C16[Cell 16: random playback]
    C16 --> C19[Cell 19: target rings]
    C19 --> C22[Cell 22: immediate reward]
    C22 --> C27[Cell 27: MDP policy]
```

## 模块拆解

### 1. 从 Motion Graph 到决策状态

`State` 和 `Action` dataclass 把可播放片段整理成决策点和可执行动作。单出口链会被折叠，减少运行时策略需要考虑的节点数量。

### 2. Reward 查询空间

`target_positions` 把连续目标离散成角色周围的采样环。每个 state-action 都预计算 immediate reward 和 next state。

### 3. Value Function

immediate reward 只看当前动作，容易短视。Bellman 更新把未来 reward 叠回当前动作，形成更稳定的查表策略。

## 关键 cell / 函数深讲

## 关键 cell / 函数深讲

### Cell 9 - Source motion graph playback

播放和预览由 Motion Graph 算法生成的离散动作片段，作为后续构建决策状态的基础数据源。

```mermaid
flowchart LR
    A[读取 Motion Graph 产出数据] --> B[重构动作片段]
    B --> C[在 Timeline Viewer 中循环播放]
```

- 代码做什么：Source motion graph playback: The viewer shows the action fragments from which avatar behavior is assembled.
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：The viewer shows the action fragments from which avatar behavior is assembled.
- 可视化主体：Source motion graph playback
- 捕获方式：`canvas`

![Source motion graph playback](assets/02_source_motion_graph_playback_result.png)

![Source motion graph playback preview](assets/02_source_motion_graph_playback_preview.gif)


https://github.com/user-attachments/assets/70eab46f-ba9f-43a6-b26d-d48d46bb6e6c

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/02_source_motion_graph_playback_result.png" src="assets/02_source_motion_graph_playback_preview.mp4"></video>

### Cell 16 - Random graph action playback

使用提取出的 State 和 Action 拓扑图，通过随机选择下一步动作，验证图的连通性和片段间播放的连续性。

```mermaid
flowchart LR
    A[从起始 State 节点开始] --> B[随机抽取一条出路 Action]
    B --> C[播放该 Action 对应的动作片段]
    C --> D[转移到下一个 State 节点]
    D --> B
```

- 代码做什么：Random graph action playback: The viewer validates that graph actions can produce continuous animated output.
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：The viewer validates that graph actions can produce continuous animated output.
- 可视化主体：Random graph action playback
- 捕获方式：`canvas`

![Random graph action playback](assets/04_random_action_playback_result.png)

![Random graph action playback preview](assets/04_random_action_playback_preview.gif)


https://github.com/user-attachments/assets/9667efe3-2b9e-4979-ad38-5d753d34f6c8

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/04_random_action_playback_result.png" src="assets/04_random_action_playback_preview.mp4"></video>

### Cell 22 - Immediate reward policy viewer

不考虑长远未来，仅根据当前离目标采样点的距离立即给出最大奖励，生成短视（Myopic）的最优动作策略。

```mermaid
flowchart LR
    A[角色当前所处的 State 节点] --> B[遍历所有出路 Action]
    B --> C[计算每个 Action 执行后的物理距离收益 immediate_reward]
    C --> D[直接选择收益最大的 Action 播放]
```

- 代码做什么：Immediate reward policy viewer: The viewer shows how local target rewards can choose graph actions.
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：The viewer shows how local target rewards can choose graph actions.
- 可视化主体：Immediate reward policy viewer
- 捕获方式：`canvas`

![Immediate reward policy viewer](assets/07_reward_policy_viewer_result.png)

![Immediate reward policy viewer preview](assets/07_reward_policy_viewer_preview.gif)


https://github.com/user-attachments/assets/9ac14a7b-01b3-4cef-8521-4097d2b2e54b

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/07_reward_policy_viewer_result.png" src="assets/07_reward_policy_viewer_preview.mp4"></video>

### Cell 27 - MDP value-policy viewer

通过 Bellman 方程预计算的价值函数（Value Function），在运行时只需查表即可做出具有长远预见性的动作决策。

```mermaid
flowchart LR
    A[预先离线进行 Bellman Value Iteration] --> B[生成 State x Target 的价值表]
    B --> C[运行时获取当前 State 和 Target]
    C --> D[查表选择 Value 最大的 Action]
    D --> E[驱动角色走向目标]
```

- 代码做什么：MDP value-policy viewer: The final viewer checks that the learned value function can drive action selection.
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：The final viewer checks that the learned value function can drive action selection.
- 可视化主体：MDP value-policy viewer
- 捕获方式：`canvas`

![MDP value-policy viewer](assets/08_mdp_value_policy_viewer_result.png)

![MDP value-policy viewer preview](assets/08_mdp_value_policy_viewer_preview.gif)


https://github.com/user-attachments/assets/aee60aa4-29d7-40b3-8714-8782e2ba912b

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/08_mdp_value_policy_viewer_result.png" src="assets/08_mdp_value_policy_viewer_preview.mp4"></video>

## 关键数据结构

- `State`、`Action`、`states`：MDP 图结构。
- `foot_tags`、`AnimPlayer`、`FootLock`：播放和脚部稳定。
- `target_positions`：局部目标采样。
- `immediate_rewards`、`next_states`：预计算 Bellman 输入。
- `value_function`、`value_function_static`：最终查表策略。

## 执行结果的意义

source graph viewer 说明动作来源；random action viewer 验证播放连续；value-policy viewer 验证预计算策略能把当前目标和未来收益连接起来。

## 重点可视化 / 动画

本节只放 `key_visual` 与 `key_animation` 的算法结果媒体。代码学习卡不作为正文主视觉；它们只在后续证据表中用于复现 cell 或源码上下文。


![Source motion graph playback](assets/02_source_motion_graph_playback_preview.gif)


https://github.com/user-attachments/assets/70eab46f-ba9f-43a6-b26d-d48d46bb6e6c

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/02_source_motion_graph_playback_result.png">
  <source src="assets/02_source_motion_graph_playback_preview.mp4" type="video/mp4">
  <source src="assets/02_source_motion_graph_playback_preview.webm" type="video/webm">
</video>


**Cell 16 - Random graph action playback**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/04_random_action_playback_result.png">
  <source src="assets/04_random_action_playback_preview.mp4" type="video/mp4">
  <source src="assets/04_random_action_playback_preview.webm" type="video/webm">
</video>

**Cell 22 - Immediate reward policy viewer**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/07_reward_policy_viewer_result.png">
  <source src="assets/07_reward_policy_viewer_preview.mp4" type="video/mp4">
  <source src="assets/07_reward_policy_viewer_preview.webm" type="video/webm">
</video>

**Cell 27 - MDP value-policy viewer**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/08_mdp_value_policy_viewer_result.png">
  <source src="assets/08_mdp_value_policy_viewer_preview.mp4" type="video/mp4">
  <source src="assets/08_mdp_value_policy_viewer_preview.webm" type="video/webm">
</video>

| Cell | 输出类型 | 媒体角色 | 可视化主体 | 捕获方式 | 结果媒体 |
| --- | --- | --- | --- | --- | --- |
| Cell 9 | `timeline_viewer` | `key_animation` | Source motion graph playback: The viewer shows the action fragments from which avatar behavior is assembled. | `canvas` | [结果 PNG](assets/02_source_motion_graph_playback_result.png) / [GIF](assets/02_source_motion_graph_playback_preview.gif) / [MP4](assets/02_source_motion_graph_playback_preview.mp4) / [WebM](assets/02_source_motion_graph_playback_preview.webm) |
| Cell 16 | `timeline_viewer` | `key_animation` | Random graph action playback: The viewer validates that graph actions can produce continuous animated output. | `canvas` | [结果 PNG](assets/04_random_action_playback_result.png) / [GIF](assets/04_random_action_playback_preview.gif) / [MP4](assets/04_random_action_playback_preview.mp4) / [WebM](assets/04_random_action_playback_preview.webm) |
| Cell 22 | `timeline_viewer` | `key_animation` | Immediate reward policy viewer: The viewer shows how local target rewards can choose graph actions. | `canvas` | [结果 PNG](assets/07_reward_policy_viewer_result.png) / [GIF](assets/07_reward_policy_viewer_preview.gif) / [MP4](assets/07_reward_policy_viewer_preview.mp4) / [WebM](assets/07_reward_policy_viewer_preview.webm) |
| Cell 27 | `timeline_viewer` | `key_animation` | MDP value-policy viewer: The final viewer checks that the learned value function can drive action selection. | `canvas` | [结果 PNG](assets/08_mdp_value_policy_viewer_result.png) / [GIF](assets/08_mdp_value_policy_viewer_preview.gif) / [MP4](assets/08_mdp_value_policy_viewer_preview.mp4) / [WebM](assets/08_mdp_value_policy_viewer_preview.webm) |


## 代码 Cell 与可视化结果

本节保留每个 cell 的可复现证据。结果 PNG 用于正文阅读，代码卡记录代码摘要与输出来源；有 timeline 或参数滑杆的 cell 同时提供 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 5 | The log identifies the bones later used for foot locking and rewards. | [结果 PNG](assets/01_character_helper_indices_result.png) / [代码卡](assets/01_character_helper_indices.png) |
| Cell 9 | The viewer shows the action fragments from which avatar behavior is assembled. | [结果 PNG](assets/02_source_motion_graph_playback_result.png) / [GIF](assets/02_source_motion_graph_playback_preview.gif) / [MP4](assets/02_source_motion_graph_playback_preview.mp4) / [WebM](assets/02_source_motion_graph_playback_preview.webm) / [代码卡](assets/02_source_motion_graph_playback.png) |
| Cell 11 | The source card explains the discrete MDP structure behind the behavior system. | [结果 PNG](assets/03_state_action_graph_result.png) / [代码卡](assets/03_state_action_graph.png) |
| Cell 16 | The viewer validates that graph actions can produce continuous animated output. | [结果 PNG](assets/04_random_action_playback_result.png) / [GIF](assets/04_random_action_playback_preview.gif) / [MP4](assets/04_random_action_playback_preview.mp4) / [WebM](assets/04_random_action_playback_preview.webm) / [代码卡](assets/04_random_action_playback.png) |
| Cell 18 | These numbers define the dimensionality of policy and value tables. | [结果 PNG](assets/05_action_count_table_result.png) / [代码卡](assets/05_action_count_table.png) |
| Cell 19 | The target set converts continuous goals into discrete reward queries. | [结果 PNG](assets/06_target_position_rings_result.png) / [代码卡](assets/06_target_position_rings.png) |
| Cell 22 | The viewer shows how local target rewards can choose graph actions. | [结果 PNG](assets/07_reward_policy_viewer_result.png) / [GIF](assets/07_reward_policy_viewer_preview.gif) / [MP4](assets/07_reward_policy_viewer_preview.mp4) / [WebM](assets/07_reward_policy_viewer_preview.webm) / [代码卡](assets/07_reward_policy_viewer.png) |
| Cell 27 | The final viewer checks that the learned value function can drive action selection. | [结果 PNG](assets/08_mdp_value_policy_viewer_result.png) / [GIF](assets/08_mdp_value_policy_viewer_preview.gif) / [MP4](assets/08_mdp_value_policy_viewer_preview.mp4) / [WebM](assets/08_mdp_value_policy_viewer_preview.webm) / [代码卡](assets/08_mdp_value_policy_viewer.png) |


## 运行方式

AnimationPapers 案例优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 precomputing_avatar_behavior
```
