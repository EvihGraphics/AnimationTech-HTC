# 全量修复 AnimationTech 博客媒体一致性并在 docs 归档 Skill

## Summary
对除 `motion_matching` 外的 18 个受管博客案例做“源视频/字幕/运行结果/博客媒体”一致性审计与修复。视频和字幕只作为对照依据，博客主图和动画必须来自 notebook/script 的真实算法输出。完成后把流程归档为当前仓库 docs 下的标准 skill 文档包。

## Key Changes
- 对照 `docs/blog/media_manifest.json`、`docs/transcripts/*.txt`、本地视频/SRT 目录和各博客 README/assets，逐案例识别空 viewer、widget error、整页截图、代码卡裁剪、静态假动画、与演讲展示不一致的媒体。
- 优先修复 `key_visual`、`key_animation`、`live_canvas`、viewer/timeline 输出；必要时调整 `live_render`、确定性输入、相机、timeline 参数、canvas crop、motion capture 范围。
- 重新采集受影响案例资产：
  ```powershell
  python .\docs\blog\capture_blog_media.py --slug <slug> --run-timeout 900
  ```
- 精简对应 README：保留有说明力的算法输出图/动画，移除坏图、重复证据、旧链接和无意义截图；代码卡集中到附录证据表。
- 加强 `check_blog_docs.ps1`：为发现的问题补充案例专项质量闸门，避免空画面、widget error 或缺少关键视觉主体的结果再次通过。
- 归档标准 skill 到：
  `D:\Users\hi\Documents\SCU\WorldModel\AnimationTech-HTC-learning\docs\skills\animationtech-blog-media-auditor`
  包含 `SKILL.md`、必要 reference 和可复用审计脚本。

## Public APIs / Interfaces / Types
- 不改变现有 `media_manifest.json` schema，只更新字段值或补充已有采集字段。
- 不改原始 notebook 的 public API；prepared/study 转换只做最小兼容修复。
- docs 内 skill 作为项目归档与复用说明，不影响仓库运行时接口。

## Test Plan
- 对每个修改过的案例重采媒体并人工 smoke 关键 PNG/GIF/MP4。
- 运行全量检查：
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1
  ```
- 运行严格发布检查和报告：
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1 -Strict
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\report_blog_docs.ps1
  ```
- 校验归档 skill 基本结构：存在 `SKILL.md`，frontmatter 包含 `name` 和 `description`，references/scripts 路径可读。

## Assumptions
- `motion_matching` 已完成，只作为参考样板，不重复重建。
- Skill 归档在当前仓库 `docs\skills\animationtech-blog-media-auditor`，不写入用户级 `C:\Users\hi\.codex\skills`。
- 视频帧不直接充当博客资产。
- 不主动覆盖用户已有无关脏改；若某个案例修复必须触碰同名脏文件，先隔离确认。
