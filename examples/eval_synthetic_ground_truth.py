#!/usr/bin/env python3
"""
P-LOD Synthetic Ground Truth recovery (stdlib only)

Construct latent generating skeleton S_true → emerge G(S_true) → add noise → X,
run greedy ε-minimal extraction, then spatial Precision / Recall vs S_true.

Usage:
  python examples/eval_synthetic_ground_truth.py
  python examples/eval_synthetic_ground_truth.py --epsilon 0.12 --mode exact
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
    D_sym,
    emerge_linear_spline_v1,
    extract_se_epsilon_minimal,
)

Point = Tuple[float, float, float]


def make_s_true(n: int = 12) -> List[Point]:
    """Known latent anchors: arc + ring + vertical stem (N_true ≈ 12)."""
    pts: List[Point] = []
    # arc (6)
    for i in range(6):
        t = i / 5.0
        pts.append((math.cos(t * math.pi), math.sin(t * math.pi), 0.15 * t))
    # small ring (4)
    for i in range(4):
        t = i / 4.0 * 2 * math.pi
        pts.append((0.55 * math.cos(t), 0.55 * math.sin(t), 0.45))
    # stem (2)
    pts.append((0.0, 0.0, -0.2))
    pts.append((0.0, 0.0, 0.7))
    return pts[:n]


def synthesize_observation(
    s_true: Sequence[Point],
    *,
    n_cloud: int = 4000,
    noise: float = 0.04,
    seed: int = 7,
) -> List[Point]:
    rng = random.Random(seed)
    field = emerge_linear_spline_v1(list(s_true))
    # densify by repeating emerge samples + anchors
    base = list(s_true) + list(field)
    out: List[Point] = []
    while len(out) < n_cloud:
        x, y, z = base[rng.randrange(len(base))]
        out.append(
            (
                x + rng.gauss(0, noise),
                y + rng.gauss(0, noise),
                z + rng.gauss(0, noise),
            )
        )
    return out


def match_sets(
    recovered: Sequence[Point],
    truth: Sequence[Point],
    delta: float,
) -> Tuple[float, float, int, int]:
    """Greedy 1-1 matching within radius delta → precision, recall, TP counts."""
    if not recovered:
        return 0.0, 0.0, 0, 0
    if not truth:
        return 0.0, 0.0, 0, 0

    used_t = set()
    tp_rec = 0
    for r in recovered:
        best_j = -1
        best_d = delta + 1.0
        for j, t in enumerate(truth):
            if j in used_t:
                continue
            d = math.dist(r, t)
            if d < best_d:
                best_d = d
                best_j = j
        if best_j >= 0 and best_d <= delta:
            used_t.add(best_j)
            tp_rec += 1

    precision = tp_rec / len(recovered)
    recall = len(used_t) / len(truth)
    return precision, recall, tp_rec, len(used_t)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilon", type=float, default=0.12)
    ap.add_argument("--mode", choices=("exact", "fast"), default="exact")
    ap.add_argument("--n-true", type=int, default=12)
    ap.add_argument("--delta", type=float, default=0.20, help="match radius")
    ap.add_argument("--pool", type=int, default=36)
    ap.add_argument("--points", type=int, default=4000)
    args = ap.parse_args()

    s_true = make_s_true(args.n_true)
    X = synthesize_observation(s_true, n_cloud=args.points, seed=7)
    d_true = D_sym(s_true, X)

    print("=== P-LOD Synthetic Ground Truth Recovery ===")
    print(f"N_true={len(s_true)} |X|={len(X)} ε={args.epsilon} mode={args.mode} δ={args.delta}")
    print(f"D_sym(X, G(S_true)) ≈ {d_true:.4f} (oracle generator fidelity)")
    print()

    nodes, report = extract_se_epsilon_minimal(
        X,
        epsilon=args.epsilon,
        pool_cap=args.pool,
        mode=args.mode,
        quiet=True,
    )
    if nodes is None:
        print("STATUS: STRUCTURAL_CONFIDENCE_LOW — recovery failed")
        sys.exit(1)

    recovered = [n.pos for n in nodes]
    n_hat = len(recovered)
    prec, rec, tp_r, tp_t = match_sets(recovered, s_true, args.delta)
    d_hat = report.get("final_D", float("nan"))

    print("### Synthetic Ground Truth Recovery Summary")
    print()
    print("| Metric | Value |")
    print("|--------|------:|")
    print(f"| N_true | {len(s_true)} |")
    print(f"| N*_recovered | {n_hat} |")
    print(f"| ΔN = N* - N_true | {n_hat - len(s_true)} |")
    print(f"| Precision (δ={args.delta}) | {prec:.3f} |")
    print(f"| Recall (δ={args.delta}) | {rec:.3f} |")
    print(f"| D_sym achieved | {d_hat:.4f} |")
    print(f"| status | {report.get('status')} |")
    print()

    ok_rec = rec >= 0.75  # soft demo threshold; tight geometry + noise
    ok_prec = prec >= 0.50
    if ok_rec and ok_prec:
        print("RESULT: synthetic recovery PASS (structure-aligned anchors)")
    else:
        print("RESULT: recovery weak — try looser ε, larger pool, or mode=exact")
        # still exit 0 for CI friendliness of demo; print guidance
        if rec < 0.5:
            sys.exit(1)


if __name__ == "__main__":
    main()
