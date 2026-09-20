#!/usr/bin/env python3
"""
P-LOD Synthetic Ground Truth recovery (stdlib only)

Pipeline:
  1) Build latent S_true (known generating anchors)
  2) X = G(S_true) + noise
  3) P = S_true ∪ distractors (tests dynamic marginal elimination)
  4) Greedy marginal elimination under D(X, G(S))
  5) Spatial Precision / Recall vs S_true

Usage:
  python examples/eval_synthetic_ground_truth.py
  python examples/eval_synthetic_ground_truth.py --mode exact --epsilon 0.08
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import (
    D_of,
    D_sym,
    emerge_linear_spline_v1,
    greedy_marginal_elimination,
    rank_by_ablation,
)

Point = Tuple[float, float, float]


def make_s_true(n: int = 12) -> List[Point]:
    pts: List[Point] = []
    for i in range(6):
        t = i / 5.0
        pts.append((math.cos(t * math.pi), math.sin(t * math.pi), 0.15 * t))
    for i in range(4):
        t = i / 4.0 * 2 * math.pi
        pts.append((0.55 * math.cos(t), 0.55 * math.sin(t), 0.45))
    pts.append((0.0, 0.0, -0.2))
    pts.append((0.0, 0.0, 0.7))
    return pts[:n]


def synthesize_observation(
    s_true: Sequence[Point],
    *,
    n_cloud: int = 4000,
    noise: float = 0.03,
    seed: int = 7,
) -> List[Point]:
    rng = random.Random(seed)
    field = emerge_linear_spline_v1(list(s_true))
    base = list(s_true) + list(field)
    out: List[Point] = []
    while len(out) < n_cloud:
        x, y, z = base[rng.randrange(len(base))]
        out.append((x + rng.gauss(0, noise), y + rng.gauss(0, noise), z + rng.gauss(0, noise)))
    return out


def make_pool_with_truth(
    s_true: Sequence[Point],
    *,
    n_distractors: int = 20,
    seed: int = 11,
) -> List[dict]:
    rng = random.Random(seed)
    pool: List[dict] = []
    for p in s_true:
        pool.append({"pos": p, "density": 1.0, "curvature": 0.5, "pre": 1.0, "is_true": True})
    for _ in range(n_distractors):
        pool.append(
            {
                "pos": (
                    rng.uniform(-1.8, 1.8),
                    rng.uniform(-1.8, 1.8),
                    rng.uniform(-0.8, 1.0),
                ),
                "density": 0.2,
                "curvature": 0.1,
                "pre": 0.15,
                "is_true": False,
            }
        )
    return pool


def match_sets(
    recovered: Sequence[Point], truth: Sequence[Point], delta: float
) -> Tuple[float, float]:
    if not recovered or not truth:
        return 0.0, 0.0
    used = set()
    tp = 0
    for r in recovered:
        best_j, best_d = -1, delta + 1.0
        for j, t in enumerate(truth):
            if j in used:
                continue
            d = math.dist(r, t)
            if d < best_d:
                best_d, best_j = d, j
        if best_j >= 0 and best_d <= delta:
            used.add(best_j)
            tp += 1
    return tp / len(recovered), len(used) / len(truth)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilon", type=float, default=0.08)
    ap.add_argument("--mode", choices=("exact", "fast"), default="fast")
    ap.add_argument("--n-true", type=int, default=12)
    ap.add_argument("--distractors", type=int, default=18)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--points", type=int, default=2500)
    args = ap.parse_args()

    s_true = make_s_true(args.n_true)
    X = synthesize_observation(s_true, n_cloud=args.points, seed=7)
    d_true = D_sym(s_true, X)

    pool = make_pool_with_truth(s_true, n_distractors=args.distractors)
    pool = rank_by_ablation(pool, X, args.mode)

    print("=== P-LOD Synthetic Ground Truth Recovery ===")
    print(
        f"N_true={len(s_true)} distractors={args.distractors} |X|={len(X)} "
        f"ε={args.epsilon} mode={args.mode} δ={args.delta}"
    )
    print(f"D_sym(X, G(S_true)) ≈ {d_true:.4f}")
    print()

    d_full = D_of([c["pos"] for c in pool], X, args.mode)
    if d_full > args.epsilon:
        print(f"Note: full P D={d_full:.4f} > ε — elimination only if intermediate D ≤ ε")

    kept, final_d = greedy_marginal_elimination(pool, X, args.epsilon, args.mode)
    recovered = [c["pos"] for c in kept]
    n_true_kept = sum(1 for c in kept if c.get("is_true"))
    prec, rec = match_sets(recovered, s_true, args.delta)

    print("### Synthetic Ground Truth Recovery Summary")
    print()
    print("| Metric | Value |")
    print("|--------|------:|")
    print(f"| N_true | {len(s_true)} |")
    print(f"| N*_recovered | {len(recovered)} |")
    print(f"| True anchors kept (flag) | {n_true_kept} |")
    print(f"| Precision (δ={args.delta}) | {prec:.3f} |")
    print(f"| Recall (δ={args.delta}) | {rec:.3f} |")
    print(f"| D achieved | {final_d:.4f} |")
    print()

    ok = rec >= 0.80 and prec >= 0.85
    if ok:
        print("RESULT: synthetic recovery PASS (latent generating structure recovered)")
    else:
        print("RESULT: recovery below target — try --mode exact or adjust ε/δ")
        if rec < 0.5 or prec < 0.4:
            sys.exit(1)


if __name__ == "__main__":
    main()
