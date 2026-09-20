#!/usr/bin/env python3
"""
P-LOD Horizon Compression — two-stage ε-minimal SE extraction (stdlib only)

Selection / evaluation alignment:
  --ablation-mode exact  → ΔE and D both use G = plod.ref.linear_spline.v1
                           (chain edges, t∈{0.25,0.50,0.75}) + symmetric Chamfer
  --ablation-mode fast   → NN residual proxy (legacy speed path)

Stage A: density + curvature candidate pool
Stage B: greedy strip lowest-impact nodes while D(X, G(S)) ≤ ε

CLI:
  python horizon_compression_demo.py --ablation-mode exact --epsilon 0.08
  python horizon_compression_demo.py --ablation-mode fast --epsilon 0.08
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_metrics import bbox_diagonal, chamfer_distance
from plod_spec_codec import SENode, encode_frame

Point = Tuple[float, float, float]
T_SAMPLES = (0.25, 0.50, 0.75)
REL_MAX_DELTA_REJECT = 0.0175
CMAX_REJECT = 50
GINI_REJECT = 0.12


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


def perturb_cloud(pts: Sequence[Point], seed: int, sigma: float = 0.02) -> List[Point]:
    rng = random.Random(seed)
    out = []
    for x, y, z in pts:
        out.append(
            (
                x + rng.gauss(0, sigma),
                y + rng.gauss(0, sigma),
                z + rng.gauss(0, sigma),
            )
        )
    return out


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
    return sum((d[0] - mx) ** 2 + (d[1] - my) ** 2 + (d[2] - mz) ** 2 for d in dirs) / len(
        dirs
    )


def emerge_linear_spline_v1(anchors: Sequence[Point]) -> List[Point]:
    """Faithful G = plod.ref.linear_spline.v1 (implicit edges by sort order)."""
    if len(anchors) < 2:
        return list(anchors)
    # Stable order by position hash so leave-one-out is consistent
    ordered = sorted(anchors, key=lambda p: (round(p[0], 6), round(p[1], 6), round(p[2], 6)))
    out: List[Point] = list(ordered)
    n = len(ordered)
    for i in range(n):
        a, b = ordered[i], ordered[(i + 1) % n]
        for t in T_SAMPLES:
            out.append(
                (
                    a[0] + (b[0] - a[0]) * t,
                    a[1] + (b[1] - a[1]) * t,
                    a[2] + (b[2] - a[2]) * t,
                )
            )
    return out


def D_exact(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 500) -> float:
    """Normalized Chamfer between G(S) and X (selection == evaluation metric)."""
    if not anchors:
        return 1e9
    recon = emerge_linear_spline_v1(anchors)
    cd = chamfer_distance(cloud, recon, sample_a=sample, sample_b=min(sample, len(recon)))
    diag = bbox_diagonal(cloud)
    return cd / diag


def D_fast(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 400) -> float:
    """NN residual / bbox (legacy fast path)."""
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
    return (total / max(count, 1)) / bbox_diagonal(cloud)


def D_of(anchors: Sequence[Point], cloud: Sequence[Point], mode: str) -> float:
    if mode == "exact":
        return D_exact(anchors, cloud)
    return D_fast(anchors, cloud)


def _gini(values: Sequence[float]) -> float:
    xs = sorted(max(0.0, float(v)) for v in values)
    n = len(xs)
    if n == 0:
        return 0.0
    s = sum(xs)
    if s <= 1e-15:
        return 0.0
    acc = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * acc) / (n * s) - (n + 1.0) / n


def stage_a_candidates(
    pts: Sequence[Point],
    *,
    grid: float = 0.35,
    pool_cap: int = 48,
) -> List[dict]:
    cells = density_map(pts, grid)
    dens_max = max((len(b) for b in cells.values()), default=1) or 1
    cands: List[dict] = []
    for bucket in cells.values():
        c = cell_centroid(bucket)
        dens = len(bucket) / dens_max
        curv = local_curvature_proxy(c, bucket)
        pre = 0.5 * dens + 0.5 * min(1.0, curv * 2.0)
        cands.append({"pos": c, "density": dens, "curvature": curv, "pre": pre})
    cands.sort(key=lambda x: x["pre"], reverse=True)
    return cands[: min(pool_cap, len(cands))]


def rank_by_ablation(
    pool: List[dict],
    cloud: Sequence[Point],
    mode: str,
) -> List[dict]:
    anchors = [c["pos"] for c in pool]
    base = D_of(anchors, cloud, mode)
    for i, c in enumerate(pool):
        reduced = [anchors[j] for j in range(len(anchors)) if j != i]
        d_wo = D_of(reduced, cloud, mode)
        c["delta_e"] = max(0.0, d_wo - base)
        c["base_err"] = base
    max_de = max((c["delta_e"] for c in pool), default=1.0) or 1.0
    for c in pool:
        ratio = max(0.0, min(1.0, c["delta_e"] / max_de))
        c["causal_depth"] = int(round(255 * ratio))
        c["score"] = 0.25 * c["density"] + 0.25 * min(1.0, c["curvature"] * 2.0) + 0.50 * ratio
    pool.sort(key=lambda x: x["score"], reverse=True)
    return pool


def structural_confidence(pool: Sequence[dict]) -> Tuple[bool, str, dict]:
    if not pool:
        return False, "empty candidate pool", {}
    depths = [int(c.get("causal_depth", 0)) for c in pool]
    deltas = [float(c.get("delta_e", 0.0)) for c in pool]
    c_max = max(depths)
    g = _gini([d / 255.0 for d in depths])
    max_de = max(deltas) if deltas else 0.0
    base_err = float(pool[0].get("base_err", 0.0))
    rel = max_de / base_err if base_err > 1e-12 else 0.0
    stats = {"c_max": c_max, "gini": g, "rel_max_delta": rel, "max_delta_e": max_de}
    if rel < REL_MAX_DELTA_REJECT:
        return False, f"rel_max_ΔE={rel:.4f}<{REL_MAX_DELTA_REJECT}", stats
    if c_max < CMAX_REJECT and g < GINI_REJECT:
        return False, f"C_max={c_max} Gini={g:.3f}", stats
    return True, "ok", stats


def stage_b_epsilon_minimal(
    pool: List[dict],
    cloud: Sequence[Point],
    epsilon: float,
    mode: str,
) -> Tuple[List[dict], float]:
    """
    Greedy elimination by ascending ΔE:
      try drop lowest-ΔE remaining node; keep if D still ≤ ε.
    """
    working = list(pool)
    # Process removals in ascending delta_e order (prefer dropping low-impact first)
    order = sorted(range(len(working)), key=lambda i: working[i]["delta_e"])
    removed = set()

    def current_anchors() -> List[Point]:
        return [working[i]["pos"] for i in range(len(working)) if i not in removed]

    d0 = D_of(current_anchors(), cloud, mode)
    if d0 > epsilon:
        return working, d0  # infeasible at full pool

    for i in order:
        if i in removed:
            continue
        if len(working) - len(removed) <= 1:
            break
        removed.add(i)
        d_try = D_of(current_anchors(), cloud, mode)
        if d_try > epsilon:
            removed.discard(i)  # essential — keep

    kept = [working[i] for i in range(len(working)) if i not in removed]
    # re-rank kept for causal_depth display
    kept = rank_by_ablation(kept, cloud, mode)
    final_d = D_of([c["pos"] for c in kept], cloud, mode)
    return kept, final_d


def _pool_to_nodes(selected: Sequence[dict]) -> List[SENode]:
    nodes: List[SENode] = []
    for i, c in enumerate(selected):
        nodes.append(
            SENode(
                i + 1,
                c["pos"],
                risk_state=1 if c["causal_depth"] >= 200 else 0,
                sub_system=0x10 if c["causal_depth"] >= 200 else 0x30,
                resonance_freq=1.0 + 0.05 * (i % 17),  # placeholder
                causal_depth=c["causal_depth"],
            )
        )
    return nodes


def extract_se_ablation(
    pts: Sequence[Point],
    *,
    grid: float = 0.35,
    max_nodes: int = 80,
    quiet: bool = False,
    mode: str = "fast",
    **_kw,
) -> List[SENode]:
    """Fixed top-k after Stage A (+ ablation rank). Backward-compatible API."""
    pool = stage_a_candidates(pts, grid=grid, pool_cap=max(48, max_nodes))
    pool = rank_by_ablation(pool, pts, mode)
    selected = pool[:max_nodes]
    if not quiet:
        print(f"Stage A top-k |S|={len(selected)} mode={mode}")
    return _pool_to_nodes(selected)


def extract_se_epsilon_minimal(
    pts: Sequence[Point],
    *,
    epsilon: float = 0.08,
    grid: float = 0.35,
    pool_cap: int = 48,
    quiet: bool = False,
    mode: str = "exact",
) -> Tuple[Optional[List[SENode]], dict]:
    """Stage A candidate discovery + Stage B ε-constrained greedy elimination."""
    pool = stage_a_candidates(pts, grid=grid, pool_cap=pool_cap)
    pool = rank_by_ablation(pool, pts, mode)
    ok, reason, conf = structural_confidence(pool)
    report: dict = {
        "epsilon": epsilon,
        "mode": mode,
        "confidence_ok": ok,
        "confidence_reason": reason,
        "confidence_stats": conf,
        "status": "OK",
    }
    if not ok:
        report["status"] = "STRUCTURAL_CONFIDENCE_LOW"
        report["message"] = (
            "No stable independent structure detected. Frame skipped or baseline pass-through."
        )
        if not quiet:
            print(f"STATUS: STRUCTURAL_CONFIDENCE_LOW | REASON: {reason}")
        return None, report

    d_full = D_of([c["pos"] for c in pool], pts, mode)
    if d_full > epsilon:
        report["n_star"] = len(pool)
        report["final_D"] = d_full
        report["status"] = "EPSILON_INFEASIBLE_FULL_POOL"
        if not quiet:
            print(f"Target ε={epsilon:.4f} | full pool D={d_full:.4f} > ε")
        return _pool_to_nodes(pool), report

    kept, final_d = stage_b_epsilon_minimal(pool, pts, epsilon, mode)
    report["n_star"] = len(kept)
    report["final_D"] = final_d
    report["status"] = "EPSILON_MINIMAL"
    if not quiet:
        print(
            f"Target Epsilon (ε): {epsilon:.3f} | "
            f"Minimal Independent Skeleton N*(ε): {len(kept)} | "
            f"Achieved Loss: {final_d:.4f} | mode={mode}"
        )
        n_anchor = sum(1 for c in kept if c["causal_depth"] >= 200)
        print(f"High-Causal-Depth Anchors in S*(ε): {n_anchor}")
    return _pool_to_nodes(kept), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilon", type=float, default=None)
    ap.add_argument("--ablation-mode", choices=("exact", "fast"), default="exact")
    ap.add_argument("--max-nodes", type=int, default=80)
    ap.add_argument("--max-pool", type=int, default=48)
    ap.add_argument("--points", type=int, default=10_000)
    args = ap.parse_args()

    pts = generate_volume(args.points)
    raw = len(pts) * 24 + 64
    mode = args.ablation_mode

    if args.epsilon is not None:
        nodes, report = extract_se_epsilon_minimal(
            pts, epsilon=args.epsilon, pool_cap=args.max_pool, mode=mode
        )
        if nodes is None:
            print("STATUS: STRUCTURAL_CONFIDENCE_LOW — no SE frame emitted")
            return
        frame = encode_frame(nodes, embodied=True, extended_meta=True)
        print()
        print("=== Horizon compression (two-stage ε-minimal) ===")
        print(f"Status:              {report.get('status')}")
        print(f"Ablation mode:       {mode}")
        print(f"Raw dense estimate:  {raw:,} bytes")
        print(f"SE-Frame:            {len(frame):,} bytes")
        print(f"N*(ε):               {report.get('n_star')}")
        print(f"Achieved Loss:       {report.get('final_D', float('nan')):.4f}")
        print(f"Collapse ratio:      {raw / max(len(frame), 1):.1f}×")
        return

    nodes = extract_se_ablation(pts, max_nodes=args.max_nodes, mode=mode)
    frame = encode_frame(nodes, embodied=True, extended_meta=True)
    print()
    print("=== Horizon compression (fixed top-k) ===")
    print(f"mode={mode} | SE-Frame={len(frame)} B | ratio={raw / max(len(frame), 1):.1f}×")
    print("Use --epsilon 0.08 --ablation-mode exact for N*(ε).")


if __name__ == "__main__":
    main()
