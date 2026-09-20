"""Backward-compatible entry: examples/plod_metrics.py → plod.metrics.fidelity """
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from plod.metrics.fidelity import *  # noqa
from plod.metrics.fidelity import (
    bbox_diagonal,
    chamfer_distance,
    compute_symmetric_chamfer_distance,
    containment_score,
    reconstruction_fidelity_score,
    tcs_aabb,
    topological_consistency_score,
)
