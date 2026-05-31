# 配置 AnimationTech 全量本地环境

## Summary
- 目标：按 [docs/README.md](e:/HTC/AnimationTech-HTC/docs/README.md) 配置并验证全量 26 个 case。
- 当前状态：仓库干净；没有 `.envs/`、`.reports/summary.json`；PATH 中没有 `conda`；`winget` 可用且能找到 `Anaconda.Miniconda3`。
- 完成标准：`validate_all.ps1` 成功退出，`.reports/summary.json` 显示 26 个 case 通过且失败数为 0；不启动 JupyterLab；最终恢复 `tools/cases.yaml`，保持 git 工作区清洁。

## Key Changes
- 安装 Miniconda：
  - 使用 `winget install -e --id Anaconda.Miniconda3 --accept-package-agreements --accept-source-agreements`。
  - 安装后在当前 PowerShell 会话中确认 `conda.exe` 可用；若 PATH 未刷新，则从常见安装路径定位 `conda.exe` 并临时加入 `$env:Path`。
  - 验证命令：`conda --version`。
- 准备工程资产：
  - 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_assets.ps1`。
  - 预期生成/下载内容落在 `.cache/` 和 `resources/lafan1/`，这些路径已被 `.gitignore` 忽略。
- 执行全量矩阵：
  - 运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate_all.ps1`。
  - 脚本会按 `tools/cases.yaml` 为每个 case 创建 `.envs/<prefix>` Conda 环境，注册本地 Jupyter kernel，写入 `.reports/` 日志、lock、执行 notebook 和 `summary.json`。
- 恢复跟踪文件：
  - `run_case.ps1` / `validate_all.ps1` 会更新 `tools/cases.yaml` 的状态时间戳。
  - 验证结束并读取 summary 后，将 `tools/cases.yaml` 恢复为运行前内容，只保留本地环境与报告产物。

## Interfaces
- 不修改公开 API、notebook 源文件、依赖模板或工程代码。
- 只产生本地环境产物：`.envs/`、`.jupyter/`、`.reports/`、`.cache/`、`resources/lafan1/` 以及部分忽略的生成数据文件。
- 不启动 JupyterLab；如后续需要学习入口，可再运行 `tools/start_animationpapers_lab.ps1`。

## Test Plan
- `conda --version` 能正常输出版本。
- `prepare_assets.ps1` 成功完成，`resources/lafan1/bvh` 中有 BVH 文件。
- `validate_all.ps1` 返回 exit code 0。
- `Get-Content .\.reports\summary.json -Raw` 中：
  - `failed` 为 `0`
  - `blocked_external` 为 `0`
  - `passed` 为 `26`
- 若有失败，先查看 `.reports/logs/<slug>.log`，修复后只重跑失败 case 或重新跑全量矩阵。
- 最后确认 `git status --short` 为空。

## Assumptions
- 使用 README 推荐的 Conda prefix 模型，不用系统 Python 3.13 作为 case 运行环境。
- 使用 `validate_all.ps1` 默认策略；训练重的 case 使用脚本内置的 `auto/validate` 配置。
- 不运行额外的人工 JupyterLab smoke test；README 中标为 `manual_smoke` 的 notebook 仅完成自动执行验证。
