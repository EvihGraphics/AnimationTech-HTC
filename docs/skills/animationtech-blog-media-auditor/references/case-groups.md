# Case Groups

Video/SRT evidence root:

```text
D:\Users\hi\Documents\SCU\Chaos\knowledge_base\raw\video\JeromeEippers\_video_mp4\AnimationTech
```

Canonical transcript references are declared per case in `docs/blog/media_manifest.json` and mirrored in `docs/transcripts`.

## Parallel Audit Split

- Worker A: `animation_format`, `footskate_cleanup_for_motion_capture_editing`, `motion_graph`, `motion_warping`
- Worker B: `near_optimal_character_animation_with_continuous_control`, `precomputing_avatar_behavior`, `verbs_and_adverbs`
- Worker C: `real_time_planning_for_parameterized_human_motion`, `motion_fields_for_interactive_character_animation`, `knowing_when_to_put_your_foot_down`
- Worker D: `halo_4_facial_animation`, `real_time_planning_multiprocess_func`, `halo_4_exporter_from_maya`, all Theory cases

`motion_matching` is the reference repair pattern. Do not rebuild it unless explicitly requested.

## Shared Files

Coordinate edits to these files serially:

- `docs/blog/media_manifest.json`
- `docs/blog/check_blog_docs.ps1`
- `tools/prepare_notebook.py`
- `tools/cases.yaml`

Case README/assets directories can be split by slug when avoiding shared files.
