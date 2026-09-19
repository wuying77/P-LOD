#!/usr/bin/env python3
"""
P-LOD Official Reference Emergence Engine 2.0
=============================================
Normative reference: SE decode + deterministic WE emergence with
Compute-Budget tiers and optional Constraint Table checks.

SE/WE = information-theoretic protocol metaphors (not quantum entanglement).

TCS = protocol compliance | RFS = fidelity vs Ground Truth (optional)

Usage:
  python reference_emergence_engine.py
  python reference_emergence_engine.py --budget coarse
  python reference_emergence_engine.py --budget constrained
  python reference_emergence_engine.py --budget high_fidelity

stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
import time
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

MAGIC = 0x504C
VERSION_V10, VERSION_V11 = 0x10, 0x11
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4

CONSTRAINT_DISTANCE = 0x01
CONSTRAINT_BOUNDARY = 0x02
CONSTRAINT_TEMPORAL = 0x03

PROFILE_ID = "plod.ref.linear_spline.v2"
DEFAULT_SEED = 0x504C4F44
TCS_PASS = 0.99

CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = struct.calcsize(CORE_FMT)


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
class Constraint:
    ctype: int
    a: int
    b: int
    value: float


@dataclass
class EmergedPoint:
    pos: Tuple[float, float, float]
    source_a: int
    source_b: int
    t: float
    level: int


@dataclass
class EmergenceResult:
    nodes: List[SENode]
    emerged: List[EmergedPoint]
    profile_id: str
    seed: int
    budget: str
    elapsed_ms: float
    tcs: float
    se_bytes: int
    emerged_count: int
    rfs: Optional[float] = None
    constraints_checked: int = 0
    log_lines: List[str] = field(default_factory=list)


def pack_se_frame(nodes: Sequence[SENode], *, embodied=True, extended_meta=True, seq=1) -> bytes:
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
                *map(float, n.pos),
                *map(float, n.vel),
                float(n.phase),
            )
        else:
            body += struct.pack(CORE_FMT, n.node_id & 0xFFFF, 1, 0, *map(float, n.pos), 0, 0, 0, 0, 0.0)
        if extended_meta:
            body += struct.pack("<fBxxx", float(n.resonance_freq), n.causal_depth & 0xFF)
    body += struct.pack("<I", zlib.crc32(bytes(body)) & 0xFFFFFFFF)
    return bytes(body)


def unpack_se_frame(data: bytes) -> Tuple[List[SENode], Dict]:
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ValueError("bad MAGIC")
    embodied = bool(flags & FLAG_EMBODIED)
    ext = bool(flags & FLAG_EXTENDED_META)
    off = 8
    nodes: List[SENode] = []
    for _ in range(count):
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from("<HBB3f3ff", data, off)
            off += 32
            node = SENode(nid, risk, sub, (px, py, pz), (vx, vy, vz), phase)
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(CORE_FMT, data, off)
            off += CORE_SIZE
            node = SENode(nid, 0, 0, (px, py, pz))
        if ext:
            freq, depth = struct.unpack_from("<fB", data, off)
            off += 8
            node.resonance_freq = freq
            node.causal_depth = depth
        nodes.append(node)
    meta = {"version": ver, "flags": flags, "seq": seq}
    if off + 4 <= len(data):
        meta["crc_ok"] = struct.unpack_from("<I", data, off)[0] == (zlib.crc32(data[:off]) & 0xFFFFFFFF)
    return nodes, meta


def _mix(seed: int, a: int, b: int, k: int) -> int:
    h = hashlib.sha256(struct.pack("<IIII", seed & 0xFFFFFFFF, a, b, k))
    return int.from_bytes(h.digest()[:4], "little")


def _jitter3(bits: int, scale: float) -> Tuple[float, float, float]:
    return (
        (((bits >> 0) & 0xFF) / 255.0 * 2 - 1) * scale,
        (((bits >> 8) & 0xFF) / 255.0 * 2 - 1) * scale,
        (((bits >> 16) & 0xFF) / 255.0 * 2 - 1) * scale,
    )


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def chain_edges(nodes: Sequence[SENode]) -> List[Tuple[int, int]]:
    by_id = sorted(nodes, key=lambda n: n.node_id)
    if len(by_id) < 2:
        return []
    edges = [(by_id[i].node_id, by_id[i + 1].node_id) for i in range(len(by_id) - 1)]
    edges.append((by_id[-1].node_id, by_id[0].node_id))
    return edges


def default_constraints(nodes: Sequence[SENode]) -> List[Constraint]:
    cs: List[Constraint] = []
    by_id = sorted(nodes, key=lambda n: n.node_id)
    for i in range(len(by_id) - 1):
        a, b = by_id[i], by_id[i + 1]
        d = math.dist(a.pos, b.pos)
        cs.append(Constraint(CONSTRAINT_DISTANCE, a.node_id, b.node_id, d * 1.15))
    if by_id:
        rmax = max(math.sqrt(n.pos[0] ** 2 + n.pos[1] ** 2 + n.pos[2] ** 2) for n in by_id) + 0.05
        cs.append(Constraint(CONSTRAINT_BOUNDARY, 0, 0, rmax))
        cs.append(Constraint(CONSTRAINT_TEMPORAL, by_id[0].node_id, by_id[-1].node_id, 1.0))
    return cs


def enforce_constraints(p, a, b, constraints):
    checks = 0
    x, y, z = p
    for c in constraints:
        if c.ctype == CONSTRAINT_DISTANCE and {c.a, c.b} == {a.node_id, b.node_id}:
            checks += 1
            mid = lerp3(a.pos, b.pos, 0.5)
            if math.dist(p, mid) > c.value * 0.5:
                scale = (c.value * 0.5) / (math.dist(p, mid) or 1e-9)
                x = mid[0] + (x - mid[0]) * scale
                y = mid[1] + (y - mid[1]) * scale
                z = mid[2] + (z - mid[2]) * scale
        elif c.ctype == CONSTRAINT_BOUNDARY:
            checks += 1
            r = math.sqrt(x * x + y * y + z * z)
            if r > c.value and r > 1e-12:
                s = c.value / r
                x, y, z = x * s, y * s, z * s
    return (x, y, z), checks


class ReferenceEmergenceEngine:
    PROFILE_ID = PROFILE_ID

    def __init__(self, seed: int = DEFAULT_SEED, budget: str = "constrained"):
        self.seed = seed
        self.budget = budget if budget in ("coarse", "constrained", "high_fidelity") else "constrained"

    def emerge_from_nodes(
        self,
        nodes: Sequence[SENode],
        *,
        constraints: Optional[Sequence[Constraint]] = None,
        ground_truth_points: Optional[Sequence[Tuple[float, float, float]]] = None,
    ) -> EmergenceResult:
        t0 = time.perf_counter()
        log: List[str] = []
        id_map = {n.node_id: n for n in nodes}
        edges = chain_edges(nodes)
        cons = list(constraints) if constraints is not None else default_constraints(nodes)
        emerged: List[EmergedPoint] = []
        checks_total = 0

        if self.budget == "coarse":
            samples, levels, use_smooth, jitter_base = [0.5], [2], False, 0.0
        elif self.budget == "constrained":
            samples, levels, use_smooth, jitter_base = [0.5], [2], False, 0.01
        else:
            samples, levels, use_smooth, jitter_base = [0.25, 0.5, 0.75], [3, 2, 3], True, 0.02

        for a_id, b_id in edges:
            if a_id not in id_map or b_id not in id_map:
                continue
            na, nb = id_map[a_id], id_map[b_id]
            depth = max(na.causal_depth, nb.causal_depth)
            stiff = 1.0 / (1.0 + depth / 64.0)
            for t, level in zip(samples, levels):
                tt = smoothstep(t) if use_smooth else t
                base = lerp3(na.pos, nb.pos, tt)
                bits = _mix(self.seed, a_id, b_id, int(t * 100) + level)
                j = _jitter3(bits, jitter_base * stiff)
                p = (base[0] + j[0], base[1] + j[1], base[2] + j[2])
                if self.budget in ("constrained", "high_fidelity"):
                    p, ch = enforce_constraints(p, na, nb, cons)
                    checks_total += ch
                emerged.append(EmergedPoint(p, a_id, b_id, t, level))

        tcs = topological_consistency_score(nodes, emerged)
        rfs = None
        if ground_truth_points is not None:
            rfs = rfs_placeholder(emerged, ground_truth_points)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        log.append(f"[REF] profile={PROFILE_ID} seed={self.seed:#x}")
        log.append(f"[REF] compute_budget={self.budget}  elapsed_ms={elapsed_ms:.3f}")
        log.append(f"[REF] SE nodes={len(nodes)}  constraints={len(cons)}  checks={checks_total}")
        log.append(f"[REF] emerged={len(emerged)}")
        log.append(
            f"[REF] TCS = {tcs:.4f} | P-LOD Protocol Compliance Test: "
            f"{'PASS' if tcs >= TCS_PASS else 'FAIL'} "
            f"(Note: TCS verifies protocol compliance. "
            f"Reconstruction Fidelity (RFS) is measured against original Ground Truth)."
        )
        log.append(f"[REF] RFS = {rfs:.4f}" if rfs is not None else "[REF] RFS = N/A (no Ground Truth supplied)")

        return EmergenceResult(
            nodes=list(nodes),
            emerged=emerged,
            profile_id=PROFILE_ID,
            seed=self.seed,
            budget=self.budget,
            elapsed_ms=elapsed_ms,
            tcs=tcs,
            se_bytes=0,
            emerged_count=len(emerged),
            rfs=rfs,
            constraints_checked=checks_total,
            log_lines=log,
        )

    def emerge_from_bytes(self, frame: bytes, **kwargs) -> EmergenceResult:
        nodes, meta = unpack_se_frame(frame)
        result = self.emerge_from_nodes(nodes, **kwargs)
        result.se_bytes = len(frame)
        result.log_lines.insert(1, f"[REF] frame_bytes={len(frame)} crc_ok={meta.get('crc_ok')}")
        return result


def topological_consistency_score(nodes, emerged) -> float:
    if not nodes:
        return 0.0
    xs, ys, zs = zip(*(n.pos for n in nodes))
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    diag = math.sqrt((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2) or 1.0
    pad = 0.05 * diag
    if not emerged:
        return 1.0
    ok = sum(
        1
        for e in emerged
        if min_x - pad <= e.pos[0] <= max_x + pad
        and min_y - pad <= e.pos[1] <= max_y + pad
        and min_z - pad <= e.pos[2] <= max_z + pad
    )
    return ok / len(emerged)


def rfs_placeholder(emerged, gt) -> float:
    if not emerged or not gt:
        return 0.0
    s = 0.0
    for e in emerged:
        best = min((e.pos[0] - g[0]) ** 2 + (e.pos[1] - g[1]) ** 2 + (e.pos[2] - g[2]) ** 2 for g in gt)
        s += 1.0 / (1.0 + math.sqrt(best))
    return s / len(emerged)


def make_demo_nodes(n: int = 80) -> List[SENode]:
    nodes = []
    for i in range(n):
        ang = 2 * math.pi * i / max(n - 1, 1)
        depth = int(120 + 100 * (0.5 + 0.5 * math.cos(ang)))
        nodes.append(
            SENode(
                i + 1,
                0 if depth < 200 else 1,
                0x10 if depth >= 200 else 0x30,
                (math.cos(ang), math.sin(ang), 0.15 * math.sin(3 * ang)),
                resonance_freq=1.0 + 0.02 * (i % 11),
                causal_depth=min(255, depth),
            )
        )
    return nodes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=80)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--budget", choices=("coarse", "constrained", "high_fidelity"), default="constrained")
    args = ap.parse_args()

    nodes = make_demo_nodes(args.nodes)
    frame = pack_se_frame(nodes)
    engine = ReferenceEmergenceEngine(seed=args.seed, budget=args.budget)
    result = engine.emerge_from_bytes(frame)

    print("=== P-LOD Official Reference Emergence Engine 2.0 ===")
    print("Structural State Representation — Progressive Realization Protocol")
    print("Note: SE/WE are protocol metaphors, not quantum entanglement.")
    print(f"Profile:          {result.profile_id}")
    print(f"Compute Budget:   {result.budget}")
    print(f"Elapsed:          {result.elapsed_ms:.3f} ms")
    print(f"SE-Frame:         {result.se_bytes} bytes")
    print(f"SE nodes:         {len(result.nodes)}")
    print(f"Constraints chk:  {result.constraints_checked}")
    print(f"Emerged WE:       {result.emerged_count}")
    print(
        f"TCS = {result.tcs:.4f} | P-LOD Protocol Compliance Test: "
        f"{'PASS' if result.tcs >= TCS_PASS else 'FAIL'} "
        f"(Note: TCS verifies protocol compliance. "
        f"Reconstruction Fidelity (RFS) is measured against original Ground Truth)."
    )
    print(f"RFS = {'N/A' if result.rfs is None else f'{result.rfs:.4f}'}")
    print()
    for line in result.log_lines:
        print(line)
    print()
    print(f"STATUS: P-LOD Protocol Compliance Test {'PASS' if result.tcs >= TCS_PASS else 'FAIL'}")


if __name__ == "__main__":
    main()
