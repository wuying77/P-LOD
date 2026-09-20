"""P-LOD reference emergence (normative v1 + experimental v2)."""
from __future__ import annotations

from typing import List, Sequence, Tuple

from plod.spec.codec import SENode

PROFILE_V1 = "plod.ref.linear_spline.v1"
PROFILE_V2 = "plod.ref.linear_spline.v2"
T_SAMPLES = (0.25, 0.50, 0.75)

_SUPPORTED_PROFILES = frozenset(
    {
        "v1",
        "v2",
        PROFILE_V1,
        PROFILE_V2,
    }
)


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def chain_edges(nodes: Sequence[SENode]) -> List[Tuple[int, int]]:
    """Derived Edge Rule: sort by node_id, closed chain."""
    ordered = sorted(range(len(nodes)), key=lambda i: nodes[i].node_id)
    n = len(ordered)
    if n < 2:
        return []
    return [(ordered[i], ordered[(i + 1) % n]) for i in range(n)]


def emerge_v1(nodes: Sequence[SENode]) -> List[Tuple[float, float, float]]:
    """Normative frozen baseline: linear samples on derived edges."""
    if len(nodes) < 2:
        return [tuple(n.pos) for n in nodes]  # type: ignore
    out: List[Tuple[float, float, float]] = []
    for i, j in chain_edges(nodes):
        a, b = nodes[i].pos, nodes[j].pos
        for t in T_SAMPLES:
            out.append(lerp3(a, b, t))
    return out


def emerge_v2(nodes: Sequence[SENode], **kwargs) -> List[Tuple[float, float, float]]:
    """Experimental profile: currently aliases v1 (deterministic)."""
    return emerge_v1(nodes)


def emerge(nodes, profile="v1", **kwargs):
    """Dispatch emergence profile. Unknown profiles fail loudly (no silent fallback)."""
    if profile not in _SUPPORTED_PROFILES:
        raise ValueError(
            f"Unknown emergence profile {profile!r}. "
            f"Supported: ['v1', 'v2', {PROFILE_V1!r}, {PROFILE_V2!r}]"
        )
    if profile in ("v1", PROFILE_V1):
        return emerge_v1(nodes)
    return emerge_v2(nodes, **kwargs)
