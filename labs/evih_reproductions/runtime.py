from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from . import common


def _core_for(case: dict[str, Any]) -> Any:
    return importlib.import_module(f"evih_reproductions.{case['slug']}.core")


def ensure_payload(case: dict[str, Any], artifact: Path) -> dict[str, Any]:
    core = _core_for(case)
    payload = core.run_pipeline(strict_baseline=True)
    core.save_generated(payload, artifact)
    return core.load_generated(artifact)


def render(payload: dict[str, Any], screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> None:
    common.render_payload(payload, screenshot, frame, width, height, max_frames)
