#!/usr/bin/env python3
"""
P-LOD Spec v1.1 public codec (stdlib only) — single source of truth for pack/decode.

FLAGS (Little-Endian wire):
  HAS_CONSTRAINT_TABLE = 0x01
  IS_EMBODIED_PROFILE  = 0x02
  HAS_EXTENDED_META    = 0x04

CRC-32/ISO-HDLC over Header+Nodes+Constraints (excludes trailing CRC).
Global/N/A node marker in constraints: 0xFFFF

Usage:
  python plod_spec_codec.py --demo
"""

from __future__ import annotations

import argparse
import math
import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

MAGIC = 0x504C
VERSION_V10 = 0x10
VERSION_V11 = 0x11

FLAG_HAS_CONSTRAINT_TABLE = 1 << 0  # 0x01
FLAG_IS_EMBODIED_PROFILE = 1 << 1  # 0x02
FLAG_HAS_EXTENDED_META = 1 << 2  # 0x04

GLOBAL_NA = 0xFFFF
MAX_SE_NODES = 65535
MAX_CONSTRAINTS = 65535
MAX_FRAME_SIZE = 16 * 1024 * 1024

CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = 24
EMBODIED_SIZE = 32
META_SIZE = 8
CONSTRAINT_SIZE = 16


class ProtocolError(Exception):
    """Mandatory rejection path for non-compliant frames."""


@dataclass
class SENode:
    node_id: int
    pos: Tuple[float, float, float]
    level: int = 1
    type_code: int = 0
    rgb: Tuple[int, int, int] = (0, 0, 0)
    node_flags: int = 0
    param0: float = 0.0
    risk_state: int = 0
    sub_system: int = 0
    vel: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    phase: float = 0.0
    resonance_freq: float = 1.0
    causal_depth: int = 0


@dataclass
class Constraint:
    ctype: int
    node_a: int
    node_b: int
    param0: float
    param1: float = 0.0


@dataclass
class DecodedFrame:
    version: int
    flags: int
    sequence_id: int
    nodes: List[SENode]
    constraints: List[Constraint] = field(default_factory=list)
    raw_size: int = 0


def _check_finite(x: float, name: str = "coord") -> None:
    if math.isnan(x) or math.isinf(x):
        raise ProtocolError(f"NaN/Inf in {name}")


def encode_frame(
    nodes: Sequence[SENode],
    *,
    constraints: Optional[Sequence[Constraint]] = None,
    embodied: bool = False,
    extended_meta: bool = False,
    version: int = VERSION_V11,
    sequence_id: int = 1,
) -> bytes:
    if len(nodes) > MAX_SE_NODES:
        raise ProtocolError("MAX_SE_NODES exceeded")
    cons = list(constraints or [])
    if len(cons) > MAX_CONSTRAINTS:
        raise ProtocolError("MAX_CONSTRAINTS exceeded")

    flags = 0
    if cons:
        flags |= FLAG_HAS_CONSTRAINT_TABLE
    if embodied:
        flags |= FLAG_IS_EMBODIED_PROFILE
    if extended_meta:
        flags |= FLAG_HAS_EXTENDED_META

    body = bytearray()
    body += struct.pack(
        "<HBBHH",
        MAGIC,
        version & 0xFF,
        flags & 0xFF,
        len(nodes) & 0xFFFF,
        sequence_id & 0xFFFF,
    )

    for n in nodes:
        for c in n.pos:
            _check_finite(c)
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
            body += struct.pack(
                CORE_FMT,
                n.node_id & 0xFFFF,
                n.level & 0xFF,
                n.type_code & 0xFF,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                n.rgb[0] & 0xFF,
                n.rgb[1] & 0xFF,
                n.rgb[2] & 0xFF,
                n.node_flags & 0xFF,
                float(n.param0),
            )
        if extended_meta:
            body += struct.pack("<fBxxx", float(n.resonance_freq), n.causal_depth & 0xFF)

    if cons:
        body += struct.pack("<H", len(cons) & 0xFFFF)
        for c in cons:
            body += struct.pack(
                "<BBHHffH",
                c.ctype & 0xFF,
                0,
                c.node_a & 0xFFFF,
                c.node_b & 0xFFFF,
                float(c.param0),
                float(c.param1),
                0,
            )

    if len(body) + 4 > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")

    crc = zlib.crc32(bytes(body)) & 0xFFFFFFFF
    body += struct.pack("<I", crc)
    return bytes(body)


def decode_frame(data: bytes) -> DecodedFrame:
    if len(data) < 12:
        raise ProtocolError("frame too short")
    if len(data) > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")

    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ProtocolError(f"bad MAGIC {magic:#x}")
    if ver not in (VERSION_V10, VERSION_V11):
        raise ProtocolError(f"unknown VERSION {ver:#x}")
    if count > MAX_SE_NODES:
        raise ProtocolError("SE_NODE_COUNT exceeds MAX_SE_NODES")

    embodied = bool(flags & FLAG_IS_EMBODIED_PROFILE)
    has_meta = bool(flags & FLAG_HAS_EXTENDED_META)
    has_ct = bool(flags & FLAG_HAS_CONSTRAINT_TABLE)
    base = EMBODIED_SIZE if embodied else CORE_SIZE

    off = 8
    nodes: List[SENode] = []
    for _ in range(count):
        need = base + (META_SIZE if has_meta else 0)
        if off + need > len(data) - 4:
            raise ProtocolError("truncated node table")
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from(
                "<HBB3f3ff", data, off
            )
            off += EMBODIED_SIZE
            for v, name in ((px, "x"), (py, "y"), (pz, "z")):
                _check_finite(v, name)
            node = SENode(
                nid,
                (px, py, pz),
                risk_state=risk,
                sub_system=sub,
                vel=(vx, vy, vz),
                phase=phase,
            )
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                CORE_FMT, data, off
            )
            off += CORE_SIZE
            for v, name in ((px, "x"), (py, "y"), (pz, "z")):
                _check_finite(v, name)
            node = SENode(
                nid,
                (px, py, pz),
                level=level,
                type_code=tcode,
                rgb=(r, g, b),
                node_flags=nfl,
                param0=p0,
            )
        if has_meta:
            freq, depth = struct.unpack_from("<fB", data, off)
            pad = data[off + 5 : off + 8]
            if pad != b"\x00\x00\x00":
                raise ProtocolError("Extended Meta pad must be zero")
            off += META_SIZE
            node.resonance_freq = freq
            node.causal_depth = depth
        nodes.append(node)

    id_set = {n.node_id for n in nodes}
    constraints: List[Constraint] = []
    if has_ct:
        if off + 2 > len(data) - 4:
            raise ProtocolError("truncated constraint count")
        (m,) = struct.unpack_from("<H", data, off)
        off += 2
        if m > MAX_CONSTRAINTS:
            raise ProtocolError("too many constraints")
        for _ in range(m):
            if off + CONSTRAINT_SIZE > len(data) - 4:
                raise ProtocolError("truncated constraint entry")
            ctype, cflags, a, b, p0, p1, reserved = struct.unpack_from(
                "<BBHHffH", data, off
            )
            off += CONSTRAINT_SIZE
            if cflags != 0 or reserved != 0:
                raise ProtocolError("constraint reserved/cflags must be zero")
            if a != GLOBAL_NA and a not in id_set:
                raise ProtocolError(f"constraint node_a {a} out of SE set")
            if b != GLOBAL_NA and b not in id_set:
                raise ProtocolError(f"constraint node_b {b} out of SE set")
            constraints.append(Constraint(ctype, a, b, p0, p1))

    if off + 4 > len(data):
        raise ProtocolError("missing CRC32")
    if off + 4 != len(data):
        raise ProtocolError("trailing garbage bytes")

    crc_stored = struct.unpack_from("<I", data, off)[0]
    crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
    if crc_stored != crc_calc:
        raise ProtocolError("CRC32 mismatch (CRC-32/ISO-HDLC)")

    return DecodedFrame(
        version=ver,
        flags=flags,
        sequence_id=seq,
        nodes=nodes,
        constraints=constraints,
        raw_size=len(data),
    )


def demo() -> None:
    nodes = [
        SENode(0, (1.0, 0.0, 0.0)),
        SENode(1, (0.0, 1.0, 0.0)),
        SENode(2, (-1.0, 0.0, 0.0)),
        SENode(3, (0.0, -1.0, 0.0)),
    ]
    cons = [
        Constraint(0x01, 0, 1, 2.5),
        Constraint(0x02, GLOBAL_NA, GLOBAL_NA, 1.75),
    ]
    blob = encode_frame(nodes, constraints=cons, embodied=False, extended_meta=False)
    fr = decode_frame(blob)
    print("=== plod_spec_codec v1.1 demo ===")
    print(f"encoded {len(blob)} bytes  flags=0x{fr.flags:02x}  nodes={len(fr.nodes)}  constraints={len(fr.constraints)}")
    print("decode_frame OK (CRC enforced)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        demo()
    else:
        demo()
