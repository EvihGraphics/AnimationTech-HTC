# 素材清单

本目录存放 `real_time_planning_multiprocess_func` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_module_imports_result.png` | imports | `result_png` | `code_evidence` | Module dependencies：The module is a small worker dependency for value-function fitting, not a standalone viewer case. |
| `01_module_imports.png` | imports | `learning_card` | `code_evidence` | Module dependencies：The module is a small worker dependency for value-function fitting, not a standalone viewer case. |
| `02_function_contract_result.png` | function-contract | `result_png` | `code_evidence` | reach_train_value_function contract：The function maps training samples and precompute query indices to a reshaped value table. |
| `02_function_contract.png` | function-contract | `learning_card` | `code_evidence` | reach_train_value_function contract：The function maps training samples and precompute query indices to a reshaped value table. |
| `03_empty_training_guard_result.png` | empty-guard | `result_png` | `code_evidence` | Empty training-set guard：The guard keeps multiprocessing workers deterministic when a motion group has no samples. |
| `03_empty_training_guard.png` | empty-guard | `learning_card` | `code_evidence` | Empty training-set guard：The guard keeps multiprocessing workers deterministic when a motion group has no samples. |
| `04_extra_trees_regressor_result.png` | extra-trees | `result_png` | `code_evidence` | ExtraTrees value fitting：This is the offline regression step used to fill a value-function table. |
| `04_extra_trees_regressor.png` | extra-trees | `learning_card` | `code_evidence` | ExtraTrees value fitting：This is the offline regression step used to fill a value-function table. |
| `05_import_validation_log_result.png` | import-check | `result_png` | `code_evidence` | Import validation log：A quiet log means the module imports successfully in the managed environment. |
| `05_import_validation_log.png` | import-check | `learning_card` | `code_evidence` | Import validation log：A quiet log means the module imports successfully in the managed environment. |
