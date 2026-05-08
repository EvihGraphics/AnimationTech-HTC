# 素材清单

本目录存放 `halo_4_facial_animation` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Halo 4 Facial Animation.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_data_load_shapes.png` | Cell 5 | `table` | Load pickled triangle indices, normals, and per-frame vertex positions. | The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream. |
| `02_raw_vertex_stream_viewer.png` | Cell 11 | `timeline_viewer` | Upload frame vertices to WebGL buffers and draw the animated face mesh. | This shows the raw per-frame geometry playback before any compression. |
| `03_memory_size_log.png` | Cell 13 | `log` | Print the raw vertex animation memory footprint. | The memory log motivates PCA compression by showing why full vertex streams are expensive. |
| `04_pca_components_shape.png` | Cell 17 | `table` | Fit PCA to flattened frame data and print the component shape. | The component count shows how a large vertex stream becomes a compact coefficient space. |
| `05_pca_component_viewer.png` | Cell 19 | `widget_controls` | Move pose and multiplier controls to inspect an individual PCA component. | The widget makes a basis component visible as a facial deformation direction. |
| `06_cpu_reconstruction_compare.png` | Cell 23 | `timeline_viewer` | Inverse-transform PCA coefficients and draw original/reconstructed animation. | The viewer checks whether the compressed representation preserves the visible expression motion. |
| `07_gpu_shader_reconstruction.png` | Cell 26 | `timeline_viewer` | Run the shader path that reconstructs vertex positions on the GPU. | The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
