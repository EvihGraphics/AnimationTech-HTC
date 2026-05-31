# Motion Graph Contract

Use the existing `motion_graph_evih` case as the canonical migration template until a newer shared Evih runtime supersedes it.

## Source Files

- Original case: `labs/AnimationPapers/Motion Graph.ipynb`
- Evih notebook wrapper: `labs/AnimationPapers/Motion Graph EvihAnimation.ipynb`
- Computation layer: `labs/AnimationPapers/evih_motion_graph/core.py`
- Raylib viewer: `labs/AnimationPapers/evih_motion_graph/viewer.py`
- Generated artifact: `labs/AnimationPapers/motion_graph_evih_generated.dat`

## Baseline Constants

Keep these values stable unless the algorithm is intentionally changed and the source notebook is re-baselined:

- BVH source: `resources/lafan1/bvh/walk1_subject5.bvh`
- Ranges: `[[80, 350], [1185, 1800], [6997, 7287]]`
- Padding frames: `10`
- Window size: `10`
- Max transition error: `5000.0`
- Min transition distance: `20`
- Local minima count: `955` with tolerance `+/- 2`
- Final nodes: `546`
- Final edges: `1416`
- Shortest-path demo: `path_found == true`
- Shortest-path frame count: `53`

The current implementation applies a small parity correction for four local-minima positions to align the Torch distance path with the original Warp result. Preserve and document this correction if the distance backend changes.

## Artifact Schema

The generated pickle payload must include:

- `bone_names`: ordered bone name list
- `parents`: int parent index array
- `framerate`: source framerate
- `trajectory_matrices`: float matrix array shaped `[frame, bone, 4, 4]`
- `trajectory_check`: float array shaped `[frame, 3]`
- `trajectory`: reference path points
- `metrics`: JSON-like dict with baseline counts and runtime details

Metrics should include at least:

- `runtime_device`
- `evih_source_frames`
- `evih_source_bones`
- `source_frames`
- `clipped_frames`
- `bone_count`
- `point_count`
- `local_minima_count`
- `initial_edges`
- `longest_scc_count`
- `final_nodes`
- `final_edges`
- `path_found`
- `path_frame_count`
- `trajectory_frames`
- `trajectory_length`

## Implementation Notes

- Load the Evih BVH with `from ai4animation.Import.BVHImporter import BVH`, then read `motion.Hierarchy.BoneNames`, `motion.Hierarchy.ParentIndices`, `motion.Frames`, and `motion.Framerate`.
- Keep matrix orientation compatible with the current Raylib viewer: positions are read from `matrices[..., :3, 3]`; root is bone `0`.
- Preserve the original point-cloud definition by reading it from the source notebook rather than duplicating constants by hand.
- Use the original graph algorithm as the behavioral contract: clip motion, build point clouds, compute transition distances, find local minima, split graph nodes, prune to the longest strongly connected component, then produce path and trajectory playback data.
- Keep viewer code thin. It should load the artifact and draw skeleton lines, trajectory, frame text, and screenshot output; expensive computation belongs in the core layer.

## Acceptable Differences

- Runtime device may be `cpu` or `cuda`.
- Screenshots can differ in camera angle or colors if they clearly show the skeleton, ground/reference path, and debug connection.
- Local minima count can differ by at most two when floating-point or backend differences are explained.

Anything else needs a written baseline update and a fresh validation run.
