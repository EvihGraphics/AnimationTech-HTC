from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evih_reproductions import common
from evih_reproductions.verbs_and_adverbs.core import load_generated, validate_metrics


def render_artifact(artifact: Path, screenshot: Path | None, frame: int, width: int, height: int, max_frames: int) -> dict[str, object]:
    payload = load_generated(artifact)
    validate_metrics(payload["metrics"])
    common.render_payload(payload, screenshot, frame, width, height, max_frames)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="View the Verbs And Adverbs Evih/Raylib reproduction artifact.")
    parser.add_argument("--artifact", default=str(Path(__file__).with_name("generated.dat")))
    parser.add_argument("--screenshot", default=None)
    parser.add_argument("--frame", type=int, default=32)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args(argv)
    render_artifact(
        Path(args.artifact),
        Path(args.screenshot) if args.screenshot else None,
        args.frame,
        args.width,
        args.height,
        args.max_frames,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
