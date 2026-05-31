from __future__ import annotations


CASES: dict[str, dict[str, object]] = {
    "motion_graph": {
        "title": "Motion Graph Evih",
        "family": "motion_graph",
        "metric": "motion graph baseline counts and trajectory playback",
        "uses_bvh": True,
    },
    "curve_and_spline": {
        "title": "Curve And Spline",
        "family": "theory_curve",
        "metric": "sampled cubic and Catmull-Rom curves",
    },
    "motiongraph_pointcloud_derivation": {
        "title": "Motion Graph Point Cloud Derivation",
        "family": "pointcloud",
        "metric": "weighted point cloud alignment",
    },
    "radial_basis_function": {
        "title": "Radial Basis Function",
        "family": "field",
        "metric": "radial basis scalar field",
    },
    "radial_basis_function_verbs_and_adverbs": {
        "title": "RBF Verbs And Adverbs",
        "family": "field",
        "metric": "verb/adverb blend field",
    },
    "laplacian_deformation": {
        "title": "Laplacian Deformation",
        "family": "deformation",
        "metric": "deformed control chain",
        "uses_bvh": True,
    },
    "animation": {
        "title": "Animation",
        "family": "bvh_motion",
        "metric": "BVH skeleton playback",
        "uses_bvh": True,
    },
    "character_usd": {
        "title": "Character USD",
        "family": "character",
        "metric": "character hierarchy demo",
        "uses_bvh": True,
    },
    "edit_material": {
        "title": "Edit Material",
        "family": "material",
        "metric": "material swatch states",
    },
    "multiple_characters": {
        "title": "Multiple Characters",
        "family": "multi_character",
        "metric": "multi-instance BVH playback",
        "uses_bvh": True,
    },
    "rigid_usd": {
        "title": "Rigid USD",
        "family": "rigid",
        "metric": "rigid transform demo",
    },
    "simple_sphere": {
        "title": "Simple Sphere",
        "family": "primitive",
        "metric": "primitive scene smoke",
    },
    "time_of_day": {
        "title": "Time Of Day",
        "family": "lighting",
        "metric": "light direction samples",
    },
    "animation_format": {
        "title": "Animation Format",
        "family": "bvh_motion",
        "metric": "motion import/export schema",
        "uses_bvh": True,
    },
    "footskate_cleanup_for_motion_capture_editing": {
        "title": "Footskate Cleanup",
        "family": "contacts",
        "metric": "foot contact debug",
        "uses_bvh": True,
    },
    "halo_4_facial_animation": {
        "title": "Halo 4 Facial Animation",
        "family": "halo",
        "metric": "synthetic facial controller stream",
    },
    "halo_4_exporter_from_maya": {
        "title": "Halo 4 Exporter From Maya",
        "family": "halo",
        "metric": "Maya fallback facial export smoke",
    },
    "knowing_when_to_put_your_foot_down": {
        "title": "Knowing When To Put Your Foot Down",
        "family": "contacts",
        "metric": "footfall classifier preview",
        "uses_bvh": True,
    },
    "motion_fields_for_interactive_character_animation": {
        "title": "Motion Fields",
        "family": "planning",
        "metric": "state field and policy path",
        "uses_bvh": True,
    },
    "motion_matching": {
        "title": "Motion Matching",
        "family": "matching",
        "metric": "feature query trajectory",
        "uses_bvh": True,
    },
    "motion_warping": {
        "title": "Motion Warping",
        "family": "warping",
        "metric": "root warp target",
        "uses_bvh": True,
    },
    "near_optimal_character_animation_with_continuous_control": {
        "title": "Near Optimal Continuous Control",
        "family": "planning",
        "metric": "continuous control policy path",
        "uses_bvh": True,
    },
    "precomputing_avatar_behavior": {
        "title": "Precomputing Avatar Behavior",
        "family": "graph",
        "metric": "precomputed graph walk",
        "uses_bvh": True,
    },
    "real_time_planning_for_parameterized_human_motion": {
        "title": "Real Time Planning For Parameterized Human Motion",
        "family": "planning",
        "metric": "value function trajectory",
        "uses_bvh": True,
    },
    "real_time_planning_multiprocess_func": {
        "title": "Real Time Planning Multiprocess Func",
        "family": "planning",
        "metric": "parallel planning worker smoke",
    },
    "verbs_and_adverbs": {
        "title": "Verbs And Adverbs",
        "family": "style",
        "metric": "style-conditioned motion preview",
        "uses_bvh": True,
    },
}


def get_case(slug: str) -> dict[str, object]:
    if slug not in CASES:
        known = ", ".join(sorted(CASES))
        raise KeyError(f"Unknown Evih reproduction case {slug!r}. Known cases: {known}")
    data = dict(CASES[slug])
    data["slug"] = slug
    return data
