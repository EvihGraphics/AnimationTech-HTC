# AnimationTech 博客工程归档

`docs/blog` 是面向学习、复盘和后续发布的中文深讲博客区。它覆盖 `tools/cases.yaml` 中受管的 `labs/AnimationPapers` 与 `labs/Theory` 案例，用工程 Markdown 解释每个案例的模块结构、数据流、关键代码和执行结果意义。

当前发布状态：

- 案例覆盖：19 个受管案例全部有独立子工程、`assets/` 目录、模块图、模块拆解和运行方式。
- 媒体覆盖：19 个案例全部迁移到 v5 媒体结构，包含 142 张结果 PNG、142 张学习卡 PNG、30 个 GIF 预览、30 个 MP4/H.264、30 个 WebM/VP9 和 19 段 walkthrough WebM。
- 深写状态：12 个代表案例已经深写完成，剩余 7 个案例保持媒体完整的发布基底，后续可继续扩写正文密度。
- 媒体质量：正文重点图和动画必须是算法输出本身；禁止使用浏览器滚动截图、整页 cell 截图、代码学习卡裁剪图或静态图平移缩放生成的假动画。

## 学习入口

AnimationPapers 的交互学习优先使用稳定 JupyterLab 入口。它会检查环境、kernel 和 study notebook，打开 `.reports/study/AnimationPapers` 中的浏览器安全副本。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证和调试使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>
```

Theory 案例通常用 `run_case.ps1 <slug>` 验证。需要交互查看时，从对应 `.envs/<case>/python.exe -m jupyter lab` 启动，并切换到对应 `animationtech-*` kernel。

## 推荐学习路线

```mermaid
flowchart TD
    A[曲线与插值直觉] --> B[curve_and_spline]
    B --> C[radial_basis_function]
    C --> D[animation_format]
    D --> E[footskate_cleanup]
    D --> F[motion_matching]
    F --> G[motion_graph]
    G --> H[real_time_planning]
    H --> I[near_optimal_control]
    C --> J[verbs_and_adverbs]
    D --> K[motion_warping]
    K --> H
```

建议顺序：

1. 从 [`curve_and_spline`](Theory/curve_and_spline/README.md) 建立插值、参数和连续性的直觉。
2. 读 [`radial_basis_function`](Theory/radial_basis_function/README.md)，理解局部样本如何形成平滑控制场。
3. 读 [`animation_format`](AnimationPapers/animation_format/README.md)，理解后续所有案例的数据载体。
4. 读 [`footskate_cleanup_for_motion_capture_editing`](AnimationPapers/footskate_cleanup_for_motion_capture_editing/README.md)，观察约束如何修复动画伪影。
5. 读 [`motion_matching`](AnimationPapers/motion_matching/README.md) 与 [`motion_graph`](AnimationPapers/motion_graph/README.md)，比较检索式和图式动作合成。
6. 读 [`real_time_planning_for_parameterized_human_motion`](AnimationPapers/real_time_planning_for_parameterized_human_motion/README.md) 与 [`near_optimal_character_animation_with_continuous_control`](AnimationPapers/near_optimal_character_animation_with_continuous_control/README.md)，把动作片段、目标和代价函数连成规划控制系统。

## 案例依赖图

```mermaid
flowchart LR
    subgraph Theory[Theory 数学工具]
        T1[curve_and_spline]
        T2[radial_basis_function]
        T3[laplacian_deformation]
        T4[motiongraph_pointcloud_derivation]
    end

    subgraph Data[动画表示与编辑]
        A1[animation_format]
        A2[motion_warping]
        A3[verbs_and_adverbs]
        A4[footskate_cleanup]
    end

    subgraph Runtime[交互动作系统]
        R1[motion_matching]
        R2[motion_graph]
        R3[motion_fields]
        R4[real_time_planning]
        R5[near_optimal_control]
        R6[precomputing_avatar_behavior]
    end

    subgraph Pipeline[工程资产管线]
        P1[halo_4_facial_animation]
        P2[halo_4_exporter_from_maya]
        P3[real_time_planning_multiprocess_func]
    end

    T1 --> A1
    T2 --> A3
    T3 --> A4
    T4 --> R2
    A1 --> R1
    A1 --> R2
    A2 --> R4
    A3 --> R1
    R1 --> R4
    R2 --> R4
    R4 --> R5
    P2 --> P1
    P3 --> R4
```

## 按主题索引

| 主题 | 案例 |
| --- | --- |
| 数学基础 | [`curve_and_spline`](Theory/curve_and_spline/README.md), [`radial_basis_function`](Theory/radial_basis_function/README.md), [`radial_basis_function_verbs_and_adverbs`](Theory/radial_basis_function_verbs_and_adverbs/README.md) |
| 几何与距离度量 | [`laplacian_deformation`](Theory/laplacian_deformation/README.md), [`motiongraph_pointcloud_derivation`](Theory/motiongraph_pointcloud_derivation/README.md) |
| 动画数据表示 | [`animation_format`](AnimationPapers/animation_format/README.md), [`motion_warping`](AnimationPapers/motion_warping/README.md), [`verbs_and_adverbs`](AnimationPapers/verbs_and_adverbs/README.md) |
| 约束修复与标注 | [`footskate_cleanup_for_motion_capture_editing`](AnimationPapers/footskate_cleanup_for_motion_capture_editing/README.md), [`knowing_when_to_put_your_foot_down`](AnimationPapers/knowing_when_to_put_your_foot_down/README.md) |
| 检索、图与控制 | [`motion_matching`](AnimationPapers/motion_matching/README.md), [`motion_graph`](AnimationPapers/motion_graph/README.md), [`motion_fields_for_interactive_character_animation`](AnimationPapers/motion_fields_for_interactive_character_animation/README.md) |
| 规划与预计算 | [`real_time_planning_for_parameterized_human_motion`](AnimationPapers/real_time_planning_for_parameterized_human_motion/README.md), [`near_optimal_character_animation_with_continuous_control`](AnimationPapers/near_optimal_character_animation_with_continuous_control/README.md), [`precomputing_avatar_behavior`](AnimationPapers/precomputing_avatar_behavior/README.md), [`real_time_planning_multiprocess_func`](AnimationPapers/real_time_planning_multiprocess_func/README.md) |
| 资产与面部动画 | [`halo_4_facial_animation`](AnimationPapers/halo_4_facial_animation/README.md), [`halo_4_exporter_from_maya`](AnimationPapers/halo_4_exporter_from_maya/README.md) |

## 按输出类型索引

| 输出类型 | 适合看什么 |
| --- | --- |
| `plot` / `formula` / `matrix` | 曲线、公式推导、核矩阵、距离矩阵和训练曲线。 |
| `viewer` / `timeline_viewer` | 角色姿态、动画播放、motion graph 搜索和交互控制结果。 |
| `log` / `table` / `command_log` | 环境验证、数据规模、训练状态、导出路径和脚本运行证据。 |
| `source_excerpt` / `artifact_summary` / `diagram` | Python module 的源码职责、产物结构和与 notebook 的关系。 |

正文中的“重点可视化 / 动画”只放 `key_visual` 与 `key_animation` 的结果媒体；代码学习卡只作为附录证据，用来复现 cell 与源码上下文。

## 深写完成案例

这些案例已经具备更完整的前置知识、代码执行路径、关键 cell / 函数深讲、Mermaid 图、执行结果读法和素材清单；新增重点案例还补齐了 cell-level Mermaid 与结果媒体读法。

| 分组 | slug | 主题 |
| --- | --- | --- |
| AnimationPapers | [`animation_format`](AnimationPapers/animation_format/README.md) | 动画数据格式和通道组织 |
| AnimationPapers | [`footskate_cleanup_for_motion_capture_editing`](AnimationPapers/footskate_cleanup_for_motion_capture_editing/README.md) | 脚滑检测、约束和修复 |
| AnimationPapers | [`motion_fields_for_interactive_character_animation`](AnimationPapers/motion_fields_for_interactive_character_animation/README.md) | motion field 查询、候选动作和交互控制 |
| AnimationPapers | [`motion_matching`](AnimationPapers/motion_matching/README.md) | 特征库检索式角色控制 |
| AnimationPapers | [`motion_graph`](AnimationPapers/motion_graph/README.md) | 动作片段图与转移边 |
| AnimationPapers | [`motion_warping`](AnimationPapers/motion_warping/README.md) | 接触约束下的时间/空间重定向 |
| AnimationPapers | [`near_optimal_character_animation_with_continuous_control`](AnimationPapers/near_optimal_character_animation_with_continuous_control/README.md) | 连续控制中的候选扩展与代价裁剪 |
| AnimationPapers | [`precomputing_avatar_behavior`](AnimationPapers/precomputing_avatar_behavior/README.md) | 离线行为图预计算与运行时查询 |
| AnimationPapers | [`real_time_planning_for_parameterized_human_motion`](AnimationPapers/real_time_planning_for_parameterized_human_motion/README.md) | 参数化动作实时规划 |
| AnimationPapers | [`verbs_and_adverbs`](AnimationPapers/verbs_and_adverbs/README.md) | RBF 语义空间中的动词/副词调制 |
| Theory | [`curve_and_spline`](Theory/curve_and_spline/README.md) | 曲线、样条、参数和连续性 |
| Theory | [`laplacian_deformation`](Theory/laplacian_deformation/README.md) | Laplacian 坐标、锚点约束和形变传播 |

## 全量案例索引

| 分组 | slug | 类型 | 发布状态 |
| --- | --- | --- | --- |
| AnimationPapers | [`animation_format`](AnimationPapers/animation_format/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`footskate_cleanup_for_motion_capture_editing`](AnimationPapers/footskate_cleanup_for_motion_capture_editing/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`halo_4_facial_animation`](AnimationPapers/halo_4_facial_animation/README.md) | `notebook` | 媒体完整 + 发布基底 |
| AnimationPapers | [`knowing_when_to_put_your_foot_down`](AnimationPapers/knowing_when_to_put_your_foot_down/README.md) | `notebook` | 媒体完整 + 发布基底 |
| AnimationPapers | [`motion_fields_for_interactive_character_animation`](AnimationPapers/motion_fields_for_interactive_character_animation/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`motion_graph`](AnimationPapers/motion_graph/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`motion_matching`](AnimationPapers/motion_matching/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`motion_warping`](AnimationPapers/motion_warping/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`near_optimal_character_animation_with_continuous_control`](AnimationPapers/near_optimal_character_animation_with_continuous_control/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`precomputing_avatar_behavior`](AnimationPapers/precomputing_avatar_behavior/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`real_time_planning_for_parameterized_human_motion`](AnimationPapers/real_time_planning_for_parameterized_human_motion/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`verbs_and_adverbs`](AnimationPapers/verbs_and_adverbs/README.md) | `notebook` | 深写完成 + 媒体完整 |
| AnimationPapers | [`real_time_planning_multiprocess_func`](AnimationPapers/real_time_planning_multiprocess_func/README.md) | `python_module` | 媒体完整 + 源码证据 |
| AnimationPapers | [`halo_4_exporter_from_maya`](AnimationPapers/halo_4_exporter_from_maya/README.md) | `python_module` | 媒体完整 + 源码证据 |
| Theory | [`curve_and_spline`](Theory/curve_and_spline/README.md) | `notebook` | 深写完成 + 媒体完整 |
| Theory | [`laplacian_deformation`](Theory/laplacian_deformation/README.md) | `notebook` | 深写完成 + 媒体完整 |
| Theory | [`motiongraph_pointcloud_derivation`](Theory/motiongraph_pointcloud_derivation/README.md) | `notebook` | 媒体完整 + 发布基底 |
| Theory | [`radial_basis_function`](Theory/radial_basis_function/README.md) | `notebook` | 媒体完整 + 术语说明增强 |
| Theory | [`radial_basis_function_verbs_and_adverbs`](Theory/radial_basis_function_verbs_and_adverbs/README.md) | `notebook` | 媒体完整 + 发布基底 |

## 发布前检查

运行质量门：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\check_blog_docs.ps1
```

生成只读状态报告：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\docs\blog\report_blog_docs.ps1
```

检查脚本会确认 manifest 覆盖、README 和 assets 目录、Mermaid 图、核心章节、媒体文件、source 路径、素材引用、导航可达性和常见生成文案瑕疵。报告脚本用于发布前快速查看案例数、媒体数、未引用素材和潜在断链；两个脚本都只读文件，不执行 notebook。

## 目录约定

每个案例目录包含：

- `README.md`：canonical 博客正文。
- `assets/`：结果 PNG、GIF 预览、MP4/WebM 视频、学习卡 PNG、walkthrough WebM 和后续素材。
- `assets/README.md`：素材清单，说明每个 PNG/GIF/MP4/WebM 的来源、用途和对应正文位置。

`docs/examples/Footskate Cleanup for Motion Capture Editing.md` 和 PDF 保留为素材源；canonical 工程化版本放在 `docs/blog/AnimationPapers/footskate_cleanup_for_motion_capture_editing/README.md`。

## 未纳入正式归档的参考

`labs/AnimationPapers/Animation Format_inv.ipynb` 当前没有收录在 `tools/cases.yaml` 中，因此不生成正式受管案例目录。它可以作为 `animation_format` 的扩展参考。
