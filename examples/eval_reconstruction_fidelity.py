#!/usr/bin/env python3
"""RFS / TCS-AABB evaluation; v1 samples t={0.25,0.50,0.75} per derived edge."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_metrics import reconstruction_fidelity_score, tcs_aabb

Point = Tuple[float, float, float]


def generate_volume(n: int = 5000, seed: int = 7) -> List[Point]:
    rng = random.Random(seed)
    pts: List[Point] = []
    for i in range(150):
        t = i / 149.0
        pts.append((math.cos(t * math.pi), math.sin(t * math.pi), 0.2 * t))
        pts.append((0.6 * math.cos(t * 2 * math.pi), 0.6 * math.sin(t * 2 * math.pi), 0.5))
    while len(pts) < n:
        pts.append((rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(-0.5, 1.0)))
    return pts


def grid_centroids(pts: Sequence[Point], grid: float = 0.4, max_n: int = 64) -> List[Point]:
    cells: dict = {}
    for p in pts:
        k = (int(math.floor(p[0] / grid)), int(math.floor(p[1] / grid)), int(math.floor(p[2] / grid)))
        cells.setdefault(k, []).append(p)
    ranked = sorted(cells.values(), key=len, reverse=True)[:max_n]
    out = []
    for bucket in ranked:
        n = len(bucket)
        out.append(
            (sum(p[0] for p in bucket) / n, sum(p[1] for p in bucket) / n, sum(p[2] for p in bucket) / n)
        )
    return out


def emerge_v1(anchors: Sequence[Point]) -> List[Point]:
    """Derived Edge Rule: consecutive + ring; t in {0.25, 0.50, 0.75}."""
    if len(anchors) < 2:
        return list(anchors)
    out: List[Point] = []
    pairs = [(anchors[i], anchors[i + 1]) for i in range(len(anchors) - 1)]
    pairs.append((anchors[-1], anchors[0]))
    for a, b in pairs:
        for t in (0.25, 0.50, 0.75):
            out.append(
                (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
            )
    return out


def main() -> None:
    cloud = generate_volume(5000)
    anchors = grid_centroids(cloud, max_n=64)
    emerged = emerge_v1(anchors)
    recon = list(anchors) + emerged

    raw_bytes = len(cloud) * 24 + 64
    se_bytes = 8 + len(anchors) * 40 + 4
    cr = raw_bytes / max(se_bytes, 1)

    rfs, cd, cd_norm = reconstruction_fidelity_score(cloud, recon)
    tcs = tcs_aabb(anchors, emerged)

    print("=== P-LOD Reconstruction Fidelity Report ===")
    print("Profile: plod.ref.linear_spline.v1 (Derived Edge Rule, t={0.25,0.50,0.75})")
    print()
    print(f"| CR                              | {cr:.2f}×")
    print(f"| Chamfer Distance (CD)           | {cd:.6f}")
    print(f"| normalized CD                   | {cd_norm:.6f}")
    print(f"| RFS                             | {rfs:.4f}")
    print(
        f"| TCS-AABB = {tcs:.4f} | Status: Protocol AABB Containment "
        f"{'PASS' if tcs >= 0.99 else 'FAIL'}"
    )
    print(
        "(Note: Verifies emerged points fall strictly within SE anchor bounding bounds; "
        "not a full graph-topology invariant.)"
    )


if __name__ == "__main__":
    main()
