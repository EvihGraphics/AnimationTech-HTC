# 素材清单

本目录存放 `knowing_when_to_put_your_foot_down` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

媒体审计说明：当前媒体是复现证据集合；`00-walkthrough.webm` 是补充卡片序列，不作为关键动态媒体。若要发布真正的 key visual，应从项目输出生成 footfall classifier/contact preview 后再加入正文。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01_clip_window_count_result.png` | Cell 8 | `result_png` | `supporting_evidence` | Animation windows and frame count：The count defines how many temporal windows can contribute foot-contact examples. |
| `01_clip_window_count.png` | Cell 8 | `learning_card` | `supporting_evidence` | Animation windows and frame count：The count defines how many temporal windows can contribute foot-contact examples. |
| `02_feature_vector_construction_result.png` | Cell 10 | `result_png` | `code_evidence` | Foot-contact feature vector construction：The source card identifies what the classifier sees when deciding whether a foot should be planted. |
| `02_feature_vector_construction.png` | Cell 10 | `learning_card` | `code_evidence` | Foot-contact feature vector construction：The source card identifies what the classifier sees when deciding whether a foot should be planted. |
| `03_annotation_ui_stability_note_result.png` | Cell 11 | `result_png` | `supporting_evidence` | Manual annotation UI stability note：This documents that the browser-safe study copy validates the pipeline without replaying the fragile annotation widget. |
| `03_annotation_ui_stability_note.png` | Cell 11 | `learning_card` | `supporting_evidence` | Manual annotation UI stability note：This documents that the browser-safe study copy validates the pipeline without replaying the fragile annotation widget. |
| `04_training_set_accumulation_result.png` | Cell 15 | `result_png` | `supporting_evidence` | Training-set accumulation stability note：The blog can still explain the intended data flow while avoiding a non-repeatable browser labeling step. |
| `04_training_set_accumulation.png` | Cell 15 | `learning_card` | `supporting_evidence` | Training-set accumulation stability note：The blog can still explain the intended data flow while avoiding a non-repeatable browser labeling step. |
| `05_classifier_training_code_result.png` | Cell 18 | `result_png` | `supporting_evidence` | Classifier construction：The card marks the transition from hand labels to a reusable prediction model. |
| `05_classifier_training_code.png` | Cell 18 | `learning_card` | `supporting_evidence` | Classifier construction：The card marks the transition from hand labels to a reusable prediction model. |
| `06_saved_feature_vectors_result.png` | Cell 25 | `result_png` | `supporting_evidence` | Saved feature-vector artifact load：The artifact load is the stable validation path for the case after manual labeling has been done once. |
| `06_saved_feature_vectors.png` | Cell 25 | `learning_card` | `supporting_evidence` | Saved feature-vector artifact load：The artifact load is the stable validation path for the case after manual labeling has been done once. |
