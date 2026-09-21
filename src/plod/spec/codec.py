#!/usr/bin/env python3
"""
P-LOD Spec v1.1 public codec (stdlib only).

Normative package module: ``plod.spec.codec``.

Strict encoding: no silent &0xFF truncation — out-of-range values raise ProtocolError.
node_id 0..65534 only (0xFFFF reserved as GLOBAL_NA).
Canonical wire order: nodes sorted by node_id; constraints sorted by
(ctype, node_a, node_b, param0, param1) so semantic equality ⇒ byte equality.
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

FLAG_HAS_CONSTRAINT_TABLE = 1 << 0
FLAG_IS_EMBODIED_PROFILE = 1 << 1
FLAG_HAS_EXTENDED_META = 1 << 2

KNOWN_FLAGS = (
    FLAG_HAS_CONSTRAINT_TABLE
    | FLAG_IS_EMBODIED_PROFILE
    | FLAG_HAS_EXTENDED_META
)

GLOBAL_NA = 0xFFFF
MAX_NODE_ID = 65534  # 0xFFFF reserved
MAX_SE_NODES = 65535
MAX_CONSTRAINTS = 65535
MAX_FRAME_SIZE = 16 * 1024 * 1024
MAX_U16 = 65535

CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = 24
EMBODIED_SIZE = 32
META_SIZE = 8
CONSTRAINT_SIZE = 16


class ProtocolError(Exception):
    pass


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


def _check_finite(x: float, field_name: str) -> None:
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        raise ProtocolError(f"Invalid non-finite float detected in [{field_name}]")


def _require_int_range(val: int, lo: int, hi: int, name: str) -> None:
    if not isinstance(val, int) or isinstance(val, bool):
        raise ProtocolError(f"{name} must be int, got {type(val).__name__}")
    if val < lo or val > hi:
        raise ProtocolError(f"{name}={val} out of range [{lo}..{hi}]")


def _assert_unique_node_ids(nodes: Sequence[SENode]) -> None:
    ids = [n.node_id for n in nodes]
    if len(ids) != len(set(ids)):
        raise ProtocolError("Duplicate node_id detected in SE Node Table")


def _validate_node_for_encode(n: SENode, embodied: bool) -> None:
    _require_int_range(n.node_id, 0, MAX_NODE_ID, "node_id")
    _check_finite(n.pos[0], "pos.x")
    _check_finite(n.pos[1], "pos.y")
    _check_finite(n.pos[2], "pos.z")
    if embodied:
        _require_int_range(n.risk_state, 0, 2, "risk_state")
        _require_int_range(n.sub_system, 0, 255, "sub_system")
        _check_finite(n.vel[0], "vel.x")
        _check_finite(n.vel[1], "vel.y")
        _check_finite(n.vel[2], "vel.z")
        _check_finite(n.phase, "phase")
    else:
        _require_int_range(n.level, 1, 3, "level")
        _require_int_range(n.type_code, 0, 255, "type_code")
        for i, c in enumerate(n.rgb):
            _require_int_range(int(c), 0, 255, f"rgb[{i}]")
        _require_int_range(n.node_flags, 0, 255, "node_flags")
        _check_finite(n.param0, "param0")
    _check_finite(n.resonance_freq, "resonance_freq")
    _require_int_range(n.causal_depth, 0, 255, "causal_depth")


def encode_frame(
    nodes: Sequence[SENode],
    *,
    constraints: Optional[Sequence[Constraint]] = None,
    embodied: bool = False,
    extended_meta: bool = False,
    version: int = VERSION_V11,
    sequence_id: int = 1,
) -> bytes:
    if version not in (VERSION_V10, VERSION_V11):
        raise ProtocolError(f"version must be 0x10 or 0x11, got {version:#x}")
    _require_int_range(sequence_id, 0, MAX_U16, "sequence_id")
    if len(nodes) > MAX_SE_NODES:
        raise ProtocolError("MAX_SE_NODES exceeded")
    _assert_unique_node_ids(nodes)

    # Canonical wire order: semantic equality ⇒ byte equality
    nodes = sorted(nodes, key=lambda n: n.node_id)
    cons = list(constraints or [])
    cons.sort(key=lambda c: (c.ctype, c.node_a, c.node_b, c.param0, c.param1))

    if version == VERSION_V10 and (cons or extended_meta):
        raise ProtocolError("v1.0 forbids Constraint Table and Extended Meta")
    if len(cons) > MAX_CONSTRAINTS:
        raise ProtocolError("MAX_CONSTRAINTS exceeded")

    for n in nodes:
        _validate_node_for_encode(n, embodied)

    id_set = {n.node_id for n in nodes}
    for c in cons:
        _require_int_range(c.ctype, 0, 255, "constraint_type")
        _check_finite(c.param0, "constraint.param0")
        _check_finite(c.param1, "constraint.param1")
        if c.node_a != GLOBAL_NA and c.node_a not in id_set:
            raise ProtocolError(f"constraint node_a {c.node_a} out of SE set")
        if c.node_b != GLOBAL_NA and c.node_b not in id_set:
            raise ProtocolError(f"constraint node_b {c.node_b} out of SE set")
        if c.node_a != GLOBAL_NA:
            _require_int_range(c.node_a, 0, MAX_NODE_ID, "constraint.node_a")
        if c.node_b != GLOBAL_NA:
            _require_int_range(c.node_b, 0, MAX_NODE_ID, "constraint.node_b")

    flags = 0
    if cons:
        flags |= FLAG_HAS_CONSTRAINT_TABLE
    if embodied:
        flags |= FLAG_IS_EMBODIED_PROFILE
    if extended_meta:
        flags |= FLAG_HAS_EXTENDED_META

    body = bytearray()
    body += struct.pack("<HBBHH", MAGIC, version, flags, len(nodes), sequence_id)

    for n in nodes:
        if embodied:
            body += struct.pack(
                "<HBB3f3ff",
                n.node_id,
                n.risk_state,
                n.sub_system,
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
                n.node_id,
                n.level,
                n.type_code,
                float(n.pos[0]),
                float(n.pos[1]),
                float(n.pos[2]),
                int(n.rgb[0]),
                int(n.rgb[1]),
                int(n.rgb[2]),
                n.node_flags,
                float(n.param0),
            )
        if extended_meta:
            body += struct.pack("<fBxxx", float(n.resonance_freq), n.causal_depth)

    if cons:
        body += struct.pack("<H", len(cons))
        for c in cons:
            body += struct.pack(
                "<BBHHffH",
                c.ctype,
                0,
                c.node_a,
                c.node_b,
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
    if flags & ~KNOWN_FLAGS:
        raise ProtocolError(f"unknown header flags 0x{flags:02X}")
    if count > MAX_SE_NODES:
        raise ProtocolError("SE_NODE_COUNT exceeds MAX_SE_NODES")

    embodied = bool(flags & FLAG_IS_EMBODIED_PROFILE)
    has_meta = bool(flags & FLAG_HAS_EXTENDED_META)
    has_ct = bool(flags & FLAG_HAS_CONSTRAINT_TABLE)
    if ver == VERSION_V10 and (has_meta or has_ct):
        raise ProtocolError("v1.0 frame must not set Extended Meta or Constraint Table flags")

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
            for v, name in (
                (px, "pos.x"),
                (py, "pos.y"),
                (pz, "pos.z"),
                (vx, "vel.x"),
                (vy, "vel.y"),
                (vz, "vel.z"),
                (phase, "phase"),
            ):
                _check_finite(v, name)
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
            if risk < 0 or risk > 2:
                raise ProtocolError(f"risk_state={risk} out of range [0..2]")
            if sub < 0 or sub > 255:
                raise ProtocolError(f"sub_system={sub} out of range [0..255]")
            node = SENode(
                nid, (px, py, pz), risk_state=risk, sub_system=sub, vel=(vx, vy, vz), phase=phase
            )
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                CORE_FMT, data, off
            )
            off += CORE_SIZE
            for v, name in ((px, "pos.x"), (py, "pos.y"), (pz, "pos.z"), (p0, "param0")):
                _check_finite(v, name)
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
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
            _check_finite(freq, "resonance_freq")
            node.resonance_freq = freq
            node.causal_depth = depth
        nodes.append(node)

    _assert_unique_node_ids(nodes)
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
            _check_finite(p0, "constraint.param0")
            _check_finite(p1, "constraint.param1")
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
    blob = encode_frame(nodes, constraints=cons)
    fr = decode_frame(blob)
    print("=== plod_spec_codec v1.1 demo ===")
    print(f"encoded {len(blob)} bytes  flags=0x{fr.flags:02x}  nodes={len(fr.nodes)}")
    print("strict encode + decode OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="P-LOD Spec v1.1 codec")
    ap.add_argument(
        "--demo",
        action="store_true",
        help="Run encode/decode demo (default if no other action)",
    )
    args = ap.parse_args()
    demo()
