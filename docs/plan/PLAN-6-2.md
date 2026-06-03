# PLAN-6-2: Evih Baseline/GIF 验收链路收尾可交付

## Summary

- 6/1 验收链路已经从静态截图 smoke 升级为 baseline comparison + 动态 GIF 证据。
- 当前仓库口径仍是 26 个原始 case 和 26 个 `_evih` case；严格 checker 已验证 26 个 `_evih` 均通过。
- `.reports/animation-baselines` 与 `.reports/animation-comparisons` 是可重建运行产物，不作为源码交付内容。

## Current Acceptance State

- 最终验收命令：

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons
```

- 当前通过标准：
  - artifact 存在且 metrics 可由 case-local `validate_metrics()` 验证。
  - screenshot 存在且只作为 viewer smoke 证据。
  - `.reports/animation-comparisons/<slug>_evih/comparison.json` 存在，且 `pass == true`。
  - `.reports/animation-comparisons/<slug>_evih/evih.gif` 与 `animationtech_source.gif` 均存在并通过动态序列质量门槛。
  - `comparison.json.visual_evidence.source_gif.algorithm_feature_match == true`。

## Visual Evidence Provenance

- comparison 目录：`.reports/animation-comparisons/<slug>_evih/`。
- 每个目录必须包含：
  - `comparison.json`
  - `evih.gif`
  - `animationtech_source.gif`
- 当前源 GIF provenance：
  - 9 个 case 使用 blog 中最后核心动画/结果资产，`origin == "blog_asset"`。
  - 16 个 case 因没有合格 blog GIF，使用 baseline/source payload 重新渲染，`origin == "baseline_render_missing_blog_asset"`。
  - 1 个 case（`motion_graph_evih`）因 blog GIF metadata 正确但算法主体不可读，使用 baseline/source payload 重新渲染，`origin == "baseline_render_algorithm_subject_unreadable"`。
- `baseline_render_missing_blog_asset` 与 `baseline_render_algorithm_subject_unreadable` 是当前阶段可接受的 provenance；它们必须在 `comparison.json` 中显式记录 `replaced_reason`，不能冒充真实 blog/source strict asset。

## Delivery Review Checklist

- `labs/evih_reproductions/common.py` 负责 input signature、baseline/report 路径、JSON-safe report、数值比较、GIF 选择/渲染/校验。
- `labs/evih_reproductions/runner.py` 负责 `--baseline`、`--comparison-report`、`--require-comparison`、`--evih-gif`、`--source-gif`、`--require-gifs` 的统一运行。
- `tools/run_case.ps1` 对 `_evih` 非 `-SmokeOnly` 默认启用 baseline comparison 和 GIF evidence；`-SmokeOnly` 只产生 `smoke_passed`。
- checker 的 `--require-baseline-comparisons` 同时检查 comparison report、两份 GIF、source subject metadata 和 `algorithm_feature_match`。
- case-local `core.py` 保留 `run_pipeline`、`save_generated`、`load_generated`、`validate_metrics`，并提供 `load_or_bake_baseline`、`compare_to_baseline`、`validate_comparison`。
- `.reports/` 已由 `.gitignore` 忽略；运行产物可复建，不纳入源码交付。

## Repro Commands

语法检查：

```powershell
python -m py_compile labs/evih_reproductions/common.py labs/evih_reproductions/runner.py skills/reproduce-animationtech-with-evih/scripts/check_evih_reproduction.py
```

代表 case 抽查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_graph_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 animation_format_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 footskate_cleanup_for_motion_capture_editing_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 halo_4_facial_animation_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 radial_basis_function_evih
```

最终验收：

```powershell
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons
```

## Backlog

- PLAN-6-3 supersedes the original Motion Graph source GIF acceptance: its Cell 45 blog GIF was metadata-correct but visually unreadable, so Motion Graph now requires `baseline_render_algorithm_subject_unreadable` until the blog asset is re-recorded.
- 为 16 个 `baseline_render_missing_blog_asset` case 补录或生成更接近原 notebook 最后核心 cell 的 AnimationTech source GIF。
- 逐步把 reduced/synthetic baseline 推向更强的原 notebook 数值输出对齐，尤其是 planning、scene/material/light、theory cases。
- 对人工审查体验可补充 side-by-side GIF index 或 HTML summary，但不得降低 `comparison.json` 和 checker 的严格通过标准。
