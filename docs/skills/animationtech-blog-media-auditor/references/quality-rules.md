# Quality Rules

## Acceptable Key Media

- Real `canvas`, `plot`, `table`, `formula`, or `artifact_summary` output from the case.
- Dynamic previews generated from a live viewer/control sequence.
- Code evidence only for non-key supporting evidence or python-module proof.

## Unacceptable Key Media

- Lecture video frames used as blog result images.
- Learning-card crops masquerading as result output.
- JupyterLab UI/chrome, error cards, widget-only screenshots, or whole-cell scroll captures.
- Ground-only viewer frames where the subject should be visible.
- Static pan/zoom animations used for a step that should show real animation behavior.

## Repair Pattern

1. Identify the missing visual subject from `visual_subject`, README text, transcript, and lecture demo.
2. Make the notebook capture deterministic with explicit input and camera setup.
3. When declared widget controls are stale or missing, use `live_prepare_cell` or `live_prepare_code` plus explicit `live_render` arguments.
4. When notebook cells share one global viewer, use `capture_cell_index` to capture the live canvas that actually receives later render commands.
5. Use `crop_canvas_render_area` when viewer sidebars pollute result images.
6. Recapture the slug and inspect key PNG/GIF/MP4 manually. A clean static inventory does not prove that the visual subject is present.
7. Compare hashes among key result files and key animation formats. Identical key media usually means two distinct claims accidentally captured the same state.
8. Add a targeted check only when a concrete failure mode was found.

## README Pattern

- Main media section: only meaningful result PNGs and visible GIF/video previews.
- Appendix table: result files, videos, and learning-card PNGs.
- No repeated media blocks.
- Preserve required published-video mirror URLs in a compact index when deduplicating the main media section.
- No stale or unexplained link-only video text.

## Motion Sampling

- Keep key animation previews based on real live-rendered frames.
- Expensive facial reconstruction or simulation steps may use a small deterministic sample set when every frame is costly.
- Tune motion thresholds per known visual scale; do not globally weaken quality gates to admit subtle motion.
- Reuse one kernel client during high-frame-count live capture; repeatedly creating channels can exhaust Windows handles.
