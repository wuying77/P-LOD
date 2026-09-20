#!/usr/bin/env python3
"""P-LOD Synthetic Ground-Truth Recovery + Candidate Diagnostics (stdlib only)."""
from __future__ import annotations
import argparse, math, random, sys
from pathlib import Path
from typing import List, Sequence, Tuple
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from horizon_compression_demo import D_of, D_sym, greedy_marginal_elimination, rank_by_ablation
from reference_emergence_engine import emerge_v1
from plod_spec_codec import SENode
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

def synthesize_observation(s_true, *, n_cloud=2500, noise=0.03, seed=7):
    rng = random.Random(seed)
    nodes = [SENode(i + 1, p) for i, p in enumerate(s_true)]
    field = list(s_true) + list(emerge_v1(nodes))
    out = []
    while len(out) < n_cloud:
        x, y, z = field[rng.randrange(len(field))]
        out.append((x + rng.gauss(0, noise), y + rng.gauss(0, noise), z + rng.gauss(0, noise)))
    return out

def make_pool(s_true, n_distractors=18, seed=11):
    rng = random.Random(seed)
    pool = [{"pos": p, "density": 1.0, "curvature": 0.5, "pre": 1.0, "is_true": True} for p in s_true]
    for _ in range(n_distractors):
        pool.append({"pos": (rng.uniform(-1.8, 1.8), rng.uniform(-1.8, 1.8), rng.uniform(-0.8, 1.0)),
                     "density": 0.2, "curvature": 0.1, "pre": 0.15, "is_true": False})
    return pool

def match_count(a, b, delta):
    used, tp = set(), 0
    for p in a:
        best_j, best_d = -1, delta + 1.0
        for j, q in enumerate(b):
            if j in used: continue
            d = math.dist(p, q)
            if d < best_d: best_d, best_j = d, j
        if best_j >= 0 and best_d <= delta:
            used.add(best_j); tp += 1
    return tp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epsilon", type=float, default=0.08)
    ap.add_argument("--mode", choices=("exact", "fast"), default="exact")
    ap.add_argument("--n-true", type=int, default=12)
    ap.add_argument("--distractors", type=int, default=18)
    ap.add_argument("--delta", type=float, default=0.15)
    ap.add_argument("--points", type=int, default=2500)
    args = ap.parse_args()
    s_true = make_s_true(args.n_true)
    X = synthesize_observation(s_true, n_cloud=args.points)
    pool = make_pool(s_true, n_distractors=args.distractors)
    r_p = match_count(s_true, [c["pos"] for c in pool], args.delta) / max(len(s_true), 1)
    pool = rank_by_ablation(pool, X, args.mode)
    kept, final_d = greedy_marginal_elimination(pool, X, args.epsilon, args.mode)
    recovered = [c["pos"] for c in kept]
    tp_hat = match_count(recovered, s_true, args.delta)
    tp_true = match_count(s_true, recovered, args.delta)
    prec = tp_hat / max(len(recovered), 1)
    rec = tp_true / max(len(s_true), 1)
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    print("=== P-LOD Ground-Truth Recovery & Candidate Diagnostics ===")
    print(f"N_true={len(s_true)} distractors={args.distractors} |X|={len(X)} ε={args.epsilon} mode={args.mode}")
    print(f"D_sym(X, G(S_true)) ≈ {D_sym(s_true, X):.4f}")
    print()
    print("| Metric | Value |")
    print("|--------|------:|")
    print(f"| Candidate Recall R_P | {r_p:.3f} |")
    print(f"| N*_recovered | {len(recovered)} |")
    print(f"| Precision | {prec:.3f} |")
    print(f"| Recall | {rec:.3f} |")
    print(f"| F1 | {f1:.3f} |")
    print(f"| D_sym achieved | {final_d:.4f} |")
    print()
    ok = r_p >= 0.95 and f1 >= 0.80 and prec >= 0.70
    print("RESULT: Ground-Truth recovery PASS" if ok else "RESULT: below target thresholds")
    if f1 < 0.5: sys.exit(1)

if __name__ == "__main__":
    main()
