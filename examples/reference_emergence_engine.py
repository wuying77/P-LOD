#!/usr/bin/env python3
"""
P-LOD Official Reference Emergence Engine
=========================================
Normative reference implementation for decoding SE-Frames and reconstructing
weak-entanglement (WE) detail in a deterministic, stdlib-only manner.

This file is the Source of Truth for P-LOD compliance tests:
  any third-party decoder/emergencer that claims "P-LOD Compliant" SHOULD
  match this engine's topological outputs within the stated TCS bounds.

Usage:
  python reference_emergence_engine.py
  python reference_emergence_engine.py --nodes 80

Dependencies: Python 3.8+ standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# ---- Spec constants ---------------------------------------------------------

MAGIC = 0x504C
VERSION_V10 = 0x10
VERSION_V11 = 0x11
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4

PROFILE_ID_LINEAR_SPLINE = "plod.ref.linear_spline.v1"
DEFAULT_SEED = 0x504C4F44  # 'PLOD'


# ---- Data model -------------------------------------------------------------

@dataclass
class SENode:
    node_id: int
    risk_state: int = 0
    sub_system: int = 0
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    vel: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    phase: float = 0.0
    resonance_freq: float = 1.0
    causal_depth: int = 0


@dataclass
class EmergedPoint:
    pos: Tuple[float, float, float]
    source_a: int
    source_b: int
    t: float
    level: int  # 2 or 3 synthetic detail


@dataclass
class EmergenceResult:
    nodes: List[SENode]
    emerged: List[EmergedPoint]
    profile_id: str
    seed: int
    tcs: float
    se_bytes: int
    emerged_count: int
    log_lines: List[str] = field(default_factory=list)


# ---- Pack / unpack (reference, mirrors Spec v1.0/v1.1) ----------------------

def pack_se_frame(
    nodes: Sequence[SENode],
    *,
    embodied: bool = True,
    extended_meta: bool = True,
    seq: int = 1,
) -> bytes:
    flags = 0
    if embodied:
        flags |= FLAG_EMBODIED
    if extended_meta:
        flags |= FLAG_EXTENDED_META
    ver = VERSION_V11 if extended_meta else VERSION_V10
    body = bytearray()
    body += struct.pack("<HBBHH", MAGIC, ver, flags & 0xFF, len(nodes) & 0xFFFF, seq & 0xFFFF)
    for n in nodes:
        if embodied:
            body += struct.pack(
                "<HBB3f3ff",
                n.node_id & 0xFFFF,
                n.risk_state & 0xFF,
                n.sub_system & 0xFF,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                float(n.vel[0]),
                float(n.vel[1]),
                float(n.vel[2]),
                float(n.phase),
            )
        else:
            # minimal core-like 24B: id, level=1, type=0, xyz, rgb0, flags0, param0
            body += struct.pack(
                "<HBB3f3Bf",
                n.node_id & 0xFFFF,
                1,
                0,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                0,
                0,
                0,
                0,
                0.0,
            )
        if extended_meta:
            body += struct.pack("<fBxxx", float(n.resonance_freq), n.causal_depth & 0xFF)
    crc = zlib.crc32(bytes(body)) & 0xFFFFFFFF
    body += struct.pack("<I", crc)
    return bytes(body)


def unpack_se_frame(data: bytes) -> Tuple[List[SENode], Dict]:
    if len(data) < 8:
        raise ValueError("frame too short")
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ValueError(f"bad MAGIC {magic:#x}")
    embodied = bool(flags & FLAG_EMBODIED)
    ext = bool(flags & FLAG_EXTENDED_META)
    off = 8
    node_size = (32 if embodied else 24) + (8 if ext else 0)
    nodes: List[SENode] = []
    for _ in range(count):
        if off + (32 if embodied else 24) > len(data) - 4:
            raise ValueError("truncated nodes")
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from(
                "<HBB3f3ff", data, off
            )
            off += 32
            node = SENode(nid, risk, sub, (px, py, pz), (vx, vy, vz), phase)
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                "<HBB3f3Bf", data, off
            )
            off += 24
            node = SENode(nid, 0, 0, (px, py, pz))
        if ext:
            freq, depth = struct.unpack_from("<fB", data, off)
            off += 8
            node.resonance_freq = freq
            node.causal_depth = depth
        nodes.append(node)
    meta = {"version": ver, "flags": flags, "seq": seq, "embodied": embodied, "extended": ext}
    if off + 4 <= len(data):
        crc_stored = struct.unpack_from("<I", data, off)[0]
        crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
        meta["crc_ok"] = crc_stored == crc_calc
    return nodes, meta


# ---- Deterministic helpers --------------------------------------------------

def _mix_seed(seed: int, a: int, b: int, k: int) -> int:
    h = hashlib.sha256()
    h.update(struct.pack("<IIII", seed & 0xFFFFFFFF, a & 0xFFFFFFFF, b & 0xFFFFFFFF, k & 0xFFFFFFFF))
    return int.from_bytes(h.digest()[:4], "little")


def _unit_jitter(seed_bits: int, scale: float) -> Tuple[float, float, float]:
    """Small deterministic offset in [-scale, scale]^3 from seed bits."""
    x = ((seed_bits >> 0) & 0xFF) / 255.0 * 2 - 1
    y = ((seed_bits >> 8) & 0xFF) / 255.0 * 2 - 1
    z = ((seed_bits >> 16) & 0xFF) / 255.0 * 2 - 1
    return (x * scale, y * scale, z * scale)


def lerp3(
    a: Tuple[float, float, float], b: Tuple[float, float, float], t: float
) -> Tuple[float, float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def chain_edges(nodes: Sequence[SENode]) -> List[Tuple[int, int]]:
    """Reference topology: connect consecutive ids, plus nearest-neighbor for last."""
    if len(nodes) < 2:
        return []
    by_id = sorted(nodes, key=lambda n: n.node_id)
    edges = [(by_id[i].node_id, by_id[i + 1].node_id) for i in range(len(by_id) - 1)]
    # close a soft ring for horizon-like shells
    edges.append((by_id[-1].node_id, by_id[0].node_id))
    return edges


# ---- Core engine ------------------------------------------------------------

class ReferenceEmergenceEngine:
    """
    Official P-LOD reference emergencer.

    Profile: plod.ref.linear_spline.v1
      - Edge set from ordered node ids (+ ring close)
      - Level-2 points: midpoints along edges with seed-locked micro-jitter
      - Level-3 points: quarter points (t=0.25, 0.75)
      - Amplitude of jitter scaled by 1 / (1 + causal_depth/64) so anchors stay stiff
    """

    PROFILE_ID = PROFILE_ID_LINEAR_SPLINE

    def __init__(self, seed: int = DEFAULT_SEED, profile_id: str = PROFILE_ID_LINEAR_SPLINE):
        self.seed = seed
        self.profile_id = profile_id

    def emerge_from_nodes(
        self,
        nodes: Sequence[SENode],
        *,
        level2_per_edge: int = 1,
        level3_per_edge: int = 2,
    ) -> EmergenceResult:
        log: List[str] = []
        log.append(f"[REF] profile={self.profile_id} seed={self.seed:#x}")
        log.append(f"[REF] SE nodes={len(nodes)}")

        id_map = {n.node_id: n for n in nodes}
        edges = chain_edges(nodes)
        emerged: List[EmergedPoint] = []

        for a_id, b_id in edges:
            if a_id not in id_map or b_id not in id_map:
                continue
            na, nb = id_map[a_id], id_map[b_id]
            depth = max(na.causal_depth, nb.causal_depth)
            stiff = 1.0 / (1.0 + depth / 64.0)
            jitter_scale = 0.02 * stiff

            # Level 2: midpoint
            if level2_per_edge >= 1:
                bits = _mix_seed(self.seed, a_id, b_id, 2)
                j = _unit_jitter(bits, jitter_scale)
                mid = lerp3(na.pos, nb.pos, 0.5)
                emerged.append(
                    EmergedPoint(
                        (mid[0] + j[0], mid[1] + j[1], mid[2] + j[2]),
                        a_id,
                        b_id,
                        0.5,
                        2,
                    )
                )

            # Level 3: quarters
            if level3_per_edge >= 1:
                for k, t in enumerate((0.25, 0.75)[:level3_per_edge]):
                    bits = _mix_seed(self.seed, a_id, b_id, 30 + k)
                    j = _unit_jitter(bits, jitter_scale * 0.7)
                    p = lerp3(na.pos, nb.pos, t)
                    emerged.append(
                        EmergedPoint(
                            (p[0] + j[0], p[1] + j[1], p[2] + j[2]),
                            a_id,
                            b_id,
                            t,
                            3,
                        )
                    )

        tcs = self.topological_consistency_score(nodes, emerged)
        log.append(f"[REF] emerged points={len(emerged)}  TCS={tcs:.6f}")
        if tcs >= 0.99:
            log.append("[REF] P-LOD Standard Compliance Test PASS (TCS >= 0.99)")
        else:
            log.append("[REF] P-LOD Standard Compliance Test FAIL (TCS < 0.99)")

        return EmergenceResult(
            nodes=list(nodes),
            emerged=emerged,
            profile_id=self.profile_id,
            seed=self.seed,
            tcs=tcs,
            se_bytes=0,
            emerged_count=len(emerged),
            log_lines=log,
        )

    def emerge_from_bytes(self, frame: bytes) -> EmergenceResult:
        nodes, meta = unpack_se_frame(frame)
        result = self.emerge_from_nodes(nodes)
        result.se_bytes = len(frame)
        result.log_lines.insert(
            1,
            f"[REF] frame bytes={len(frame)} crc_ok={meta.get('crc_ok')} "
            f"ver={meta.get('version'):#x} flags={meta.get('flags'):#04x}",
        )
        return result

    @staticmethod
    def topological_consistency_score(
        nodes: Sequence[SENode], emerged: Sequence[EmergedPoint]
    ) -> float:
        """
        TCS in [0, 1]: fraction of emerged points that remain inside the
        axis-aligned bounding box of SE nodes expanded by 5% of diagonal.
        Reference rule is intentionally simple, deterministic, and public.
        """
        if not nodes:
            return 0.0
        xs = [n.pos[0] for n in nodes]
        ys = [n.pos[1] for n in nodes]
        zs = [n.pos[2] for n in nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        diag = math.sqrt(
            (max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2
        ) or 1.0
        pad = 0.05 * diag
        if not emerged:
            return 1.0  # structure-only is always consistent with itself
        ok = 0
        for e in emerged:
            x, y, z = e.pos
            if (
                min_x - pad <= x <= max_x + pad
                and min_y - pad <= y <= max_y + pad
                and min_z - pad <= z <= max_z + pad
            ):
                ok += 1
        return ok / len(emerged)


# ---- Demo scaffolding -------------------------------------------------------

def make_demo_nodes(n: int = 80) -> List[SENode]:
    nodes: List[SENode] = []
    for i in range(n):
        t = i / max(n - 1, 1)
        ang = t * 2 * math.pi
        x = math.cos(ang)
        y = math.sin(ang)
        z = 0.15 * math.sin(3 * ang)
        depth = int(120 + 100 * (0.5 + 0.5 * math.cos(ang)))
        nodes.append(
            SENode(
                node_id=i + 1,
                risk_state=0 if depth < 200 else 1,
                sub_system=0x10 if depth >= 200 else 0x30,
                pos=(x, y, z),
                resonance_freq=1.0 + 0.02 * (i % 11),
                causal_depth=min(255, depth),
            )
        )
    return nodes


def main() -> None:
    ap = argparse.ArgumentParser(description="P-LOD Official Reference Emergence Engine")
    ap.add_argument("--nodes", type=int, default=80, help="demo SE node count")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    nodes = make_demo_nodes(args.nodes)
    frame = pack_se_frame(nodes, embodied=True, extended_meta=True)
    engine = ReferenceEmergenceEngine(seed=args.seed)
    result = engine.emerge_from_bytes(frame)

    print("=== P-LOD Official Reference Emergence Engine ===")
    print(f"Profile:     {result.profile_id}")
    print(f"Seed:        {result.seed:#x}")
    print(f"SE-Frame:    {result.se_bytes} bytes ({result.se_bytes/1024:.2f} KB)")
    print(f"SE nodes:    {len(result.nodes)}")
    print(f"Emerged WE:  {result.emerged_count} points (L2/L3 spline fill)")
    print(f"TCS:         {result.tcs:.6f}")
    print()
    for line in result.log_lines:
        print(line)
    print()
    # sample a few emerged points for visibility
    print("Sample emerged points (first 5):")
    for e in result.emerged[:5]:
        print(
            f"  L{e.level} t={e.t:.2f} edge=({e.source_a}->{e.source_b}) "
            f"pos=({e.pos[0]:+.4f},{e.pos[1]:+.4f},{e.pos[2]:+.4f})"
        )
    print()
    if result.tcs >= 0.99:
        print("STATUS: P-LOD Standard Compliance Test PASS")
    else:
        print("STATUS: P-LOD Standard Compliance Test FAIL")


if __name__ == "__main__":
    main()
