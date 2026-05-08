# 素材清单

本目录存放 `knowing_when_to_put_your_foot_down` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `.reports/study/AnimationPapers/Knowing When To Put Your Foot Down.ipynb` 的学习卡片序列 | The video walks through the case by sequencing its code-output learning cards. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01_clip_window_count.png` | Cell 8 | `table` | Accumulate source clip ranges and print the available training-frame count. | The count defines how many temporal windows can contribute foot-contact examples. |
| `02_feature_vector_construction.png` | Cell 10 | `code_only` | Build a local pose and velocity feature vector around leg and foot bones. | The source card identifies what the classifier sees when deciding whether a foot should be planted. |
| `03_annotation_ui_stability_note.png` | Cell 11 | `log` | Record the prepared-notebook skip for the original manual contact-labeling UI. | This documents that the browser-safe study copy validates the pipeline without replaying the fragile annotation widget. |
| `04_training_set_accumulation.png` | Cell 15 | `log` | Record the prepared skip for the manual oracle accumulation cell. | The blog can still explain the intended data flow while avoiding a non-repeatable browser labeling step. |
| `05_classifier_training_code.png` | Cell 18 | `table` | Create and fit the contact classifier from accumulated mirrored labels. | The card marks the transition from hand labels to a reusable prediction model. |
| `06_saved_feature_vectors.png` | Cell 25 | `table` | Load saved feature vectors and labels from disk. | The artifact load is the stable validation path for the case after manual labeling has been done once. |
