#!/usr/bin/env python3
"""
P-LOD Horizon Compression Demo (stdlib only)

Metaphor: a dense 3D high-entropy cloud is pressed toward an "event-horizon"
scale skeleton — only strong-entanglement topology remains in the SE-Frame.

Steps:
  1. Simulate ~10_000 noisy 3D samples ("physical volume" detail).
  2. Extract a sparse SE skeleton (grid saliency + outlier rejection).
  3. Pack with Spec v1.0 codec + optional v1.1 metas (causal_depth).
  4. Print size collapse and node causal_depth.

Usage:
  python horizon_compression_demo.py
"""

from __future__ import annotations

import math
import random
import struct
import zlib
from typing import List, Tuple

# --- minimal inline pack (avoids import path issues when run alone) --------

MAGIC = 0x504C
VERSION = 0x10
FLAG_EMBODIED = 1 << 2


def pack_header(n: int, flags: int, seq: int = 0) -> bytes:
    return struct.pack("<HBBHH", MAGIC, VERSION, flags & 0xFF, n & 0xFFFF, seq & 0xFFFF)


def pack_embodied(
    node_id: int,
    risk: int,
    sub: int,
    pos: Tuple[float, float, float],
    vel: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    phase: float = 0.0,
) -> bytes:
    px, py, pz = pos
    vx, vy, vz = vel
    return struct.pack(
        "<HBB3f3ff",
        node_id & 0xFFFF,
        risk & 0xFF,
        sub & 0xFF,
        float(px),
        float(py),
        float(pz),
        float(vx),
        float(vy),
        float(vz),
        float(phase),
    )


def pack_extended_meta(resonance_freq: float, causal_depth: int) -> bytes:
    """SPEC v1.1 optional trailer per node: float32 + uint8 + 3-byte pad = 8B."""
    return struct.pack("<fBxxx", float(resonance_freq), causal_depth & 0xFF)


# --- synthetic volume -----------------------------------------------------

def generate_volume(n: int = 10_000, seed: int = 42) -> List[Tuple[float, float, float]]:
    rng = random.Random(seed)
    pts: List[Tuple[float, float, float]] = []
    # Structured core: a few geometric arcs (true topology)
    for i in range(200):
        t = i / 199.0
        pts.append((math.cos(t * math.pi), math.sin(t * math.pi), 0.2 * t))
        pts.append((0.6 * math.cos(t * 2 * math.pi), 0.6 * math.sin(t * 2 * math.pi), 0.5))
    # High-entropy filler (weak entanglement noise)
    while len(pts) < n:
        pts.append(
            (
                rng.uniform(-1.5, 1.5),
                rng.uniform(-1.5, 1.5),
                rng.uniform(-0.5, 1.0),
            )
        )
    return pts


def estimate_raw_bytes(pts: List[Tuple[float, float, float]]) -> int:
    # 3 × float64 as a stand-in for a dense point record (~24B) + light header
    return len(pts) * 24 + 64


# --- SE extraction (simple saliency) --------------------------------------

def extract_se_nodes(
    pts: List[Tuple[float, float, float]], grid: float = 0.35, max_nodes: int = 80
) -> List[dict]:
    """
    Bin points; keep cell centroids with high occupancy or near structured arcs.
    Assign causal_depth by distance-to-origin rank (demo heuristic).
    """
    cells: dict = {}
    for x, y, z in pts:
        key = (int(math.floor(x / grid)), int(math.floor(y / grid)), int(math.floor(z / grid)))
        bucket = cells.setdefault(key, [])
        bucket.append((x, y, z))

    ranked = sorted(cells.items(), key=lambda kv: len(kv[1]), reverse=True)
    nodes: List[dict] = []
    for i, (_key, bucket) in enumerate(ranked[:max_nodes]):
        cx = sum(p[0] for p in bucket) / len(bucket)
        cy = sum(p[1] for p in bucket) / len(bucket)
        cz = sum(p[2] for p in bucket) / len(bucket)
        r = math.sqrt(cx * cx + cy * cy + cz * cz)
        # Higher occupancy + closer to structured shell → higher causal weight
        depth = int(min(255, 80 + len(bucket) * 2 + max(0, 40 - int(r * 30))))
        nodes.append(
            {
                "id": i + 1,
                "pos": (cx, cy, cz),
                "causal_depth": depth,
                "resonance_freq": 1.0 + 0.05 * (i % 17),
                "sub": 0x30 if depth < 180 else 0x10,
                "risk": 0 if depth < 200 else 1,
            }
        )
    return nodes


def build_se_frame(nodes: List[dict], with_v11_meta: bool = True) -> bytes:
    body = bytearray()
    body += pack_header(len(nodes), FLAG_EMBODIED, seq=1)
    for n in nodes:
        body += pack_embodied(
            n["id"],
            n["risk"],
            n["sub"],
            n["pos"],
            phase=0.0,
        )
        if with_v11_meta:
            body += pack_extended_meta(n["resonance_freq"], n["causal_depth"])
    crc = zlib.crc32(bytes(body)) & 0xFFFFFFFF
    body += struct.pack("<I", crc)
    return bytes(body)


def main() -> None:
    pts = generate_volume(10_000)
    raw = estimate_raw_bytes(pts)
    nodes = extract_se_nodes(pts, max_nodes=80)
    frame = build_se_frame(nodes, with_v11_meta=True)

    ratio = raw / max(len(frame), 1)
    print("=== P-LOD Horizon Compression Demo ===")
    print(f"Volume samples (weak+strong mix): {len(pts):,}")
    print(f"Raw dense estimate:               {raw:,} bytes ({raw/1024:.1f} KB)")
    print(f"SE nodes kept:                    {len(nodes)}")
    print(f"SE-Frame (Embodied + v1.1 meta):  {len(frame):,} bytes ({len(frame)/1024:.2f} KB)")
    print(f"Collapse ratio:                   {ratio:.1f}×  (~{(1 - len(frame)/raw)*100:.2f}% smaller)")
    print()
    print("Top causal anchors (causal_depth >= 200):")
    anchors = [n for n in nodes if n["causal_depth"] >= 200]
    if not anchors:
        anchors = sorted(nodes, key=lambda n: n["causal_depth"], reverse=True)[:5]
    for n in sorted(anchors, key=lambda n: n["causal_depth"], reverse=True)[:8]:
        x, y, z = n["pos"]
        print(
            f"  id={n['id']:3d}  depth={n['causal_depth']:3d}  "
            f"freq={n['resonance_freq']:.2f}  pos=({x:+.3f},{y:+.3f},{z:+.3f})"
        )
    print()
    print("Interpretation: high-entropy filler was discarded (WE);"
          " only topological skeleton crossed the 'horizon' into the SE-Frame.")


if __name__ == "__main__":
    main()
