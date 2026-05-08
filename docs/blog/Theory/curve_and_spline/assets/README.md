# 素材清单

本目录存放 `curve_and_spline` 的博客媒体。v5 媒体把正文结果图/动画和代码学习卡分开维护。

| 文件 | 来源 | 类型 | 角色 | 说明 |
| --- | --- | --- | --- | --- |
| `00-walkthrough.webm` | case walkthrough | `walkthrough_webm` | `supporting_evidence` | 总览短视频 |
| `01-bezier-de-casteljau_result.png` | Cell 13 | `result_png` | `key_visual` | Bezier control polygons and curves：The curve is constrained by the control polygon rather than being an isolated function plot. |
| `01-bezier-de-casteljau.png` | Cell 13 | `learning_card` | `key_visual` | Bezier control polygons and curves：The curve is constrained by the control polygon rather than being an isolated function plot. |
| `02-bernstein-basis_result.png` | Cell 64 | `result_png` | `key_visual` | Cox-De Boor basis functions：Local support explains why one B-Spline control point affects only a local curve span. |
| `02-bernstein-basis.png` | Cell 64 | `learning_card` | `key_visual` | Cox-De Boor basis functions：Local support explains why one B-Spline control point affects only a local curve span. |
| `03-bezier-control-polygon_result.png` | Cell 22 | `result_png` | `key_visual` | Multi-segment Bezier spline：Long paths are built from local spans, and shared endpoints control continuity. |
| `03-bezier-control-polygon.png` | Cell 22 | `learning_card` | `key_visual` | Multi-segment Bezier spline：Long paths are built from local spans, and shared endpoints control continuity. |
| `04-rational-bezier-weight_result.png` | Cell 15 | `result_png` | `supporting_evidence` | De Casteljau versus Bernstein derivation：The symbolic output proves that recursive interpolation and Bernstein polynomials describe the same cubic Bezier. |
| `04-rational-bezier-weight.png` | Cell 15 | `learning_card` | `supporting_evidence` | De Casteljau versus Bernstein derivation：The symbolic output proves that recursive interpolation and Bernstein polynomials describe the same cubic Bezier. |
| `05-cubic-bezier-spline_result.png` | Cell 24 | `result_png` | `key_visual` | Cubic curve shape control：Cubic curves can control both position and derivative, which is why they are common in animation curves. |
| `05-cubic-bezier-spline.png` | Cell 24 | `learning_card` | `key_visual` | Cubic curve shape control：Cubic curves can control both position and derivative, which is why they are common in animation curves. |
| `06-hermite-tangents_result.png` | Cell 40 | `result_png` | `key_visual` | Hermite endpoints and tangents：Velocity and tangent information are as important as position values in animation curves. |
| `06-hermite-tangents.png` | Cell 40 | `learning_card` | `key_visual` | Hermite endpoints and tangents：Velocity and tangent information are as important as position values in animation curves. |
| `07-cardinal-tension_result.png` | Cell 56 | `result_png` | `key_visual` | Cardinal spline tension：Cardinal splines estimate tangents from neighboring points and pass through key points. |
| `07-cardinal-tension.png` | Cell 56 | `learning_card` | `key_visual` | Cardinal spline tension：Cardinal splines estimate tangents from neighboring points and pass through key points. |
| `08-cardinal-continuity_result.png` | Cell 62 | `result_png` | `key_visual` | Continuity construction：The output separates positional continuity, velocity continuity, and higher-order smoothness. |
| `08-cardinal-continuity.png` | Cell 62 | `learning_card` | `key_visual` | Continuity construction：The output separates positional continuity, velocity continuity, and higher-order smoothness. |
| `09-bspline-local-support_result.png` | Cell 72 | `result_png` | `key_visual` | Uniform cubic B-Spline：B-Splines are smooth approximations and usually do not pass through every control point. |
| `09-bspline-local-support.png` | Cell 72 | `learning_card` | `key_visual` | Uniform cubic B-Spline：B-Splines are smooth approximations and usually do not pass through every control point. |
| `10-keyframe-hermite_result.png` | Cell 77 | `result_png` | `key_visual` | 1D Hermite keyframe curve：This transfers geometric curve ideas to animation-editor keyframe curves. |
| `10-keyframe-hermite.png` | Cell 77 | `learning_card` | `key_visual` | 1D Hermite keyframe curve：This transfers geometric curve ideas to animation-editor keyframe curves. |
| `11-nonuniform-cardinal-time_result.png` | Cell 83 | `result_png` | `key_visual` | Non-uniform Cardinal time：Treating parameter t as real time can place samples incorrectly. |
| `11-nonuniform-cardinal-time.png` | Cell 83 | `learning_card` | `key_visual` | Non-uniform Cardinal time：Treating parameter t as real time can place samples incorrectly. |
| `12-bezier-time-root_result.png` | Cell 88 | `result_png` | `key_visual` | Bezier time root solving：Animation systems often need to solve internal curve parameters from frame time. |
| `12-bezier-time-root.png` | Cell 88 | `learning_card` | `key_visual` | Bezier time root solving：Animation systems often need to solve internal curve parameters from frame time. |
| `13-bspline-fitting_result.png` | Cell 92 | `result_png` | `key_visual` | B-Spline least-squares fitting：The fitted curve does not need to pass through every sample, but it preserves a stable trend. |
| `13-bspline-fitting.png` | Cell 92 | `learning_card` | `key_visual` | B-Spline least-squares fitting：The fitted curve does not need to pass through every sample, but it preserves a stable trend. |
