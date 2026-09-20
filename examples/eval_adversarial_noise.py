#!/usr/bin/env python3
"""
P-LOD Adversarial / Degeneracy Benchmark (stdlib only)

Case A — Structured geometry + ambient noise: expect higher Gini of ΔE ranks,
         more High-Causal-Depth Anchors in a relative sense.
Case B — Pure Gaussian-like scatter: flatter ΔE mass (lower Gini), few C_i≥200.

Note: C_i is *relative* (normalized by max_j ΔE_j). On pure noise, max C can still
be 255 for the least-irrelevant candidate even when absolute ΔE is tiny. The
contrast is Gini / fraction of high anchors / structured vs noise ranking mass.

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
    rng = random.Random(seed)
    pts: List[Point] = []
    while len(pts) < n:
        u1 = max(rng.random(), 1e-12)
        u2 = rng.random()
        r = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2
        x = 0.5 * r * math.cos(theta)
        y = 0.5 * r * math.sin(theta)
        u3 = max(rng.random(), 1e-12)
        u4 = rng.random()
        r2 = math.sqrt(-2.0 * math.log(u3))
        z = 0.25 * r2 * math.cos(2.0 * math.pi * u4)
        pts.append((x, y, z))
    return pts


def gini(values: Sequence[float]) -> float:
    xs = sorted(max(0.0, float(v)) for v in values)
    n = len(xs)
    if n == 0:
        return 0.0
    s = sum(xs)
    if s <= 1e-15:
        return 0.0
    acc = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * acc) / (n * s) - (n + 1.0) / n


def entropy_norm(values: Sequence[float]) -> float:
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
    masses = [d / 255.0 for d in depths]
    n_high = sum(1 for d in depths if d >= 200)
    return {
        "name": name,
        "n_pts": len(pts),
        "n_se": len(nodes),
        "n_high": n_high,
        "depth_max": max(depths) if depths else 0,
        "depth_mean": sum(depths) / max(len(depths), 1),
        "gini": gini(masses),
        "entropy": entropy_norm(masses),
        "frac_high": n_high / max(len(nodes), 1),
    }


def main() -> None:
    print("=== P-LOD Adversarial Degeneracy Benchmark ===")
    print("High-Causal-Depth Anchor: C_i ≥ 200 (relative rank under max-normalized ΔE)")
    print("ε-essential = absolute (Spec §0); this script contrasts relative ΔE geometry.")
    print()

    a = analyze_case("Case A: Structured + ambient scatter", generate_volume(10_000, seed=42))
    b = analyze_case("Case B: Pure Gaussian-like noise", pure_noise_cloud(10_000, seed=99))

    print("### Ablation Contrast Table")
    print()
    print("| Case | |X| | |S| | C≥200 | max C | mean C | Gini | H_norm |")
    print("|------|----:|----:|------:|------:|-------:|-----:|-------:|")
    for r in (a, b):
        print(
            f"| {r['name'][:36]:36s} | {r['n_pts']:5d} | {r['n_se']:4d} | "
            f"{r['n_high']:5d} | {r['depth_max']:5d} | {r['depth_mean']:6.1f} | "
            f"{r['gini']:5.3f} | {r['entropy']:6.3f} |"
        )
    print()
    print(
        "Note: pure-noise max C can still hit 255 (relative scale); "
        "look at Gini and C≥200 fraction for degeneracy."
    )
    print()

    ok_struct = a["n_high"] >= 1
    ok_noise = b["frac_high"] <= 0.15
    ok_contrast = a["gini"] > b["gini"] or a["n_high"] > b["n_high"]

    print("Checks:")
    print(f"  structured High-Causal-Depth Anchors: {'PASS' if ok_struct else 'WEAK'}")
    print(f"  pure-noise C≥200 fraction ≤ 15%:       {'PASS' if ok_noise else 'FAIL'} "
          f"(frac={b['frac_high']:.2%})")
    print(f"  structured vs noise Gini/anchor contrast: {'PASS' if ok_contrast else 'FAIL'}")
    print()
    if ok_struct and ok_noise and ok_contrast:
        print("RESULT: adversarial degeneracy contrast PASS")
    else:
        print("RESULT: contrast weak")
        sys.exit(1)


if __name__ == "__main__":
    main()
