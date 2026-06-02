# PLAN-6-5: Character Mesh Strict Visual Comparison

## Summary

- 在 15 个骨骼/BVH `_evih` case 的 skeleton source channel 之上，新增 strict character mesh channel。
- Mesh strict 不使用 blog GIF、静态截图、骨架线段或 procedural proxy；它使用真实 `AnimLabSimpleMale.usd` skinned mesh buffer。
- Source 与 Evih mesh GIF 由同一个 deterministic CPU/PIL renderer 生成，保持相机、采样帧、轨迹 overlay 和缩放一致。

## Acceptance

- 每个骨骼/BVH comparison 目录包含：
  - `animationtech_source_mesh.dat`
  - `evih_mesh.dat`
  - `animationtech_source_mesh.gif`
  - `evih_mesh.gif`
- `comparison.json` 包含：
  - `mesh_channel: "animationtech_skinned_character_mesh"`
  - `source_mesh_data`
  - `evih_mesh_data`
  - `mesh_visual_evidence`
  - `mesh_comparison.pass == true`
- Checker 新增 `--require-character-mesh-comparisons`，并拒绝 `blog_asset`、`proxy_only`、`skeleton_only` 作为 mesh strict origin。

## Validation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 motion_warping_evih
python skills\reproduce-animationtech-with-evih\scripts\check_evih_reproduction.py --repo-root . --expect-full-matrix --strict --require-artifacts --require-screenshots --validate-metrics --require-baseline-comparisons --require-source-skeleton-baselines --require-character-mesh-comparisons
```

## Notes

- `.reports/animation-comparisons` 下的 mesh DAT/GIF 是可重建产物。
- Mesh DAT 保存完整 static mesh buffers、skinning buffers、character-compatible global matrices、sampled skinned vertices、bbox、root trajectory 和 signature。
