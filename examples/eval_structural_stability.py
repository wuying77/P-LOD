#!/usr/bin/env python3
"""
P-LOD Structural Stability (SS_i) across multi-seed runs (stdlib only)

Runs Stage A+B ε-minimal extraction on a fixed geometry with independent
perturbations / seeds, then estimates selection frequency:

  SS_i ≈ (# runs where a quantized cell near p_i is kept) / n_runs

High SS + high causal_depth → stable independent structure.

Usage:
  python examples/eval_structural_stability.py
  python examples/eval_structural_stability.py --runs 20 --epsilon 0.08 --mode exact
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import (
    extract_se_epsilon_minimal,
    generate_volume,
    perturb_cloud,
)


def quant_key(pos: Tuple[float, float, float], grid: float = 0.15) -> Tuple[int, int, int]:
    return (
        int(round(pos[0] / grid)),
        int(round(pos[1] / grid)),
        int(round(pos[2] / grid)),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--epsilon", type=float, default=0.08)
    ap.add_argument("--mode", choices=("exact", "fast"), default="fast")
    ap.add_argument("--points", type=int, default=4000)
    ap.add_argument("--pool", type=int, default=32)
    args = ap.parse_args()

    base = generate_volume(args.points, seed=42)
    counts: Counter = Counter()
    depth_sum: Dict[Tuple[int, int, int], float] = {}
    depth_n: Dict[Tuple[int, int, int], int] = {}
    n_ok = 0
    n_reject = 0
    n_sizes: List[int] = []

    print("=== P-LOD Structural Stability ===")
    print(f"runs={args.runs} ε={args.epsilon} mode={args.mode} |X|={args.points}")
    print()

    for r in range(args.runs):
        seed = 1000 + r
        cloud = perturb_cloud(base, seed=seed, sigma=0.025)
        nodes, report = extract_se_epsilon_minimal(
            cloud,
            epsilon=args.epsilon,
            pool_cap=args.pool,
            mode=args.mode,
            quiet=True,
        )
        if nodes is None:
            n_reject += 1
            continue
        n_ok += 1
        n_sizes.append(report.get("n_star", len(nodes)))
        for nd in nodes:
            k = quant_key(nd.pos)
            counts[k] += 1
            depth_sum[k] = depth_sum.get(k, 0.0) + nd.causal_depth
            depth_n[k] = depth_n.get(k, 0) + 1

    if n_ok == 0:
        print("All runs rejected (STRUCTURAL_CONFIDENCE_LOW).")
        sys.exit(1)

    rows = []
    for k, c in counts.items():
        ss = c / args.runs
        mean_c = depth_sum[k] / max(depth_n[k], 1)
        rows.append((ss, mean_c, c, k))
    rows.sort(reverse=True)

    print("### Structural Stability Summary")
    print()
    print(f"Successful runs: {n_ok}/{args.runs}  |  Rejected: {n_reject}")
    if n_sizes:
        print(
            f"N*(ε) mean={sum(n_sizes)/len(n_sizes):.1f}  "
            f"min={min(n_sizes)}  max={max(n_sizes)}"
        )
    print()
    print("| Rank | SS_i | mean C_i | hits | quant-key |")
    print("|-----:|-----:|---------:|-----:|-----------|")
    stable = 0
    for i, (ss, mean_c, hits, k) in enumerate(rows[:15], 1):
        flag = "*" if ss >= 0.90 else " "
        if ss >= 0.90:
            stable += 1
        print(f"| {i:4d} | {ss:5.2f}{flag}| {mean_c:8.1f} | {hits:4d} | {k} |")
    print()
    print(f"Nodes with SS_i ≥ 0.90: {stable}")
    print("(*) high cross-run stability under seed/perturbation")
    print()
    print("RESULT: structural stability table emitted")


if __name__ == "__main__":
    main()
