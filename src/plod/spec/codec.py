#!/usr/bin/env python3
"""
P-LOD Spec v1.1 public codec (stdlib only).

Normative package module: plod.spec.codec

Strict encoding: no silent &0xFF truncation — out-of-range values raise ProtocolError.
node_id 0..65534 only (0xFFFF reserved as GLOBAL_NA).
"""

from __future__ import annotations

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
MAX_NODE_ID = 65534
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


def _check_finite(val: float, field_name: str = "value") -> float:
    if not math.isfinite(val):
        raise ProtocolError(f"Invalid non-finite float detected in [{field_name}]")
    return float(val)


def _check_int(val: int, lo: int, hi: int, name: str) -> int:
    if not isinstance(val, int) or isinstance(val, bool):
        raise ProtocolError(f"{name} must be int, got {type(val).__name__}")
    if val < lo or val > hi:
        raise ProtocolError(f"{name}={val} out of range [{lo}..{hi}]")
    return val


def _check_unique_node_ids(nodes: Sequence[SENode]) -> None:
    seen = set()
    for n in nodes:
        if n.node_id in seen:
            raise ProtocolError("Duplicate node_id detected in SE Node Table")
        seen.add(n.node_id)


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def encode_frame(
    nodes: Sequence[SENode],
    *,
    constraints: Optional[Sequence[Constraint]] = None,
    embodied: bool = False,
    extended_meta: bool = False,
    version: int = VERSION_V11,
    sequence_id: int = 0,
) -> bytes:
    constraints = list(constraints or [])
    version = _check_int(version, 0, 255, "version")
    if version not in (VERSION_V10, VERSION_V11):
        raise ProtocolError(f"version must be 0x10 or 0x11, got {version:#x}")
    sequence_id = _check_int(sequence_id, 0, MAX_U16, "sequence_id")
    if len(nodes) > MAX_SE_NODES:
        raise ProtocolError("MAX_SE_NODES exceeded")
    _check_unique_node_ids(nodes)

    if version == VERSION_V10 and (constraints or extended_meta):
        raise ProtocolError("v1.0 forbids Constraint Table and Extended Meta")
    if len(constraints) > MAX_CONSTRAINTS:
        raise ProtocolError("MAX_CONSTRAINTS exceeded")

    id_set = {n.node_id for n in nodes}
    for c in constraints:
        if c.node_a != GLOBAL_NA and c.node_a not in id_set:
            raise ProtocolError(f"constraint node_a {c.node_a} out of SE set")
        if c.node_b != GLOBAL_NA and c.node_b not in id_set:
            raise ProtocolError(f"constraint node_b {c.node_b} out of SE set")

    flags = 0
    if constraints:
        flags |= FLAG_HAS_CONSTRAINT_TABLE
    if embodied:
        flags |= FLAG_IS_EMBODIED_PROFILE
    if extended_meta:
        flags |= FLAG_HAS_EXTENDED_META

    parts: List[bytes] = []
    header = struct.pack(
        "<HBBHH",
        MAGIC,
        version,
        flags,
        len(nodes),
        sequence_id,
    )
    parts.append(header)

    for n in nodes:
        nid = _check_int(n.node_id, 0, MAX_NODE_ID, "node_id")
        x, y, z = (_check_finite(n.pos[0], "x"), _check_finite(n.pos[1], "y"), _check_finite(n.pos[2], "z"))
        if embodied:
            vx, vy, vz = (
                _check_finite(n.vel[0], "vx"),
                _check_finite(n.vel[1], "vy"),
                _check_finite(n.vel[2], "vz"),
            )
            parts.append(
                struct.pack(
                    "<HBB3f3f f",
                    nid,
                    _check_int(n.risk_state, 0, 255, "risk_state"),
                    _check_int(n.sub_system, 0, 255, "sub_system"),
                    x, y, z,
                    vx, vy, vz,
                    _check_finite(n.phase, "phase"),
                )
            )
        else:
            r, g, b = n.rgb
            parts.append(
                struct.pack(
                    CORE_FMT,
                    nid,
                    _check_int(n.level, 1, 3, "level"),
                    _check_int(n.type_code, 0, 255, "type_code"),
                    x, y, z,
                    _check_int(r, 0, 255, "r"),
                    _check_int(g, 0, 255, "g"),
                    _check_int(b, 0, 255, "b"),
                    _check_int(n.node_flags, 0, 255, "node_flags"),
                    _check_finite(n.param0, "param0"),
                )
            )
        if extended_meta:
            parts.append(
                struct.pack(
                    "<fBBH",
                    _check_finite(n.resonance_freq, "resonance_freq"),
                    _check_int(n.causal_depth, 0, 255, "causal_depth"),
                    0,
                    0,
                )
            )

    if constraints:
        parts.append(struct.pack("<H", len(constraints)))
        for c in constraints:
            parts.append(
                struct.pack(
                    "<BHH ff BB",
                    _check_int(c.ctype, 0, 255, "ctype"),
                    _check_int(c.node_a, 0, MAX_U16, "node_a"),
                    _check_int(c.node_b, 0, MAX_U16, "node_b"),
                    _check_finite(c.param0, "c.param0"),
                    _check_finite(c.param1, "c.param1"),
                    0,
                    0,
                )
            )

    body = b"".join(parts)
    if len(body) + 4 > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")
    crc = _crc32(body)
    return body + struct.pack("<I", crc)


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

    off = 8
    nodes: List[SENode] = []
    node_size = EMBODIED_SIZE if embodied else CORE_SIZE
    meta_extra = META_SIZE if has_meta else 0

    for _ in range(count):
        if off + node_size > len(data) - 4:
            raise ProtocolError("truncated node table")
        if embodied:
            nid, risk, sub, x, y, z, vx, vy, vz, phase = struct.unpack_from("<HBB3f3ff", data, off)
            off += EMBODIED_SIZE
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
            n = SENode(
                node_id=nid,
                pos=(_check_finite(x, "x"), _check_finite(y, "y"), _check_finite(z, "z")),
                risk_state=risk,
                sub_system=sub,
                vel=(_check_finite(vx, "vx"), _check_finite(vy, "vy"), _check_finite(vz, "vz")),
                phase=_check_finite(phase, "phase"),
            )
        else:
            nid, level, tcode, x, y, z, r, g, b, nflags, p0 = struct.unpack_from(CORE_FMT, data, off)
            off += CORE_SIZE
            if nid == GLOBAL_NA:
                raise ProtocolError("node_id must not be 0xFFFF (GLOBAL_NA reserved)")
            n = SENode(
                node_id=nid,
                pos=(_check_finite(x, "x"), _check_finite(y, "y"), _check_finite(z, "z")),
                level=level,
                type_code=tcode,
                rgb=(r, g, b),
                node_flags=nflags,
                param0=_check_finite(p0, "param0"),
            )
        if has_meta:
            if off + META_SIZE > len(data) - 4:
                raise ProtocolError("truncated Extended Meta")
            rf, cd, pad, reserved = struct.unpack_from("<fBBH", data, off)
            off += META_SIZE
            if pad != 0 or reserved != 0:
                raise ProtocolError("Extended Meta pad must be zero")
            n.resonance_freq = _check_finite(rf, "resonance_freq")
            n.causal_depth = cd
        nodes.append(n)

    _check_unique_node_ids(nodes)
    id_set = {n.node_id for n in nodes}

    constraints: List[Constraint] = []
    if has_ct:
        if off + 2 > len(data) - 4:
            raise ProtocolError("truncated constraint count")
        (n_ct,) = struct.unpack_from("<H", data, off)
        off += 2
        if n_ct > MAX_CONSTRAINTS:
            raise ProtocolError("too many constraints")
        for _ in range(n_ct):
            if off + CONSTRAINT_SIZE > len(data) - 4:
                raise ProtocolError("truncated constraint entry")
            ctype, na, nb, p0, p1, cflags, reserved = struct.unpack_from("<BHHffBB", data, off)
            off += CONSTRAINT_SIZE
            if cflags != 0 or reserved != 0:
                raise ProtocolError("constraint reserved/cflags must be zero")
            if na != GLOBAL_NA and na not in id_set:
                raise ProtocolError(f"constraint node_a {na} out of SE set")
            if nb != GLOBAL_NA and nb not in id_set:
                raise ProtocolError(f"constraint node_b {nb} out of SE set")
            constraints.append(
                Constraint(
                    ctype=ctype,
                    node_a=na,
                    node_b=nb,
                    param0=_check_finite(p0, "c.param0"),
                    param1=_check_finite(p1, "c.param1"),
                )
            )

    if off + 4 != len(data):
        raise ProtocolError("trailing garbage or truncated CRC")
    (crc_stored,) = struct.unpack_from("<I", data, off)
    crc_calc = _crc32(data[:off])
    if crc_stored != crc_calc:
        raise ProtocolError("CRC32 mismatch")

    return DecodedFrame(
        version=ver,
        flags=flags,
        sequence_id=seq,
        nodes=nodes,
        constraints=constraints,
    )
