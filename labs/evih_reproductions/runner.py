from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from evih_reproductions.cases import get_case
    from evih_reproductions.runtime import ensure_payload, render
else:
    from .cases import get_case
    from .runtime import ensure_payload, render


def main(argv: list[str] | None = None, default_case: str | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an EvihAnimation/Raylib reproduction case.")
    parser.add_argument("--case", default=default_case, required=default_case is None)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--screenshot", default=None)
    parser.add_argument("--frame", type=int, default=32)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args(argv)

    case = get_case(args.case)
    payload = ensure_payload(case, Path(args.artifact))
    render(
        payload,
        Path(args.screenshot) if args.screenshot else None,
        args.frame,
        args.width,
        args.height,
        args.max_frames,
    )
    print(payload["metrics"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
