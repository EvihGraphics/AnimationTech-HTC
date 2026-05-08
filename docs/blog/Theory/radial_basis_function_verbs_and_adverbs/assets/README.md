# 素材清单

本目录存放 `radial_basis_function_verbs_and_adverbs` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/Theory/radial_basis_function_verbs_and_adverbs.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_sample_adverb_space.png` | Cell 3 | `plot` | Plot sample points in a two-dimensional adverb space. | The plot connects semantic directions to observed color/motion samples. |
| `02_4d_adverb_encoding.png` | Cell 4 | `matrix` | Encode right, left, up, and down adverb components. | The matrix is the feature space used for linear and radial interpolation. |
| `03_linear_coefficients.png` | Cell 7 | `table` | Fit and print least-squares linear coefficients. | The coefficients capture the broad global trend in adverb space. |
| `04_linear_color_field.png` | Cell 9 | `plot` | Plot the color field produced by the linear model. | The broad field shows what linear interpolation can and cannot explain. |
| `05_linear_residuals.png` | Cell 11 | `table` | Print the residuals left after the linear model. | Residuals are the local details that the radial basis layer must recover. |
| `06_cubic_bspline_basis.png` | Cell 14 | `plot` | Plot the B3 radial basis shape. | The compact-support basis defines how far each example influences the field. |
| `07_radial_system_solve.png` | Cell 20 | `matrix` | Compute distances, scales, D matrix, and residual coefficients. | The system transforms residual examples into a smooth correction field. |
| `08_final_rbf_field.png` | Cell 21 | `plot` | Plot the final field after adding the RBF residual correction. | The field shows local semantic control beyond the linear trend. |
