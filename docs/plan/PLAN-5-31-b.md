# 将 Evih 复刻升级为 Motion Graph 式方案与 Skill

## Summary
- 以 `labs/AnimationPapers/evih_motion_graph` 作为正式模板，而不是当前共享 `runtime.py` 的 family smoke 框架。
- 每个 `_evih` 复刻都要有 case-local `core.py`、`viewer.py`、artifact schema、baseline/metrics contract 和 `validate_metrics()`，共享 runner 只做分发。
- Skill 也改成 Motion Graph 风格：要求先抽取源案例合约，再实现纯计算层、Raylib viewer、指标校验和视觉证据。

## Key Changes
- 复刻目录标准改为：
  - `labs/evih_reproductions/<slug>/core.py`
  - `labs/evih_reproductions/<slug>/viewer.py`
  - `labs/evih_reproductions/<slug>/__init__.py`
  - `labs/evih_reproductions/<slug>/generated.dat`
- 每个 `core.py` 暴露同一组接口：`run_pipeline(...)`、`save_generated(...)`、`load_generated(...)`、`validate_metrics(...)`；Motion Graph 继续作为最完整参考。
- 每个 `viewer.py` 保持标准 CLI：`--artifact`、`--screenshot`、`--frame`、`--max-frames`、`--width`、`--height`，并只负责加载 artifact 和渲染。
- `labs/evih_reproductions/runner.py` 改为轻量 dispatcher：根据 `--case` 调用对应 case module，不再承载核心算法或通用假数据。
- `motion_graph_evih` 保留 `labs/AnimationPapers/evih_motion_graph` 为 canonical template；共享 runner 可通过薄 adapter 调用它，避免复制核心算法。

## Skill Updates
- 更新 `skills/reproduce-animationtech-with-evih/SKILL.md`：明确“不接受仅 family smoke 作为完成”，完成标准必须类似 Motion Graph。
- 更新 `references/evih-runtime-patterns.md`：把 `core.py + viewer.py + generated.dat + validate_metrics()` 设为默认结构。
- 扩展 checker：严格模式下检查每个 `_evih` case 是否存在 case-local `core.py`、`viewer.py`、标准 CLI、artifact、screenshot，并可选检查 `validate_metrics` 与 artifact metrics。
- 增加 `references/case-contract-template.md`：记录每个 case 需要抽取的源 notebook 合约、关键数组形状、计数、截图证据和允许差异。

## Migration Plan
- 第一阶段保留现有 26 个 `_evih` manifest 与产物，但标记当前共享 runtime 结果为 smoke baseline。
- 第二阶段按 case 分组迁移为 Motion Graph 式模块：Theory、ipyanimlab scene、BVH/motion editing、planning/matching、Halo/facial。
- 每迁移一个 case，就把算法/数据生成移入该 case 的 `core.py`，把绘制逻辑移入 `viewer.py`，并让 runner 调用新模块。
- 对重型 planning/precompute case 使用 reduced validation profile，但仍要在 metrics 中记录采样规模、缓存来源和 intentional differences。
- 最后删除或降级共享 `runtime.py` 中的通用 synthetic 逻辑，只保留真正跨 case 的小工具函数。

## Test Plan
- 结构验证：checker strict 模式要求 26 个 `_evih` 都有 Motion Graph 式模块结构。
- 行为验证：每个 `core.validate_metrics()` 通过；Motion Graph baseline 继续保持 `local_minima_count ~= 955`、`final_nodes=546`、`final_edges=1416`。
- 视觉验证：每个 `viewer.py --screenshot --max-frames 0` 生成非空 PNG，并显示该 case 的关键证据而不是泛用装饰图。
- 集成验证：`tools/run_case.ps1 <slug>_evih` 对全部 Evih case 通过，原始 26 个 case 不被替换或移动。

## Assumptions
- 你的目标是把复刻质量和 skill 方法论对齐 `evih_motion_graph`，不是只追求 26 个 `_evih` case 能跑通。
- 现有共享 runner/manifest 可以保留，但共享 runtime 不能作为最终核心实现。
- 对外部工具不可用的 case，可以使用 synthetic fallback，但必须像 Motion Graph 一样写清 artifact schema、metrics 和允许差异。
