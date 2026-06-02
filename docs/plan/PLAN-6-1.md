# 将 Evih 复现升级为动画序列级 Baseline 对齐验证

## Summary
- 你质疑成立：当前 26 个 `_evih` 的 `final.png` 只能证明 viewer/screenshot smoke，不足以证明复现成功。
- 新完成标准改为：使用与 AnimationTech 原始 case 完全一致的输入，烘焙或读取 AnimationTech baseline 动画/数组，再由 EvihAnimation pipeline 计算对应输出，并做逐帧、逐骨骼、逐控制量的数值比较。
- 静态截图降级为辅助证据；是否通过以 `comparison.json` 和 `validate_comparison()` 为准。

## Key Changes
- 为每个 case 增加 baseline contract：
  - 记录原始输入路径、hash、frame count、fps、bone names、parents、坐标空间、单位、允许差异。
  - 对 motion case 保存 AnimationTech baseline：local pos/quats、global matrices、root trajectory、contacts/controls/targets。
  - 对非 motion case 保存对应数值 baseline：曲线采样、RBF field、USD transforms、material/light/time samples 等，不再只看图片。
- 扩展每个 `core.py` 接口：
  - 保留 `run_pipeline()`、`save_generated()`、`load_generated()`、`validate_metrics()`。
  - 新增 `load_or_bake_baseline()`、`compare_to_baseline()`、`validate_comparison()`。
  - `generated.dat` 中必须包含 `input_signature`、`baseline_signature`、`evih_output`、`comparison`。
- 新增统一比较输出：
  - `.reports/animation-comparisons/<slug>_evih/comparison.json`
  - `.reports/animation-comparisons/<slug>_evih/overlay.mp4` 或 `contact_sheet.png` 作为人工审查辅助。
  - `.reports/animation-comparisons/<slug>_evih/input_signature.json`
- `runner.py` 增加标准参数：
  - `--baseline <path>`
  - `--comparison-report <path>`
  - `--require-comparison`
  - 当 `--require-comparison` 启用时，baseline 缺失、输入 hash 不一致、比较未通过都必须让 case fail。
- checker 增加严格验证：
  - `--require-baseline-comparisons`
  - 检查 26 个 `_evih` 都有 comparison report，且 `comparison.pass == true`。
  - 检查 artifact 中的 Evih 输出不是 procedural/synthetic 替代，除非 case contract 明确允许且有 baseline 数值对齐。

## Comparison Policy
- 输入一致性是硬门槛：
  - 原始 AnimationTech 和 Evih pipeline 必须使用同一个输入文件或同一份已烘焙数据。
  - 记录并校验 SHA256；不一致直接 fail。
- 动画比较默认指标：
  - `frame_count`、`fps`、`bone_count`、`bone_names`、`parents` 必须一致，除非 contract 显式声明 remap。
  - global joint position RMSE、max error。
  - root trajectory RMSE、max drift。
  - quaternion angular RMSE、max angular error。
  - contact labels 用 precision/recall/F1。
  - facial/control-point case 比较 control curves、vertex/control positions、blend weights。
- 默认阈值：
  - import/playback/pass-through case：shape exact，global position RMSE <= `1e-3` source units，max <= `1e-2`，angular RMSE <= `0.05` deg。
  - algorithmic/reduced case：使用 case-local threshold，并在 contract 中写明 reduction profile 和允许差异。
  - Motion Graph 继续保留 baseline counts，同时新增 `trajectory_matrices` 和 root trajectory 数值比较。
- 当前 procedural smoke 数据不再作为完成结果；只能作为 fallback debug，并且不能让 strict comparison 通过。

## Implementation Steps
- 第一阶段：基线烘焙
  - 新增 baseline baker，从原始 notebooks / python modules 提取 AnimationTech 计算结果。
  - 优先复用仓库已有 `.dat`：Motion Graph、Motion Fields、Near Optimal、Realtime Planning、Halo face 等。
  - 对 notebook 中未保存的动画，新增 extractor 在原始环境中运行关键 cell 后序列化 baseline。
- 第二阶段：Evih 计算替换
  - 按 case 组迁移当前 `common.build_case_payload()` synthetic 输出。
  - BVH/motion case 必须通过 EvihAnimation/ai4animation 加载同一输入动画，并输出统一 global matrices。
  - ipyanimlab scene case 记录可比较 transforms/material/light samples；动画 scene 也要比较 motion arrays。
  - Theory case 比较源 notebook 的采样数组，不以截图作为通过条件。
- 第三阶段：比较与报告
  - 每个 case 的 `run_pipeline()` 生成 Evih 输出后立即调用 `compare_to_baseline()`。
  - `validate_comparison()` 失败则 `tools/run_case.ps1 <slug>_evih` 失败。
  - viewer 改为可选 side-by-side / overlay 播放，辅助查看差异，但不作为唯一验证。
- 第四阶段：状态修正
  - 在完成序列级比较前，把当前 26 个 `_evih` 的结果视为 `smoke_passed`，不是 `passed`。
  - 只有 baseline comparison 通过后才恢复 `passed`。

## Test Plan
- 单 case：
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>_evih`
  - 必须生成 artifact、screenshot、comparison report，并且 `comparison.pass == true`。
- 全矩阵：
  - `python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons`
- 数值抽查：
  - `motion_graph_evih`：baseline counts + `trajectory_matrices` 对齐。
  - `animation_format_evih`：同一 BVH 输入、raw/mapped animation arrays 对齐。
  - `footskate_cleanup_for_motion_capture_editing_evih`：contacts 和 cleaned motion 对齐。
  - `halo_4_facial_animation_evih`：control curves / face point stream 对齐。
  - 一个 theory case：曲线或 field 数组与 notebook baseline 对齐。

## Assumptions
- 当前 26 个 `_evih` 运行成功只保留为 smoke 证据，不再宣称完整复现成功。
- 允许使用 AnimationTech 已烘焙 `.dat` 作为 baseline，但必须记录来源和 hash。
- 对确实没有动画输出的 case，使用源 notebook 的数值结果作为 baseline。
- 对外部工具不可用的 case，synthetic fallback 可以保留，但 strict comparison 下必须标为 fallback，不算完整通过。
