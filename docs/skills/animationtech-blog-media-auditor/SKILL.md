---
name: animationtech-blog-media-auditor
description: Audit and repair AnimationTech blog media when screenshots, GIFs, videos, or README evidence may not match the Jerome Eippers lecture videos, transcripts, or real notebook/script outputs.
---

# AnimationTech Blog Media Auditor

Use this skill when asked to fix or review `docs/blog` media for AnimationTech cases, especially when a blog image is empty, captures widgets/Jupyter chrome, uses a code card as evidence, or diverges from the corresponding lecture demo.

## Core Rule

Blog media must be real project output. Use lecture MP4/SRT files and `docs/transcripts` only as reference evidence. Do not use lecture frames as replacement blog assets.

## Workflow

1. Inspect the case in `docs/blog/media_manifest.json`, the blog `README.md`, `assets/README.md`, and existing assets.
2. Cross-check the declared transcript and the matching local video/SRT under:
   `D:\Users\hi\Documents\SCU\Chaos\knowledge_base\raw\video\JeromeEippers\_video_mp4\AnimationTech`
3. Run the helper for an inventory:
   ```powershell
   python .\docs\skills\animationtech-blog-media-auditor\scripts\audit_media_case.py --slug <slug>
   ```
4. For bad media, fix the capture path first: `live_render`, deterministic input, camera, timeline fraction, crop, motion sampling, or prepared-notebook conversion.
5. Recapture real assets:
   ```powershell
   python .\docs\blog\capture_blog_media.py --slug <slug> --run-timeout 900
   ```
   Never use `--derive-from-cards` for key media.
6. Trim the README so the main media section only contains meaningful algorithm outputs. Put learning cards and non-key evidence in the appendix table.
7. Add or update quality gates when the failure mode could recur.
8. Validate:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1
   powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1 -Strict
   powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\report_blog_docs.ps1
   ```

## What To Flag

- Empty checkerboard/ground-only viewer captures.
- Widget error cards, notebook chrome, whole-cell screenshots, or scroll captures.
- Key media sourced from `learning_card`, `derived_card_crop`, `static_pan_zoom`, or similar fallback provenance.
- GIF/MP4/WebM that only pans a static image when the lecture shows dynamic viewer behavior.
- Result images without the key visual subject described by `visual_subject`.
- README sections with repeated media blocks, stale GitHub attachment links, or many low-value evidence paragraphs.

## Editing Boundaries

- Keep source notebooks in `labs/` as references unless the user explicitly asks to edit them.
- Prefer prepared/study transforms and manifest capture configuration for automation fixes.
- Do not change the `media_manifest.json` schema; update existing fields or add established fields only.
- Preserve all manifest-declared media references in README or the appendix evidence table.

## References

- Read `references/case-groups.md` for known case grouping, video root, and parallel work split.
- Read `references/quality-rules.md` before adding new checks or deciding whether an asset is acceptable.
