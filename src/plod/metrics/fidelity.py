"""P-LOD reconstruction metrics (stdlib only)."""
from __future__ import annotations
import math
from typing import Sequence, Tuple

Point = Tuple[float, float, float]


def _mean_nn(a: Sequence[Point], b: Sequence[Point], sample: int = 400) -> float:
    if not a or not b:
        return 1e9
    step = max(1, len(a) // sample)
    total = 0.0
    count = 0
    for i in range(0, len(a), step):
        x, y, z = a[i]
        best = min((x - q[0]) ** 2 + (y - q[1]) ** 2 + (z - q[2]) ** 2 for q in b)
        total += math.sqrt(best)
        count += 1
    return total / max(count, 1)


def chamfer_distance(
    a: Sequence[Point], b: Sequence[Point], sample_a: int = 400, sample_b: int = 400
) -> float:
    return 0.5 * (_mean_nn(a, b, sample_a) + _mean_nn(b, a, sample_b))


def compute_symmetric_chamfer_distance(
    a: Sequence[Point], b: Sequence[Point], sample_a: int = 400, sample_b: int = 400
) -> float:
    """Symmetric Chamfer distance between two point sets.

    Uses a fixed-point sampled symmetric Chamfer estimator with a max-points
    sample limit for numerical stability.
    """
    return chamfer_distance(a, b, sample_a=sample_a, sample_b=sample_b)


def bbox_diagonal(pts: Sequence[Point]) -> float:
    if not pts:
        return 1.0
    xs, ys, zs = zip(*pts)
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)
    return math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0


def reconstruction_fidelity_score(
    ground_truth: Sequence[Point], reconstructed: Sequence[Point]
) -> Tuple[float, float, float]:
    cd = chamfer_distance(ground_truth, reconstructed)
    diag = bbox_diagonal(ground_truth)
    cd_norm = min(1.0, cd / diag)
    rfs = max(0.0, 1.0 - cd_norm)
    return rfs, cd, cd_norm


def topological_consistency_score(
    anchors: Sequence[Point], emerged: Sequence[Point], pad_frac: float = 0.05
) -> float:
    if not anchors or not emerged:
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


containment_score = topological_consistency_score
tcs_aabb = topological_consistency_score
