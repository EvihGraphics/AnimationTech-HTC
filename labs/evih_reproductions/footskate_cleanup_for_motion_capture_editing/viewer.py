from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evih_reproductions.runner import main


if __name__ == "__main__":
    raise SystemExit(main(default_case="footskate_cleanup_for_motion_capture_editing"))
