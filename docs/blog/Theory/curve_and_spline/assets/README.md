# 素材清单

本目录存放 `curve_and_spline` 的学习型 cell 媒体。每张 PNG 都来自 `docs/blog/media_manifest.json` 指定的 notebook cell，并合成代码摘要、实际输出和结果读法。

## Walkthrough

| 文件 | 来源 | 用途 |
| --- | --- | --- |
| `00-walkthrough.webm` | `labs/Theory/curve_and_spline.ipynb` 的学习卡片序列 | The video links Bezier, Hermite, Cardinal, B-Spline, and keyframe curves. |

## 媒体条目

| 文件 | 锚点 | 输出类型 | 代码目的 | 结果意义 |
| --- | --- | --- | --- | --- |
| `01-bezier-de-casteljau.png` | Cell 13 | `plot` | Plot Bezier curves of different orders with their control points. | The curve is constrained by the control polygon rather than being an isolated function plot. |
| `02-bernstein-basis.png` | Cell 64 | `plot` | Plot recursively constructed B-Spline basis functions. | Local support explains why one B-Spline control point affects only a local curve span. |
| `03-bezier-control-polygon.png` | Cell 22 | `plot` | Connect multiple cubic Bezier spans and draw their control points. | Long paths are built from local spans, and shared endpoints control continuity. |
| `04-rational-bezier-weight.png` | Cell 15 | `log` | Expand the De Casteljau form using SymPy. | The symbolic output proves that recursive interpolation and Bernstein polynomials describe the same cubic Bezier. |
| `05-cubic-bezier-spline.png` | Cell 24 | `plot` | Compare low-order and cubic polynomial interpolation behavior. | Cubic curves can control both position and derivative, which is why they are common in animation curves. |
| `06-hermite-tangents.png` | Cell 40 | `plot` | Plot a 2D Hermite curve with endpoint tangent controls. | Velocity and tangent information are as important as position values in animation curves. |
| `07-cardinal-tension.png` | Cell 56 | `plot` | Plot a Cardinal spline with control points. | Cardinal splines estimate tangents from neighboring points and pass through key points. |
| `08-cardinal-continuity.png` | Cell 62 | `plot` | Plot interpolation points, midpoints, and helper structures for continuity. | The output separates positional continuity, velocity continuity, and higher-order smoothness. |
| `09-bspline-local-support.png` | Cell 72 | `plot` | Plot a uniform cubic B-Spline and its control points. | B-Splines are smooth approximations and usually do not pass through every control point. |
| `10-keyframe-hermite.png` | Cell 77 | `plot` | Generate a 1D Hermite curve from key time, key value, and tangent. | This transfers geometric curve ideas to animation-editor keyframe curves. |
| `11-nonuniform-cardinal-time.png` | Cell 83 | `plot` | Compare Cardinal sampling under non-uniform key times. | Treating parameter t as real time can place samples incorrectly. |
| `12-bezier-time-root.png` | Cell 88 | `plot` | Show a non-uniform Bezier time curve and recovered internal parameter. | Animation systems often need to solve internal curve parameters from frame time. |
| `13-bspline-fitting.png` | Cell 92 | `plot` | Fit a complex sampled function with a uniform cubic B-Spline. | The fitted curve does not need to pass through every sample, but it preserves a stable trend. |
