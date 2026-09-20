#!/usr/bin/env python3
"""
P-LOD Candidate Pool Sufficiency: N*(ε, K_pool) plateau (stdlib only)

Sweep K_pool and record |S*_ε| from greedy marginal elimination.
A stable plateau for larger K implies N* is driven by structure, not by cap.

Usage:
  python examples/eval_pool_sufficiency.py
  python examples/eval_pool_sufficiency.py --epsilon 0.12 --mode fast
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import extract_se_epsilon_minimal, generate_volume

K_GRID = (16, 24, 32, 40, 48, 64, 80)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilon", type=float, default=0.12)
    ap.add_argument("--mode", choices=("exact", "fast"), default="fast")
    ap.add_argument("--points", type=int, default=4000)
    args = ap.parse_args()

    cloud = generate_volume(args.points, seed=42)

    print("=== P-LOD Pool Sufficiency ===")
    print(f"ε={args.epsilon} mode={args.mode} |X|={args.points}")
    print()
    print("| K_pool | N*(ε) | D | status |")
    print("|-------:|------:|----:|--------|")

    rows = []
    for k in K_GRID:
        nodes, report = extract_se_epsilon_minimal(
            cloud,
            epsilon=args.epsilon,
            pool_cap=k,
            mode=args.mode,
            quiet=True,
        )
        if nodes is None:
            print(f"| {k:6d} |   —  |  —  | REJECT |")
            continue
        n_star = report.get("n_star", len(nodes))
        d = report.get("final_D", float("nan"))
        st = report.get("status", "?")
        print(f"| {k:6d} | {n_star:5d} | {d:.4f} | {st} |")
        rows.append((k, n_star, d, st))

    print()
    # crude plateau: last 3 finite N* within ±2 of their median
    sizes = [n for _, n, _, st in rows if st == "EPSILON_MINIMAL"]
    if len(sizes) >= 3:
        tail = sizes[-3:]
        med = sorted(tail)[1]
        if max(tail) - min(tail) <= 2:
            print(f"Plateau check (last 3 MINIMAL N*): {tail} ≈ {med} → STABLE")
        else:
            print(f"Plateau check (last 3 MINIMAL N*): {tail} → still moving")
    print("RESULT: pool sufficiency table emitted")


if __name__ == "__main__":
    main()
