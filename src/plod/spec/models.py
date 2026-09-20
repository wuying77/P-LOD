"""P-LOD data models (re-exported from normative codec for stable import paths)."""
from .codec import (
    Constraint,
    DecodedFrame,
    ProtocolError,
    SENode,
)

# Aliases requested by package API surface
PLODFrame = DecodedFrame

__all__ = [
    "SENode",
    "Constraint",
    "DecodedFrame",
    "PLODFrame",
    "ProtocolError",
]
