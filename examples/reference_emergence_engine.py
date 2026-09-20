"""Backward-compatible entry: examples/reference_emergence_engine.py → plod.emergence.reference """
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from plod.emergence.reference import *  # noqa
from plod.emergence.reference import (
    PROFILE_V1,
    PROFILE_V2,
    emerge,
    emerge_v1,
    emerge_v2,
)
