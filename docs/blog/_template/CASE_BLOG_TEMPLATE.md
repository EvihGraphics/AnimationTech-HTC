# <案例标题>

## 元数据

| 字段 | 值 |
| --- | --- |
| slug | `<slug>` |
| source path | [`<source>`](../../../../<source>) |
| kind | `notebook` / `python_module` |
| env | `<env_prefix>` |
| kernel | `<kernel_name>` |
| validation | `passed` |
| publish tier | `深写完成 + 媒体完整` / `媒体完整 + 发布基底` |

## 问题背景

说明这个案例解决的动画、数学或工程问题。写清楚输入是什么、输出是什么，以及为什么这个问题值得单独学习。

## 阅读前置知识

- 需要理解的数学概念。
- 需要熟悉的数据结构或动画术语。
- 与其他案例的依赖关系。

## 总模块图

```mermaid
flowchart TD
    A[输入数据 / 理论背景] --> B[预处理与表示]
    B --> C[核心算法模块]
    C --> D[执行结果 / 可视化解释]
```

## 代码执行路径

```mermaid
flowchart LR
    C1[Cell 1: imports] --> C2[Cell 2: data load]
    C2 --> C3[Cell 3: core function]
    C3 --> C4[Cell 4: visualization]
```

用工程语言说明 notebook/script 的执行顺序，而不是逐行翻译代码。

## 模块拆解

### 1. <模块名称>

模块职责、输入、输出，以及它在整条链路里的位置。

**执行结果怎么看：** 说明本模块输出代表什么，读者应该从图、曲线、viewer 或日志中看懂什么。

## 关键 cell / 函数深讲

- `<cell or function>`：说明它承担的职责、关键参数和容易误解的地方。
- `<cell or function>`：说明它如何把上游数据转成下游模块需要的结构。

## 关键数据结构

- `<name>`：含义、shape 或字段组成。
- `<name>`：生命周期，以及它在哪些模块之间传递。

## 执行结果的意义

- 图像或 viewer：说明能观察到什么现象。
- 曲线或数值：说明它验证了哪条算法假设。
- 文件产物或日志：说明它在工程链路中的用途。

## 代码 Cell 与可视化结果

notebook 案例使用本节记录学习型媒体。每个条目都绑定 cell、输出类型、代码目的、结果意义和素材文件。

<video controls muted src="assets/00-walkthrough.webm"></video>

[下载 WebM](assets/00-walkthrough.webm)

| Cell | 输出类型 | 代码做什么 | 结果说明什么 | 素材 |
| --- | --- | --- | --- | --- |
| `<cell_index>` | `<output_type>` | `<code_purpose>` | `<result_meaning>` | [PNG](assets/<file>.png) |

python module 案例把本节标题替换为 `## 源码模块与执行证据`，并使用 source path、symbol、command log 或 artifact summary 来说明可复现证据。

## 运行方式

AnimationPapers notebook 优先使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_animationpapers_lab.ps1
```

单案例验证使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\run_case.ps1 <slug>
```

## 素材清单

每个案例在 `assets/README.md` 中维护素材清单。正文只引用已经存在的 PNG 或 WebM 文件，并说明它们来自哪个 cell、源码片段或命令输出。
