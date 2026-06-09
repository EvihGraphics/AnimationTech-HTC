import argparse
import json
import re
from pathlib import Path


MOTION_FIELDS_SLUG = "motion_fields_for_interactive_character_animation"
REALTIME_PLANNING_SLUG = "real_time_planning_for_parameterized_human_motion"
KNOWING_FOOT_DOWN_SLUG = "knowing_when_to_put_your_foot_down"
NEAR_OPTIMAL_SLUG = "near_optimal_character_animation_with_continuous_control"
MOTION_MATCHING_SLUG = "motion_matching"
VERBS_AND_ADVERBS_SLUG = "verbs_and_adverbs"


GAMEPAD_HELPER_SOURCE = """def animationtech_gamepad_axis(gamepad, index, default=0.0):
    try:
        axes = getattr(gamepad, "axes", ())
        if axes is None or len(axes) <= index:
            return default
        return axes[index].value
    except Exception:
        return default


def animationtech_gamepad_button(gamepad, index, default=0.0):
    try:
        buttons = getattr(gamepad, "buttons", ())
        if buttons is None or len(buttons) <= index:
            return default
        return buttons[index].value
    except Exception:
        return default
"""

GAMEPAD_AXIS_PATTERN = re.compile(r"gamepad\.axes\s*\[\s*(\d+)\s*\]\.value")
GAMEPAD_BUTTON_PATTERN = re.compile(r"gamepad\.buttons\s*\[\s*(\d+)\s*\]\.value")


VERBS_AND_ADVERBS_INTERPOLATE_SOURCE = """# Show how a value selects one segment and four B-spline control points.
from IPython.display import display

fig2, ax2 = plt.subplots(1, 1)

def test_value(value):
    BS = np.array([[-1,3,-3,1],[3,-6,0,4],[-3,3,3,1], [1,0,0,0]], dtype=np.double).T/6.0
    t = np.linspace(0, 1, 101)
    T = np.column_stack([t**3, t**2, t, np.ones_like(t)])

    index = min(int(value * 20), 19)
    ratio = (value * 20) - index
    pts = bspline_animations.quats[5, :, 1, 1][index:index+4]

    y = np.dot(T, np.dot(BS, pts))

    # x points along keyframes
    x_actual = np.arange(401, dtype=np.int32)
    ax2.cla()

    ax2.plot((index+t)*400/20, y, label='Cubic B Spline')
    ax2.plot(x_actual, resampled_animations[5].quats[:, 1, 1], label='Original', linestyle='dashed')
    ax2.scatter(x_points[index:index+4], pts, label='Control Points', color='red')
    ax2.scatter((index+ratio)*400/20, y[int(ratio*100)], label='value', color='blue')

    ax2.set_title('Selecting a Cubic B-Spline Segment')
    ax2.set_xlabel('Keyframe')
    ax2.set_ylabel('Value')
    ax2.legend(loc='best')
    fig2.canvas.draw_idle()

value_slider = widgets.FloatSlider(
    description='value', min=0, max=1, step=0.001, value=0,
    layout=widgets.Layout(width='800px'), continuous_update=True,
)

def update_test_value(change):
    test_value(change['new'])

value_slider.observe(update_test_value, names='value')
test_value(value_slider.value)
display(widgets.VBox([value_slider, fig2.canvas]))
"""


def get_motion_fields_settings(training_profile: str, torch_device: str) -> dict:
    use_gpu = torch_device.startswith("cuda")
    profiles = {
        "validate": {
            "umap_neighbors": 20,
            "state_ranges": {
                "add_states(2, slice(100,2800))\n": "add_states(2, slice(100,260))\n",
                "add_states(15, slice(1200,1800))\n": "add_states(15, slice(1200,1260))\n",
                "add_states(15, slice(3450,3860))\n": "add_states(15, slice(3450,3510))\n",
                "add_states(14, slice(180,800))\n": "add_states(14, slice(180,240))\n",
                "add_states(13, slice(200,2300))\n": "add_states(13, slice(200,320))\n",
            },
            "k_neighbors": 6,
            "theta_count": 9,
            "epoch": 20,
        },
        "adaptive_cpu": {
            "umap_neighbors": 30,
            "state_ranges": {
                "add_states(2, slice(100,2800))\n": "add_states(2, slice(100,500))\n",
                "add_states(15, slice(1200,1800))\n": "add_states(15, slice(1200,1320))\n",
                "add_states(15, slice(3450,3860))\n": "add_states(15, slice(3450,3570))\n",
                "add_states(14, slice(180,800))\n": "add_states(14, slice(180,320))\n",
                "add_states(13, slice(200,2300))\n": "add_states(13, slice(200,520))\n",
            },
            "k_neighbors": 8,
            "theta_count": 13,
            "epoch": 35,
        },
        "adaptive_gpu": {
            "umap_neighbors": 40,
            "state_ranges": {
                "add_states(2, slice(100,2800))\n": "add_states(2, slice(100,900))\n",
                "add_states(15, slice(1200,1800))\n": "add_states(15, slice(1200,1500))\n",
                "add_states(15, slice(3450,3860))\n": "add_states(15, slice(3450,3690))\n",
                "add_states(14, slice(180,800))\n": "add_states(14, slice(180,500))\n",
                "add_states(13, slice(200,2300))\n": "add_states(13, slice(200,900))\n",
            },
            "k_neighbors": 10,
            "theta_count": 17,
            "epoch": 80,
        },
        "quality_cpu": {
            "umap_neighbors": 45,
            "state_ranges": {
                "add_states(2, slice(100,2800))\n": "add_states(2, slice(100,1200))\n",
                "add_states(15, slice(1200,1800))\n": "add_states(15, slice(1200,1560))\n",
                "add_states(15, slice(3450,3860))\n": "add_states(15, slice(3450,3750))\n",
                "add_states(14, slice(180,800))\n": "add_states(14, slice(180,620))\n",
                "add_states(13, slice(200,2300))\n": "add_states(13, slice(200,1200))\n",
            },
            "k_neighbors": 10,
            "theta_count": 17,
            "epoch": 60,
        },
        "quality_gpu": {
            "umap_neighbors": 60,
            "state_ranges": {
                "add_states(2, slice(100,2800))\n": "add_states(2, slice(100,1800))\n",
                "add_states(15, slice(1200,1800))\n": "add_states(15, slice(1200,1700))\n",
                "add_states(15, slice(3450,3860))\n": "add_states(15, slice(3450,3820))\n",
                "add_states(14, slice(180,800))\n": "add_states(14, slice(180,720))\n",
                "add_states(13, slice(200,2300))\n": "add_states(13, slice(200,1800))\n",
            },
            "k_neighbors": 12,
            "theta_count": 17,
            "epoch": 120,
        },
    }

    if training_profile == "quality":
        return profiles["quality_gpu" if use_gpu else "quality_cpu"]
    if training_profile == "adaptive":
        return profiles["adaptive_gpu" if use_gpu else "adaptive_cpu"]
    return profiles["validate"]


def get_realtime_planning_settings(training_profile: str) -> dict:
    profiles = {
        "validate": {
            "replacements": [
                ("X = np.zeros([CLIP_COUNT, 100000])", "X = np.zeros([CLIP_COUNT, 20000])"),
                ("y = np.zeros([CLIP_COUNT, 100000])", "y = np.zeros([CLIP_COUNT, 20000])"),
                ("for path in range(800):", "for path in range(80):"),
                ("residuals = np.zeros([CLIP_COUNT * 100000])", "residuals = np.zeros([CLIP_COUNT * 20000])"),
                ("pre_compute_table_x = np.linspace(-1000, 1000, 1001)", "pre_compute_table_x = np.linspace(-300, 300, 201)"),
                ("pre_compute_table_z = np.linspace(-1000, 1000, 1001)", "pre_compute_table_z = np.linspace(-300, 300, 201)"),
                ("all_valid_states = np.zeros([1000000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([300000, 4], dtype=np.float32)"),
                ("all_valid_states = np.zeros([100000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([200000, 4], dtype=np.float32)"),
                ("for _ in range(100):", "for _ in range(5):"),
                ("EPOCH = 50", "EPOCH = 6"),
                ("RESTART_EPOCH = 10", "RESTART_EPOCH = 3"),
                ("for _ in range(20):", "for _ in range(2):"),
                ("EPOCH = 15", "EPOCH = 4"),
                ("RESTART_EPOCH = 100", "RESTART_EPOCH = 4"),
                ("clip_index = np.zeros([GROUP_VALUE_COUNT, 100000], dtype=np.uint32)", "clip_index = np.zeros([GROUP_VALUE_COUNT, 15000], dtype=np.uint32)"),
                ("X = np.zeros([GROUP_VALUE_COUNT, 100000, 2])", "X = np.zeros([GROUP_VALUE_COUNT, 15000, 2])"),
                ("y = np.zeros([GROUP_VALUE_COUNT, 100000])", "y = np.zeros([GROUP_VALUE_COUNT, 15000])"),
                ("dist = 500", "dist = 200"),
            ],
        },
        "adaptive": {
            "replacements": [
                ("X = np.zeros([CLIP_COUNT, 100000])", "X = np.zeros([CLIP_COUNT, 40000])"),
                ("y = np.zeros([CLIP_COUNT, 100000])", "y = np.zeros([CLIP_COUNT, 40000])"),
                ("for path in range(800):", "for path in range(200):"),
                ("residuals = np.zeros([CLIP_COUNT * 100000])", "residuals = np.zeros([CLIP_COUNT * 40000])"),
                ("pre_compute_table_x = np.linspace(-1000, 1000, 1001)", "pre_compute_table_x = np.linspace(-500, 500, 401)"),
                ("pre_compute_table_z = np.linspace(-1000, 1000, 1001)", "pre_compute_table_z = np.linspace(-500, 500, 401)"),
                ("all_valid_states = np.zeros([1000000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([600000, 4], dtype=np.float32)"),
                ("all_valid_states = np.zeros([100000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([350000, 4], dtype=np.float32)"),
                ("for _ in range(100):", "for _ in range(10):"),
                ("EPOCH = 50", "EPOCH = 10"),
                ("RESTART_EPOCH = 10", "RESTART_EPOCH = 4"),
                ("for _ in range(20):", "for _ in range(4):"),
                ("EPOCH = 15", "EPOCH = 6"),
                ("RESTART_EPOCH = 100", "RESTART_EPOCH = 6"),
                ("clip_index = np.zeros([GROUP_VALUE_COUNT, 100000], dtype=np.uint32)", "clip_index = np.zeros([GROUP_VALUE_COUNT, 30000], dtype=np.uint32)"),
                ("X = np.zeros([GROUP_VALUE_COUNT, 100000, 2])", "X = np.zeros([GROUP_VALUE_COUNT, 30000, 2])"),
                ("y = np.zeros([GROUP_VALUE_COUNT, 100000])", "y = np.zeros([GROUP_VALUE_COUNT, 30000])"),
                ("dist = 500", "dist = 300"),
            ],
        },
        "quality": {
            "replacements": [
                ("X = np.zeros([CLIP_COUNT, 100000])", "X = np.zeros([CLIP_COUNT, 70000])"),
                ("y = np.zeros([CLIP_COUNT, 100000])", "y = np.zeros([CLIP_COUNT, 70000])"),
                ("for path in range(800):", "for path in range(350):"),
                ("residuals = np.zeros([CLIP_COUNT * 100000])", "residuals = np.zeros([CLIP_COUNT * 70000])"),
                ("pre_compute_table_x = np.linspace(-1000, 1000, 1001)", "pre_compute_table_x = np.linspace(-700, 700, 601)"),
                ("pre_compute_table_z = np.linspace(-1000, 1000, 1001)", "pre_compute_table_z = np.linspace(-700, 700, 601)"),
                ("all_valid_states = np.zeros([1000000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([1000000, 4], dtype=np.float32)"),
                ("all_valid_states = np.zeros([100000000, 4], dtype=np.float32)", "all_valid_states = np.zeros([600000, 4], dtype=np.float32)"),
                ("for _ in range(100):", "for _ in range(20):"),
                ("EPOCH = 50", "EPOCH = 14"),
                ("RESTART_EPOCH = 10", "RESTART_EPOCH = 5"),
                ("for _ in range(20):", "for _ in range(8):"),
                ("EPOCH = 15", "EPOCH = 10"),
                ("RESTART_EPOCH = 100", "RESTART_EPOCH = 8"),
                ("clip_index = np.zeros([GROUP_VALUE_COUNT, 100000], dtype=np.uint32)", "clip_index = np.zeros([GROUP_VALUE_COUNT, 50000], dtype=np.uint32)"),
                ("X = np.zeros([GROUP_VALUE_COUNT, 100000, 2])", "X = np.zeros([GROUP_VALUE_COUNT, 50000, 2])"),
                ("y = np.zeros([GROUP_VALUE_COUNT, 100000])", "y = np.zeros([GROUP_VALUE_COUNT, 50000])"),
                ("dist = 500", "dist = 400"),
            ],
        },
    }
    return profiles.get(training_profile, profiles["validate"])


def get_foot_down_settings(training_profile: str) -> dict:
    profiles = {
        "validate": {
            "ranges": "ranges = {\n    'walk1_subject5' : [(60, 320)],\n}\n",
            "clip_length": 60,
            "n_neighbors": 5,
        },
        "adaptive": {
            "ranges": "ranges = {\n    'walk1_subject5' : [(60, 720)],\n    'run1_subject2' : [(100, 520)],\n}\n",
            "clip_length": 120,
            "n_neighbors": 8,
        },
        "quality": {
            "ranges": "ranges = {\n    'walk1_subject5' : [(60, 1200)],\n    'run1_subject2' : [(100, 1000)],\n    'dance1_subject2' : [(100, 620)],\n}\n",
            "clip_length": 160,
            "n_neighbors": 10,
        },
    }
    return profiles.get(training_profile, profiles["validate"])


def get_profile_artifact_name(filename: str, training_profile: str, suffix_hint: str = "") -> str:
    if training_profile == "validate":
        return filename
    path = Path(filename)
    suffix = f"_{training_profile}"
    if suffix_hint:
        suffix += f"_{suffix_hint}"
    return f"{path.stem}{suffix}{path.suffix}"


def load_notebook(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_notebook(path: Path, notebook: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(notebook, handle, indent=1, ensure_ascii=False)
        handle.write("\n")


def set_kernel_metadata(notebook: dict, kernel_name: str, display_name: str) -> None:
    if not kernel_name:
        return

    notebook.setdefault("metadata", {})["kernelspec"] = {
        "display_name": display_name or kernel_name,
        "language": "python",
        "name": kernel_name,
    }


def clear_code_outputs(notebook: dict) -> None:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        cell["execution_count"] = None
        cell["outputs"] = []
        cell.get("metadata", {}).pop("execution", None)


def ensure_working_directory(notebook: dict, working_directory: str) -> None:
    if not working_directory:
        return

    marker = "ANIMATIONTECH_NOTEBOOK_CWD"
    cells = notebook.setdefault("cells", [])
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        if marker in "".join(cell.get("source", [])):
            return

    source = (
        "import os\n"
        f"ANIMATIONTECH_NOTEBOOK_CWD = {working_directory!r}\n"
        "os.chdir(ANIMATIONTECH_NOTEBOOK_CWD)\n"
    )
    cwd_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": "animationtech-cwd",
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }
    cells.insert(1 if cells and cells[0].get("cell_type") == "markdown" else 0, cwd_cell)


def patch_gamepad_access(source: str) -> tuple[str, bool]:
    updated = GAMEPAD_AXIS_PATTERN.sub(
        lambda match: f"animationtech_gamepad_axis(gamepad, {match.group(1)})",
        source,
    )
    updated = GAMEPAD_BUTTON_PATTERN.sub(
        lambda match: f"animationtech_gamepad_button(gamepad, {match.group(1)})",
        updated,
    )
    return updated, updated != source


def ensure_gamepad_helper(notebook: dict) -> None:
    cells = notebook.setdefault("cells", [])
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        if "def animationtech_gamepad_axis" in "".join(cell.get("source", [])):
            return

    helper_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": "animationtech-gamepad",
        "metadata": {},
        "outputs": [],
        "source": GAMEPAD_HELPER_SOURCE.splitlines(keepends=True),
    }
    cells.insert(1 if cells and cells[0].get("cell_type") == "markdown" else 0, helper_cell)


NEAR_OPTIMAL_FINAL_INTERACT_SOURCE = """controller_position = np.array([0,0,0], dtype=np.float32)
animationtech_last_frame = -1


def animationtech_reset_near_optimal_player():
    global player, controller_position, animationtech_last_frame
    player = Player()
    player.set_next_clip(0)
    controller_position = np.array([0,0,0], dtype=np.float32)
    animationtech_last_frame = -1


def animationtech_controller_orient():
    controller_orient = np.array([1,0,0,0], dtype=np.float32)
    posx = gamepad.axes[0].value
    posz = -gamepad.axes[1].value
    if np.abs(posx) > 0.001 or np.abs(posz) > 0.001:
        angle = np.atan2(posz, posx)
        controller_orient[0] = np.cos(angle/2)
        controller_orient[2] = np.sin(angle/2)
    return controller_orient


def animationtech_advance_near_optimal_frame(controller_orient):
    global debug_struct, controller_position, player

    if player.next_clip is None and clips_timings[player.current_clip.clip_id, 1] <= player.current_clip.frame:
        f = clips_timings[player.current_clip.clip_id, 1]

        q = lab.utils.quat_mul(lab.utils.quat_inv(controller_orient), player.current_clip.quaternions[f, 0, :])
        theta =  np.atan2(
            2 * q[0] * q[2],
            1.0 - (2 * q[2] * q[2])
        )

        v = lab.utils.quat_mul_vec(controller_orient, np.array([1,0,0], dtype=np.float32))
        x = np.dot(v, player.current_clip.positions[f, 0, :] - controller_position) * 0.01

        next_clip_id, _ = optimal_policy(
            coefficients_forward_0,
            0.95,
            player.current_clip.clip_id,
            x,
            theta,
            physic_factor=.99, direction_factor=1.,
        )
        player.set_next_clip(next_clip_id)

    player.tick()

    v = lab.utils.quat_mul_vec(controller_orient, np.array([0,0,1], dtype=np.float32))
    dist = np.dot(v, player.positions[0] - controller_position)
    controller_position += v * dist
    controller_position = (controller_position*.90 + player.positions[0]*.10)


animationtech_reset_near_optimal_player()


def render(frame, draw_debug=False):
    global debug_struct, controller_position, player, animationtech_last_frame

    target_frame = max(0, min(int(frame), MAX_STEP_LEN - 1))
    controller_orient = animationtech_controller_orient()

    if target_frame < animationtech_last_frame:
        animationtech_reset_near_optimal_player()

    while animationtech_last_frame < target_frame:
        animationtech_advance_near_optimal_frame(controller_orient)
        animationtech_last_frame += 1

    q = player.quaternions
    p = player.positions

    a = lab.utils.quat_to_mat(q, p)
    viewer.set_shadow_poi(p[0])

    viewer.begin_shadow()
    viewer.draw(character, a)
    viewer.end_shadow()

    viewer.begin_display()
    viewer.draw_ground()
    viewer.draw(character, a)
    d = lab.utils.quat_to_mat(controller_orient, p[0])
    viewer.draw(direction, d)

    viewer.end_display()

    viewer.disable(depth_test=True)

    if draw_debug:
        a = lab.utils.quat_to_mat(player.current_clip.quaternions[player.current_clip.frame], player.current_clip.positions[player.current_clip.frame])
        viewer.draw_lines(character.world_skeleton_lines(a), np.array([1,0,0], dtype=np.float32))
        viewer.draw_axis(character.world_skeleton_xforms(a))
        if player.next_clip is not None:
            f = max(player.next_clip.frame, 0)
            a = lab.utils.quat_to_mat(player.next_clip.quaternions[f], player.next_clip.positions[f])
            viewer.draw_lines(character.world_skeleton_lines(a), np.array([0,1,0], dtype=np.float32))

    viewer.execute_commands()


interact(
    render,
    frame=lab.Timeline(max=MAX_STEP_LEN-1)
)
viewer
"""


def transform_near_optimal_source(source: str) -> str:
    if (
        "controller_position = np.array([0,0,0], dtype=np.float32)" in source
        and "def render(frame, draw_debug=False):" in source
        and "optimal_policy(" in source
    ):
        return NEAR_OPTIMAL_FINAL_INTERACT_SOURCE
    return source


def transform_motion_matching_source(source: str) -> str:
    if (
        "def render(frame, max_speed=4." not in source
        or "player.set_next_frame(best_frame+1, inertialize)" not in source
        or "features_normalized[player.frame, :].copy()" not in source
    ):
        return source

    updated = source.replace(
        "def render(frame, max_speed=4., halflife=.5, halflife_rot=.4, code_vs_anim=0., fast_stop=False, inertialize=False):",
        "def render(frame, max_speed=4., halflife=.5, halflife_rot=.4, code_vs_anim=0., fast_stop=False, inertialize=True, use_gamepad=False, move_x=1.0, move_z=0.0, turn_x=0.0, turn_z=0.0):",
    )
    updated = updated.replace(
        "    posx = gamepad.axes[0].value \n    posz = -gamepad.axes[1].value \n",
        "    if use_gamepad:\n        posx = animationtech_gamepad_axis(gamepad, 0)\n        posz = -animationtech_gamepad_axis(gamepad, 1)\n    else:\n        posx = move_x\n        posz = move_z\n",
    )
    updated = updated.replace(
        "    posx = gamepad.axes[2].value \n    posz = -gamepad.axes[3].value \n",
        "    if use_gamepad:\n        posx = animationtech_gamepad_axis(gamepad, 2)\n        posz = -animationtech_gamepad_axis(gamepad, 3)\n    else:\n        posx = turn_x\n        posz = turn_z\n",
    )
    updated = updated.replace(
        "interact(\n    render, \n    frame=lab.Timeline(max=100),\n)",
        "interact(\n    render,\n    frame=lab.Timeline(max=100),\n    max_speed=widgets.FloatSlider(value=4.0, min=0.0, max=8.0, step=0.1),\n    halflife=widgets.FloatSlider(value=0.5, min=0.05, max=1.5, step=0.05),\n    halflife_rot=widgets.FloatSlider(value=0.4, min=0.05, max=1.5, step=0.05),\n    code_vs_anim=widgets.FloatSlider(value=0.0, min=0.0, max=1.0, step=0.05),\n    fast_stop=widgets.Checkbox(value=False),\n    inertialize=widgets.Checkbox(value=True),\n    use_gamepad=widgets.Checkbox(value=False),\n    move_x=widgets.FloatSlider(value=1.0, min=-1.0, max=1.0, step=0.05),\n    move_z=widgets.FloatSlider(value=0.0, min=-1.0, max=1.0, step=0.05),\n    turn_x=widgets.FloatSlider(value=0.0, min=-1.0, max=1.0, step=0.05),\n    turn_z=widgets.FloatSlider(value=0.0, min=-1.0, max=1.0, step=0.05),\n)",
    )
    return updated


def transform_verbs_and_adverbs_source(source: str) -> str:
    if "def test_value(value):" not in source or "# showing picking the right points" not in source:
        return source
    return VERBS_AND_ADVERBS_INTERPOLATE_SOURCE


def transform_source(slug: str, source: str, enable_precompute: bool, training_profile: str, torch_device: str) -> str:
    if slug == NEAR_OPTIMAL_SLUG:
        return transform_near_optimal_source(source)

    if slug == MOTION_MATCHING_SLUG:
        return transform_motion_matching_source(source)

    if slug == VERBS_AND_ADVERBS_SLUG:
        return transform_verbs_and_adverbs_source(source)

    if slug == MOTION_FIELDS_SLUG:
        settings = get_motion_fields_settings(training_profile, torch_device)
        artifact_name = get_profile_artifact_name(
            "motion_fields_precomputed_all_states_tables.dat",
            training_profile,
            "gpu" if torch_device.startswith("cuda") else "cpu",
        )
        updated = source
        updated = updated.replace(
            "import torch\n",
            "import os\nimport torch\nTORCH_DEVICE_NAME = os.environ.get('ANIMATIONTECH_TORCH_DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')\nTORCH_DEVICE = torch.device(TORCH_DEVICE_NAME)\n",
        )
        updated = updated.replace("motion_fields_precomputed_all_states_tables.dat", artifact_name)
        updated = updated.replace("dtype=np.bool)\n", "dtype=np.bool_)\n")
        updated = updated.replace(
            "reducer = UMAP(n_components=3, metric='euclidean', n_neighbors = 80)",
            f"reducer = UMAP(n_components=3, metric='euclidean', n_neighbors={settings['umap_neighbors']}, random_state=42)",
        )
        for old, new in settings["state_ranges"].items():
            updated = updated.replace(old, new)
        updated = updated.replace("K_NEIGHBORS = 15\n", f"K_NEIGHBORS = {settings['k_neighbors']}\n")
        updated = updated.replace("theta_count = 17\n", f"theta_count = {settings['theta_count']}\n")
        updated = updated.replace("EPOCH = 300\n", f"EPOCH = {settings['epoch']}\n")
        updated = updated.replace(".to('cuda')", ".to(TORCH_DEVICE)")
        updated = updated.replace('device=\'cuda\'', "device=TORCH_DEVICE")
        if enable_precompute:
            updated = updated.replace("#_build_precomputed_tables()", "_build_precomputed_tables()")
        if "interact(" in updated and "viewer" in updated:
            if "def render(frame, ratio=.1, select=0, on_spot=False, plot_map=False):" in updated:
                return updated
            return "print('AnimationTech automated run: skipped interactive UI cell.')\n"
        return updated

    if slug == REALTIME_PLANNING_SLUG:
        settings = get_realtime_planning_settings(training_profile)
        updated = source.replace("%%time\n", "")
        updated = updated.replace(
            "from sklearn.ensemble import ExtraTreesRegressor\n",
            "import os\nfrom sklearn.dummy import DummyRegressor\nfrom sklearn.ensemble import ExtraTreesRegressor\nANIMATIONTECH_MAX_WORKERS = int(os.environ.get('ANIMATIONTECH_MAX_WORKERS', '0') or '0')\nANIMATIONTECH_TREE_N_JOBS = int(os.environ.get('ANIMATIONTECH_TREE_N_JOBS', '1') or '1')\n",
            1,
        )
        updated = updated.replace(
            "from multiprocessing import Pool\n",
            "import os\nfrom multiprocessing import Pool\nANIMATIONTECH_MAX_WORKERS = int(os.environ.get('ANIMATIONTECH_MAX_WORKERS', '0') or '0')\nANIMATIONTECH_TREE_N_JOBS = int(os.environ.get('ANIMATIONTECH_TREE_N_JOBS', '1') or '1')\n",
        )
        replacements = [
            (
                "# with progress_output:\n#     physics_costs, delta_theta, delta_x, delta_z = pre_compute_transitions_costs(motion_clips, 'realtime_planning_animations_costs.dat')",
                "physics_costs, delta_theta, delta_x, delta_z = pre_compute_transitions_costs(motion_clips, 'realtime_planning_animations_costs.dat')",
            ),
            (
                "# with progress_output:\n#     value_functions_precompute, scores = train_optimal_policy()",
                "value_functions_precompute, scores = train_optimal_policy()",
            ),
            (
                "# with progress_output:\n#     physics_costs, delta_theta, delta_x, delta_z = pre_compute_transitions_costs(motion_groups, 'realtime_planning_animations_group_costs.dat')",
                "physics_costs, delta_theta, delta_x, delta_z = pre_compute_transitions_costs(motion_groups, 'realtime_planning_animations_group_costs.dat')",
            ),
        ]
        for old, new in replacements:
            updated = updated.replace(old, new)
        updated = updated.replace(
            "    value_functions_precompute, scores = train_optimal_policy()",
            "    value_functions_precompute, scores = train_optimal_policy()\n    globals()['value_functions_precompute'] = value_functions_precompute\n    globals()['scores'] = scores",
        )
        updated = updated.replace(
            "    value_functions_precompute, scores = pickle.load(f)",
            "    value_functions_precompute, scores = pickle.load(f)\n    globals()['value_functions_precompute'] = value_functions_precompute\n    globals()['scores'] = scores",
        )
        updated = updated.replace(
            "model = ExtraTreesRegressor(n_estimators=50, random_state=None, n_jobs=-1)",
            "model = ExtraTreesRegressor(n_estimators=50, random_state=None, n_jobs=ANIMATIONTECH_TREE_N_JOBS)",
        )
        updated = updated.replace(
            "                X_train, y_train = X[i, :count[i]], y[i, :count[i]]\n                model = ExtraTreesRegressor(n_estimators=50, random_state=None, n_jobs=ANIMATIONTECH_TREE_N_JOBS)\n                model.fit(X_train.reshape(-1, 1), y_train)\n                value_functions.append(model)",
            "                X_train, y_train = X[i, :count[i]], y[i, :count[i]]\n                if count[i] == 0:\n                    model = DummyRegressor(strategy='constant', constant=0.0)\n                    model.fit(np.zeros((1, 1)), np.zeros(1))\n                else:\n                    model = ExtraTreesRegressor(n_estimators=50, random_state=None, n_jobs=ANIMATIONTECH_TREE_N_JOBS)\n                    model.fit(X_train.reshape(-1, 1), y_train)\n                value_functions.append(model)",
        )
        updated = updated.replace(
            "                X_train, y_train = X[i, :count[i]], y[i, :count[i]]\n                refit_tree(value_functions[i], X_train.reshape(-1, 1), y_train)",
            "                X_train, y_train = X[i, :count[i]], y[i, :count[i]]\n                if count[i] > 0:\n                    refit_tree(value_functions[i], X_train.reshape(-1, 1), y_train)",
        )
        updated = updated.replace("with Pool() as pool:", "with Pool(processes=ANIMATIONTECH_MAX_WORKERS if ANIMATIONTECH_MAX_WORKERS > 0 else None) as pool:")
        for old, new in settings["replacements"]:
            updated = updated.replace(old, new)
        realtime_artifacts = [
            "realtime_planning_animations_costs.dat",
            "realtime_planning_orientation_value_functions.dat",
            "realtime_planning_reach_position_value_functions.dat",
            "realtime_planning_animations_group_costs.dat",
            "realtime_planning_reach_position_group_value_functions.dat",
        ]
        for artifact_name in realtime_artifacts:
            updated = updated.replace(artifact_name, get_profile_artifact_name(artifact_name, training_profile))
        if "interact(" in updated and "viewer" in updated:
            if "player = Player(motion_clips)" in updated or "player = Player(motion_groups)" in updated:
                return updated
            return "print('AnimationTech automated run: skipped interactive UI cell.')\n"
        return updated

    if slug == KNOWING_FOOT_DOWN_SLUG:
        settings = get_foot_down_settings(training_profile)
        updated = source.replace(
            "ranges = {\n    'walk1_subject5' : [(60, 7060)],\n    'walk3_subject1' : [(100, 900), (1300, 2500), (4400, 5200), (7150,7350)], \n    'run1_subject2' : [(100, 5100) ], \n    'dance1_subject2' : [(100, 1900) ], \n    'aiming2_subject2' : [(100, 4100), (4900, 6100), (8300,8900)], \n}\n",
            settings["ranges"],
        )
        updated = updated.replace("clip_length = 200\n", f"clip_length = {settings['clip_length']}\n")
        updated = updated.replace("n_neighbors = 10\n", f"n_neighbors = {settings['n_neighbors']}\n")
        updated = updated.replace(
            "repeat(current_feature_vector.shape[1]/3, axis=0)",
            "repeat(int(current_feature_vector.shape[1] / 3), axis=0)",
        )
        if "# get the first range, to see if it works" in updated or "# get the worst labeling" in updated:
            return "print('AnimationTech automated run: skipped expensive nearest-neighbor demo cell.')\n"
        if "interact(" in updated or "display(buttons)" in updated or "display(canvas)" in updated or "display(viewer)" in updated:
            if "canvas = Canvas(width=1280, height=160)" in updated and "def render(frame):" in updated:
                return updated
            return "print('AnimationTech automated run: skipped interactive UI cell.')\n"
        return updated

    return source


def prepare_notebook(
    slug: str,
    notebook: dict,
    enable_precompute: bool,
    training_profile: str,
    torch_device: str,
    kernel_name: str = "",
    display_name: str = "",
    clear_outputs: bool = False,
    working_directory: str = "",
) -> dict:
    needs_gamepad_helper = False
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        updated = transform_source(slug, source, enable_precompute, training_profile, torch_device)
        updated, patched_gamepad = patch_gamepad_access(updated)
        needs_gamepad_helper = needs_gamepad_helper or patched_gamepad
        if updated != source:
            cell["source"] = updated.splitlines(keepends=True)

    ensure_working_directory(notebook, working_directory)
    if needs_gamepad_helper:
        ensure_gamepad_helper(notebook)
    set_kernel_metadata(notebook, kernel_name, display_name)
    if clear_outputs:
        clear_code_outputs(notebook)
    return notebook


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an execution copy of a notebook.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--input", required=True, dest="input_path")
    parser.add_argument("--output", required=True, dest="output_path")
    parser.add_argument("--enable-precompute", action="store_true")
    parser.add_argument("--training-profile", choices=["validate", "adaptive", "quality"], default="validate")
    parser.add_argument("--torch-device", default="cpu")
    parser.add_argument("--kernel-name", default="")
    parser.add_argument("--display-name", default="")
    parser.add_argument("--clear-outputs", action="store_true")
    parser.add_argument("--working-directory", default="")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    notebook = load_notebook(input_path)
    prepared = prepare_notebook(
        args.slug,
        notebook,
        args.enable_precompute,
        args.training_profile,
        args.torch_device,
        args.kernel_name,
        args.display_name,
        args.clear_outputs,
        args.working_directory,
    )
    dump_notebook(output_path, prepared)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
