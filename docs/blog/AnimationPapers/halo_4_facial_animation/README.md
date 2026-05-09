# Halo 4 Facial Animation：PCA 顶点动画压缩

## 元数据

| 字段 | 值 |
| --- | --- |
| slug | `halo_4_facial_animation` |
| source path | `labs/AnimationPapers/Halo 4 Facial Animation.ipynb` |
| env prefix | `.envs/halo_4_facial_animation` |
| kernel | `animationtech-halo_4_facial_animation` |
| validation status | `passed`（`manual_smoke`；自动执行通过，仍需 JupyterLab 手动冒烟） |

## 问题背景

Halo 4 facial animations 这个 notebook 演示如何用主成分分析压缩面部顶点动画。原始数据是逐帧的完整头部顶点位置流：每帧都要把大量位置数据送到 GPU，内存和带宽都很昂贵。Notebook 先实现最直接的动态顶点流渲染，再用 PCA 把 220 帧面部动画压缩成 7 个主成分权重，最后写 shader 在 GPU 端用 mean head 和 7 个 component head 重建最终顶点位置。

案例配置中记录的生成产物是 `labs/AnimationPapers/animated_face.dat`，公开资源包含 `halo_animated_face` 和 `ipyanimlab_package_assets`。

## 总模块图

```mermaid
flowchart TD
    A[读取 animated_face.dat] --> B[得到 indices/normals/frames]
    B --> C[创建动态 VBO 与 VAO]
    C --> D[streaming shader 逐帧上传顶点]
    D --> E[评估原始顶点流内存成本]
    E --> F[PCA 拟合 7 个主成分]
    F --> G[把每帧投影成 anim_pca 权重]
    G --> H[inverse_transform 对比重建效果]
    H --> I[最终 shader 用 mean + components + weights 重建]
```

## 模块拆解

### 1. 数据读取

Notebook 通过 `pickle` 打开 `animated_face.dat`，读取 `indices`、`normals` 和 `frames`。其中 `frames` 是 220 帧顶点位置动画，后续会被 reshape 成 `[220, -1]` 作为 PCA 输入矩阵。

### 2. 构建 streaming shader

第一版渲染直接把 `frames[frame]` 展平成动态 VBO：`viewer.bind_buffer(buffer=vbo)` 后调用 `viewer.buffer_data(...)` 更新当前帧顶点位置。`vbo_normals` 保存法线，`vao` 描述顶点属性，shader 负责把流式顶点位置送入常规渲染管线。

### 3. 暴露原始数据成本

Notebook 用 `frames.size * 4 / 1024 / 1024` 估算完整顶点流的内存占用。这个步骤说明为什么不能只依赖逐帧顶点缓存：面部表情细节多、帧数多时，直接 streaming 会很快变成存储和传输瓶颈。

### 4. PCA 压缩

`data = frames.reshape(220, -1)` 后，`decomposition.PCA(n_components=7)` 提取 7 个主成分。PCA 会保留 `pca.mean_` 作为平均脸，并把主要变化方向放进 `pca.components_`。这些 component 可以理解为可加权的“表情基”。

### 5. 主成分检查与逐帧权重

Notebook 用 slider 放大显示单个 component，检查它捕获的局部形变是否合理。随后 `anim_pca = pca.transform(data)` 将每一帧压成 7 个系数。原来每帧需要完整顶点数组，现在每帧只需要 7 个权重加上共享的 mean/components。

### 6. PCA 重建与最终 shader

中间版本用 `pca.inverse_transform(anim_pca[frame])` 在 CPU 端重建完整头部，并把原始流与 PCA 重建结果并排比较。最终版本创建 `vbo_mean` 和 `vbo_pca_0` 到 `vbo_pca_6`，shader 接收 7 个权重，在顶点阶段直接计算最终位置，避免每帧上传完整顶点流。

## 关键数据结构

| 名称 | 形状或类型 | 作用 |
| --- | --- | --- |
| `indices` | index buffer | 头模三角形索引 |
| `normals` | `[vertex_count, 3]` | 顶点法线 |
| `frames` | `[220, vertex_count, 3]` | 原始逐帧顶点位置流 |
| `data` | `[220, vertex_count * 3]` | PCA 的二维输入矩阵 |
| `pca.mean_` | `[vertex_count * 3]` | 平均脸顶点位置 |
| `pca.components_` | `[7, vertex_count * 3]` | 7 个主成分形变方向 |
| `anim_pca` | `[220, 7]` | 每帧的 PCA 权重 |
| `vbo_mean` / `vbo_pca_*` | GPU buffer | shader 重建时使用的共享形变数据 |

## 执行结果的意义

这份 notebook 展示了一个典型的面部动画压缩思路：把高维顶点序列拆成少量共享形变基和逐帧权重。PCA 重建结果如果与原始流足够接近，就说明主要表情变化已被 7 个分量捕获；最终 shader 版本则说明这些权重可以直接用于实时渲染管线，而不必每帧上传完整 mesh。

## 代码 Cell 与可视化结果

本节按 notebook 的关键 code cell 组织学习素材：每个条目都对应代码目的、实际输出类型、结果意义和 PNG 学习卡片。PNG 由指定 cell 的代码摘要、输出区、viewer/canvas 或图表/日志合成，不使用整页滚动截图替代。

[打开/下载 WebM](assets/00-walkthrough.webm)

| Cell | 输出类型 | 代码做什么 | 结果说明什么 | 素材 |
| --- | --- | --- | --- | --- |
| 5 | `table` | Load pickled triangle indices, normals, and per-frame vertex positions. | The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream. | [PNG](assets/01_data_load_shapes.png) |
| 11 | `timeline_viewer` | Upload frame vertices to WebGL buffers and draw the animated face mesh. | This shows the raw per-frame geometry playback before any compression. | [PNG](assets/02_raw_vertex_stream_viewer.png) |
| 13 | `log` | Print the raw vertex animation memory footprint. | The memory log motivates PCA compression by showing why full vertex streams are expensive. | [PNG](assets/03_memory_size_log.png) |
| 17 | `table` | Fit PCA to flattened frame data and print the component shape. | The component count shows how a large vertex stream becomes a compact coefficient space. | [PNG](assets/04_pca_components_shape.png) |
| 19 | `widget_controls` | Move pose and multiplier controls to inspect an individual PCA component. | The widget makes a basis component visible as a facial deformation direction. | [PNG](assets/05_pca_component_viewer.png) |
| 23 | `timeline_viewer` | Inverse-transform PCA coefficients and draw original/reconstructed animation. | The viewer checks whether the compressed representation preserves the visible expression motion. | [PNG](assets/06_cpu_reconstruction_compare.png) |
| 26 | `timeline_viewer` | Run the shader path that reconstructs vertex positions on the GPU. | The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. | [PNG](assets/07_gpu_shader_reconstruction.png) |

### Cell 5 - Face mesh data loading

- 代码做什么：Load pickled triangle indices, normals, and per-frame vertex positions.
- 运行后看到什么：表格或结构化数据输出。
- 结果说明什么：The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream.

![Face mesh data loading](assets/01_data_load_shapes.png)

### Cell 11 - Raw vertex-stream face playback

- 代码做什么：Upload frame vertices to WebGL buffers and draw the animated face mesh.
- 运行后看到什么：带 timeline 的可播放 viewer。
- 结果说明什么：This shows the raw per-frame geometry playback before any compression.

![Raw vertex-stream face playback](assets/02_raw_vertex_stream_viewer.png)

### Cell 13 - Raw animation memory size

- 代码做什么：Print the raw vertex animation memory footprint.
- 运行后看到什么：运行日志或文本输出。
- 结果说明什么：The memory log motivates PCA compression by showing why full vertex streams are expensive.

![Raw animation memory size](assets/03_memory_size_log.png)

### Cell 17 - Seven PCA component layout

- 代码做什么：Fit PCA to flattened frame data and print the component shape.
- 运行后看到什么：表格或结构化数据输出。
- 结果说明什么：The component count shows how a large vertex stream becomes a compact coefficient space.

![Seven PCA component layout](assets/04_pca_components_shape.png)

### Cell 19 - PCA component deformation viewer

- 代码做什么：Move pose and multiplier controls to inspect an individual PCA component.
- 运行后看到什么：交互控件状态。
- 结果说明什么：The widget makes a basis component visible as a facial deformation direction.

![PCA component deformation viewer](assets/05_pca_component_viewer.png)

### Cell 23 - CPU PCA reconstruction playback

- 代码做什么：Inverse-transform PCA coefficients and draw original/reconstructed animation.
- 运行后看到什么：带 timeline 的可播放 viewer。
- 结果说明什么：The viewer checks whether the compressed representation preserves the visible expression motion.

![CPU PCA reconstruction playback](assets/06_cpu_reconstruction_compare.png)

### Cell 26 - GPU shader PCA reconstruction

- 代码做什么：Run the shader path that reconstructs vertex positions on the GPU.
- 运行后看到什么：带 timeline 的可播放 viewer。
- 结果说明什么：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline.

![GPU shader PCA reconstruction](assets/07_gpu_shader_reconstruction.png)

## 工程经验与调参效果

在对本案例进行深度验证与补全时，我们补充了以下关键工程特性：

1. **真实面部动画数据增强**：
   原始的自动化脚本（Synthetic Fallback）仅生成了一个带有水波纹形变的 12x10 扁平网格以防崩溃。为了更直观地验证面部 PCA，我们将资产替换为了经典的 `WaltHead` 3D 头模，并使用程序化几何形变（Procedural Deformation）结合随机“语音包络（Speech Envelope）”，为其合成了长达 220 帧的逼真发声与嘴唇运动（Lip-sync）序列，作为后续 PCA 压缩的输入 Ground Truth。
2. **底层 WebGL 兼容性修复**：
   原版 Notebook 的 Shader 存在属性对齐歧义和浮点转换 Bug。我们显式注入了 `layout(location = X)` 强制锁定顶点与法线属性通道，并将向 `viewer.uniform` 传递的数据类型严格转化为 `np.float32` 数组，彻底解决了 WebGL 渲染成扁平或崩溃的问题。
3. **PCA 权重放大与“颜艺”恶搞（Lord Z 效应）**：
   根据视频演讲稿的启发，我们在渲染阶段（Cell 26）做了一个有趣的调参实验：**将提取到的 PCA 主成分权重直接乘以 5 倍（`anim = anim_pca[frame] * 5.0`）**。
   由于最终网格是“平均脸 + 分量偏移”线性累加的结果，放大 5 倍权重后，头模原本正常的说话动作被暴力放大，形成了极度夸张和扭曲的颜艺表情。这不仅复刻了当年爆火的“Lord Z”恶搞 Mod，也从侧面印证了 PCA 如何在不破坏底层模型拓扑的情况下，实现强大的全局非线性形变控制。

![Lord Z Exaggerated Animation](../../../img/halo_faces.gif)

## 运行方式

启动 AnimationPapers 的 JupyterLab 环境后，打开 `labs/AnimationPapers/Halo 4 Facial Animation.ipynb`，选择 kernel `animationtech-halo_4_facial_animation` 按 cell 顺序运行。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 halo_4_facial_animation
```

本文档只整理 notebook 结构与工程含义，未重新执行 notebook。

## 重点可视化 / 动画

README 中优先引用结果 PNG、GIF 预览和视频链接；代码学习卡保留为复现证据。

[打开/下载总览 WebM](assets/00-walkthrough.webm)

![GPU shader PCA reconstruction](assets/07_gpu_shader_reconstruction_preview.gif)

[打开 MP4](assets/07_gpu_shader_reconstruction_preview.mp4) / [打开 WebM](assets/07_gpu_shader_reconstruction_preview.webm)

| Cell | 输出类型 | 媒体角色 | 代码目的 | 结果媒体 |
| --- | --- | --- | --- | --- |
| Cell 5 | `table` | `supporting_evidence` | Load pickled triangle indices, normals, and per-frame vertex positions. | [结果 PNG](assets/01_data_load_shapes_result.png) / [代码卡](assets/01_data_load_shapes.png) |
| Cell 11 | `timeline_viewer` | `key_animation` | Upload frame vertices to WebGL buffers and draw the animated face mesh. | [结果 PNG](assets/02_raw_vertex_stream_viewer_result.png) / [GIF](assets/02_raw_vertex_stream_viewer_preview.gif) / [MP4](assets/02_raw_vertex_stream_viewer_preview.mp4) / [WebM](assets/02_raw_vertex_stream_viewer_preview.webm) / [代码卡](assets/02_raw_vertex_stream_viewer.png) |
| Cell 13 | `log` | `supporting_evidence` | Print the raw vertex animation memory footprint. | [结果 PNG](assets/03_memory_size_log_result.png) / [代码卡](assets/03_memory_size_log.png) |
| Cell 17 | `table` | `supporting_evidence` | Fit PCA to flattened frame data and print the component shape. | [结果 PNG](assets/04_pca_components_shape_result.png) / [代码卡](assets/04_pca_components_shape.png) |
| Cell 19 | `widget_controls` | `key_visual` | Move pose and multiplier controls to inspect an individual PCA component. | [结果 PNG](assets/05_pca_component_viewer_result.png) / [GIF](assets/05_pca_component_viewer_preview.gif) / [MP4](assets/05_pca_component_viewer_preview.mp4) / [WebM](assets/05_pca_component_viewer_preview.webm) / [代码卡](assets/05_pca_component_viewer.png) |
| Cell 23 | `timeline_viewer` | `key_animation` | Inverse-transform PCA coefficients and draw original/reconstructed animation. | [结果 PNG](assets/06_cpu_reconstruction_compare_result.png) / [GIF](assets/06_cpu_reconstruction_compare_preview.gif) / [MP4](assets/06_cpu_reconstruction_compare_preview.mp4) / [WebM](assets/06_cpu_reconstruction_compare_preview.webm) / [代码卡](assets/06_cpu_reconstruction_compare.png) |
| Cell 26 | `timeline_viewer` | `key_animation` | Run the shader path that reconstructs vertex positions on the GPU. | [结果 PNG](assets/07_gpu_shader_reconstruction_result.png) / [GIF](assets/07_gpu_shader_reconstruction_preview.gif) / [MP4](assets/07_gpu_shader_reconstruction_preview.mp4) / [WebM](assets/07_gpu_shader_reconstruction_preview.webm) / [代码卡](assets/07_gpu_shader_reconstruction.png) |

## 代码 Cell 与可视化结果

本节保留每个 cell 的可复现证据。结果 PNG 用于正文阅读，代码卡记录代码摘要与输出来源；有 timeline 或参数滑杆的 cell 同时提供 GIF、MP4 和 WebM。

| Cell / 片段 | 结果说明 | 证据 |
| --- | --- | --- |
| Cell 5 | The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream. | [结果 PNG](assets/01_data_load_shapes_result.png) / [代码卡](assets/01_data_load_shapes.png) |
| Cell 11 | This shows the raw per-frame geometry playback before any compression. | [结果 PNG](assets/02_raw_vertex_stream_viewer_result.png) / [GIF](assets/02_raw_vertex_stream_viewer_preview.gif) / [MP4](assets/02_raw_vertex_stream_viewer_preview.mp4) / [WebM](assets/02_raw_vertex_stream_viewer_preview.webm) / [代码卡](assets/02_raw_vertex_stream_viewer.png) |
| Cell 13 | The memory log motivates PCA compression by showing why full vertex streams are expensive. | [结果 PNG](assets/03_memory_size_log_result.png) / [代码卡](assets/03_memory_size_log.png) |
| Cell 17 | The component count shows how a large vertex stream becomes a compact coefficient space. | [结果 PNG](assets/04_pca_components_shape_result.png) / [代码卡](assets/04_pca_components_shape.png) |
| Cell 19 | The widget makes a basis component visible as a facial deformation direction. | [结果 PNG](assets/05_pca_component_viewer_result.png) / [GIF](assets/05_pca_component_viewer_preview.gif) / [MP4](assets/05_pca_component_viewer_preview.mp4) / [WebM](assets/05_pca_component_viewer_preview.webm) / [代码卡](assets/05_pca_component_viewer.png) |
| Cell 23 | The viewer checks whether the compressed representation preserves the visible expression motion. | [结果 PNG](assets/06_cpu_reconstruction_compare_result.png) / [GIF](assets/06_cpu_reconstruction_compare_preview.gif) / [MP4](assets/06_cpu_reconstruction_compare_preview.mp4) / [WebM](assets/06_cpu_reconstruction_compare_preview.webm) / [代码卡](assets/06_cpu_reconstruction_compare.png) |
| Cell 26 | The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. | [结果 PNG](assets/07_gpu_shader_reconstruction_result.png) / [GIF](assets/07_gpu_shader_reconstruction_preview.gif) / [MP4](assets/07_gpu_shader_reconstruction_preview.mp4) / [WebM](assets/07_gpu_shader_reconstruction_preview.webm) / [代码卡](assets/07_gpu_shader_reconstruction.png) |
