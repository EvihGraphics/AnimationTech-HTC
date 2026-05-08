# 素材清单

本目录存放 `motion_graph` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Motion Graph.ipynb` 的学习卡片序列 | The video links point clouds, distance matrices, SCC pruning, and path following. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `cropped_ranges_padding.png` | Cell 2 | `log` | Initialize Warp, NumPy, ipyanimlab, and graph dependencies. | The log confirms that distance matrices and local minima can be computed in the available environment. |
| `motion_graph_overview.png` | Cell 6 | `viewer` | Render the source walking animation used to build the graph. | The graph input is a playable sequence of walking frames. |
| `point_cloud_pose.png` | Cell 12 | `viewer` | Convert the skeleton pose to world-space point samples. | Point-cloud distance is closer to visible pose similarity than comparing only root or quaternions. |
| `alignment_pair.png` | Cell 15 | `viewer` | Show source and target windows after horizontal translation and rotation alignment. | Similar gait windows can transition even when their world positions differ. |
| `distance_matrix_minima.png` | Cell 21 | `plot` | Plot the distance heatmap and mark local_minima candidates. | Low-error regions in the matrix become potential transition edges. |
| `scc_pruning.png` | Cell 28 | `log` | Print the strongly connected component pruning process. | Pruning keeps the runtime graph from entering dead ends that cannot continue generating motion. |
| `graph_nodes_edges.png` | Cell 33 | `viewer` | Play along graph edges while printing the current node and frame. | This validates Node and Edge abstractions as a playable animation sequence. |
| `follow_path_visualization.png` | Cell 45 | `timeline_viewer` | Display the graph-search result and the Bezier target path together. | The final viewer checks whether graph search can serve a path-following goal. |
