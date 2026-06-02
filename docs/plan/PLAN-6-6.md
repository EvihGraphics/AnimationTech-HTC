# PLAN-6-6: EvihAnimation Style Mesh Visual Comparison

## Summary

- PLAN-6-5 added strict character mesh DAT/GIF evidence for the 15 skeletal/BVH `_evih` cases.
- The first mesh GIF renderer used the real `AnimLabSimpleMale.usd` mesh data, but it rendered simplified CPU/PIL polygons and did not match the EvihAnimation visual style.
- PLAN-6-6 changes strict mesh GIF evidence to an EvihAnimation-style Raylib channel while keeping DAT-based numeric comparison as the pass authority.

## Key Changes

- EvihAnimation reference is kept outside source control under `.reports/external`.
- Renderer metadata records the EvihAnimation reference repo, commit, key renderer files, and style notes in `comparison.json.mesh_visual_evidence.renderer_reference`.
- `animationtech_source_mesh.gif` and `evih_mesh.gif` now use `renderer == "evihanimation_style_raylib"`.
- The Raylib renderer uses the real mesh DAT buffers, deterministic CPU skinning, a perspective actor camera, cool sky, ground grid, warm directional light model, and root trajectory overlay.
- `--require-character-mesh-comparisons` rejects CPU/PIL mesh GIFs, blog assets, proxy-only views, and skeleton-only views as strict mesh visual evidence.

## Test Plan

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_matching_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_warping_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_graph_evih
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 animation_format_evih
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons --require-source-skeleton-baselines --require-character-mesh-comparisons
```

## Assumptions

- The EvihAnimation repository is a style/interface reference and is not vendored into this repository.
- Strict pass still comes from same-channel skeleton and mesh DAT comparison; GIFs are dynamic visual evidence.
- If Raylib rendering is unavailable, strict mesh GIF generation must fail instead of falling back to CPU/PIL.
