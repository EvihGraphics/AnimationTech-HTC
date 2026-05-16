# Motion Fields for Interactive Character Animation：Pose+Velocity 样本场控制

## 元数据

| 字段 | 内容 |
| --- | --- |
| slug | `motion_fields_for_interactive_character_animation` |
| source path | [`labs/AnimationPapers/Motion Fields For Interactive Character Animation.ipynb`](../../../../labs/AnimationPapers/Motion Fields For Interactive Character Animation.ipynb) |
| transcript sources | [`docs/transcripts/ukobLRLKZDM_Reinforcement Learning 04 _ Motion Fields For Interactive Character Animation_.txt`](../../../../docs/transcripts/ukobLRLKZDM_Reinforcement Learning 04 _ Motion Fields For Interactive Character Animation_.txt) |
| env prefix | `.envs/motion_fields` |
| kernel | `animationtech-motion_fields_for_interactive_character_animation` |
| validation status | `passed` (`manual_smoke`) |

## 问题背景

Motion Fields 不把动作表示成 clip graph，而是把每一帧编码为 pose 和 velocity 的样本状态。语音稿强调四个核心概念：pose、velocity、motion state 和 similarity metric。运行时根据当前状态和目标速度在样本场中找邻居，插值得到下一状态，再用 value function 改善长期行为。

## 阅读前置知识

- pose/velocity state：姿态与下一帧 delta 一起构成 motion field。
- quaternion 姿态代数：pose pack/unpack/add/subtract/lerp。
- k-NN 与 metric matrix：距离定义决定动作相似性。
- fitted value iteration：用预计算邻居和权重做 Bellman backup。

## 总模块图

```mermaid
flowchart TD
    A[Walk/Run BVH clips] --> B[PoseData pack/unpack]
    B --> C[states_x / states_v / states_y / states_c]
    C --> D[metric_matrix and UMAP]
    D --> E[Torch k-NN]
    E --> F[compute_new_state]
    F --> G[action/value precompute]
    G --> H[value_function walk/jog]
```

## 代码执行路径

```mermaid
flowchart LR
    C7[Cell 7: interaction note] --> C11[Cell 11: state tables]
    C11 --> C17[Cell 17: UMAP field]
    C17 --> C20[Cell 20: Torch kNN]
    C20 --> C25[Cell 25: controller widget]
    C25 --> C32[Cell 32: transition precompute]
    C32 --> C35[Cell 35: value learning]
```

## 模块拆解

### 1. Motion State Database

`PoseData` 把 root、hips 和 bone quaternions 打包进统一 buffer。`states_x` 是 pose，`states_v` 是 velocity，二者合起来描述当前状态和自然通向的下一帧。

### 2. Similarity Metric 与 k-NN

`metric_matrix` 给不同 pose 维度分配权重。UMAP 只是可视化投影，真正运行时依赖 Torch k-NN 在高维空间中找邻居。

### 3. Value Function

greedy action 只看即时目标；transition table 和 value function 让系统估计不同 theta/action 的未来收益。

## 关键 cell / 函数深讲

## 关键 cell / 函数深讲

### Cell 7 - Interactive UI skip note

考虑到浏览器自动化验证和渲染的稳定性，该笔记记录了原案例中部分易崩溃的探索性 UI 控件的跳过情况。

```mermaid
flowchart LR
    A[Jupyter Notebook] --> B[交互式 Widget Canvas]
    B --> C[在自动化脚本环境中阻塞运行]
    C --> D[由脚本自动检测并跳过]
```

- 代码做什么：The note separates browser-safe validation from the original exploratory UI.
- 运行后看到什么：`log`
- 结果说明什么：The note separates browser-safe validation from the original exploratory UI.
- 可视化主体：Interactive UI skip note
- 捕获方式：`log`

![Interactive UI skip note](assets/01_interactive_ui_skip_note_result.png)

### Cell 11 - State table build

基于包含 Pose 及其对应的下一帧 Velocity 信息的样本库，搭建供系统运行时高速匹配查询的状态数据库。

```mermaid
flowchart LR
    A[Raw BVH clips] --> B[打包成 states_x 和 states_v]
    B --> C[结合 contact 信息]
    C --> D[生成状态矩阵]
```

- 代码做什么：The table-like log shows the scale and layout of the state database.
- 运行后看到什么：`log`
- 结果说明什么：The table-like log shows the scale and layout of the state database.
- 可视化主体：State table build
- 捕获方式：`log`

![State table build](assets/02_state_table_build_result.png)

### Cell 17 - UMAP motion-field embedding

使用 UMAP 对高维状态空间特征进行降维投影，从可视化的二维散点图中确认近邻样本的合理性和聚类情况。

```mermaid
flowchart LR
    A[states_x 高维数据] --> B[metric_matrix 加权处理]
    B --> C[输入 UMAP 模型]
    C --> D[生成二维散点簇并绘制]
```

- 代码做什么：UMAP motion-field embedding: The plot makes the motion-field neighborhood structure visible.
- 运行后看到什么：`plot`
- 结果说明什么：The plot makes the motion-field neighborhood structure visible.
- 可视化主体：UMAP motion-field embedding
- 捕获方式：`plot`

![UMAP motion-field embedding](assets/03_umap_motion_field_result.png)

### Cell 20 - Torch k-NN functions

利用 GPU 加速的 PyTorch 实现运行时 K 近邻搜索（k-NN），根据角色当前姿态与摇杆意图从库里召回最佳下一步候选。

```mermaid
flowchart LR
    A[当前控制意图与实时 Pose] --> B[Torch k-NN 搜索最邻近样本]
    B --> C[计算样本间混合权重]
    C --> D[生成插值后的下一帧状态]
```

- 代码做什么：The source card explains how a controller state becomes candidate future motions.
- 运行后看到什么：`code_only`
- 结果说明什么：The source card explains how a controller state becomes candidate future motions.
- 可视化主体：Torch k-NN functions
- 捕获方式：`source_excerpt`

![Torch k-NN functions](assets/04_torch_knn_functions_result.png)

### Cell 25 - Controller widget note

该部分对外部控制器的默认映射进行说明，强调验证模式下使用模拟输入而非强制物理外设。

```mermaid
flowchart LR
    A[控制器 Widget 模块] --> B[检查是否有真实 Gamepad]
    B --> C[无则提供模拟默认摇杆参数]
    C --> D[进行下一步贪婪代价测试]
```

- 代码做什么：The log documents why browser capture uses default input rather than requiring physical hardware.
- 运行后看到什么：`log`
- 结果说明什么：The log documents why browser capture uses default input rather than requiring physical hardware.
- 可视化主体：Controller widget note
- 捕获方式：`log`

![Controller widget note](assets/05_controller_widget_note_result.png)

### Cell 32 - Transition table precompute

预先计算任意起始状态和可能输入操作（Action）下的下一状态及其评估收益，以空间换取交互时间。

```mermaid
flowchart LR
    A[所有 state_id] --> B[组合各种 Action 输入]
    B --> C[计算 k-NN 下一状态转移概率]
    C --> D[构建 offline 转移概率大表]
```

- 代码做什么：Moving the expensive search offline is what makes runtime interaction feasible.
- 运行后看到什么：`log`
- 结果说明什么：Moving the expensive search offline is what makes runtime interaction feasible.
- 可视化主体：Transition table precompute
- 捕获方式：`log`

![Transition table precompute](assets/06_transition_table_precompute_result.png)

### Cell 35 - Value learning curve

训练基于 Bellman 方程的值函数策略，对当前策略执行效果进行自我强化迭代并绘制损失历史。

```mermaid
flowchart LR
    A[获取预计算的离线 Transition 表] --> B[评估 immediate_reward]
    B --> C[Torch 加速 Bellman Backup]
    C --> D[多轮迭代直至价值收敛]
```

- 代码做什么：Value-learning score curve: The curve gives a quick read on whether the learned policy is stabilizing.
- 运行后看到什么：`plot`
- 结果说明什么：The curve gives a quick read on whether the learned policy is stabilizing.
- 可视化主体：Value learning curve
- 捕获方式：`plot`

![Value learning curve](assets/07_value_learning_curve_result.png)

## 关键数据结构

- `PoseData`：pose buffer 的 pack/unpack/add/subtract/lerp 接口。
- `states_x`、`states_v`、`states_y`、`states_c`：motion field 样本、速度、标签和 contact。
- `metric_matrix`、`toch_knn_features`：近邻查询的距离空间。
- `all_states_actions_states_x/v`、`all_states_actions_value_function_indices/weights`：预计算转移表。
- `thetas`、`value_function_walk`、`value_function_jog`：策略学习结果。

## 执行结果的意义

当前 prepared notebook 跳过了部分原始交互 cell，因此正文把重点放在可复现的 state table、UMAP、k-NN 和 value learning 证据上。

## 重点可视化 / 动画

本节只放 `key_visual` 与 `key_animation` 的算法结果媒体。代码学习卡不作为正文主视觉；它们只在后续证据表中用于复现 cell 或源码上下文。


| Cell | 输出类型 | 媒体角色 | 可视化主体 | 捕获方式 | 结果媒体 |
| --- | --- | --- | --- | --- | --- |
| Cell 17 | `plot` | `key_visual` | UMAP motion-field embedding: The plot makes the motion-field neighborhood structure visible. | `plot` | [结果 PNG](assets/03_umap_motion_field_result.png) |
| Cell 35 | `plot` | `key_visual` | Value-learning score curve: The curve gives a quick read on whether the learned policy is stabilizing. | `plot` | [结果 PNG](assets/07_value_learning_curve_result.png) |


## 代码 Cell 与可视化结果

本节保留每个 cell 的可复现证据。结果 PNG 用于正文阅读，代码卡记录代码摘要与输出来源；有 timeline 或参数滑杆的 cell 同时提供 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 7 | The note separates browser-safe validation from the original exploratory UI. | [结果 PNG](assets/01_interactive_ui_skip_note_result.png) / [代码卡](assets/01_interactive_ui_skip_note.png) |
| Cell 11 | The table-like log shows the scale and layout of the state database. | [结果 PNG](assets/02_state_table_build_result.png) / [代码卡](assets/02_state_table_build.png) |
| Cell 17 | The plot makes the motion-field neighborhood structure visible. | [结果 PNG](assets/03_umap_motion_field_result.png) / [代码卡](assets/03_umap_motion_field.png) |
| Cell 20 | The source card explains how a controller state becomes candidate future motions. | [结果 PNG](assets/04_torch_knn_functions_result.png) / [代码卡](assets/04_torch_knn_functions.png) |
| Cell 25 | The log documents why browser capture uses default input rather than requiring physical hardware. | [结果 PNG](assets/05_controller_widget_note_result.png) / [代码卡](assets/05_controller_widget_note.png) |
| Cell 32 | Moving the expensive search offline is what makes runtime interaction feasible. | [结果 PNG](assets/06_transition_table_precompute_result.png) / [代码卡](assets/06_transition_table_precompute.png) |
| Cell 35 | The curve gives a quick read on whether the learned policy is stabilizing. | [结果 PNG](assets/07_value_learning_curve_result.png) / [代码卡](assets/07_value_learning_curve.png) |


## 运行方式

AnimationPapers 案例优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_fields_for_interactive_character_animation
```
