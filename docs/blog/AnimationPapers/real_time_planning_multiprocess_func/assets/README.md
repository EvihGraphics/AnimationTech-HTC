# 素材清单

本目录存放 `real_time_planning_multiprocess_func` 的源码模块媒体。每张 PNG 由 `docs/blog/media_manifest.json` 指定的源码片段、日志、产物摘要或流程说明生成。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/AnimationPapers/RealTimePlanning_MultiProcess_Func.py` 的学习卡片序列 | The video walks through source excerpts, validation logs, and generated artifacts. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_module_imports.png` | imports | `source_excerpt` | Show the imports for NumPy and ExtraTreesRegressor. | The module is a small worker dependency for value-function fitting, not a standalone viewer case. |
| `02_function_contract.png` | reach_train_value_function | `source_excerpt` | Show the function signature and primary inputs. | The function maps training samples and precompute query indices to a reshaped value table. |
| `03_empty_training_guard.png` | empty-guard | `source_excerpt` | Show the zero-table fallback for empty training data. | The guard keeps multiprocessing workers deterministic when a motion group has no samples. |
| `04_extra_trees_regressor.png` | extra-trees | `source_excerpt` | Show the n_jobs setting, ExtraTreesRegressor fit, prediction, and reshape. | This is the offline regression step used to fill a value-function table. |
| `05_import_validation_log.png` | import-check | `command_log` | Show the managed validation import check output. | A quiet log means the module imports successfully in the managed environment. |
