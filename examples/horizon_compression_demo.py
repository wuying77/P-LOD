#!/usr/bin/env python3
"""
P-LOD Horizon Compression Demo — Ablation-based Minimal Independent SE (stdlib only)

Mathematical objective (Minimal Independent Structure S*):

  S* = arg min_{S ⊆ X} |S|   subject to   D(X, G(S)) ≤ ε

where G is the emergence map (plod.ref.linear_spline.v1) and D is a normalized
topological distortion (e.g. symmetric Chamfer / bbox diagonal).

Node removal loss (leave-one-out ablation):
  ΔE_i = D(X, G(S \\ {p_i})) - D(X, G(S))
  causal_depth_i = round(255 * clamp(ΔE_i / max_j(ΔE_j), 0, 1))
  depth >= 200 → Causal Anchor (non-degenerate degree of freedom)

Heuristic ranking for candidate selection also mixes density + curvature proxies;
the formal causal_depth is always the ablation-normalized quantity above.

Wire: Spec v1.1 via plod_spec_codec.encode_frame
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_spec_codec import SENode, encode_frame

Point = Tuple[float, float, float]


def generate_volume(n: int = 10_000, seed: int = 42) -> List[Point]:
    rng = random.Random(seed)
    pts: List[Point] = []
    for i in range(200):
        t = i / 199.0
        pts.append((math.cos(t * math.pi), math.sin(t * math.pi), 0.2 * t))
        pts.append((0.6 * math.cos(t * 2 * math.pi), 0.6 * math.sin(t * 2 * math.pi), 0.5))
    while len(pts) < n:
        pts.append(
            (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(-0.5, 1.0))
        )
    return pts


def _cell_key(p: Point, grid: float) -> Tuple[int, int, int]:
    return (
        int(math.floor(p[0] / grid)),
        int(math.floor(p[1] / grid)),
        int(math.floor(p[2] / grid)),
    )


def density_map(pts: Sequence[Point], grid: float) -> dict:
    cells: dict = {}
    for p in pts:
        k = _cell_key(p, grid)
        cells.setdefault(k, []).append(p)
    return cells


def cell_centroid(bucket: Sequence[Point]) -> Point:
    n = len(bucket)
    return (
        sum(p[0] for p in bucket) / n,
        sum(p[1] for p in bucket) / n,
        sum(p[2] for p in bucket) / n,
    )


def local_curvature_proxy(centroid: Point, bucket: Sequence[Point]) -> float:
    if len(bucket) < 3:
        return 0.0
    dirs = []
    for p in bucket:
        dx, dy, dz = p[0] - centroid[0], p[1] - centroid[1], p[2] - centroid[2]
        nrm = math.sqrt(dx * dx + dy * dy + dz * dz) or 1e-9
        dirs.append((dx / nrm, dy / nrm, dz / nrm))
    mx = sum(d[0] for d in dirs) / len(dirs)
    my = sum(d[1] for d in dirs) / len(dirs)
    mz = sum(d[2] for d in dirs) / len(dirs)
    return sum((d[0] - mx) ** 2 + (d[1] - my) ** 2 + (d[2] - mz) ** 2 for d in dirs) / len(dirs)


def nn_recon_error(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 400) -> float:
    """Proxy for D(X, G(S)) using nearest-anchor residual (fast ablation surrogate)."""
    if not anchors:
        return 1e9
    step = max(1, len(cloud) // sample)
    total = 0.0
    count = 0
    for i in range(0, len(cloud), step):
        x, y, z = cloud[i]
        best = min((x - a[0]) ** 2 + (y - a[1]) ** 2 + (z - a[2]) ** 2 for a in anchors)
        total += math.sqrt(best)
        count += 1
    return total / max(count, 1)


def ablation_delta(
    candidates: List[Point], cloud: Sequence[Point], idx: int, base_err: float
) -> float:
    """ΔE_i = E_without_i - E_full  (non-negative structural loss)."""
    reduced = [c for i, c in enumerate(candidates) if i != idx]
    err = nn_recon_error(reduced, cloud, sample=300)
    return max(0.0, err - base_err)


def extract_se_ablation(
    pts: Sequence[Point],
    *,
    grid: float = 0.35,
    max_nodes: int = 80,
    w_density: float = 0.25,
    w_curvature: float = 0.25,
    w_ablation: float = 0.50,
    quiet: bool = False,
) -> List[SENode]:
    """
    Approximate S* by ranking cell centroids with ablation loss, then taking top |S|=max_nodes.

    This is a practical heuristic for the discrete program:
      S* = arg min |S|  s.t.  D(X, G(S)) ≤ ε
    Full combinatorial search is NP-hard; ablation ranks non-degenerate anchors.
    """
    cells = density_map(pts, grid)
    cands: List[dict] = []
    dens_max = max(len(b) for b in cells.values()) or 1
    for bucket in cells.values():
        c = cell_centroid(bucket)
        dens = len(bucket) / dens_max
        curv = local_curvature_proxy(c, bucket)
        cands.append({"pos": c, "density": dens, "curvature": curv})

    for c in cands:
        c["pre"] = 0.5 * c["density"] + 0.5 * min(1.0, c["curvature"] * 2.0)
    cands.sort(key=lambda x: x["pre"], reverse=True)
    pool = cands[: min(120, len(cands))]
    anchors = [c["pos"] for c in pool]
    base_err = nn_recon_error(anchors, pts, sample=300)

    if not quiet:
        print("=== Ablation-based Minimal Independent SE (S*) ===")
        print("S* ≈ arg min |S|  s.t.  D(X, G(S)) ≤ ε")
        print(f"Volume points:     {len(pts):,}")
        print(f"Ablation pool:     {len(pool)}")
        print(f"E_full (base):     {base_err:.6f}")

    for i in range(len(pool)):
        pool[i]["delta_e"] = ablation_delta(anchors, pts, i, base_err)

    max_de = max(c["delta_e"] for c in pool) or 1.0

    for c in pool:
        # Task-conditioned causal depth from removal loss:
        # C_i = round(255 * clamp(ΔE_i / max_j(ΔE_j), 0, 1))
        ratio = max(0.0, min(1.0, c["delta_e"] / max_de))
        c["causal_depth"] = int(round(255 * ratio))
        c["score"] = (
            w_density * c["density"]
            + w_curvature * min(1.0, c["curvature"] * 2.0)
            + w_ablation * ratio
        )

    pool.sort(key=lambda x: x["score"], reverse=True)
    selected = pool[:max_nodes]

    if not quiet:
        print(f"Selected |S|:      {len(selected)}")
        print(
            f"causal_depth range: "
            f"{min(c['causal_depth'] for c in selected)} .. {max(c['causal_depth'] for c in selected)}"
        )
        n_anchor = sum(1 for c in selected if c["causal_depth"] >= 200)
        print(f"Causal Anchors (depth≥200): {n_anchor}")
        print()
        print("Top 8 (ΔE / formal causal_depth):")
        for i, c in enumerate(selected[:8], 1):
            x, y, z = c["pos"]
            print(
                f"  #{i:02d}  ΔE={c['delta_e']:.6f}  depth={c['causal_depth']:3d}  "
                f"score={c['score']:.4f}  pos=({x:+.3f},{y:+.3f},{z:+.3f})"
            )

    nodes: List[SENode] = []
    for i, c in enumerate(selected):
        nodes.append(
            SENode(
                i + 1,
                c["pos"],
                risk_state=1 if c["causal_depth"] >= 200 else 0,
                sub_system=0x10 if c["causal_depth"] >= 200 else 0x30,
                resonance_freq=1.0 + 0.05 * (i % 17),
                causal_depth=c["causal_depth"],
            )
        )
    return nodes


def main() -> None:
    pts = generate_volume(10_000)
    raw = len(pts) * 24 + 64
    nodes = extract_se_ablation(pts, max_nodes=80)
    frame = encode_frame(nodes, embodied=True, extended_meta=True)
    ratio = raw / max(len(frame), 1)

    print()
    print("=== Horizon compression (minimal independent SE) ===")
    print(f"Raw dense estimate:  {raw:,} bytes ({raw/1024:.1f} KB)")
    print(f"SE-Frame:            {len(frame):,} bytes ({len(frame)/1024:.2f} KB)")
    print(f"Collapse ratio:      {ratio:.1f}×")
    print()
    print("S* = arg min |S|  s.t.  D(X, G(S)) ≤ ε")
    print("ΔE_i = E_without_i - E_full")
    print("causal_depth_i = round(255 * clamp(ΔE_i / max(ΔE), 0, 1))")


if __name__ == "__main__":
    main()
