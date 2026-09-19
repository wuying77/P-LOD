#!/usr/bin/env python3
"""Shared TCS / RFS metrics for P-LOD (stdlib only)."""

from __future__ import annotations

import math
from typing import Sequence, Tuple

Point = Tuple[float, float, float]


def mean_nn(src: Sequence[Point], dst: Sequence[Point], sample: int = 800) -> float:
    if not src or not dst:
        return 1e9
    step = max(1, len(src) // sample)
    total = 0.0
    n = 0
    for i in range(0, len(src), step):
        x, y, z = src[i]
        best = min((x - q[0]) ** 2 + (y - q[1]) ** 2 + (z - q[2]) ** 2 for q in dst)
        total += math.sqrt(best)
        n += 1
    return total / max(n, 1)


def chamfer_distance(
    a: Sequence[Point], b: Sequence[Point], sample_a: int = 800, sample_b: int = 800
) -> float:
    """Symmetric Chamfer: 0.5 * (mean_nn(A,B) + mean_nn(B,A))."""
    return 0.5 * (mean_nn(a, b, sample_a) + mean_nn(b, a, sample_b))


def bbox_diagonal(pts: Sequence[Point]) -> float:
    if not pts:
        return 1.0
    xs, ys, zs = zip(*pts)
    return (
        math.sqrt(
            (max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2 + (max(zs) - min(zs)) ** 2
        )
        or 1.0
    )


def reconstruction_fidelity_score(
    ground_truth: Sequence[Point], reconstructed: Sequence[Point]
) -> Tuple[float, float, float]:
    """
    Returns (RFS, CD, normalized_CD).

    CD = 0.5 * (mean_nn(A,B) + mean_nn(B,A))
    normalized_CD = min(1.0, CD / bbox_diagonal(ground_truth))
    RFS = max(0.0, 1.0 - normalized_CD)
    """
    cd = chamfer_distance(ground_truth, reconstructed)
    diag = bbox_diagonal(ground_truth)
    cd_norm = min(1.0, cd / diag)
    rfs = max(0.0, 1.0 - cd_norm)
    return rfs, cd, cd_norm


def topological_consistency_score(
    anchors: Sequence[Point], emerged: Sequence[Point], pad_frac: float = 0.05
) -> float:
    """
    TCS: fraction of emerged points inside SE AABB expanded by pad_frac * diagonal.
    Empty emerged set → 0.0 (no WE produced under a profile that expected samples).
    No anchors → 0.0.
    """
    if not anchors:
        return 0.0
    if not emerged:
        return 0.0
    xs, ys, zs = zip(*anchors)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    diag = math.sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2) or 1.0
    pad = pad_frac * diag
    ok = sum(
        1
        for p in emerged
        if min_x - pad <= p[0] <= max_x + pad
        and min_y - pad <= p[1] <= max_y + pad
        and min_z - pad <= p[2] <= max_z + pad
    )
    return ok / len(emerged)
