#!/usr/bin/env python3
"""
P-LOD Horizon Compression Demo — Ablation-based SE extraction (stdlib only)

Extracts a sparse SE skeleton from a dense high-entropy volume using:
  Score(p) = w1*Density + w2*Curvature + w3*AblationLoss

causal_depth(i) ∝ Δ Reconstruction Error when node i is removed
  (Node Ablation & Structural Loss).

Usage:
  python horizon_compression_demo.py
"""

from __future__ import annotations

import math
import random
import struct
import zlib
from typing import List, Sequence, Tuple

MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4

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
    """Variance of directions from centroid — higher ≈ more structured bend."""
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
    var = sum((d[0] - mx) ** 2 + (d[1] - my) ** 2 + (d[2] - mz) ** 2 for d in dirs) / len(dirs)
    return var


def nn_recon_error(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 400) -> float:
    """Mean distance from sampled cloud points to nearest anchor (proxy recon error)."""
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
    """ΔE when removing candidate idx from the anchor set."""
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
) -> List[dict]:
    """
    Score(p) = w1*Density + w2*Curvature + w3*AblationLoss
    causal_depth ∝ normalized ablation ΔE (mapped to 0..255).
    """
    cells = density_map(pts, grid)
    # candidate centroids from occupied cells
    cands: List[dict] = []
    dens_max = max(len(b) for b in cells.values()) or 1
    for key, bucket in cells.items():
        c = cell_centroid(bucket)
        dens = len(bucket) / dens_max
        curv = local_curvature_proxy(c, bucket)
        cands.append({"pos": c, "density": dens, "curvature": curv, "bucket_n": len(bucket)})

    # pre-filter top-K by density+curvature to keep ablation tractable
    for c in cands:
        c["pre"] = 0.5 * c["density"] + 0.5 * min(1.0, c["curvature"] * 2.0)
    cands.sort(key=lambda x: x["pre"], reverse=True)
    pool = cands[: min(120, len(cands))]
    anchors = [c["pos"] for c in pool]
    base_err = nn_recon_error(anchors, pts, sample=300)

    print("=== Ablation-based SE extraction ===")
    print(f"Volume points:     {len(pts):,}")
    print(f"Occupied cells:    {len(cells)}")
    print(f"Ablation pool:     {len(pool)} candidates")
    print(f"Base recon error:  {base_err:.6f} (all pool anchors)")

    deltas = []
    for i in range(len(pool)):
        dE = ablation_delta(anchors, pts, i, base_err)
        pool[i]["ablation"] = dE
        deltas.append(dE)

    d_max = max(deltas) if deltas else 1.0
    if d_max < 1e-12:
        d_max = 1.0

    for c in pool:
        ab_n = c["ablation"] / d_max
        c["score"] = (
            w_density * c["density"]
            + w_curvature * min(1.0, c["curvature"] * 2.0)
            + w_ablation * ab_n
        )
        # causal_depth: map ablation importance to 0..255; anchors >=200 if top tier
        c["causal_depth"] = int(min(255, round(ab_n * 255)))

    pool.sort(key=lambda x: x["score"], reverse=True)
    selected = pool[:max_nodes]

    # re-scale depths so top ablation nodes sit as Causal Anchors (>=200)
    if selected:
        top_ab = max(c["ablation"] for c in selected) or 1.0
        for c in selected:
            ab_n = c["ablation"] / top_ab
            depth = int(min(255, 80 + round(ab_n * 175)))
            c["causal_depth"] = depth

    print(f"Selected SE nodes: {len(selected)}")
    print(
        f"causal_depth range: "
        f"{min(c['causal_depth'] for c in selected)} .. {max(c['causal_depth'] for c in selected)}"
    )
    n_anchor = sum(1 for c in selected if c["causal_depth"] >= 200)
    print(f"Causal Anchors (depth>=200): {n_anchor}")
    print()
    print("Top 8 by score (ablation-driven):")
    for i, c in enumerate(selected[:8], 1):
        x, y, z = c["pos"]
        print(
            f"  #{i:02d}  score={c['score']:.4f}  ablationΔE={c['ablation']:.6f}  "
            f"depth={c['causal_depth']:3d}  dens={c['density']:.3f}  "
            f"pos=({x:+.3f},{y:+.3f},{z:+.3f})"
        )

    nodes = []
    for i, c in enumerate(selected):
        nodes.append(
            {
                "id": i + 1,
                "pos": c["pos"],
                "causal_depth": c["causal_depth"],
                "resonance_freq": 1.0 + 0.05 * (i % 17),
                "ablation": c["ablation"],
                "score": c["score"],
            }
        )
    return nodes


def pack_embodied(nodes: List[dict]) -> bytes:
    flags = FLAG_EMBODIED | FLAG_EXTENDED_META
    body = bytearray()
    body += struct.pack("<HBBHH", MAGIC, 0x11, flags, len(nodes) & 0xFFFF, 1)
    for n in nodes:
        x, y, z = n["pos"]
        risk = 1 if n["causal_depth"] >= 200 else 0
        body += struct.pack(
            "<HBB3f3ff",
            n["id"] & 0xFFFF,
            risk,
            0x10 if n["causal_depth"] >= 200 else 0x30,
            float(x),
            float(y),
            float(z),
            0.0,
            0.0,
            0.0,
            0.0,
        )
        body += struct.pack("<fBxxx", float(n["resonance_freq"]), n["causal_depth"] & 0xFF)
    body += struct.pack("<I", zlib.crc32(bytes(body)) & 0xFFFFFFFF)
    return bytes(body)


def main() -> None:
    pts = generate_volume(10_000)
    raw = len(pts) * 24 + 64
    nodes = extract_se_ablation(pts, max_nodes=80)
    frame = pack_embodied(nodes)
    ratio = raw / max(len(frame), 1)

    print()
    print("=== Horizon compression (ablation SE) ===")
    print(f"Raw dense estimate:  {raw:,} bytes ({raw/1024:.1f} KB)")
    print(f"SE-Frame:            {len(frame):,} bytes ({len(frame)/1024:.2f} KB)")
    print(f"Collapse ratio:      {ratio:.1f}×  (~{(1 - len(frame)/raw)*100:.2f}% smaller)")
    print()
    print("Definition: causal_depth(i) ∝ ΔE when node i is ablated from the skeleton.")
    print("High ΔE → irreplaceable Strong-Entanglement / Causal Anchor.")


if __name__ == "__main__":
    main()
