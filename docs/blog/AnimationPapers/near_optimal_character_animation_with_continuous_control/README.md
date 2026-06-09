# Near-optimal Character Animation with Continuous Control：离散片段与连续状态的近似最优控制

## 元数据

| 字段 | 内容 |
| --- | --- |
| slug | `near_optimal_character_animation_with_continuous_control` |
| source path | [`labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb`](<../../../../labs/AnimationPapers/Near-optimal Character Animation with Continuous Control.ipynb>) |
| transcript sources | [`docs/transcripts/_S4vpMV0-UY_Reinforcement Learning 02 _ Near Optimal Character Animation with Continuous Con.txt`](<../../../../docs/transcripts/_S4vpMV0-UY_Reinforcement Learning 02 _ Near Optimal Character Animation with Continuous Con.txt>) |
| kind | `notebook` |
| env | `.envs/near_opt_ctrl` |
| kernel | `animationtech-near_optimal_character_animation_with_continuous_control` |
| validation | `passed` (`manual_smoke`；自动执行通过，viewer 建议 JupyterLab 人工检查) |
| publish tier | `深写完成 + 媒体完整` |
| media quality | key_visual/key_animation 必须是算法输出本身，禁止滚动截图、整页 cell、代码卡裁剪和静态假动画 |

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

### Cell 9 - Source clip playback

渲染最初被裁切出的所有离散片段，建立动作规划的可用词汇表。

```mermaid
flowchart LR
    A[加载原始运动数据] --> B[按预定义区间切分成离散 clips]
    B --> C[在 Timeline Viewer 中依次播放]
```

- 代码做什么：源片段播放：建立规划器可使用的动作词汇表。
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：viewer 建立规划器可使用的动作词汇表。
- 可视化主体：Source clip playback
- 捕获方式：`canvas`

### Cell 16 - Clip contact constraints

提取每个片段的脚部接触窗口和位置，用以约束后续拼接动作的物理合理性。

```mermaid
flowchart LR
    A[获取片段各帧骨骼位置] --> B[检测 Foot 与 Toe 的离地高度]
    B --> C[生成布尔型 contact 约束数组]
    C --> D[渲染带有地面接触标记的动作]
```

- 代码做什么：片段接触约束：展示规划前如何表达物理合理性。
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：viewer 展示规划前如何表达物理合理性。
- 可视化主体：Clip contact constraints
- 捕获方式：`canvas`

### Cell 19 - Random transition player

通过随机选择可接续的动作片段进行播放，验证基础过渡算法能否顺利将片段拼接起来。

```mermaid
flowchart LR
    A[选择当前片段的退出状态] --> B[选择下一片段的起始状态]
    B --> C[使用 Root Delta 对齐]
    C --> D[过渡 Blend 并连续播放]
```

- 代码做什么：随机转移播放器：验证片段能否拼接成连续播放。
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：验证片段能否拼接成连续播放。
- 可视化主体：Random transition player
- 捕获方式：`canvas`

### Cell 36 - Learned value surface

使用多项式基函数拟合未来收益（Value Function），并将空间状态对应的代价分布可视化。

```mermaid
flowchart LR
    A[定义关于 (x, z, theta) 的基函数] --> B[迭代计算每个状态的 Bellman Cost]
    B --> C[回归得到系数 coefficients]
    C --> D[将未来收益绘制成等高线/曲面图]
```

- 代码做什么：学到的价值曲面：把最优控制目标显示成未来代价。
- 运行后看到什么：`plot`
- 结果说明什么：曲面把最优控制目标显示成未来代价。
- 可视化主体：Learned value surface
- 捕获方式：`plot`

### Cell 38 - Optimal-policy controller

在运行时评估贪婪选择和价值表（Value Policy），让角色自主做出更长远的最优动作规划。

```mermaid
flowchart LR
    A[评估候选项的物理过渡代价 physics_cost] --> B[加上评估的未来代价 value]
    B --> C[选择总代价最小的转移]
    C --> D[控制器平滑播放选中的最佳片段]
```

- 代码做什么：最优策略控制器：检查没有实体手柄时策略回调也能推进。
- 运行后看到什么：`timeline_viewer`
- 结果说明什么：viewer 检查没有实体手柄时策略回调也能推进。
- 可视化主体：Optimal-policy controller
- 捕获方式：`canvas`

## 关键数据结构

- `all_clips`、`clips_q`、`clips_p`、`clips_timings`：离散动作片段。
- `clips_constraints_q/p`：接触和姿态约束。
- `ClipPlayer`、`Player`：运行时转移播放模型。
- `physics_costs`、`delta_x`、`delta_z`、`delta_theta`：离线 transition model。
- `samples`、`coefficients_forward_0`：value function 训练与评估数据。

## 执行结果的意义

contact viewer 验证物理约束；transition cost 说明离线控制模型；value surface 展示未来代价；final viewer 检查 near-optimal policy 的实际动作选择。

## 重点可视化 / 动画

本节只保留最能说明算法结果的图像和动画。代码学习卡移到文末证据表，供需要复现或追溯 cell 上下文时查看。


![Source clip playback](assets/02_source_clip_playback_preview.gif)


https://github.com/user-attachments/assets/bfff5417-4489-4a83-819b-d4d05318fe99

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/02_source_clip_playback_result.png">
  <source src="assets/02_source_clip_playback_preview.mp4" type="video/mp4">
  <source src="assets/02_source_clip_playback_preview.webm" type="video/webm">
</video>


**Cell 16 - Clip contact constraints**

https://github.com/user-attachments/assets/6f827c0f-ea4c-4ed3-b7d2-36571202bd12

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/04_contact_constraint_viewer_result.png">
  <source src="assets/04_contact_constraint_viewer_preview.mp4" type="video/mp4">
  <source src="assets/04_contact_constraint_viewer_preview.webm" type="video/webm">
</video>

**Cell 19 - Random transition player**

https://github.com/user-attachments/assets/85a27653-0c55-408c-b5be-5e945b46adc9

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/05_random_transition_player_result.png">
  <source src="assets/05_random_transition_player_preview.mp4" type="video/mp4">
  <source src="assets/05_random_transition_player_preview.webm" type="video/webm">
</video>

**Cell 36 - Learned value surface**

![Learned value surface](assets/07_learned_value_surface_result.png)

**Cell 38 - Optimal-policy controller**

https://github.com/user-attachments/assets/4a71849b-72a9-47d3-b778-40811c83b5b9

<video controls muted loop playsinline preload="metadata" width="100%" poster="assets/08_optimal_policy_player_result.png">
  <source src="assets/08_optimal_policy_player_preview.mp4" type="video/mp4">
  <source src="assets/08_optimal_policy_player_preview.webm" type="video/webm">
</video>

| Cell | 输出类型 | 阅读位置 | 可视化主体 | 捕获方式 | 结果媒体 |
| --- | --- | --- | --- | --- | --- |
| Cell 9 | `timeline_viewer` | 核心动画 | 源片段播放：建立规划器可使用的动作词汇表。 | `canvas` | [结果 PNG](assets/02_source_clip_playback_result.png) / [GIF](assets/02_source_clip_playback_preview.gif) / [MP4](assets/02_source_clip_playback_preview.mp4) / [WebM](assets/02_source_clip_playback_preview.webm) |
| Cell 16 | `timeline_viewer` | 核心动画 | 片段接触约束：展示规划前如何表达物理合理性。 | `canvas` | [结果 PNG](assets/04_contact_constraint_viewer_result.png) / [GIF](assets/04_contact_constraint_viewer_preview.gif) / [MP4](assets/04_contact_constraint_viewer_preview.mp4) / [WebM](assets/04_contact_constraint_viewer_preview.webm) |
| Cell 19 | `timeline_viewer` | 核心动画 | 随机转移播放器：验证片段能否拼接成连续播放。 | `canvas` | [结果 PNG](assets/05_random_transition_player_result.png) / [GIF](assets/05_random_transition_player_preview.gif) / [MP4](assets/05_random_transition_player_preview.mp4) / [WebM](assets/05_random_transition_player_preview.webm) |
| Cell 36 | `plot` | 核心图解 | 学到的价值曲面：把最优控制目标显示成未来代价。 | `plot` | [结果 PNG](assets/07_learned_value_surface_result.png) |
| Cell 38 | `timeline_viewer` | 核心动画 | 最优策略控制器：检查没有实体手柄时策略回调也能推进。 | `canvas` | [结果 PNG](assets/08_optimal_policy_player_result.png) / [GIF](assets/08_optimal_policy_player_preview.gif) / [MP4](assets/08_optimal_policy_player_preview.mp4) / [WebM](assets/08_optimal_policy_player_preview.webm) |


## 代码 Cell 与可视化证据

下面是附录式证据索引：结果 PNG 便于快速核对，代码卡用于追溯代码摘要与输出来源；带时间轴或参数滑杆的条目同时保留 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 5 | 这些 helper 索引后续用于接触、代价和调试绘制。 | [结果 PNG](assets/01_load_character_helpers_result.png) / [代码卡](assets/01_load_character_helpers.png) |
| Cell 9 | viewer 建立规划器可使用的动作词汇表。 | [结果 PNG](assets/02_source_clip_playback_result.png) / [GIF](assets/02_source_clip_playback_preview.gif) / [MP4](assets/02_source_clip_playback_preview.mp4) / [WebM](assets/02_source_clip_playback_preview.webm) / [代码卡](assets/02_source_clip_playback.png) |
| Cell 11 | 这个数量决定控制器可用的离散动作集合。 | [结果 PNG](assets/03_clip_count_table_result.png) / [代码卡](assets/03_clip_count_table.png) |
| Cell 16 | viewer 展示规划前如何表达物理合理性。 | [结果 PNG](assets/04_contact_constraint_viewer_result.png) / [GIF](assets/04_contact_constraint_viewer_preview.gif) / [MP4](assets/04_contact_constraint_viewer_preview.mp4) / [WebM](assets/04_contact_constraint_viewer_preview.webm) / [代码卡](assets/04_contact_constraint_viewer.png) |
| Cell 19 | 验证片段能否拼接成连续播放。 | [结果 PNG](assets/05_random_transition_player_result.png) / [GIF](assets/05_random_transition_player_preview.gif) / [MP4](assets/05_random_transition_player_preview.mp4) / [WebM](assets/05_random_transition_player_preview.webm) / [代码卡](assets/05_random_transition_player.png) |
| Cell 21 | 日志显示昂贵的规划数据已提前离线准备。 | [结果 PNG](assets/06_transition_cost_precompute_result.png) / [代码卡](assets/06_transition_cost_precompute.png) |
| Cell 36 | 曲面把最优控制目标显示成未来代价。 | [结果 PNG](assets/07_learned_value_surface_result.png) / [代码卡](assets/07_learned_value_surface.png) |
| Cell 38 | viewer 检查没有实体手柄时策略回调也能推进。 | [结果 PNG](assets/08_optimal_policy_player_result.png) / [GIF](assets/08_optimal_policy_player_preview.gif) / [MP4](assets/08_optimal_policy_player_preview.mp4) / [WebM](assets/08_optimal_policy_player_preview.webm) / [代码卡](assets/08_optimal_policy_player.png) |


## 运行方式

AnimationPapers 案例优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 near_optimal_character_animation_with_continuous_control
```
