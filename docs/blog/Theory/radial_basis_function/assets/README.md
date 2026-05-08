# 素材清单

本目录存放 `radial_basis_function` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_sample_function_points_result.png` | Cell 6 | `result_png` | `key_visual` | Sample function and sparse points：The plot establishes what the RBF interpolator must reconstruct. |
| `01_sample_function_points.png` | Cell 6 | `learning_card` | `key_visual` | Sample function and sparse points：The plot establishes what the RBF interpolator must reconstruct. |
| `02_gaussian_kernel_influence_result.png` | Cell 7 | `result_png` | `key_visual` | Gaussian kernel influence：The graph shows each sample as a local influence field. |
| `02_gaussian_kernel_influence.png` | Cell 7 | `learning_card` | `key_visual` | Gaussian kernel influence：The graph shows each sample as a local influence field. |
| `03_distance_kernel_matrix_result.png` | Cell 9 | `result_png` | `supporting_evidence` | Distance and kernel matrices：The matrix is the linear system that determines interpolation weights. |
| `03_distance_kernel_matrix.png` | Cell 9 | `learning_card` | `supporting_evidence` | Distance and kernel matrices：The matrix is the linear system that determines interpolation weights. |
| `04_rbf_weights_result.png` | Cell 10 | `result_png` | `supporting_evidence` | Solved RBF weights：The weights tell how much each radial basis contributes to the reconstruction. |
| `04_rbf_weights.png` | Cell 10 | `learning_card` | `supporting_evidence` | Solved RBF weights：The weights tell how much each radial basis contributes to the reconstruction. |
| `05_interpolated_query_result_result.png` | Cell 16 | `result_png` | `key_visual` | Interpolated curve and query sample：The plot checks that local kernels reconstruct the target curve between samples. |
| `05_interpolated_query_result.png` | Cell 16 | `learning_card` | `key_visual` | Interpolated curve and query sample：The plot checks that local kernels reconstruct the target curve between samples. |
| `06_polynomial_basis_matrix_result.png` | Cell 21 | `result_png` | `supporting_evidence` | Polynomial augmentation matrix：The augmentation adds a global trend term alongside local kernels. |
| `06_polynomial_basis_matrix.png` | Cell 21 | `learning_card` | `supporting_evidence` | Polynomial augmentation matrix：The augmentation adds a global trend term alongside local kernels. |
| `07_augmented_rbf_fit_result.png` | Cell 27 | `result_png` | `key_visual` | Augmented RBF fit：The final curve preserves both sparse samples and stable large-scale behavior. |
| `07_augmented_rbf_fit.png` | Cell 27 | `learning_card` | `key_visual` | Augmented RBF fit：The final curve preserves both sparse samples and stable large-scale behavior. |
