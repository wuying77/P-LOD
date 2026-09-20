#!/usr/bin/env python3
"""
P-LOD ε → N*(ε) rate–distortion style sweep (stdlib only).

For each target ε, run greedy marginal elimination over P(X):
  S*_ε = arg min |S| ⊆ P(X)  s.t.  D_sym(X, G(S)) ≤ ε

Outputs Markdown table + docs/rate_distortion_curve.svg

Usage:
  python examples/eval_rate_distortion.py
  python examples/eval_rate_distortion.py --mode fast --points 4000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import extract_se_epsilon_minimal, generate_volume
from plod_spec_codec import encode_frame

# Coarse → fine tolerance grid
EPSILON_GRID = (0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05)


def write_svg(path: Path, rows: List[dict]) -> None:
    w, h, pad = 720, 420, 60
    xs = [r["epsilon"] for r in rows]
    ys = [r["n_star"] for r in rows]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = 0.0, max(max(ys), 1) * 1.15

    def sx(x: float) -> float:
        # larger ε on the left (easier → fewer nodes)
        return pad + (xmax - x) / (xmax - xmin or 1) * (w - 2 * pad)

    def sy(y: float) -> float:
        return h - pad - (y - ymin) / (ymax - ymin or 1) * (h - 2 * pad)

    poly = " ".join(f"{sx(r['epsilon']):.1f},{sy(r['n_star']):.1f}" for r in rows)
    circles = "\n".join(
        f'<circle cx="{sx(r["epsilon"]):.1f}" cy="{sy(r["n_star"]):.1f}" r="5" fill="#2563eb"/>'
        for r in rows
    )
    labels = "\n".join(
        f'<text x="{sx(r["epsilon"]):.1f}" y="{h - pad + 18}" text-anchor="middle" '
        f'font-size="11" fill="#334155">{r["epsilon"]}</text>'
        for r in rows
    )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="{w/2}" y="28" text-anchor="middle" font-size="16" font-family="sans-serif" fill="#0f172a">
    P-LOD ε → N*(ε): minimal independent degrees of freedom
  </text>
  <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#94a3b8"/>
  <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#94a3b8"/>
  <polyline fill="none" stroke="#3b82f6" stroke-width="2" points="{poly}"/>
  {circles}
  {labels}
  <text x="{w/2}" y="{h-12}" text-anchor="middle" font-size="12" fill="#475569">ε (looser → left)</text>
  <text x="16" y="{h/2}" text-anchor="middle" font-size="12" fill="#475569"
        transform="rotate(-90 16 {h/2})">N*(ε) skeleton size</text>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("exact", "fast"), default="fast")
    ap.add_argument("--points", type=int, default=5000)
    ap.add_argument("--pool", type=int, default=36)
    args = ap.parse_args()

    pts = generate_volume(args.points, seed=42)
    raw = len(pts) * 24 + 64
    rows: List[dict] = []

    print("=== P-LOD ε → N*(ε) sweep ===")
    print(f"|X|={args.points} |P|≤{args.pool} mode={args.mode} G=linear_spline.v1 D=D_sym")
    print()
    print("| ε | N*(ε) | D_sym | SE-Frame (B) | status |")
    print("|----:|------:|------:|-------------:|--------|")

    for eps in EPSILON_GRID:
        nodes, report = extract_se_epsilon_minimal(
            pts,
            epsilon=eps,
            pool_cap=args.pool,
            mode=args.mode,
            quiet=True,
        )
        if nodes is None:
            print(f"| {eps:.2f} |  —  |  —  |  —  | REJECT |")
            continue
        frame = encode_frame(nodes, embodied=True, extended_meta=True)
        n_star = report.get("n_star", len(nodes))
        d = report.get("final_D", float("nan"))
        status = report.get("status", "?")
        print(f"| {eps:.2f} | {n_star:5d} | {d:6.4f} | {len(frame):11d} | {status} |")
        rows.append(
            {
                "epsilon": eps,
                "n_star": n_star,
                "d_sym": d,
                "bytes": len(frame),
                "status": status,
            }
        )

    if rows:
        svg_path = _ROOT / "docs" / "rate_distortion_curve.svg"
        write_svg(svg_path, rows)
        print()
        print(f"Wrote {svg_path}")
        print(f"Raw dense ~ {raw:,} B")
    print()
    print("RESULT: ε → N*(ε) table emitted")


if __name__ == "__main__":
    main()
