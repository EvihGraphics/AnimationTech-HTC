# 素材清单

本目录存放 `halo_4_exporter_from_maya` 的源码模块媒体。每张 PNG 由 `docs/blog/media_manifest.json` 指定的源码片段、日志、产物摘要或流程说明生成。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/AnimationPapers/Halo 4 exporter from maya.py` 的学习卡片序列 | The video walks through source excerpts, validation logs, and generated artifacts. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_maya_fallback_imports.png` | maya-fallback | `source_excerpt` | Show argparse/pickle imports, Maya detection, and synthetic asset writer import. | The script can run inside Maya or fall back to generating a compatible synthetic face asset. |
| `02_maya_export_function.png` | export_from_maya | `source_excerpt` | Show the selected mesh, topology extraction, normals, frame sampling, and pickle write. | The exporter records topology once and vertex positions over time for facial animation playback. |
| `03_cli_entrypoint.png` | cli-path | `source_excerpt` | Show CLI arguments and the --force-synthetic path. | The command-line path makes the case reproducible without an interactive Maya session. |
| `04_export_command_log.png` | export-log | `command_log` | Show the managed run log for the exporter. | The log records the generated artifact path used by the notebook case. |
| `05_animated_face_artifact_summary.png` | artifact-summary | `artifact_summary` | Inspect the generated pickle artifact. | The summary verifies that the artifact contains topology, normals, and per-frame vertices. |
| `06_exporter_dataflow.png` | dataflow | `diagram` | Summarize the exporter path from Maya or synthetic fallback into a notebook-readable .dat file. | The diagram links the supporting script to the Halo 4 Facial Animation notebook. |
