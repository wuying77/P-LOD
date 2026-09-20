#!/usr/bin/env python3
"""
P-LOD Exhaustive Oracle vs Greedy Marginal Elimination (stdlib only)

On a small candidate pool |P| ∈ {10..14}, enumerate all 2^|P| subsets
that satisfy D_sym(X, G(S)) ≤ ε and take minimum |S| as the oracle.
Compare to greedy_marginal_elimination approximation ratio:

  ρ = |S_greedy| / |S_oracle|

Usage:
  python examples/eval_oracle_vs_greedy.py
  python examples/eval_oracle_vs_greedy.py --pool 12 --epsilon 0.15 --mode fast
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import (
    D_of,
    generate_volume,
    greedy_marginal_elimination,
    rank_by_ablation,
    stage_a_candidates,
)

Point = Tuple[float, float, float]


def exhaustive_oracle(
    pool: List[dict],
    cloud: Sequence[Point],
    epsilon: float,
    mode: str,
) -> Tuple[Optional[int], Optional[float], int]:
    """
    Return (min_size, best_D, n_feasible) over all non-empty subsets of pool.
    For |P|=12 → 4095 subsets (excluding empty).
    """
    n = len(pool)
    anchors = [c["pos"] for c in pool]
    best_size = None
    best_d = None
    feasible = 0
    # iterate masks 1 .. 2^n - 1
    for mask in range(1, 1 << n):
        sel = [anchors[i] for i in range(n) if mask & (1 << i)]
        d = D_of(sel, cloud, mode)
        if d <= epsilon:
            feasible += 1
            sz = len(sel)
            if best_size is None or sz < best_size or (sz == best_size and d < best_d):
                best_size = sz
                best_d = d
    return best_size, best_d, feasible


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=int, default=12, help="|P(X)| (≤14 recommended)")
    ap.add_argument("--epsilon", type=float, default=0.15)
    ap.add_argument("--mode", choices=("exact", "fast"), default="fast")
    ap.add_argument("--points", type=int, default=3000)
    args = ap.parse_args()

    if args.pool > 16:
        print("Refuse |P|>16 (2^16 exhaustive too heavy for stdlib demo).")
        sys.exit(2)

    cloud = generate_volume(args.points, seed=42)
    pool = stage_a_candidates(cloud, pool_cap=args.pool)
    pool = rank_by_ablation(pool, cloud, args.mode)

    print("=== P-LOD Exhaustive Oracle vs Greedy ===")
    print(f"|P|={len(pool)} ε={args.epsilon} mode={args.mode} |X|={args.points}")
    print(f"Exhaustive subsets: {2 ** len(pool) - 1}")
    print()

    # Greedy
    d_full = D_of([c["pos"] for c in pool], cloud, args.mode)
    if d_full > args.epsilon:
        print(f"Full pool D={d_full:.4f} > ε — no feasible skeleton in P(X)")
        print("RESULT: INFEASIBLE on this (P, ε)")
        return

    greedy_kept, greedy_d = greedy_marginal_elimination(
        list(pool), cloud, args.epsilon, args.mode
    )
    n_g = len(greedy_kept)

    # Oracle
    n_o, d_o, n_feas = exhaustive_oracle(pool, cloud, args.epsilon, args.mode)

    print("### Approximation Summary")
    print()
    print("| Method | |S*| | D | feasible subsets |")
    print("|--------|-----:|----:|-----------------:|")
    print(f"| Greedy marginal | {n_g:4d} | {greedy_d:.4f} | — |")
    if n_o is None:
        print("| Exhaustive oracle |  —  |  —  | 0 |")
        print()
        print("Oracle found no feasible subset (unexpected if greedy succeeded).")
        sys.exit(1)
    print(f"| Exhaustive oracle | {n_o:4d} | {d_o:.4f} | {n_feas} |")
    rho = n_g / max(n_o, 1)
    print()
    print(f"Approximation ratio ρ = |S_greedy| / |S_oracle| = {rho:.3f}")
    if rho <= 1.0 + 1e-9:
        print("RESULT: greedy matches oracle cardinality (ρ = 1)")
    elif rho <= 1.25:
        print("RESULT: greedy within 25% of oracle cardinality")
    else:
        print("RESULT: greedy gap > 25% — inspect ε / pool / mode")


if __name__ == "__main__":
    main()
