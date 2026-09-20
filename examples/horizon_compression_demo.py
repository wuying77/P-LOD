#!/usr/bin/env python3
"""
P-LOD Horizon Compression Demo — ε-Minimal Independent SE (stdlib only)

Objective:
  S*(ε) = arg min |S|  s.t.  D(X, G(S)) ≤ ε

Modes:
  1) Fixed top-k ablation ranking (legacy / rate-distortion sweeps)
  2) ε-constrained dynamic minimality: greedily strip lowest-impact nodes
     until any further removal would breach ε (proxy D = NN residual / bbox_diag)

No-structure reject:
  If relative max ablation mass is degenerate (pure noise), emit
  STATUS: STRUCTURAL_CONFIDENCE_LOW instead of a forced pseudo-skeleton.

CLI:
  python horizon_compression_demo.py
  python horizon_compression_demo.py --epsilon 0.08
  python horizon_compression_demo.py --epsilon 0.08 --max-pool 120
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_spec_codec import SENode, encode_frame

Point = Tuple[float, float, float]

CMAX_REJECT = 50
GINI_REJECT = 0.12
REL_MAX_DELTA_REJECT = 0.0175  # max ΔE / E_full below this → degenerate field


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
    return sum((d[0] - mx) ** 2 + (d[1] - my) ** 2 + (d[2] - mz) ** 2 for d in dirs) / len(
        dirs
    )


def bbox_diag(pts: Sequence[Point]) -> float:
    if not pts:
        return 1.0
    xs, ys, zs = zip(*pts)
    return (
        math.sqrt(
            (max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2 + (max(zs) - min(zs)) ** 2
        )
        or 1.0
    )


def nn_recon_error(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 400) -> float:
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


def normalized_D(anchors: Sequence[Point], cloud: Sequence[Point], sample: int = 400) -> float:
    return nn_recon_error(anchors, cloud, sample) / bbox_diag(cloud)


def ablation_delta(
    candidates: List[Point], cloud: Sequence[Point], idx: int, base_err: float
) -> float:
    reduced = [c for i, c in enumerate(candidates) if i != idx]
    err = nn_recon_error(reduced, cloud, sample=300)
    return max(0.0, err - base_err)


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


def structural_confidence(pool: Sequence[dict]) -> Tuple[bool, str, dict]:
    if not pool:
        return False, "empty candidate pool", {"c_max": 0, "gini": 0.0}
    depths = [int(c.get("causal_depth", 0)) for c in pool]
    deltas = [float(c.get("delta_e", 0.0)) for c in pool]
    c_max = max(depths)
    g = _gini([d / 255.0 for d in depths])
    mean_de = sum(deltas) / len(deltas)
    max_de = max(deltas) if deltas else 0.0
    base_err = float(pool[0].get("base_err", 0.0))
    rel = max_de / base_err if base_err > 1e-12 else 0.0
    stats = {
        "c_max": c_max,
        "gini": g,
        "mean_delta_e": mean_de,
        "max_delta_e": max_de,
        "rel_max_delta": rel,
    }
    if rel < REL_MAX_DELTA_REJECT:
        return False, f"rel_max_ΔE={rel:.4f}<{REL_MAX_DELTA_REJECT} (ablation field degenerate)", stats
    if c_max < CMAX_REJECT and g < GINI_REJECT:
        return False, f"C_max={c_max}<{CMAX_REJECT} and Gini={g:.3f}<{GINI_REJECT}", stats
    if mean_de < 1e-9 and c_max < CMAX_REJECT:
        return False, f"mean ΔE≈0 and C_max={c_max}", stats
    return True, "ok", stats


def _build_ranked_pool(
    pts: Sequence[Point],
    *,
    grid: float = 0.35,
    pool_cap: int = 120,
    quiet: bool = False,
) -> List[dict]:
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
    pool = cands[: min(pool_cap, len(cands))]
    anchors = [c["pos"] for c in pool]
    base_err = nn_recon_error(anchors, pts, sample=300)

    for i in range(len(pool)):
        pool[i]["delta_e"] = ablation_delta(anchors, pts, i, base_err)
        pool[i]["base_err"] = base_err

    max_de = max(c["delta_e"] for c in pool) or 1.0
    for c in pool:
        ratio = max(0.0, min(1.0, c["delta_e"] / max_de))
        c["causal_depth"] = int(round(255 * ratio))
        c["score"] = (
            0.25 * c["density"]
            + 0.25 * min(1.0, c["curvature"] * 2.0)
            + 0.50 * ratio
        )
    pool.sort(key=lambda x: x["score"], reverse=True)

    if not quiet:
        print(f"Ablation pool: {len(pool)}  E_full={base_err:.6f}  maxΔE={max_de:.6f}")
    return pool


def _pool_to_nodes(selected: Sequence[dict]) -> List[SENode]:
    nodes: List[SENode] = []
    for i, c in enumerate(selected):
        nodes.append(
            SENode(
                i + 1,
                c["pos"],
                risk_state=1 if c["causal_depth"] >= 200 else 0,
                sub_system=0x10 if c["causal_depth"] >= 200 else 0x30,
                resonance_freq=1.0 + 0.05 * (i % 17),  # Profile-Defined Placeholder
                causal_depth=c["causal_depth"],
            )
        )
    return nodes


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
    del w_density, w_curvature, w_ablation
    pool = _build_ranked_pool(pts, grid=grid, pool_cap=max(120, max_nodes), quiet=quiet)
    ok, reason, stats = structural_confidence(pool)
    if not ok and not quiet:
        print(f"WARNING structural confidence low: {reason} stats={stats}")
    selected = pool[:max_nodes]
    if not quiet:
        print(f"Selected |S|={len(selected)} (fixed top-k)")
        n_anchor = sum(1 for c in selected if c["causal_depth"] >= 200)
        print(f"High-Causal-Depth Anchors (C≥200): {n_anchor}")
    return _pool_to_nodes(selected)


def extract_se_epsilon_minimal(
    pts: Sequence[Point],
    *,
    epsilon: float = 0.08,
    grid: float = 0.35,
    pool_cap: int = 120,
    quiet: bool = False,
) -> Tuple[Optional[List[SENode]], dict]:
    pool = _build_ranked_pool(pts, grid=grid, pool_cap=pool_cap, quiet=quiet)
    ok, reason, conf = structural_confidence(pool)
    report: dict = {
        "epsilon": epsilon,
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
            print(report["message"])
        return None, report

    working = list(pool)

    def D_of(sel: Sequence[dict]) -> float:
        return normalized_D([c["pos"] for c in sel], pts, sample=350)

    d0 = D_of(working)
    if d0 > epsilon:
        report["n_star"] = len(working)
        report["final_D"] = d0
        report["status"] = "EPSILON_INFEASIBLE_FULL_POOL"
        if not quiet:
            print(f"Target ε={epsilon:.4f} | full pool D={d0:.4f} > ε — cannot meet budget")
        return _pool_to_nodes(working), report

    while len(working) > 1:
        trial = working[:-1]
        if D_of(trial) > epsilon:
            break
        working = trial

    final_d = D_of(working)
    report["n_star"] = len(working)
    report["final_D"] = final_d
    report["status"] = "EPSILON_MINIMAL"
    if not quiet:
        print(
            f"Target Epsilon (ε): {epsilon:.3f} | "
            f"Discovered Minimal Independent Nodes N*(ε): {len(working)} | "
            f"Final Reconstruction Error D: {final_d:.4f}"
        )
        n_anchor = sum(1 for c in working if c["causal_depth"] >= 200)
        print(f"High-Causal-Depth Anchors in S*(ε): {n_anchor}")
    return _pool_to_nodes(working), report


def main() -> None:
    ap = argparse.ArgumentParser(description="P-LOD horizon / ε-minimal SE extraction")
    ap.add_argument("--epsilon", type=float, default=None, help="ε-minimal search (e.g. 0.08)")
    ap.add_argument("--max-nodes", type=int, default=80)
    ap.add_argument("--max-pool", type=int, default=120)
    ap.add_argument("--points", type=int, default=10_000)
    args = ap.parse_args()

    pts = generate_volume(args.points)
    raw = len(pts) * 24 + 64

    if args.epsilon is not None:
        nodes, report = extract_se_epsilon_minimal(
            pts, epsilon=args.epsilon, pool_cap=args.max_pool
        )
        if nodes is None:
            print()
            print("=== Horizon compression ===")
            print("STATUS: STRUCTURAL_CONFIDENCE_LOW — no SE frame emitted")
            return
        frame = encode_frame(nodes, embodied=True, extended_meta=True)
        print()
        print("=== Horizon compression (ε-minimal S*) ===")
        print(f"Status:              {report.get('status')}")
        print(f"Raw dense estimate:  {raw:,} bytes")
        print(f"SE-Frame:            {len(frame):,} bytes")
        print(f"N*(ε):               {report.get('n_star')}")
        print(f"Final D:             {report.get('final_D', float('nan')):.4f}")
        print(f"Collapse ratio:      {raw / max(len(frame), 1):.1f}×")
        return

    nodes = extract_se_ablation(pts, max_nodes=args.max_nodes, quiet=False)
    frame = encode_frame(nodes, embodied=True, extended_meta=True)
    print()
    print("=== Horizon compression (fixed top-k) ===")
    print(f"Raw dense estimate:  {raw:,} bytes ({raw/1024:.1f} KB)")
    print(f"SE-Frame:            {len(frame):,} bytes ({len(frame)/1024:.2f} KB)")
    print(f"Collapse ratio:      {raw / max(len(frame), 1):.1f}×")
    print()
    print("S* = arg min |S|  s.t.  D(X, G(S)) ≤ ε")
    print("Use --epsilon 0.08 for dynamic N*(ε) search.")


if __name__ == "__main__":
    main()
