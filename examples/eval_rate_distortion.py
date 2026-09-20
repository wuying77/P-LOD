#!/usr/bin/env python3
"""
P-LOD Rate–Distortion evaluation (stdlib only).

Sweeps |S| = N_SE ∈ {4,8,16,32,64,128,256} on a high-entropy point cloud X,
extracts ablation-ranked SE skeleton, emerges via plod.ref.linear_spline.v1,
and reports frame bytes vs Chamfer distortion D(X, G(S)).

Objective (Spec):
  S* = arg min |S|  s.t.  D(X, G(S)) ≤ ε

Outputs:
  - Markdown rate–distortion table (stdout)
  - docs/rate_distortion_curve.svg (always)
  - docs/rate_distortion_curve.png (if matplotlib available)

Usage:
  python examples/eval_rate_distortion.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from horizon_compression_demo import extract_se_ablation, generate_volume
from plod_metrics import bbox_diagonal, chamfer_distance, reconstruction_fidelity_score
from plod_spec_codec import SENode, encode_frame
from reference_emergence_engine import emerge_v1

Point = Tuple[float, float, float]

N_SE_GRID = (4, 8, 16, 32, 64, 128, 256)


def emerge_and_recon(nodes: Sequence[SENode]) -> List[Point]:
    anchors = [n.pos for n in nodes]
    emerged = emerge_v1(list(nodes))
    return list(anchors) + list(emerged)


def write_svg(path: Path, rows: List[dict]) -> None:
    """Minimal SVG scatter+polyline for N_SE vs normalized Chamfer (no deps)."""
    w, h, pad = 720, 420, 60
    xs = [r["n_se"] for r in rows]
    ys = [r["cd_norm"] for r in rows]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = 0.0, max(max(ys), 1e-6)
    # pad y a bit
    ymax = ymax * 1.15 if ymax > 0 else 1.0

    def sx(x: float) -> float:
        return pad + (x - xmin) / (xmax - xmin or 1) * (w - 2 * pad)

    def sy(y: float) -> float:
        return h - pad - (y - ymin) / (ymax - ymin or 1) * (h - 2 * pad)

    poly = " ".join(f"{sx(r['n_se']):.1f},{sy(r['cd_norm']):.1f}" for r in rows)
    circles = "\n".join(
        f'<circle cx="{sx(r["n_se"]):.1f}" cy="{sy(r["cd_norm"]):.1f}" r="5" fill="#2563eb"/>'
        for r in rows
    )
    labels = "\n".join(
        f'<text x="{sx(r["n_se"]):.1f}" y="{h - pad + 18}" text-anchor="middle" '
        f'font-size="11" fill="#334155">{r["n_se"]}</text>'
        for r in rows
    )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="{w/2}" y="28" text-anchor="middle" font-size="16" font-family="sans-serif" fill="#0f172a">
    P-LOD Rate–Distortion: |S| vs normalized Chamfer D(X, G(S))
  </text>
  <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#94a3b8"/>
  <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#94a3b8"/>
  <polyline fill="none" stroke="#3b82f6" stroke-width="2" points="{poly}"/>
  {circles}
  {labels}
  <text x="{w/2}" y="{h-12}" text-anchor="middle" font-size="12" fill="#475569">N_SE (minimal independent skeleton size)</text>
  <text x="16" y="{h/2}" text-anchor="middle" font-size="12" fill="#475569"
        transform="rotate(-90 16 {h/2})">normalized Chamfer (lower is better)</text>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def try_write_png(path: Path, rows: List[dict]) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = [r["n_se"] for r in rows]
    ys = [r["cd_norm"] for r in rows]
    ax.plot(xs, ys, "o-", color="#2563eb", linewidth=2, markersize=7)
    ax.set_xscale("log", base=2)
    ax.set_xlabel(r"$N_{SE} = |S|$ (SE nodes)")
    ax.set_ylabel(r"normalized Chamfer $D(X,G(S))$")
    ax.set_title("P-LOD Rate–Distortion Curve")
    ax.grid(True, which="both", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return True


def main() -> None:
    print("=== P-LOD Rate–Distortion Sweep ===")
    print("Objective:  S* = arg min |S|  s.t.  D(X, G(S)) ≤ ε")
    print("Emergence:  plod.ref.linear_spline.v1")
    print()

    cloud = generate_volume(10_000, seed=42)
    raw_bytes = len(cloud) * 24 + 64
    diag = bbox_diagonal(cloud)
    print(f"|X| = {len(cloud):,} points   raw≈{raw_bytes:,} B   bbox_diag={diag:.4f}")
    print()

    rows: List[dict] = []
    for n_se in N_SE_GRID:
        # Suppress verbose ablation prints by temporarily patching print? keep brief:
        print(f"--- N_SE = {n_se} ---")
        nodes = extract_se_ablation(cloud, max_nodes=n_se, grid=0.35)
        # extract prints details; acceptable for demo
        frame = encode_frame(nodes, embodied=True, extended_meta=True)
        recon = emerge_and_recon(nodes)
        rfs, cd, cd_norm = reconstruction_fidelity_score(cloud, recon)
        cr = raw_bytes / max(len(frame), 1)
        rows.append(
            {
                "n_se": n_se,
                "bytes": len(frame),
                "cd": cd,
                "cd_norm": cd_norm,
                "rfs": rfs,
                "cr": cr,
            }
        )

    print()
    print("### Rate–Distortion Table")
    print()
    print("| N_SE | SE-Frame (B) | Compression | Chamfer D | D/diag | RFS |")
    print("|-----:|-------------:|------------:|----------:|------:|----:|")
    for r in rows:
        print(
            f"| {r['n_se']:5d} | {r['bytes']:12d} | {r['cr']:10.1f}× | "
            f"{r['cd']:9.6f} | {r['cd_norm']:5.4f} | {r['rfs']:.4f} |"
        )
    print()

    svg_path = _ROOT / "docs" / "rate_distortion_curve.svg"
    write_svg(svg_path, rows)
    print(f"Wrote {svg_path.relative_to(_ROOT)}")

    png_path = _ROOT / "docs" / "rate_distortion_curve.png"
    if try_write_png(png_path, rows):
        print(f"Wrote {png_path.relative_to(_ROOT)} (matplotlib)")
    else:
        print("PNG skipped (matplotlib not installed); SVG is the canonical curve artifact.")

    # Highlight knee: first N where cd_norm < 0.08 if any
    knee = next((r for r in rows if r["cd_norm"] <= 0.08), rows[-1])
    print()
    print(
        f"Illustrative operating point: N_SE={knee['n_se']} → "
        f"{knee['bytes']} B, D/diag={knee['cd_norm']:.4f}, RFS={knee['rfs']:.4f}"
    )


if __name__ == "__main__":
    main()
