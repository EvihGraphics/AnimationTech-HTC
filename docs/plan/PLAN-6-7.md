# 并行修复博客媒体一致性并归档项目 Skill

## Summary
在执行阶段使用 subagents 并行审计和修复除 `motion_matching` 外的 18 个受管案例。每个 subagent 负责一组案例的媒体一致性排查、重采建议和案例目录修复；主 agent 负责共享文件合并、全量质量闸门、最终 skill 归档到 `D:\Users\hi\Documents\SCU\WorldModel\AnimationTech-HTC-learning\docs\skills\animationtech-blog-media-auditor`。

## Parallel Work Split
- Worker A：viewer/key animation 高风险案例  
  `animation_format`、`footskate_cleanup_for_motion_capture_editing`、`motion_graph`、`motion_warping`
- Worker B：角色控制/规划类案例  
  `near_optimal_character_animation_with_continuous_control`、`precomputing_avatar_behavior`、`verbs_and_adverbs`
- Worker C：重计算或非实时案例  
  `real_time_planning_for_parameterized_human_motion`、`motion_fields_for_interactive_character_animation`、`knowing_when_to_put_your_foot_down`
- Worker D：剩余 notebook 与 python_module 案例  
  `halo_4_facial_animation`、`real_time_planning_multiprocess_func`、`halo_4_exporter_from_maya`、Theory 分组 5 个案例
- Main agent：不重复处理案例；只做共享文件整合、冲突消解、全量检查、skill 归档。

## Key Changes
- 每个 worker 对照对应视频/SRT、`docs/transcripts`、manifest、README 和 assets，找出与演讲展示不一致或无意义的媒体。
- Worker 可修改自己负责的案例目录：README、assets、assets/README、必要的 USER_GUIDE；不得直接改其他案例。
- `docs/blog/media_manifest.json`、`check_blog_docs.ps1`、`tools/prepare_notebook.py` 由 main agent 统一修改；worker 只在最终报告里列出所需 manifest/check/notebook 转换变更。
- 对需重采案例运行：
  ```powershell
  python .\docs\blog\capture_blog_media.py --slug <slug> --run-timeout 900
  ```
- 不使用视频帧冒充博客结果；视频和字幕只作为参考证据。

## Test Plan
- 每个 worker 对负责案例做人工 smoke：关键 PNG/GIF/MP4 必须有实际算法主体，不是空 viewer、widget error、代码卡、Jupyter chrome 或假动画。
- Main agent 合并后运行：
  ```powershell
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1 -Strict
  powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\report_blog_docs.ps1
  ```
- Skill 归档后校验 `SKILL.md` frontmatter、references/scripts 可读，并记录 Motion Matching 作为标准样板。

## Assumptions
- 当前仍处于 Plan Mode，因此这里只规划 subagent fan-out；执行阶段再实际 spawn workers。
- `motion_matching` 不重做，只作为修复模板和 skill 参考案例。
- 共享文件由 main agent 串行修改，避免 subagent 并发写同一文件导致冲突。
- 不覆盖用户已有无关脏改；若某案例必须触碰已有脏文件，先由 main agent隔离确认。
