# EvihAnimation/Raylib 全案例复现计划

## Summary
- 目标从“运行现有 notebook 矩阵”改为“新增 EvihAnimation 框架复现矩阵”：为当前 27 个 case 新增 Evih/Raylib 复现版本，不替换原案例。
- 输出形态统一为纯 Raylib 应用：每个 case 至少有一个可执行 Python viewer/demo 脚本，自动运行时支持 `--screenshot`，避免 notebook/Jupyter 作为主入口。
- 验收标准为“指标 + 视觉”：算法类 case 对齐关键数值指标；所有 Evih case 产出非空截图并展示合理可视结果。
- Motion Graph 作为样板先归档成可复用 skill，再用该 skill 指导其余 case 的 Evih 迁移。

## Key Changes
- 新增复现命名规范：
  - case slug 使用 `<original_slug>_evih`
  - 环境 prefix 使用 `.envs/<original_slug>_evih`
  - viewer 入口使用 `labs/evih_reproductions/<original_slug>/viewer.py`
  - 产物使用 `labs/evih_reproductions/<original_slug>/generated.dat`
  - 截图使用 `.reports/visual-checks/<original_slug>_evih/final.png`
- 新增共享 Evih runtime 层：
  - 统一封装 BVH/FBX/GLB import、Motion frame sampling、skeleton drawing、trajectory/debug drawing、screenshot capture、matplotlib fallback。
  - 统一 CLI：`--artifact`、`--screenshot`、`--frame`、`--max-frames`、`--width`、`--height`。
  - 所有 Raylib demo 必须可无交互退出并保存截图。
- 新增模板：
  - 复用/扩展 `papers-evih`，固定 Python `3.12`、EvihAnimation pinned dependency、Torch、Raylib、NumPy/SciPy/Matplotlib。
  - 保留原模板，避免影响 27 个旧 case。
- 新增 skill：
  - 仓库归档：`skills/reproduce-animationtech-with-evih/`
  - 安装副本：`C:\Users\Administrator\.codex\skills\reproduce-animationtech-with-evih\`
  - skill 只保存迁移流程、baseline 合约、失败模式和检查脚本；不保存 `.envs/`、`.reports/`、生成数据或完整 notebook。

## Implementation Plan
- 第 0 阶段：Motion Graph 样板固化
  - 将现有 `motion_graph_evih` 调整为标准样板：纯 Raylib viewer 为主入口，notebook 降级为参考或可选说明。
  - 保留 Motion Graph 指标门槛：`local_minima_count=955`、`final_nodes=546`、`final_edges=1416`、`path_found=true`、`path_frame_count=53`。
  - skill 记录这套迁移模式：算法核心模块、Evih loader、Raylib viewer、artifact schema、截图 smoke。
- 第 1 阶段：轻量 Theory Evih demo
  - 迁移 `curve_and_spline`、`motiongraph_pointcloud_derivation`、`radial_basis_function`、`radial_basis_function_verbs_and_adverbs`。
  - 这些不依赖骨骼动画，使用 Raylib 绘制曲线、点云、权重场、矩阵/图形调试视图。
  - 验收：关键采样点/曲线统计对齐，截图非空。
- 第 2 阶段：基础角色/场景 demo
  - 迁移 `simple_sphere`、`rigid_usd`、`edit_material`、`time_of_day`、`character_usd`。
  - 用 Evih/Raylib 做等价可视 demo：primitive、mesh/scene import、材质参数、光照/昼夜、角色骨架展示。
  - 不要求逐 cell 复刻 ipyanimlab UI，只要求同主题行为和视觉结果。
- 第 3 阶段：BVH/运动编辑类
  - 迁移 `animation`、`multiple_characters`、`laplacian_deformation`、`animation_format`、`motion_warping`、`footskate_cleanup_for_motion_capture_editing`、`knowing_when_to_put_your_foot_down`、`verbs_and_adverbs`。
  - 统一使用 EvihAnimation `Motion`/BVH import 和 Raylib skeleton/trajectory/contacts 可视化。
  - 验收：帧数、骨骼数、关键轨迹/foot contact/warp 输出统计对齐；截图显示角色和调试元素。
- 第 4 阶段：论文算法核心类
  - 迁移 `motion_matching`、`motion_fields_for_interactive_character_animation`、`near_optimal_character_animation_with_continuous_control`、`precomputing_avatar_behavior`、`real_time_planning_for_parameterized_human_motion`、`real_time_planning_multiprocess_func`。
  - 保留原算法的核心数据流和指标，替换 viewer/export 为 Evih/Raylib。
  - 重型训练/precompute case 使用现有缩减策略，不强制 GPU。
- 第 5 阶段：Halo/非 BVH 特殊类
  - 迁移 `halo_4_facial_animation`、`halo_4_exporter_from_maya`。
  - 使用 synthetic fallback 数据驱动 Raylib 面部点/曲线/控制器可视化；Maya 可用时保留真实导出路径。
  - 验收：synthetic asset 可加载，面部控制数据非空，截图可见表情/控制点。

## Subagent Parallel Plan
- 主 agent 负责共享 Evih runtime、case manifest、skill、最终集成和验收。
- worker 分片必须使用不重叠写入目录：
  - Worker A：Theory 4 个 case，写 `labs/evih_reproductions/theory_*`
  - Worker B：基础场景/ipyanimlab 5 个 case
  - Worker C：BVH/运动编辑 7 个 case
  - Worker D：Motion Graph / Motion Matching / Avatar Behavior
  - Worker E：Motion Fields / RTP / Near Optimal / multiprocessing
  - Worker F：Halo 2 个 case
- 每个 worker 明确：不要改共享 manifest、模板、skill；只提交本分片 helper/viewer/artifact-check 代码和本地验证结果。
- 主 agent 集成后统一新增 `tools/cases.yaml` Evih entries，避免并发写 manifest。
- 重型 worker 不与其他重型 worker 同时跑完整 precompute；只做本地单 case 验证，最终由主 agent 排队全量验证。

## Test Plan
- 每个 `<slug>_evih` case：
  - `run_case.ps1 <slug>_evih` exit code `0`
  - generated artifact 存在且非空
  - Raylib `--screenshot` 生成非空 PNG
  - `.reports/status/<slug>_evih.json` 为 `passed`
- 全 Evih 矩阵：
  - 新增 Evih-only validator 或 `validate_all.ps1 -Only <all *_evih slugs>`
  - 预期 27 个 Evih case 全 passed，0 failed，0 blocked
- 回归：
  - 原 27 个 case 不改行为，现有 `motion_graph` 和 `motion_graph_evih` 继续 passed
  - `tools/cases.yaml` 运行时间戳类变更在验证后恢复
- Skill：
  - `quick_validate.py` 通过
  - 新会话能用 skill 指导新增 Evih case 或排查 Evih case 失败

## Assumptions
- “EvihAnimation 框架复现”指新增 Evih/Raylib 等价实现，不要求删除或替换原 notebook。
- “纯 Raylib 应用”是主入口；notebook 只作为参考、解释或可选开发视图。
- “指标 + 视觉”等价不要求逐 cell 输出一致；算法关键指标必须对齐，视觉 smoke 必须可自动截图。
- EvihAnimation 不完全覆盖 ipyanimlab/USD/Jupyter widget 能力；这些 case 采用同主题等价 Raylib demo，而不是逐 API 翻译。
