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
3. Use `crop_canvas_render_area` when viewer sidebars pollute result images.
4. Recapture the slug and inspect key PNG/GIF/MP4 manually.
5. Add a targeted check only when a concrete failure mode was found.

## README Pattern

- Main media section: only meaningful result PNGs and visible GIF/video previews.
- Appendix table: result files, videos, and learning-card PNGs.
- No repeated media blocks.
- No stale link-only video text.
