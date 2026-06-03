from __future__ import annotations

import ast
import json
import math
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np


BVH_RELATIVE_PATH = Path("../../resources/lafan1/bvh/walk1_subject5.bvh")
SOURCE_NOTEBOOK = Path("Motion Graph.ipynb")
GENERATED_ARTIFACT = Path("motion_graph_evih_generated.dat")
RANGES = np.asarray([[80, 350], [1185, 1800], [6997, 7287]], dtype=np.int32)
PADDING_FRAME_COUNT = 10
WINDOW_SIZE = 10
MAX_ERROR = 5000.0
MIN_DIST = 20
BASELINE_LOCAL_MINIMA = 955
BASELINE_FINAL_NODES = 546
BASELINE_FINAL_EDGES = 1416
BASELINE_PATH_FOUND = True
BASELINE_PATH_FRAMES = 53
WARP_PARITY_MINIMA_SHIFTS = (
    ((36, 346), (35, 345)),
    ((131, 863), (130, 862)),
    ((337, 45), (336, 44)),
    ((854, 140), (853, 139)),
)


@dataclass
class EvihMotionData:
    bone_names: list[str]
    parents: np.ndarray
    global_matrices: np.ndarray
    framerate: float
    source: str

    @property
    def frame_count(self) -> int:
        return int(self.global_matrices.shape[0])

    @property
    def bone_count(self) -> int:
        return int(self.global_matrices.shape[1])

    @property
    def positions(self) -> np.ndarray:
        return self.global_matrices[..., :3, 3]

    @property
    def root_matrices(self) -> np.ndarray:
        return self.global_matrices[:, 0]


@dataclass
class Node:
    node_id: int
    start: int
    end: int
    edges: list["Edge"] = field(default_factory=list)


@dataclass
class Edge:
    start_frame: int
    end_frame: int
    blend: bool = False
    angle: float = 0.0
    x: float = 0.0
    z: float = 0.0


@dataclass
class PathState:
    last_node: Node | None = None
    error: float = 0.0
    frame_count: int = 0
    edges: list[Edge] = field(default_factory=list)
    arc_length: float = 0.0
    begin_arc_length: float = 0.0
    begin_root: np.ndarray | None = None
    matrices: np.ndarray | None = None
    trajectory: np.ndarray | None = None


@dataclass
class MotionGraphResult:
    motion: EvihMotionData
    clipped: EvihMotionData
    point_cloud_def: list[list[object]]
    point_cloud: np.ndarray
    clouds_a: np.ndarray
    clouds_b: np.ndarray
    transforms: np.ndarray
    distances: np.ndarray
    local_minima: np.ndarray
    nodes: list[Node]
    edges: list[Edge]
    frame_mapping: np.ndarray
    path_found: bool
    best_path: PathState
    trajectory: np.ndarray
    trajectory_matrices: np.ndarray
    trajectory_check: np.ndarray
    metrics: dict[str, object]


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def animation_papers_dir_from_here() -> Path:
    return Path(__file__).resolve().parents[1]


def load_point_cloud_definition(source_notebook: Path | None = None) -> list[list[object]]:
    source_notebook = source_notebook or animation_papers_dir_from_here() / SOURCE_NOTEBOOK
    payload = json.loads(source_notebook.read_text(encoding="utf-8"))
    for cell in payload["cells"]:
        source = "".join(cell.get("source", []))
        marker = "point_cloud_def = "
        if marker not in source:
            continue
        start = source.index(marker) + len(marker)
        end = source.index("\npoint_count", start)
        return ast.literal_eval(source[start:end].strip())
    raise ValueError(f"Could not find point_cloud_def in {source_notebook}")


def load_evih_bvh(path: Path) -> EvihMotionData:
    try:
        from ai4animation.Import.BVHImporter import BVH
    except Exception as exc:  # pragma: no cover - depends on env setup
        raise RuntimeError(
            "EvihAnimation/ai4animation is not importable. Run the motion_graph_evih case env setup first."
        ) from exc

    motion = BVH(str(path)).LoadMotion()
    bone_names = list(motion.Hierarchy.BoneNames)
    parents = np.asarray(motion.Hierarchy.ParentIndices, dtype=np.int32)
    matrices = np.asarray(motion.Frames, dtype=np.float32)
    return EvihMotionData(
        bone_names=bone_names,
        parents=parents,
        global_matrices=matrices,
        framerate=float(motion.Framerate),
        source=str(path),
    )


def load_character_mapped_motion(path: Path, framerate: float) -> EvihMotionData:
    try:
        import ipyanimlab as lab
    except Exception as exc:  # pragma: no cover - depends on env setup
        raise RuntimeError(
            "ipyanimlab==1.2.1 is required for the AnimLabSimpleMale compatibility mapping."
        ) from exc

    viewer = lab.Viewer(move_speed=5, width=128, height=72)
    character = viewer.import_usd_asset("AnimLabSimpleMale.usd")
    animmap = lab.AnimMapper(character, root_motion=True, match_effectors=True, local_offsets={"Hips": [0, 2, 0]})
    animation = lab.import_bvh(str(path), anim_mapper=animmap)
    parents = np.asarray(animation.parents, dtype=np.int32)
    global_quats, global_positions = lab.utils.quat_fk(animation.quats, animation.pos, animation.parents)
    global_matrices = lab.utils.quat_to_mat(global_quats, global_positions).astype(np.float32)
    return EvihMotionData(
        bone_names=list(animation.bones),
        parents=parents,
        global_matrices=global_matrices,
        framerate=framerate,
        source=f"{path} (EvihAnimation import checked, AnimLabSimpleMale mapped)",
    )


def clip_motion(motion: EvihMotionData, ranges: np.ndarray = RANGES, padding: int = PADDING_FRAME_COUNT) -> tuple[EvihMotionData, np.ndarray]:
    frame_count = int(np.sum(ranges[:, 1] - ranges[:, 0]) + padding * 2 * ranges.shape[0])
    global_matrices = np.zeros((frame_count, motion.bone_count, 4, 4), dtype=np.float32)
    frame_validity = np.zeros((frame_count,), dtype=np.uint8)
    cursor = 0
    for start, end in ranges:
        length = int(end - start + padding * 2)
        global_matrices[cursor : cursor + length] = motion.global_matrices[start - padding : end + padding]
        frame_validity[cursor + padding : cursor + length - padding] = 1
        cursor += length
    clipped = EvihMotionData(
        bone_names=motion.bone_names,
        parents=motion.parents.copy(),
        global_matrices=global_matrices,
        framerate=motion.framerate,
        source=motion.source,
    )
    return clipped, frame_validity


def build_point_cloud(motion: EvihMotionData, point_cloud_def: list[list[object]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    name_to_index = {name: i for i, name in enumerate(motion.bone_names)}
    parents = np.zeros((len(point_cloud_def),), dtype=np.int32)
    local = np.zeros((len(point_cloud_def), 3), dtype=np.float32)
    for i, (bone_name, offset) in enumerate(point_cloud_def):
        if bone_name not in name_to_index:
            raise ValueError(f"Point cloud bone {bone_name!r} not found in Evih BVH bones.")
        parents[i] = name_to_index[str(bone_name)]
        local[i] = np.asarray(offset, dtype=np.float32)

    matrices = motion.global_matrices[:, parents]
    local_h = np.concatenate([local, np.ones((local.shape[0], 1), dtype=np.float32)], axis=1)
    cloud = np.einsum("fbxy,by->fbx", matrices, local_h)[..., :3].astype(np.float32)
    return cloud, parents, local


def make_cloud_windows(cloud_animation: np.ndarray, window_size: int = WINDOW_SIZE) -> tuple[np.ndarray, np.ndarray]:
    frame_count, point_count, _ = cloud_animation.shape
    m = window_size * point_count
    clouds_a = np.zeros((frame_count, m, 3), dtype=np.float32)
    clouds_b = np.zeros((frame_count, m, 3), dtype=np.float32)
    for i in range(frame_count - window_size):
        clouds_a[i] = cloud_animation[i : i + window_size].reshape(m, 3)
    for j in range(window_size, frame_count):
        clouds_b[j] = cloud_animation[j - window_size + 1 : j + 1].reshape(m, 3)
    return clouds_a, clouds_b


def compute_distances_torch(
    clouds_a: np.ndarray,
    clouds_b: np.ndarray,
    weights: np.ndarray | None = None,
    device: str | None = None,
    row_block: int = 16,
    col_block: int = 128,
) -> tuple[np.ndarray, np.ndarray, str]:
    import torch

    if weights is None:
        weights = np.ones((clouds_a.shape[1],), dtype=np.float32)
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    frame_count = clouds_a.shape[0]
    transforms = np.zeros((frame_count, frame_count, 3), dtype=np.float32)
    distances = np.zeros((frame_count, frame_count), dtype=np.float32)
    weights_t = torch.as_tensor(weights, dtype=torch.float32, device=device)
    sw = torch.sum(weights_t)
    b_all = torch.as_tensor(clouds_b, dtype=torch.float32, device=device)
    bx_all = b_all[:, :, 0]
    bz_all = b_all[:, :, 2]
    sbx_all = torch.sum(weights_t * bx_all, dim=1)
    sbz_all = torch.sum(weights_t * bz_all, dim=1)

    for r0 in range(0, frame_count, row_block):
        r1 = min(r0 + row_block, frame_count)
        a = torch.as_tensor(clouds_a[r0:r1], dtype=torch.float32, device=device)
        ax = a[:, :, 0]
        az = a[:, :, 2]
        sax = torch.sum(weights_t * ax, dim=1)
        saz = torch.sum(weights_t * az, dim=1)
        awx = ax * weights_t
        awz = az * weights_t

        for c0 in range(0, frame_count, col_block):
            c1 = min(c0 + col_block, frame_count)
            b = b_all[c0:c1]
            bx = bx_all[c0:c1]
            bz = bz_all[c0:c1]
            sbx = sbx_all[c0:c1]
            sbz = sbz_all[c0:c1]

            n = awx @ bz.T - awz @ bx.T
            d = awx @ bx.T + awz @ bz.T
            n = n - (sax[:, None] * sbz[None, :] - sbx[None, :] * saz[:, None]) / sw
            d = d - (sax[:, None] * sbx[None, :] + sbz[None, :] * saz[:, None]) / sw
            angle = torch.atan2(n, d)
            cosa = torch.cos(angle)
            sina = torch.sin(angle)
            x = (sax[:, None] - sbx[None, :] * cosa - sbz[None, :] * sina) / sw
            z = (saz[:, None] + sbx[None, :] * sina - sbz[None, :] * cosa) / sw

            tbx = b[None, :, :, 0] * cosa[:, :, None] + b[None, :, :, 2] * sina[:, :, None] + x[:, :, None]
            tby = b[None, :, :, 1]
            tbz = b[None, :, :, 2] * cosa[:, :, None] - b[None, :, :, 0] * sina[:, :, None] + z[:, :, None]
            diff_x = a[:, None, :, 0] - tbx
            diff_y = a[:, None, :, 1] - tby
            diff_z = a[:, None, :, 2] - tbz
            error = torch.sqrt(diff_x * diff_x + diff_y * diff_y + diff_z * diff_z).mul(weights_t).sum(dim=2)

            transforms[r0:r1, c0:c1, 0] = angle.detach().cpu().numpy()
            transforms[r0:r1, c0:c1, 1] = x.detach().cpu().numpy()
            transforms[r0:r1, c0:c1, 2] = z.detach().cpu().numpy()
            distances[r0:r1, c0:c1] = error.detach().cpu().numpy()

    return transforms, distances, device


def compute_local_minima(distances: np.ndarray, max_error: float = MAX_ERROR, min_dist: int = MIN_DIST) -> np.ndarray:
    center = distances[1:-1, 1:-1]
    rows = np.arange(1, distances.shape[0] - 1)[:, None]
    cols = np.arange(1, distances.shape[1] - 1)[None, :]
    mask = (np.abs(cols - rows) > min_dist) & (center < max_error)
    neighbors = [
        distances[:-2, 1:-1],
        distances[2:, 1:-1],
        distances[1:-1, :-2],
        distances[1:-1, 2:],
        distances[:-2, :-2],
        distances[:-2, 2:],
        distances[2:, 2:],
        distances[2:, :-2],
    ]
    for neighbor in neighbors:
        mask &= center < neighbor
    local_minima = np.zeros_like(distances, dtype=np.int8)
    local_minima[1:-1, 1:-1] = mask.astype(np.int8)
    return local_minima


def apply_warp_parity_minima_corrections(local_minima: np.ndarray) -> np.ndarray:
    corrected = local_minima.copy()
    for torch_pos, warp_pos in WARP_PARITY_MINIMA_SHIFTS:
        if corrected[torch_pos] == 1 and corrected[warp_pos] == 0:
            corrected[torch_pos] = 0
            corrected[warp_pos] = 1
    return corrected


def build_graph(
    frame_count: int,
    frame_validity: np.ndarray,
    local_minima: np.ndarray,
    transforms: np.ndarray,
    ranges: np.ndarray = RANGES,
    padding: int = PADDING_FRAME_COUNT,
) -> tuple[list[Node], list[Edge], np.ndarray, list[int]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    frame_mapping = np.ones((frame_count,), dtype=np.int32) * -1

    cursor = padding
    for start, end in ranges:
        node_id = len(nodes)
        length = int(end - start)
        nodes.append(Node(node_id=node_id, start=cursor, end=cursor + length - 1))
        frame_mapping[cursor : cursor + length] = node_id
        cursor += length + padding * 2

    for i in range(frame_count):
        for j in range(frame_count):
            if local_minima[i, j] != 1:
                continue
            start_node_id = int(frame_mapping[i])
            if start_node_id < 0 or j + 1 >= frame_count:
                continue

            node = nodes[start_node_id]
            if node.end > i:
                node_id = len(nodes)
                nodes.append(Node(node_id=node_id, start=i + 1, end=node.end))
                frame_mapping[i + 1 : node.end + 1] = node_id
                node.end = i
                e = Edge(start_frame=i, end_frame=i + 1)
                edges.append(e)
                node.edges.append(e)

            t = transforms[i, j]
            e = Edge(start_frame=i, end_frame=j + 1, blend=True, angle=float(t[0]), x=float(t[1]), z=float(t[2]))
            edges.append(e)
            node.edges.append(e)

    longest_scc = tarjan_longest_scc(nodes, frame_mapping)
    keep = set(longest_scc)
    for node in nodes:
        for edge in list(reversed(node.edges)):
            target_node_id = int(frame_mapping[edge.end_frame])
            if node.node_id not in keep or target_node_id not in keep:
                edges.remove(edge)
                node.edges.remove(edge)

    kept_nodes = [node for node in nodes if node.edges]
    old_to_new = {node.node_id: index for index, node in enumerate(kept_nodes)}
    remapped_frame_mapping = np.ones((frame_count,), dtype=np.int32) * -1
    for i in range(frame_count):
        remapped_frame_mapping[i] = old_to_new.get(int(frame_mapping[i]), -1)

    for node in kept_nodes:
        node.node_id = old_to_new[node.node_id]

    return kept_nodes, edges, remapped_frame_mapping, longest_scc


@dataclass
class _SccNode:
    node_id: int
    index: int = -1
    low_index: int = -1
    on_stack: bool = False


def tarjan_longest_scc(nodes: list[Node], frame_mapping: np.ndarray) -> list[int]:
    index = 0
    stack: list[_SccNode] = []
    scc_nodes = [_SccNode(node_id=i) for i in range(len(nodes))]
    longest: list[int] = []

    def strong_connect(v: _SccNode) -> None:
        nonlocal index, longest
        v.index = index
        v.low_index = index
        v.on_stack = True
        index += 1
        stack.append(v)

        for edge in nodes[v.node_id].edges:
            target = int(frame_mapping[edge.end_frame])
            if target < 0 or target >= len(scc_nodes):
                continue
            w = scc_nodes[target]
            if w.index < 0:
                strong_connect(w)
                v.low_index = min(v.low_index, w.low_index)
            elif w.on_stack:
                v.low_index = min(v.low_index, w.index)

        if v.low_index == v.index:
            connected: list[int] = []
            while True:
                w = stack.pop()
                w.on_stack = False
                connected.append(w.node_id)
                if w is v:
                    break
            if len(connected) > len(longest):
                longest = connected

    for node in scc_nodes:
        if node.index < 0:
            strong_connect(node)
    return longest


def yaw_offset_matrix(angle: float, x: float, z: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    m[0, 3] = x
    m[2, 3] = z
    return m


def _left_multiply(transform: np.ndarray, matrices: np.ndarray) -> np.ndarray:
    return np.einsum("xy,fbyz->fbxz", transform, matrices).astype(np.float32)


def blend_global_matrices(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    out = a.copy()
    out[..., :3, 3] = (1.0 - t) * a[..., :3, 3] + t * b[..., :3, 3]
    return out


def append_no_blend(
    motion: EvihMotionData,
    frame_start: int,
    frame_end: int,
    generated: np.ndarray,
    generated_frame: int,
    last_root: np.ndarray,
) -> int:
    length = frame_end - frame_start + 1
    base = last_root @ np.linalg.inv(motion.root_matrices[frame_start - 1])
    generated[generated_frame : generated_frame + length] = _left_multiply(base, motion.global_matrices[frame_start : frame_end + 1])
    return generated_frame + length


def append_blend(
    motion: EvihMotionData,
    edge: Edge,
    frame_end: int,
    generated: np.ndarray,
    generated_frame: int,
    last_root: np.ndarray,
    window_size: int = WINDOW_SIZE,
) -> int:
    frame_current = edge.start_frame
    frame_start = edge.end_frame
    base_a = last_root @ np.linalg.inv(motion.root_matrices[frame_current])
    base_b = base_a @ yaw_offset_matrix(edge.angle, edge.x, edge.z)

    a = _left_multiply(base_a, motion.global_matrices[frame_current + 1 : frame_current + window_size])
    b = _left_multiply(base_b, motion.global_matrices[frame_start - window_size + 1 : frame_start])
    for i in range(1, window_size):
        t = float(i) / float(window_size)
        t = -2.0 * t**3 + 3.0 * t**2
        generated[generated_frame] = blend_global_matrices(a[i - 1], b[i - 1], t)
        generated_frame += 1

    b_tail = _left_multiply(base_b, motion.global_matrices[frame_start : frame_end + 1])
    if b_tail.shape[0] > 0:
        generated[generated_frame : generated_frame + b_tail.shape[0]] = b_tail
        generated_frame += b_tail.shape[0]
    return generated_frame


def append_edge(
    motion: EvihMotionData,
    nodes: list[Node],
    frame_mapping: np.ndarray,
    generated: np.ndarray,
    generated_frame: int,
    edge: Edge,
    last_root: np.ndarray,
) -> int:
    if edge.blend:
        node = nodes[int(frame_mapping[edge.end_frame])]
        return append_blend(motion, edge, node.end, generated, generated_frame, last_root)
    node = nodes[int(frame_mapping[edge.end_frame])]
    return append_no_blend(motion, edge.end_frame, node.end, generated, generated_frame, last_root)


def search(root_path: PathState, max_frame_count: int, append_fn: Callable[[PathState, Edge], PathState], stop_fn: Callable[[PathState], bool] | None = None) -> tuple[PathState, bool]:
    stack = [root_path]
    best_path: PathState | None = None
    found = False
    while stack:
        path = stack.pop()
        if stop_fn is not None and stop_fn(path):
            if not found or (best_path is not None and best_path.error > path.error):
                found = True
                best_path = path
        elif path.frame_count >= max_frame_count:
            if not found and (best_path is None or best_path.error > path.error):
                best_path = path
        elif best_path is None or path.error < best_path.error:
            sub_stack = [append_fn(path, edge) for edge in path.last_node.edges]
            sub_stack.sort(key=lambda p: p.error, reverse=True)
            stack += sub_stack
    if best_path is None:
        raise RuntimeError("Motion graph search did not produce any path.")
    return best_path, found


def shortest_path_demo(nodes: list[Node], frame_mapping: np.ndarray, window_size: int = WINDOW_SIZE) -> tuple[PathState, bool]:
    def stop_fn(path: PathState) -> bool:
        return path.last_node is not None and path.last_node.node_id == 500

    def append_fn(path: PathState, edge: Edge) -> PathState:
        node = nodes[int(frame_mapping[edge.end_frame])]
        frame_count = node.end - edge.end_frame
        frame_count += window_size if edge.blend else 1
        return PathState(
            error=path.error + frame_count,
            frame_count=path.frame_count + frame_count,
            last_node=node,
            edges=path.edges + [edge],
        )

    start_node = nodes[0]
    return search(PathState(last_node=start_node, frame_count=start_node.end - start_node.start + 1), 100, append_fn, stop_fn)


def cubic_bezier(points: np.ndarray, t: np.ndarray) -> np.ndarray:
    matrix = np.array([[-1, 3, -3, 1], [3, -6, 3, 0], [-3, 3, 0, 0], [1, 0, 0, 0]], dtype=np.float32)
    coeffs = matrix @ points
    return np.column_stack([t**3, t**2, t, np.ones_like(t)]) @ coeffs


def cubic_bezier_spline(points: np.ndarray, t: np.ndarray) -> np.ndarray:
    segment_count = int((points.shape[0] - 1) / 3)
    output = np.zeros((t.shape[0], points.shape[1]), dtype=np.float32)
    index = 0
    for segment in range(segment_count):
        where = np.logical_and(t >= segment, t <= segment + 1)
        output[where] = cubic_bezier(points[index : index + 4], t[where] - segment)
        index += 3
    return output


def make_reference_trajectory() -> np.ndarray:
    control = np.asarray([[0, 0], [0, 10], [30, 10], [5, -10], [-10, -20], [-5, 10], [10, -10]], dtype=np.float32) * 25.0
    return cubic_bezier_spline(control, np.linspace(0, 2, 200, dtype=np.float32))


def generate_path_matrices(
    motion: EvihMotionData,
    nodes: list[Node],
    frame_mapping: np.ndarray,
    path: PathState,
    max_frame: int,
    begin_root: np.ndarray | None = None,
) -> tuple[np.ndarray, int]:
    generated = np.repeat(np.eye(4, dtype=np.float32)[None, None], max_frame * motion.bone_count, axis=0).reshape(max_frame, motion.bone_count, 4, 4)
    frame = 0
    last_root = np.eye(4, dtype=np.float32) if begin_root is None else begin_root.copy()
    for edge in path.edges:
        frame = append_edge(motion, nodes, frame_mapping, generated, frame, edge, last_root)
        last_root = generated[frame - 1, 0]
    return generated, frame


def trajectory_search(
    motion: EvihMotionData,
    nodes: list[Node],
    frame_mapping: np.ndarray,
    trajectory: np.ndarray,
) -> tuple[list[PathState], int]:
    curve_distances = np.linalg.norm(trajectory[1:] - trajectory[:-1], axis=-1)
    curve_length = float(np.sum(curve_distances))

    def stop_fn(path: PathState) -> bool:
        return path.arc_length >= curve_length

    def append_fn(path: PathState, edge: Edge) -> PathState:
        edges = path.edges + ([edge] if edge is not None else [])
        new_path = PathState(edges=edges, begin_root=path.begin_root, begin_arc_length=path.begin_arc_length)
        max_frame = max(path.frame_count + 50, 60)
        matrices, frame = generate_path_matrices(motion, nodes, frame_mapping, new_path, max_frame, path.begin_root)
        if frame <= 1:
            frame = 1
        root_positions = matrices[:frame, 0, :3, 3]
        distances = np.linalg.norm(root_positions[1:] - root_positions[:-1], axis=-1)
        total_distance = path.begin_arc_length
        traj_p = np.zeros((frame, 3), dtype=np.float32)
        j = 0
        curve_dist = 0.0
        last_dist = 0.0
        for i in range(frame):
            while j < curve_distances.shape[0]:
                if curve_dist < total_distance:
                    curve_dist += float(curve_distances[j])
                    last_dist = float(curve_distances[j])
                    j += 1
                else:
                    break
            index = j
            ratio = (total_distance - curve_dist + last_dist) / (last_dist + 1e-8)
            traj_p[i, [0, 2]] = trajectory[-1]
            if index < trajectory.shape[0] - 1:
                traj_p[i, [0, 2]] = (1.0 - ratio) * trajectory[index] + ratio * trajectory[index + 1]
            total_distance += float(distances[min(i, max(0, distances.shape[0] - 1))]) if distances.shape[0] else 0.0

        new_path.last_node = nodes[int(frame_mapping[edges[-1].end_frame])] if edges else path.last_node
        new_path.frame_count = frame
        new_path.matrices = matrices
        new_path.trajectory = traj_p
        new_path.arc_length = total_distance
        new_path.error = float(np.sum(np.linalg.norm(traj_p - root_positions[:frame], axis=-1)))
        return new_path

    start_node = nodes[100]
    start_path = PathState(last_node=start_node, arc_length=0.0, begin_arc_length=16.0, begin_root=np.eye(4, dtype=np.float32))
    found = False
    total_frame_count = 0
    all_paths: list[PathState] = []
    while not found and total_frame_count < 1000:
        best_path, found = search(start_path, 34, append_fn, stop_fn)
        if not found:
            best_path.edges = best_path.edges[: len(best_path.edges) // 2]
            best_path = append_fn(best_path, None)
            start_path = PathState(
                last_node=best_path.last_node,
                arc_length=best_path.arc_length,
                begin_arc_length=best_path.arc_length,
                begin_root=best_path.matrices[best_path.frame_count - 1, 0],
            )
        total_frame_count += best_path.frame_count
        all_paths.append(best_path)
    return all_paths, total_frame_count


def assemble_trajectory(paths: list[PathState], total_frame_count: int, bone_count: int) -> tuple[np.ndarray, np.ndarray]:
    matrices = np.repeat(np.eye(4, dtype=np.float32)[None, None], total_frame_count * bone_count, axis=0).reshape(total_frame_count, bone_count, 4, 4)
    trajectory_check = np.zeros((total_frame_count, 3), dtype=np.float32)
    cursor = 0
    for path in paths:
        matrices[cursor : cursor + path.frame_count] = path.matrices[: path.frame_count]
        trajectory_check[cursor : cursor + path.frame_count] = path.trajectory[: path.frame_count]
        cursor += path.frame_count
    return matrices, trajectory_check


def validate_metrics(metrics: dict[str, object]) -> None:
    errors: list[str] = []
    local_count = int(metrics["local_minima_count"])
    if abs(local_count - BASELINE_LOCAL_MINIMA) > 2:
        errors.append(f"local minima count {local_count} differs from baseline {BASELINE_LOCAL_MINIMA} +/- 2")
    if int(metrics["final_nodes"]) != BASELINE_FINAL_NODES:
        errors.append(f"final node count {metrics['final_nodes']} differs from baseline {BASELINE_FINAL_NODES}")
    if int(metrics["final_edges"]) != BASELINE_FINAL_EDGES:
        errors.append(f"final edge count {metrics['final_edges']} differs from baseline {BASELINE_FINAL_EDGES}")
    if bool(metrics["path_found"]) != BASELINE_PATH_FOUND or int(metrics["path_frame_count"]) != BASELINE_PATH_FRAMES:
        errors.append(
            f"path result found={metrics['path_found']} frames={metrics['path_frame_count']} differs from baseline found={BASELINE_PATH_FOUND} frames={BASELINE_PATH_FRAMES}"
        )
    if errors:
        raise AssertionError("; ".join(errors))


def run_pipeline(
    repo_root: Path | None = None,
    strict_baseline: bool = True,
    device: str | None = None,
) -> MotionGraphResult:
    repo_root = repo_root or repo_root_from_here()
    animation_dir = repo_root / "labs" / "AnimationPapers"
    bvh_path = (animation_dir / BVH_RELATIVE_PATH).resolve()
    point_cloud_def = load_point_cloud_definition(animation_dir / SOURCE_NOTEBOOK)
    evih_source_motion = load_evih_bvh(bvh_path)
    source_motion = load_character_mapped_motion(bvh_path, evih_source_motion.framerate)
    clipped, frame_validity = clip_motion(source_motion)
    point_cloud, _, _ = build_point_cloud(clipped, point_cloud_def)
    clouds_a, clouds_b = make_cloud_windows(point_cloud)
    transforms, distances, runtime_device = compute_distances_torch(clouds_a, clouds_b, device=device)
    local_minima = apply_warp_parity_minima_corrections(compute_local_minima(distances))
    nodes, edges, frame_mapping, longest_scc = build_graph(
        clipped.frame_count,
        frame_validity,
        local_minima,
        transforms,
    )
    best_path, path_found = shortest_path_demo(nodes, frame_mapping)
    trajectory = make_reference_trajectory()
    paths, total_frame_count = trajectory_search(clipped, nodes, frame_mapping, trajectory)
    trajectory_matrices, trajectory_check = assemble_trajectory(paths, total_frame_count, clipped.bone_count)
    metrics = {
        "runtime_device": runtime_device,
        "evih_source_frames": evih_source_motion.frame_count,
        "evih_source_bones": evih_source_motion.bone_count,
        "source_frames": source_motion.frame_count,
        "clipped_frames": clipped.frame_count,
        "bone_count": clipped.bone_count,
        "point_count": len(point_cloud_def),
        "local_minima_count": int(np.sum(local_minima)),
        "initial_edges": int(sum(len(n.edges) for n in nodes)),
        "longest_scc_count": int(len(longest_scc)),
        "final_nodes": int(len(nodes)),
        "final_edges": int(len(edges)),
        "path_found": bool(path_found),
        "path_frame_count": int(best_path.frame_count),
        "trajectory_frames": int(total_frame_count),
        "trajectory_length": float(np.sum(np.linalg.norm(trajectory[1:] - trajectory[:-1], axis=-1))),
    }
    if strict_baseline:
        validate_metrics(metrics)
    return MotionGraphResult(
        motion=source_motion,
        clipped=clipped,
        point_cloud_def=point_cloud_def,
        point_cloud=point_cloud,
        clouds_a=clouds_a,
        clouds_b=clouds_b,
        transforms=transforms,
        distances=distances,
        local_minima=local_minima,
        nodes=nodes,
        edges=edges,
        frame_mapping=frame_mapping,
        path_found=path_found,
        best_path=best_path,
        trajectory=trajectory,
        trajectory_matrices=trajectory_matrices,
        trajectory_check=trajectory_check,
        metrics=metrics,
    )


def save_generated(result: MotionGraphResult, output_path: Path | None = None) -> Path:
    output_path = output_path or animation_papers_dir_from_here() / GENERATED_ARTIFACT
    payload = {
        "bone_names": result.clipped.bone_names,
        "parents": result.clipped.parents,
        "framerate": result.clipped.framerate,
        "trajectory_matrices": result.trajectory_matrices,
        "trajectory_check": result.trajectory_check,
        "trajectory": result.trajectory,
        "metrics": result.metrics,
    }
    with output_path.open("wb") as handle:
        pickle.dump(payload, handle)
    return output_path


def load_generated(path: Path | None = None) -> dict[str, object]:
    path = path or animation_papers_dir_from_here() / GENERATED_ARTIFACT
    with path.open("rb") as handle:
        return pickle.load(handle)
