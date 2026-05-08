# 素材清单

本目录存放 `radial_basis_function` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/Theory/radial_basis_function.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_sample_function_points.png` | Cell 6 | `plot` | Plot the target function and sparse interpolation samples. | The plot establishes what the RBF interpolator must reconstruct. |
| `02_gaussian_kernel_influence.png` | Cell 7 | `plot` | Plot per-sample Gaussian radial basis functions. | The graph shows each sample as a local influence field. |
| `03_distance_kernel_matrix.png` | Cell 9 | `matrix` | Print the pairwise distances and Phi kernel matrix. | The matrix is the linear system that determines interpolation weights. |
| `04_rbf_weights.png` | Cell 10 | `table` | Solve Phi w = y and print the weights. | The weights tell how much each radial basis contributes to the reconstruction. |
| `05_interpolated_query_result.png` | Cell 16 | `plot` | Evaluate the RBF curve and mark a query point. | The plot checks that local kernels reconstruct the target curve between samples. |
| `06_polynomial_basis_matrix.png` | Cell 21 | `matrix` | Build and print the polynomial basis matrix P. | The augmentation adds a global trend term alongside local kernels. |
| `07_augmented_rbf_fit.png` | Cell 27 | `plot` | Plot the final polynomial-augmented RBF interpolation. | The final curve preserves both sparse samples and stable large-scale behavior. |
