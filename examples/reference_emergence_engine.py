"""Backward-compatible entry: examples/reference_emergence_engine.py → plod.emergence.reference

Set ``PLOD_FORCE_INSTALLED=1`` to load the installed package instead of ``src/``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if (
    os.environ.get("PLOD_FORCE_INSTALLED", "") not in ("1", "true", "TRUE", "yes")
    and _SRC.is_dir()
    and str(_SRC) not in sys.path
):
    sys.path.insert(0, str(_SRC))

from plod.emergence.reference import *  # noqa: F401,F403
from plod.emergence.reference import (  # noqa: F401
    PROFILE_V1,
    PROFILE_V2,
    emerge,
    emerge_v1,
    emerge_v2,
)

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="v1", choices=("v1", "v2"))
    args = ap.parse_args()
    from plod import SENode

    nodes = [SENode(1, (0.0, 0.0, 0.0)), SENode(2, (4.0, 0.0, 0.0))]
    pts = emerge(nodes, profile=args.profile)
    print(f"profile={args.profile} samples={len(pts)}")
    if pts:
        print("first", pts[0], "last", pts[-1])
