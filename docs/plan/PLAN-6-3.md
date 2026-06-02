# PLAN-6-3: Motion Graph 源 GIF 主体质量门修复

## Summary

- `motion_graph_evih` 的 blog 源 GIF 虽然来自 Cell 45 `key_animation`，但实际内容缺少可读的角色/路径主体，不能作为有效视觉证据。
- 根因是旧 gate 只校验 metadata、帧数和基础运动量，没有判断算法主体是否可读。
- 本次修复把 `algorithm_subject_quality` 变成内容级 gate：metadata 正确但主体不可读时，必须 fallback 到 baseline/source payload render。

## Implementation

- `sequence_quality` 继续负责 GIF 基础质量：帧数、非静态、运动区域不退化。
- `algorithm_subject_quality` 负责算法主体可读性：
  - 对 Motion Graph，要求 follow-path / graph-search 源 GIF 中角色与目标路径/轨迹主体不能被 UI 或背景区域吞掉。
  - blog GIF 若 UI/背景占比过高、主体不可读或运动主体退化，则判定失败。
- fallback provenance：
  - `replaced_reason == "algorithm_subject_unreadable"`
  - `origin == "baseline_render_algorithm_subject_unreadable"`
  - 保留 `rejected_blog_subject_quality` 以追踪被拒绝的 blog GIF 原因。

## Acceptance

- `motion_graph_evih` 重新运行后，`.reports/animation-comparisons/motion_graph_evih/animationtech_source.gif` 不再复制无价值 blog GIF，而是 baseline/source render。
- `comparison.json.visual_evidence.source_gif.algorithm_subject_quality.pass == true`。
- checker 的 `--require-baseline-comparisons` 继续验证 26 个 `_evih` 的 report、GIF、source metadata 和算法主体质量。

## Backlog

- 后续可以重新录制 Motion Graph blog GIF，使 Cell 45 的真实 source asset 本身包含可读角色和路径，再把 provenance 切回 `blog_asset`。
- 同类问题若出现在其他 blog GIF，应优先修 source asset；当前 fallback 机制用于避免无价值视觉证据冒充 strict pass。
