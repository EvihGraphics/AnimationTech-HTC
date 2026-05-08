# 素材清单

本目录存放 `halo_4_facial_animation` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_data_load_shapes_result.png` | Cell 5 | `result_png` | `supporting_evidence` | Face mesh data loading：The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream. |
| `01_data_load_shapes.png` | Cell 5 | `learning_card` | `supporting_evidence` | Face mesh data loading：The output confirms the face animation is stored as mesh topology plus a frame-indexed vertex stream. |
| `02_raw_vertex_stream_viewer_result.png` | Cell 11 | `result_png` | `key_animation` | Raw vertex-stream face playback：This shows the raw per-frame geometry playback before any compression. |
| `02_raw_vertex_stream_viewer_preview.gif` | Cell 11 | `preview_gif` | `key_animation` | Raw vertex-stream face playback：This shows the raw per-frame geometry playback before any compression. |
| `02_raw_vertex_stream_viewer_preview.mp4` | Cell 11 | `video_mp4` | `key_animation` | Raw vertex-stream face playback：This shows the raw per-frame geometry playback before any compression. |
| `02_raw_vertex_stream_viewer_preview.webm` | Cell 11 | `video_webm` | `key_animation` | Raw vertex-stream face playback：This shows the raw per-frame geometry playback before any compression. |
| `02_raw_vertex_stream_viewer.png` | Cell 11 | `learning_card` | `key_animation` | Raw vertex-stream face playback：This shows the raw per-frame geometry playback before any compression. |
| `03_memory_size_log_result.png` | Cell 13 | `result_png` | `supporting_evidence` | Raw animation memory size：The memory log motivates PCA compression by showing why full vertex streams are expensive. |
| `03_memory_size_log.png` | Cell 13 | `learning_card` | `supporting_evidence` | Raw animation memory size：The memory log motivates PCA compression by showing why full vertex streams are expensive. |
| `04_pca_components_shape_result.png` | Cell 17 | `result_png` | `supporting_evidence` | Seven PCA component layout：The component count shows how a large vertex stream becomes a compact coefficient space. |
| `04_pca_components_shape.png` | Cell 17 | `learning_card` | `supporting_evidence` | Seven PCA component layout：The component count shows how a large vertex stream becomes a compact coefficient space. |
| `05_pca_component_viewer_result.png` | Cell 19 | `result_png` | `key_visual` | PCA component deformation viewer：The widget makes a basis component visible as a facial deformation direction. |
| `05_pca_component_viewer_preview.gif` | Cell 19 | `preview_gif` | `key_visual` | PCA component deformation viewer：The widget makes a basis component visible as a facial deformation direction. |
| `05_pca_component_viewer_preview.mp4` | Cell 19 | `video_mp4` | `key_visual` | PCA component deformation viewer：The widget makes a basis component visible as a facial deformation direction. |
| `05_pca_component_viewer_preview.webm` | Cell 19 | `video_webm` | `key_visual` | PCA component deformation viewer：The widget makes a basis component visible as a facial deformation direction. |
| `05_pca_component_viewer.png` | Cell 19 | `learning_card` | `key_visual` | PCA component deformation viewer：The widget makes a basis component visible as a facial deformation direction. |
| `06_cpu_reconstruction_compare_result.png` | Cell 23 | `result_png` | `key_animation` | CPU PCA reconstruction playback：The viewer checks whether the compressed representation preserves the visible expression motion. |
| `06_cpu_reconstruction_compare_preview.gif` | Cell 23 | `preview_gif` | `key_animation` | CPU PCA reconstruction playback：The viewer checks whether the compressed representation preserves the visible expression motion. |
| `06_cpu_reconstruction_compare_preview.mp4` | Cell 23 | `video_mp4` | `key_animation` | CPU PCA reconstruction playback：The viewer checks whether the compressed representation preserves the visible expression motion. |
| `06_cpu_reconstruction_compare_preview.webm` | Cell 23 | `video_webm` | `key_animation` | CPU PCA reconstruction playback：The viewer checks whether the compressed representation preserves the visible expression motion. |
| `06_cpu_reconstruction_compare.png` | Cell 23 | `learning_card` | `key_animation` | CPU PCA reconstruction playback：The viewer checks whether the compressed representation preserves the visible expression motion. |
| `07_gpu_shader_reconstruction_result.png` | Cell 26 | `result_png` | `key_animation` | GPU shader PCA reconstruction：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
| `07_gpu_shader_reconstruction_preview.gif` | Cell 26 | `preview_gif` | `key_animation` | GPU shader PCA reconstruction：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
| `07_gpu_shader_reconstruction_preview.mp4` | Cell 26 | `video_mp4` | `key_animation` | GPU shader PCA reconstruction：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
| `07_gpu_shader_reconstruction_preview.webm` | Cell 26 | `video_webm` | `key_animation` | GPU shader PCA reconstruction：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
| `07_gpu_shader_reconstruction.png` | Cell 26 | `learning_card` | `key_animation` | GPU shader PCA reconstruction：The final viewer shows the runtime-friendly form of the PCA facial animation pipeline. |
