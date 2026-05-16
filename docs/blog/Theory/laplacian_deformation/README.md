# Laplacian Deformation：网格与动画的局部形状编辑

## 元数据

| 字段 | 内容 |
| --- | --- |
| slug | `laplacian_deformation` |
| source path | [`labs/Theory/laplacian_deformation.ipynb`](../../../../labs/Theory/laplacian_deformation.ipynb) |
| transcript sources | [`docs/transcripts/0hyEbxAQVNY_Laplacian Mesh and Animation Deformation (re-upload).txt`](../../../../docs/transcripts/0hyEbxAQVNY_Laplacian Mesh and Animation Deformation (re-upload).txt) |
| env prefix | `.envs/laplacian_deformation` |
| kernel | `animationtech-laplacian_deformation` |
| validation status | `passed` (`manual_smoke`) |

## 问题背景

Laplacian deformation 解决的是移动少量控制点时尽量保持局部形状的问题。语音稿从图上的局部差分讲起：`delta = L @ V` 记录每个顶点相对邻居的形状，而 anchor 决定这些局部差分最终落在什么全局位置。notebook 先在条带网格上讲 nullspace、anchor、KKT、Kronecker 3D 和 rotation-invariant 约束，再把同一套结构迁移到跨帧骨骼动画图，用路径 anchor、脚高和腿长约束弯曲 locomotion。

## 阅读前置知识

- 图 Laplacian：`L = D - A`、局部差分和平移自由度。
- 最小二乘、伪逆、KKT：软约束和硬约束的求解差异。
- Kronecker product：把 2D 标量系统扩展到 3D 坐标。
- FK/IK、quaternion、foot contact：动画图还原时会用到。

## 总模块图

```mermaid
flowchart TD
    A[条带网格 / 骨骼动画] --> B[Adjacency 与 L = D - A]
    B --> C[Laplacian 坐标 delta = L V]
    C --> D[Anchor / edge / foot 约束]
    D --> E[LSQR / pinv / KKT 求解]
    E --> F[变形顶点图]
    F --> G[还原网格或 quats/pos]
    G --> H[结果 viewer / curved locomotion]
```

## 代码执行路径

```mermaid
flowchart LR
    C5[Cell 5: strip graph] --> C7[Cell 7: unanchored solve]
    C7 --> C9[Cell 9: endpoint anchors]
    C9 --> C19[Cell 19: Kronecker 3D]
    C19 --> C29[Cell 29: rotation invariant deform]
    C29 --> C40[Cell 40: animation graph]
    C40 --> C46[Cell 46: curved locomotion]
```

## 模块拆解

### 1. 图 Laplacian 与局部坐标

`generate_laplacian`、`compute_degree_matrix` 和 `draw` 建立最小演示环境。`delta = L @ vertices` 保留局部形状，但没有 anchor 时无法决定整体位置。

### 2. Anchor 与约束求解

`A_anchor` 和 `d_anchors` 把控制点目标拼到系统中。软约束适合平滑拖拽；硬约束用 KKT 保证指定点严格命中目标。

### 3. 动画作为跨帧图

`get_animation` 把每帧骨骼点展开为顶点，`connect_frames` 加跨帧边，`compute_animation` 再把变形后的点云还原成骨骼动画。

## 关键 cell / 函数深讲

### Cell 5-10 - 从 nullspace 到 anchor

```mermaid
flowchart LR
    C5[Cell 5 strip baseline] --> C7[delta = L * V]
    C7 --> N[无 anchor: 只有局部差分]
    N --> C9[两个端点 anchor]
    C9 --> C10[第三控制点驱动形变]
```

这些 cell 说明 Laplacian 坐标为什么必须配合 anchor。结果图中如果整体位置漂移，问题通常不是 delta 错，而是约束没有钉住全局自由度。

![Cell 5-10 - 从 nullspace 到 anchor](assets/04_three_anchor_deformation_result.png)

### Cell 18-29 - 3D 与 rotation-invariant 求解

```mermaid
flowchart LR
    L[L scalar graph] --> K[Kronecker L3D]
    K --> A[3D anchors]
    A --> E[edge length targets]
    E --> R[local rotation update]
    R --> V[viewer controls]
```

edge length 让结构不被过度拉长，rotation-invariant 项让局部形状跟着旋转，而不是被线性系统剪切。

![Cell 18-29 - 3D 与 rotation-invariant 求解](assets/06_rotation_invariance_controls_result.png)

![Cell 18-29 - 3D 与 rotation-invariant 求解 preview](assets/06_rotation_invariance_controls_preview.gif)

[打开 MP4](assets/06_rotation_invariance_controls_preview.mp4) / [打开 WebM](assets/06_rotation_invariance_controls_preview.webm)

### Cell 36-46 - 把 locomotion 变成可编辑图

```mermaid
flowchart LR
    A[walk quats/pos] --> B[FK 得到骨骼点]
    B --> C[跨帧连接成图]
    C --> D[路径 / 脚高 / 腿长约束]
    D --> E[Laplacian deform]
    E --> F[还原 quats/pos]
    F --> G[curved locomotion]
```

最终结果不是简单移动 root，而是对一段动画的时空结构求解。观察重点是脚步是否贴地、腿长是否稳定、转弯是否连续。

![Cell 36-46 - 把 locomotion 变成可编辑图](assets/08_curved_locomotion_result_result.png)

![Cell 36-46 - 把 locomotion 变成可编辑图 preview](assets/08_curved_locomotion_result_preview.gif)

[打开 MP4](assets/08_curved_locomotion_result_preview.mp4) / [打开 WebM](assets/08_curved_locomotion_result_preview.webm)

## 关键数据结构

- `Adjacency`、`Degree`、`L`：图结构与 Laplacian 矩阵。
- `vertices`、`delta`、`L3D`：顶点坐标、局部差分和三维扩展系统。
- `A_anchor`、`d_anchors`、`anchor_indices`：控制点约束。
- `edges`、`edges_Lengths`、`H`：边长保持约束。
- `foot_tags`、`feet_height`、`animation.quats/pos/parents`：动画图和骨骼还原数据。

## 执行结果的意义

网格结果验证 anchor 和局部约束如何控制形状传播。动画结果验证同一套数学结构能处理跨帧 motion editing：路径可以被重定向，但局部步态仍应保持。

## 重点可视化 / 动画

本节只放 `key_visual` 与 `key_animation` 的算法结果媒体。代码学习卡不作为正文主视觉；它们只在后续证据表中用于复现 cell 或源码上下文。

[打开/下载总览 WebM](assets/00-walkthrough.webm)

![Rotation-invariant deformation controls](assets/06_rotation_invariance_controls_preview.gif)

[打开 MP4](assets/06_rotation_invariance_controls_preview.mp4) / [打开 WebM](assets/06_rotation_invariance_controls_preview.webm)

| Cell | 输出类型 | 媒体角色 | 可视化主体 | 捕获方式 | 结果媒体 |
| --- | --- | --- | --- | --- | --- |
| Cell 5 | `viewer` | `key_visual` | Generated strip mesh baseline: This baseline shows the graph vertices and edges before Laplacian reconstruction. | `canvas` | [结果 PNG](assets/01_strip_mesh_baseline_result.png) |
| Cell 7 | `viewer` | `key_visual` | Unanchored Laplacian reconstruction: The result shows why Laplacian coordinates alone do not fix global placement. | `canvas` | [结果 PNG](assets/02_unanchored_reconstruction_result.png) |
| Cell 9 | `viewer` | `key_visual` | Two-anchor reconstruction: Anchors turn relative differential coordinates into a positioned shape. | `canvas` | [结果 PNG](assets/03_two_anchor_solve_result.png) |
| Cell 10 | `viewer` | `key_visual` | Three-anchor deformation: The viewer shows local deformation propagating through the graph. | `canvas` | [结果 PNG](assets/04_three_anchor_deformation_result.png) |
| Cell 19 | `viewer` | `key_visual` | Vectorized 3D Laplacian solve: The same linear machinery scales from 2D graph points to 3D animation vertices. | `canvas` | [结果 PNG](assets/05_vectorized_3d_solve_result.png) |
| Cell 29 | `widget_controls` | `key_visual` | Rotation-invariant deformation controls: The controls reveal which constraints preserve shape while allowing deformation. | `widget_controls` | [结果 PNG](assets/06_rotation_invariance_controls_result.png) / [GIF](assets/06_rotation_invariance_controls_preview.gif) / [MP4](assets/06_rotation_invariance_controls_preview.mp4) / [WebM](assets/06_rotation_invariance_controls_preview.webm) |
| Cell 40 | `timeline_viewer` | `key_animation` | Animation graph reconstruction: The timeline viewer shows Laplacian deformation applied to animated pose data. | `canvas` | [结果 PNG](assets/07_animation_graph_deformation_result.png) / [GIF](assets/07_animation_graph_deformation_preview.gif) / [MP4](assets/07_animation_graph_deformation_preview.mp4) / [WebM](assets/07_animation_graph_deformation_preview.webm) |
| Cell 46 | `timeline_viewer` | `key_animation` | Curved locomotion result: The final viewer checks whether graph deformation can redirect locomotion smoothly. | `canvas` | [结果 PNG](assets/08_curved_locomotion_result_result.png) / [GIF](assets/08_curved_locomotion_result_preview.gif) / [MP4](assets/08_curved_locomotion_result_preview.mp4) / [WebM](assets/08_curved_locomotion_result_preview.webm) |


## 代码 Cell 与可视化结果

本节保留每个 cell 的可复现证据。结果 PNG 用于正文阅读，代码卡记录代码摘要与输出来源；有 timeline 或参数滑杆的 cell 同时提供 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 5 | This baseline shows the graph vertices and edges before Laplacian reconstruction. | [结果 PNG](assets/01_strip_mesh_baseline_result.png) / [代码卡](assets/01_strip_mesh_baseline.png) |
| Cell 7 | The result shows why Laplacian coordinates alone do not fix global placement. | [结果 PNG](assets/02_unanchored_reconstruction_result.png) / [代码卡](assets/02_unanchored_reconstruction.png) |
| Cell 9 | Anchors turn relative differential coordinates into a positioned shape. | [结果 PNG](assets/03_two_anchor_solve_result.png) / [代码卡](assets/03_two_anchor_solve.png) |
| Cell 10 | The viewer shows local deformation propagating through the graph. | [结果 PNG](assets/04_three_anchor_deformation_result.png) / [代码卡](assets/04_three_anchor_deformation.png) |
| Cell 19 | The same linear machinery scales from 2D graph points to 3D animation vertices. | [结果 PNG](assets/05_vectorized_3d_solve_result.png) / [代码卡](assets/05_vectorized_3d_solve.png) |
| Cell 29 | The controls reveal which constraints preserve shape while allowing deformation. | [结果 PNG](assets/06_rotation_invariance_controls_result.png) / [GIF](assets/06_rotation_invariance_controls_preview.gif) / [MP4](assets/06_rotation_invariance_controls_preview.mp4) / [WebM](assets/06_rotation_invariance_controls_preview.webm) / [代码卡](assets/06_rotation_invariance_controls.png) |
| Cell 40 | The timeline viewer shows Laplacian deformation applied to animated pose data. | [结果 PNG](assets/07_animation_graph_deformation_result.png) / [GIF](assets/07_animation_graph_deformation_preview.gif) / [MP4](assets/07_animation_graph_deformation_preview.mp4) / [WebM](assets/07_animation_graph_deformation_preview.webm) / [代码卡](assets/07_animation_graph_deformation.png) |
| Cell 46 | The final viewer checks whether graph deformation can redirect locomotion smoothly. | [结果 PNG](assets/08_curved_locomotion_result_result.png) / [GIF](assets/08_curved_locomotion_result_preview.gif) / [MP4](assets/08_curved_locomotion_result_preview.mp4) / [WebM](assets/08_curved_locomotion_result_preview.webm) / [代码卡](assets/08_curved_locomotion_result.png) |


## 运行方式

AnimationPapers 案例优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 laplacian_deformation
```
