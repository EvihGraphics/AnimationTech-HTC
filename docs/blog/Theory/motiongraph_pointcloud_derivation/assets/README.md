# 素材清单

本目录存放 `motiongraph_pointcloud_derivation` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/Theory/motiongraph_pointcloud_derivation.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_alignment_objective_formula.png` | Cell 4 | `formula` | Display the weighted squared-distance objective for point-cloud alignment. | The formula states exactly what motion-graph transition alignment minimizes. |
| `02_partial_derivatives.png` | Cell 6 | `latex` | Differentiate the objective with respect to rotation and translation. | The derivatives define the first-order conditions for the optimal alignment. |
| `03_expanded_stationarity.png` | Cell 8 | `latex` | Expand the derivative equations before substitution. | The raw equations show where the sine, cosine, and translation terms come from. |
| `04_weighted_sum_shorthand.png` | Cell 13 | `latex` | Introduce compact weighted-sum symbols for the derivation. | The shorthand turns large sums into readable centroid-like expressions. |
| `05_translation_solution.png` | Cell 16 | `formula` | Solve the translation equations for x0 and z0. | The result separates translation from the remaining rotation solve. |
| `06_theta_solution.png` | Cell 20 | `formula` | Collect sine/cosine terms and derive the atan form. | The final expression is the closed-form rotation used for point-cloud alignment. |
