# PLAN-6-4: Evih 骨骼动画 Source Skeleton Channel

## Summary

- `motion_warping_evih` 暴露出原先视觉对照不在同一通道：`animationtech_source.gif` 可能来自 blog 录屏，而 `evih.gif` 来自统一骨架 renderer。
- 本次收尾把 15 个 `uses_bvh`/骨骼动画 `_evih` case 的 strict 对照切到 source-data-first：先写 `.reports/animation-comparisons/<slug>_evih/animationtech_source.dat`，再用同一个 skeleton/trajectory renderer 生成 `animationtech_source.gif`。
- Blog GIF 对骨骼 case 只保留为 `supplemental_blog_gif` 元数据，不再决定 strict pass。

## Scope

覆盖 15 个骨骼 case：

`motion_graph`, `laplacian_deformation`, `animation`, `character_usd`, `multiple_characters`, `animation_format`, `footskate_cleanup_for_motion_capture_editing`, `knowing_when_to_put_your_foot_down`, `motion_fields_for_interactive_character_animation`, `motion_matching`, `motion_warping`, `near_optimal_character_animation_with_continuous_control`, `precomputing_avatar_behavior`, `real_time_planning_for_parameterized_human_motion`, `verbs_and_adverbs`.

## Acceptance

- `run_case.ps1 <slug>_evih` 对上述 15 个 case 默认传入 `--source-skeleton` 和 `--require-source-skeleton-baseline`。
- `comparison.json` 包含：
  - `source_channel: "animationtech_skeleton_trajectory"`
  - `source_data.path`
  - `source_data.signature`
  - `source_skeleton_comparison.pass == true`
- `visual_evidence.source_gif.origin == "animationtech_source_payload"`。
- `animationtech_source.gif` 与 `evih.gif` 均由统一 skeleton/trajectory renderer 生成，避免 blog 录屏与骨架 renderer 的跨通道视觉比较。

## Validation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_warping_evih
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons --require-source-skeleton-baselines
```

## Backlog

- 继续把每个骨骼 case 的 source extractor 从 reduced source payload 推进到对应 notebook final cell 的显式导出。
- Blog 核心 GIF 仍可用于人工审阅，但不能再替代 strict source skeleton data。
