"""P-LOD protocol SDK — normative codec, emergence, and metrics.

Fail-loudly policy: import errors must surface. Silent empty/zero fallbacks are forbidden
(they would produce false “perfect reconstruction” metrics).
"""

from .spec.codec import decode_frame, encode_frame
from .spec.models import Constraint, PLODFrame, PLODHeader, SENode
from .emergence.reference import emerge, emerge_v1, emerge_v2
from .metrics.fidelity import (
    compute_symmetric_chamfer_distance,
    reconstruction_fidelity_score,
)

__version__ = "0.1.1"

__all__ = [
    "encode_frame",
    "decode_frame",
    "PLODHeader",
    "PLODFrame",
    "SENode",
    "Constraint",
    "emerge",
    "emerge_v1",
    "emerge_v2",
    "reconstruction_fidelity_score",
    "compute_symmetric_chamfer_distance",
    "__version__",
]
