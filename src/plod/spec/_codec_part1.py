#!/usr/bin/env python3
"""
P-LOD Spec v1.1 public codec (stdlib only).

Strict encoding: no silent &0xFF truncation — out-of-range values raise ProtocolError.
node_id 0..65534 only (0xFFFF reserved as GLOBAL_NA).

Usage:
  python plod_spec_codec.py
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
    _require_int_range(n.node_id, 0, MAX_NODE_ID, "node_id")  # excludes 0xFFFF
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

