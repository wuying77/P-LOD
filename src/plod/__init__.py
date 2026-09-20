"""P-LOD protocol SDK — normative codec, emergence, and metrics."""

from .emergence.reference import emerge, emerge_v1
from .metrics.fidelity import (
    compute_symmetric_chamfer_distance,
    reconstruction_fidelity_score,
)
from .spec.codec import decode_frame, encode_frame
from .spec.models import Constraint, PLODFrame, SENode

__version__ = "0.1.1"

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
