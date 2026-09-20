#!/usr/bin/env python3
"""
P-LOD Adversarial / Degeneracy Benchmark (stdlib only)

Case A — Structured geometry + ambient noise: expect High-Causal-Depth Anchors (C_i ≥ 200).
Case B — Pure Gaussian-like scatter (Box–Muller): expect ΔE ≈ 0 hierarchy, almost no C_i ≥ 200.

Supports Spec §0 Adversarial Degeneracy Criterion:
  under unstructured noise, causal depth collapses → no spurious ε-essential topology.

Usage:
  python examples/eval_adversarial_noise.py
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

from horizon_compression_demo import extract_se_ablation, generate_volume

Point = Tuple[float, float, float]


def pure_noise_cloud(n: int = 10_000, seed: int = 99) -> List[Point]:
    """i.i.d. approximately Gaussian points in a box (Box–Muller), no planted topology."""
    rng = random.Random(seed)
    pts: List[Point] = []
    while len(pts) < n:
        u1, u2 = rng.random(), rng.random()
        u1 = max(u1, 1e-12)
        r = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2
        x = 0.5 * r * math.cos(theta)
        y = 0.5 * r * math.sin(theta)
        u3, u4 = rng.random(), rng.random()
        u3 = max(u3, 1e-12)
        r2 = math.sqrt(-2.0 * math.log(u3))
        z = 0.25 * r2 * math.cos(2.0 * math.pi * u4)
        pts.append((x, y, z))
    return pts


def gini(values: Sequence[float]) -> float:
    """Gini coefficient of non-negative values; 0 = equal, 1 = maximally unequal."""
    xs = sorted(max(0.0, float(v)) for v in values)
    n = len(xs)
    if n == 0:
        return 0.0
    s = sum(xs)
    if s <= 1e-15:
        return 0.0
    # sum i*x_i with 1-based rank
    acc = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * acc) / (n * s) - (n + 1.0) / n

def entropy_norm(values: Sequence[float]) -> float:
    """Normalized Shannon entropy of a non-negative mass (0..1)."""
    xs = [max(0.0, float(v)) for v in values]
    s = sum(xs)
    if s <= 1e-15:
        return 0.0
    h = 0.0
    for x in xs:
        if x <= 0:
            continue
        p = x / s
        h -= p * math.log(p + 1e-15)
    hmax = math.log(len(xs)) if len(xs) > 1 else 1.0
    return h / hmax if hmax > 0 else 0.0


def analyze_case(name: str, pts: Sequence[Point], max_nodes: int = 64) -> dict:
    nodes = extract_se_ablation(pts, max_nodes=max_nodes, grid=0.35, quiet=True)
    depths = [n.causal_depth for n in nodes]
    # Approximate ΔE ranking mass from causal_depth (already ΔE-normalized × 255)
    masses = [d / 255.0 for d in depths]
    n_high = sum(1 for d in depths if d >= 200)
    return {
        "name": name,
        "n_pts": len(pts),
        "n_se": len(nodes),
        "n_high": n_high,
        "depth_min": min(depths) if depths else 0,
        "depth_max": max(depths) if depths else 0,
        "depth_mean": sum(depths) / max(len(depths), 1),
        "gini": gini(masses),
        "entropy": entropy_norm(masses),
        "frac_high": n_high / max(len(nodes), 1),
    }


def main() -> None:
    print("=== P-LOD Adversarial Degeneracy Benchmark ===")
    print("High-Causal-Depth Anchor: C_i ≥ 200 (relative rank)")
    print("Expect: structured → high Gini / more C_i≥200; pure noise → flat ΔE / few anchors")
    print()

    structured = generate_volume(10_000, seed=42)
    noise = pure_noise_cloud(10_000, seed=99)

    a = analyze_case("Case A: Structured geometry + ambient scatter", structured)
    b = analyze_case("Case B: Pure Gaussian-like noise (no topology)", noise)

    print("### Ablation Contrast Table")
    print()
    print("| Case | |X| | |S| | C≥200 | max C | mean C | Gini(ΔE) | H_norm |")
    print("|------|----:|----:|------:|------:|-------:|---------:|-------:|")
    for r in (a, b):
        print(
            f"| {r['name'][:42]:42s} | {r['n_pts']:5d} | {r['n_se']:4d} | "
            f"{r['n_high']:5d} | {r['depth_max']:5d} | {r['depth_mean']:6.1f} | "
            f"{r['gini']:8.3f} | {r['entropy']:6.3f} |"
        )
    print()

    # Soft assertions (demo thresholds; not CI-hard gates)
    ok_struct = a["n_high"] >= 1 and a["gini"] > b["gini"]
    ok_noise = b["frac_high"] <= 0.15  # pure noise should not mint many high anchors
    ok_contrast = a["gini"] - b["gini"] > 0.02 or a["n_high"] > b["n_high"]

    print("Checks:")
    print(f"  structured produces High-Causal-Depth Anchors: {'PASS' if a['n_high'] >= 1 else 'WEAK'}")
    print(f"  pure-noise high-anchor fraction ≤ 15%:          {'PASS' if ok_noise else 'FAIL'} "
          f"(frac={b['frac_high']:.2%})")
    print(f"  structured vs noise contrast (Gini / anchors):  {'PASS' if ok_contrast else 'FAIL'}")
    print()
    if ok_struct and ok_noise and ok_contrast:
        print("RESULT: adversarial degeneracy contrast PASS")
        print("(P-LOD does not invent strong causal anchors in pure unstructured noise.)")
    else:
        print("RESULT: contrast weak — inspect grid/extractor heuristics")
        sys.exit(1)


if __name__ == "__main__":
    main()
