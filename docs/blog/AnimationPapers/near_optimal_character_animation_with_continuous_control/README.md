# Near-optimal Character Animation with Continuous Control：离散片段与连续状态的近似最优控制

## 元数据

| 字段 | 内容 |
| --- | --- |
| slug | `near_optimal_character_animation_with_continuous_control` |
| source path | [`labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb`](../../../../labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb) |
| transcript sources | [`docs/transcripts/_S4vpMV0-UY_Reinforcement Learning 02 _ Near Optimal Character Animation with Continuous Con.txt`](../../../../docs/transcripts/_S4vpMV0-UY_Reinforcement Learning 02 _ Near Optimal Character Animation with Continuous Con.txt) |
| env prefix | `.envs/near_opt_ctrl` |
| kernel | `animationtech-near_optimal_character_animation_with_continuous_control` |
| validation status | `passed` (`manual_smoke`) |

## 问题背景

这个案例把动作控制建模为离散 clip 选择加连续状态代价。语音稿强调 greedy transition 容易陷入局部最优，所以 notebook 预计算 clip 之间的 physics cost 和 root delta，再用 polynomial basis 与线性规划学习未来代价，让运行时策略不只看下一步。

## 阅读前置知识

- clip 切分、contact timing 和接触脚对齐。
- transition cost：姿态连续性、接触约束和方向目标共同决定代价。
- 连续状态 `(clip, x, z, theta)` 与 basis function。
- value function / policy iteration 的基本直觉。

## 总模块图

```mermaid
flowchart TD
    A[Source clips] --> B[Clip timing and contact constraints]
    B --> C[ClipPlayer transition blend]
    C --> D[physics_costs and deltas]
    D --> E[Greedy policy baseline]
    D --> F[Polynomial basis value function]
    F --> G[Near-optimal policy]
    G --> H[Final controller viewer]
```

## 代码执行路径

```mermaid
flowchart LR
    C5[Cell 5: helpers] --> C9[Cell 9: source clips]
    C9 --> C11[Cell 11: clip count]
    C11 --> C16[Cell 16: contact constraints]
    C16 --> C19[Cell 19: random player]
    C19 --> C21[Cell 21: transition costs]
    C21 --> C36[Cell 36: value surface]
    C36 --> C38[Cell 38: optimal policy]
```

## 模块拆解

### 1. Clip Motion Model

`compute_root` 和 `compute_clip` 把长动作切成可比较的片段。contact constraints 标出脚接触窗口。

### 2. Transition Cost

`ClipPlayer` 和 `Player` 验证片段能被 blend。`physics_costs`、`delta_x/z/theta` 把每个候选转移的代价和状态变化离线保存。

### 3. Near-optimal Policy

greedy policy 只看当前 deviation、physics 和 direction；near-optimal policy 额外查询 value function，估计未来代价。

## 关键 cell / 函数深讲

### Cell 5-16 - Clip 与 contact 约束

```mermaid
flowchart LR
    H[helper bones] --> C[source clip playback]
    C --> N[clip count]
    N --> R[compute_root / compute_clip]
    R --> K[contact constraint viewer]
```

contact viewer 验证片段切分是否保留物理约束。

![Cell 5-16 - Clip 与 contact 约束](assets/04_contact_constraint_viewer_result.png)

![Cell 5-16 - Clip 与 contact 约束 preview](assets/04_contact_constraint_viewer_preview.gif)

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/04_contact_constraint_viewer_result.png">
  <source src="assets/04_contact_constraint_viewer_preview.mp4" type="video/mp4">
  <source src="assets/04_contact_constraint_viewer_preview.webm" type="video/webm">
</video>

### Cell 18-21 - Transition Player 与离线代价

```mermaid
flowchart LR
    P[ClipPlayer + Player] --> R[random transition playback]
    R --> C[transition-cost precompute]
    C --> D[physics_costs + delta_x/z/theta]
    D --> S[least-cost sanity check]
```

transition cost log 说明昂贵计算已经离线，random player 检查转移播放是否平滑。

![Cell 18-21 - Transition Player 与离线代价](assets/05_random_transition_player_result.png)

![Cell 18-21 - Transition Player 与离线代价 preview](assets/05_random_transition_player_preview.gif)

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/05_random_transition_player_result.png">
  <source src="assets/05_random_transition_player_preview.mp4" type="video/mp4">
  <source src="assets/05_random_transition_player_preview.webm" type="video/webm">
</video>

### Cell 30-38 - Value Surface 与 near-optimal controller

```mermaid
flowchart LR
    G[greedy policy baseline] --> B[polynomial basis over x/z/theta]
    B --> L[learn value coefficients]
    L --> S[value surface plot]
    S --> O[optimal-policy player]
```

value surface 让未来代价可见，final viewer 检查 policy 是否能持续选择合理片段。

![Cell 30-38 - Value Surface 与 near-optimal controller](assets/08_optimal_policy_player_result.png)

![Cell 30-38 - Value Surface 与 near-optimal controller preview](assets/08_optimal_policy_player_preview.gif)

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/08_optimal_policy_player_result.png">
  <source src="assets/08_optimal_policy_player_preview.mp4" type="video/mp4">
  <source src="assets/08_optimal_policy_player_preview.webm" type="video/webm">
</video>

## 关键数据结构

- `all_clips`、`clips_q`、`clips_p`、`clips_timings`：离散动作片段。
- `clips_constraints_q/p`：接触和姿态约束。
- `ClipPlayer`、`Player`：运行时转移播放模型。
- `physics_costs`、`delta_x`、`delta_z`、`delta_theta`：离线 transition model。
- `samples`、`coefficients_forward_0`：value function 训练与评估数据。

## 执行结果的意义

contact viewer 验证物理约束；transition cost 说明离线控制模型；value surface 展示未来代价；final viewer 检查 near-optimal policy 的实际动作选择。

## 重点可视化 / 动画

本节只放 `key_visual` 与 `key_animation` 的算法结果媒体。代码学习卡不作为正文主视觉；它们只在后续证据表中用于复现 cell 或源码上下文。


![Source clip playback](assets/02_source_clip_playback_preview.gif)

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/02_source_clip_playback_result.png">
  <source src="assets/02_source_clip_playback_preview.mp4" type="video/mp4">
  <source src="assets/02_source_clip_playback_preview.webm" type="video/webm">
</video>


**Cell 16 - Clip contact constraints**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/04_contact_constraint_viewer_result.png">
  <source src="assets/04_contact_constraint_viewer_preview.mp4" type="video/mp4">
  <source src="assets/04_contact_constraint_viewer_preview.webm" type="video/webm">
</video>

**Cell 19 - Random transition player**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/05_random_transition_player_result.png">
  <source src="assets/05_random_transition_player_preview.mp4" type="video/mp4">
  <source src="assets/05_random_transition_player_preview.webm" type="video/webm">
</video>

**Cell 38 - Optimal-policy controller**

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/08_optimal_policy_player_result.png">
  <source src="assets/08_optimal_policy_player_preview.mp4" type="video/mp4">
  <source src="assets/08_optimal_policy_player_preview.webm" type="video/webm">
</video>

| Cell | 输出类型 | 媒体角色 | 可视化主体 | 捕获方式 | 结果媒体 |
| --- | --- | --- | --- | --- | --- |
| Cell 9 | `timeline_viewer` | `key_animation` | Source clip playback: The viewer establishes the motion vocabulary available to the planner. | `canvas` | [结果 PNG](assets/02_source_clip_playback_result.png) / [GIF](assets/02_source_clip_playback_preview.gif) / [MP4](assets/02_source_clip_playback_preview.mp4) / [WebM](assets/02_source_clip_playback_preview.webm) |
| Cell 16 | `timeline_viewer` | `key_animation` | Clip contact constraints: The viewer shows how physical plausibility is represented before planning. | `canvas` | [结果 PNG](assets/04_contact_constraint_viewer_result.png) / [GIF](assets/04_contact_constraint_viewer_preview.gif) / [MP4](assets/04_contact_constraint_viewer_preview.mp4) / [WebM](assets/04_contact_constraint_viewer_preview.webm) |
| Cell 19 | `timeline_viewer` | `key_animation` | Random transition player: This validates that clips can be stitched into continuous playback. | `canvas` | [结果 PNG](assets/05_random_transition_player_result.png) / [GIF](assets/05_random_transition_player_preview.gif) / [MP4](assets/05_random_transition_player_preview.mp4) / [WebM](assets/05_random_transition_player_preview.webm) |
| Cell 36 | `plot` | `key_visual` | Learned value surface: The surface makes the optimal-control objective visible as future cost. | `plot` | [结果 PNG](assets/07_learned_value_surface_result.png) |
| Cell 38 | `timeline_viewer` | `key_animation` | Optimal-policy controller: The viewer checks that the policy callback advances without requiring a physical gamepad. | `canvas` | [结果 PNG](assets/08_optimal_policy_player_result.png) / [GIF](assets/08_optimal_policy_player_preview.gif) / [MP4](assets/08_optimal_policy_player_preview.mp4) / [WebM](assets/08_optimal_policy_player_preview.webm) |


## 代码 Cell 与可视化结果

本节保留每个 cell 的可复现证据。结果 PNG 用于正文阅读，代码卡记录代码摘要与输出来源；有 timeline 或参数滑杆的 cell 同时提供 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 5 | The helper indices are later used for contacts, costs, and debug drawing. | [结果 PNG](assets/01_load_character_helpers_result.png) / [代码卡](assets/01_load_character_helpers.png) |
| Cell 9 | The viewer establishes the motion vocabulary available to the planner. | [结果 PNG](assets/02_source_clip_playback_result.png) / [GIF](assets/02_source_clip_playback_preview.gif) / [MP4](assets/02_source_clip_playback_preview.mp4) / [WebM](assets/02_source_clip_playback_preview.webm) / [代码卡](assets/02_source_clip_playback.png) |
| Cell 11 | The count determines the discrete action set used by the controller. | [结果 PNG](assets/03_clip_count_table_result.png) / [代码卡](assets/03_clip_count_table.png) |
| Cell 16 | The viewer shows how physical plausibility is represented before planning. | [结果 PNG](assets/04_contact_constraint_viewer_result.png) / [GIF](assets/04_contact_constraint_viewer_preview.gif) / [MP4](assets/04_contact_constraint_viewer_preview.mp4) / [WebM](assets/04_contact_constraint_viewer_preview.webm) / [代码卡](assets/04_contact_constraint_viewer.png) |
| Cell 19 | This validates that clips can be stitched into continuous playback. | [结果 PNG](assets/05_random_transition_player_result.png) / [GIF](assets/05_random_transition_player_preview.gif) / [MP4](assets/05_random_transition_player_preview.mp4) / [WebM](assets/05_random_transition_player_preview.webm) / [代码卡](assets/05_random_transition_player.png) |
| Cell 21 | The log shows the expensive planning data being prepared offline. | [结果 PNG](assets/06_transition_cost_precompute_result.png) / [代码卡](assets/06_transition_cost_precompute.png) |
| Cell 36 | The surface makes the optimal-control objective visible as future cost. | [结果 PNG](assets/07_learned_value_surface_result.png) / [代码卡](assets/07_learned_value_surface.png) |
| Cell 38 | The viewer checks that the policy callback advances without requiring a physical gamepad. | [结果 PNG](assets/08_optimal_policy_player_result.png) / [GIF](assets/08_optimal_policy_player_preview.gif) / [MP4](assets/08_optimal_policy_player_preview.mp4) / [WebM](assets/08_optimal_policy_player_preview.webm) / [代码卡](assets/08_optimal_policy_player.png) |


## 运行方式

AnimationPapers 案例优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 near_optimal_character_animation_with_continuous_control
```
