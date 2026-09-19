#!/usr/bin/env python3
"""
P-LOD Reconstruction Fidelity (RFS) evaluation (stdlib only)

Compares a dense synthetic cloud vs SE skeleton + linear-spline emergence.
Reports: Compression Ratio (CR), Chamfer Distance (CD), TCS, RFS.

Usage:
  python eval_reconstruction_fidelity.py
"""

from __future__ import annotations

import math
import random
from typing import List, Sequence, Tuple

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
        out.append((sum(p[0] for p in bucket) / n, sum(p[1] for p in bucket) / n, sum(p[2] for p in bucket) / n))
    return out


def emerge_midpoints(anchors: Sequence[Point]) -> List[Point]:
    """Frozen linear_spline.v1-style: consecutive midpoints + ring close."""
    if len(anchors) < 2:
        return list(anchors)
    out: List[Point] = []
    for i in range(len(anchors) - 1):
        a, b = anchors[i], anchors[i + 1]
        out.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
    a, b = anchors[-1], anchors[0]
    out.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2))
    return out


def chamfer(a: Sequence[Point], b: Sequence[Point], sample_a: int = 800, sample_b: int = 800) -> float:
    """Symmetric mean nearest-neighbor distance (Chamfer proxy)."""

    def mean_nn(src: Sequence[Point], dst: Sequence[Point], sample: int) -> float:
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

    return 0.5 * (mean_nn(a, b, sample_a) + mean_nn(b, a, sample_b))


def tcs_box(anchors: Sequence[Point], emerged: Sequence[Point]) -> float:
    if not anchors:
        return 0.0
    xs, ys, zs = zip(*anchors)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    diag = math.sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2) or 1.0
    pad = 0.05 * diag
    if not emerged:
        return 1.0
    ok = sum(
        1
        for p in emerged
        if min_x - pad <= p[0] <= max_x + pad
        and min_y - pad <= p[1] <= max_y + pad
        and min_z - pad <= p[2] <= max_z + pad
    )
    return ok / len(emerged)


def main() -> None:
    cloud = generate_volume(5000)
    anchors = grid_centroids(cloud, max_n=64)
    emerged = emerge_midpoints(anchors)
    recon = list(anchors) + emerged

    raw_bytes = len(cloud) * 24 + 64
    # SE frame size proxy: 8 header + 64*(32+8) + 4 crc (embodied+meta)
    se_bytes = 8 + len(anchors) * 40 + 4
    cr = raw_bytes / max(se_bytes, 1)

    cd = chamfer(cloud, recon)
    # normalize CD by bbox diagonal for RFS in [0,1]
    xs, ys, zs = zip(*cloud)
    diag = math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2 + (max(zs) - min(zs)) ** 2) or 1.0
    cd_norm = min(1.0, cd / diag)
    rfs = max(0.0, 1.0 - cd_norm)
    tcs = tcs_box(anchors, emerged)

    print("=== P-LOD Reconstruction Fidelity Report ===")
    print("Profile baseline: plod.ref.linear_spline.v1 (frozen normative midpoint emergence)")
    print()
    print("| Metric                         | Value")
    print("|--------------------------------|------------------")
    print(f"| Original cloud points          | {len(cloud):,}")
    print(f"| SE anchors                     | {len(anchors)}")
    print(f"| Emerged WE samples             | {len(emerged)}")
    print(f"| Raw size estimate (bytes)      | {raw_bytes:,}")
    print(f"| SE-Frame size estimate (bytes) | {se_bytes:,}")
    print(f"| Compression Ratio (CR)         | {cr:.2f}×")
    print(f"| Chamfer Distance (CD)          | {cd:.6f}")
    print(f"| CD / bbox diagonal             | {cd_norm:.6f}")
    print(f"| TCS (protocol compliance)      | {tcs:.4f}")
    print(f"| RFS = 1 - normalized CD        | {rfs:.4f}")
    print()
    print("Note: TCS measures protocol topology bounds; RFS measures fidelity to Ground Truth.")
    print("STATUS:", "TCS PASS" if tcs >= 0.99 else "TCS FAIL")


if __name__ == "__main__":
    main()
