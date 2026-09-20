"""P-LOD data models (re-exported from normative codec for stable import paths)."""
from __future__ import annotations

from dataclasses import dataclass

from .codec import (
    Constraint,
    DecodedFrame,
    ProtocolError,
    SENode,
)

# Aliases requested by package API surface
PLODFrame = DecodedFrame


@dataclass(frozen=True)
class PLODHeader:
    """Lightweight header view extracted from a decoded frame."""

    version: int
    flags: int
    sequence_id: int
    node_count: int

    @classmethod
    def from_frame(cls, frame: DecodedFrame) -> "PLODHeader":
        return cls(
            version=frame.version,
            flags=frame.flags,
            sequence_id=frame.sequence_id,
            node_count=len(frame.nodes),
        )


__all__ = [
    "SENode",
    "Constraint",
    "DecodedFrame",
    "PLODFrame",
    "PLODHeader",
    "ProtocolError",
]
