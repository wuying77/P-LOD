#!/usr/bin/env python3
"""
P-LOD Official Reference Emergence Engine

  plod.ref.linear_spline.v1 — normative frozen baseline (Derived Edge Rule)
  plod.ref.linear_spline.v2 — experimental budgets / jitter / constraints

Decode via plod_spec_codec.decode_frame only.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_metrics import tcs_aabb
from plod_spec_codec import (
    GLOBAL_NA,
    SENode,
    Constraint,
    decode_frame,
    encode_frame,
)

PROFILE_V1 = "plod.ref.linear_spline.v1"
PROFILE_V2 = "plod.ref.linear_spline.v2"
TCS_PASS = 0.99
DEFAULT_SEED = 0x504C4F44
CONSTRAINT_DISTANCE = 0x01
CONSTRAINT_BOUNDARY = 0x02


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


def _mix(seed: int, a: int, b: int, k: int) -> int:
    h = hashlib.sha256(struct.pack("<IIII", seed & 0xFFFFFFFF, a, b, k))
    return int.from_bytes(h.digest()[:4], "little")


def _jitter3(bits: int, scale: float) -> Tuple[float, float, float]:
    return (
        (((bits >> 0) & 0xFF) / 255.0 * 2 - 1) * scale,
        (((bits >> 8) & 0xFF) / 255.0 * 2 - 1) * scale,
        (((bits >> 16) & 0xFF) / 255.0 * 2 - 1) * scale,
    )


def default_constraints(nodes: Sequence[SENode]) -> List[Constraint]:
    cs: List[Constraint] = []
    by_id = sorted(nodes, key=lambda n: n.node_id)
    for i in range(len(by_id) - 1):
        a, b = by_id[i], by_id[i + 1]
        d = math.dist(a.pos, b.pos)
        cs.append(Constraint(CONSTRAINT_DISTANCE, a.node_id, b.node_id, d * 1.15))
    if by_id:
        rmax = max(math.sqrt(sum(x * x for x in n.pos)) for n in by_id) + 0.05
        cs.append(Constraint(CONSTRAINT_BOUNDARY, GLOBAL_NA, GLOBAL_NA, rmax))
    return cs


def enforce_constraints(p, a, b, constraints):
    checks = 0
    x, y, z = p
    for c in constraints:
        if c.ctype == CONSTRAINT_DISTANCE and {c.node_a, c.node_b} == {a.node_id, b.node_id}:
            checks += 1
            mid = lerp3(a.pos, b.pos, 0.5)
            if math.dist(p, mid) > c.param0 * 0.5:
                scale = (c.param0 * 0.5) / (math.dist(p, mid) or 1e-9)
                x = mid[0] + (x - mid[0]) * scale
                y = mid[1] + (y - mid[1]) * scale
                z = mid[2] + (z - mid[2]) * scale
        elif c.ctype == CONSTRAINT_BOUNDARY:
            checks += 1
            r = math.sqrt(x * x + y * y + z * z)
            if r > c.param0 and r > 1e-12:
                s = c.param0 / r
                x, y, z = x * s, y * s, z * s
    return (x, y, z), checks


def emerge_v1(nodes: Sequence[SENode]) -> List[Tuple[float, float, float]]:
    id_map = {n.node_id: n for n in nodes}
    out: List[Tuple[float, float, float]] = []
    for a_id, b_id in chain_edges(nodes):
        if a_id not in id_map or b_id not in id_map:
            continue
        na, nb = id_map[a_id], id_map[b_id]
        for t in (0.25, 0.5, 0.75):
            out.append(lerp3(na.pos, nb.pos, t))
    return out


def emerge_v2(
    nodes: Sequence[SENode],
    *,
    budget: str = "constrained",
    seed: int = DEFAULT_SEED,
    constraints: Optional[Sequence[Constraint]] = None,
) -> Tuple[List[Tuple[float, float, float]], int]:
    id_map = {n.node_id: n for n in nodes}
    cons = list(constraints) if constraints is not None else default_constraints(nodes)
    emerged: List[Tuple[float, float, float]] = []
    checks = 0
    if budget == "coarse":
        samples, use_smooth, jitter_base = [0.5], False, 0.0
    elif budget == "constrained":
        samples, use_smooth, jitter_base = [0.5], False, 0.01
    else:
        samples, use_smooth, jitter_base = [0.25, 0.5, 0.75], True, 0.02
    for a_id, b_id in chain_edges(nodes):
        if a_id not in id_map or b_id not in id_map:
            continue
        na, nb = id_map[a_id], id_map[b_id]
        depth = max(na.causal_depth, nb.causal_depth)
        stiff = 1.0 / (1.0 + depth / 64.0)
        for t in samples:
            tt = smoothstep(t) if use_smooth else t
            base = lerp3(na.pos, nb.pos, tt)
            bits = _mix(seed, a_id, b_id, int(t * 100))
            j = _jitter3(bits, jitter_base * stiff)
            p = (base[0] + j[0], base[1] + j[1], base[2] + j[2])
            if budget in ("constrained", "high_fidelity"):
                p, ch = enforce_constraints(p, na, nb, cons)
                checks += ch
            emerged.append(p)
    return emerged, checks


def make_demo_nodes(n: int = 80) -> List[SENode]:
    nodes = []
    for i in range(n):
        ang = 2 * math.pi * i / max(n - 1, 1)
        depth = int(120 + 100 * (0.5 + 0.5 * math.cos(ang)))
        nodes.append(
            SENode(
                i + 1,
                (math.cos(ang), math.sin(ang), 0.15 * math.sin(3 * ang)),
                risk_state=0 if depth < 200 else 1,
                sub_system=0x10 if depth >= 200 else 0x30,
                resonance_freq=1.0 + 0.02 * (i % 11),
                causal_depth=min(255, depth),
            )
        )
    return nodes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("v1", "v2"), default="v1")
    ap.add_argument("--budget", choices=("coarse", "constrained", "high_fidelity"), default="constrained")
    ap.add_argument("--nodes", type=int, default=80)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    nodes = make_demo_nodes(args.nodes)
    frame = encode_frame(nodes, embodied=True, extended_meta=True)
    decoded = decode_frame(frame)

    t0 = time.perf_counter()
    if args.profile == "v1":
        profile_id = PROFILE_V1
        emerged = emerge_v1(decoded.nodes)
        checks = 0
    else:
        profile_id = PROFILE_V2
        emerged, checks = emerge_v2(decoded.nodes, budget=args.budget, seed=args.seed)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    anchors = [n.pos for n in decoded.nodes]
    tcs = tcs_aabb(anchors, emerged)

    print("=== P-LOD Official Reference Emergence Engine ===")
    print(f"Profile:        {profile_id}")
    if args.profile == "v2":
        print(f"Budget:         {args.budget}  checks={checks}")
    print(f"Elapsed:        {elapsed_ms:.3f} ms")
    print(f"SE-Frame:       {len(frame)} bytes")
    print(f"SE nodes:       {len(decoded.nodes)}")
    print(f"Emerged WE:     {len(emerged)}")
    status = "PASS" if tcs >= TCS_PASS else "FAIL"
    print(
        f"TCS-AABB: {tcs:.4f} | Status: AABB Containment {status} "
        f"(Note: Containment Proxy Verification)."
    )
    print(f"STATUS: P-LOD Protocol Compliance Test {status}")


if __name__ == "__main__":
    main()
