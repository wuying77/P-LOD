"""P-LOD protocol SDK — normative codec, emergence, and metrics."""

from .spec.codec import decode_frame, encode_frame
from .spec.models import Constraint, PLODFrame, SENode

try:
    from .emergence.reference import emerge, emerge_v1
except Exception:  # pragma: no cover
    def emerge_v1(nodes):  # type: ignore
        return []

    def emerge(nodes, profile="v1", **kwargs):  # type: ignore
        return emerge_v1(nodes)

try:
    from .metrics.fidelity import (
        compute_symmetric_chamfer_distance,
        reconstruction_fidelity_score,
    )
except Exception:  # pragma: no cover
    def compute_symmetric_chamfer_distance(*a, **k):  # type: ignore
        return 0.0

    def reconstruction_fidelity_score(*a, **k):  # type: ignore
        return 0.0, 0.0, 0.0

__version__ = "0.1.0"

__all__ = [
    "encode_frame",
    "decode_frame",
    "PLODFrame",
    "SENode",
    "Constraint",
    "emerge",
    "emerge_v1",
    "reconstruction_fidelity_score",
    "compute_symmetric_chamfer_distance",
    "__version__",
]
