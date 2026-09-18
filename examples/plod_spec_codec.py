#!/usr/bin/env python3
"""
P-LOD Protocol Specification v1.0 — Python reference codec

Pack / unpack:
  - 8-byte header
  - Core profile nodes (24 bytes each)  OR  Embodied profile nodes (32 bytes each)
  - Optional topology edge list
  - Optional CRC32 trailer

See docs/SPECIFICATION.md

Usage:
  python plod_spec_codec.py              # self-test round-trip
  python plod_spec_codec.py --demo       # pack a tiny embodied frame and print sizes
"""

from __future__ import annotations

import argparse
import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

MAGIC = 0x504C  # 'P''L'
VERSION = 0x10  # v1.0

FLAG_WE_PRESENT = 1 << 0
FLAG_TOPOLOGY_INLINE = 1 << 1
FLAG_EMBODIED_PROFILE = 1 << 2
FLAG_FORWARD_FOCUS = 1 << 3

# type_code for core profile (illustrative enum)
TYPE_CODES = {
    "solid": 1,
    "hollow": 2,
    "semi-hollow": 3,
    "joint": 4,
    "end": 5,
    "control": 6,
    "emitter": 7,
}
TYPE_NAMES = {v: k for k, v in TYPE_CODES.items()}


@dataclass
class CoreNode:
    node_id: int
    level: int
    type_name: str
    x: float
    y: float
    z: float = 0.0
    r: int = 0
    g: int = 0
    b: int = 0
    flags: int = 0
    param0: float = 0.0


@dataclass
class EmbodiedNode:
    node_id: int
    risk_state: int  # 0 SAFE, 1 WATCH, 2 CRITICAL
    sub_system: int  # 0x10 upper, 0x20 lower, 0x30 peripheral
    pos: Tuple[float, float, float]
    vel: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    phase_angle: float = 0.0
    reserved: int = 0


@dataclass
class PlodPacket:
    sequence_id: int = 0
    flags: int = 0
    core_nodes: List[CoreNode] = field(default_factory=list)
    embodied_nodes: List[EmbodiedNode] = field(default_factory=list)
    edges: List[Tuple[int, int]] = field(default_factory=list)
    we_blob: Optional[bytes] = None  # optional weak payload (not required for structure)

    @property
    def embodied(self) -> bool:
        return bool(self.flags & FLAG_EMBODIED_PROFILE)


def _pack_header(node_count: int, flags: int, sequence_id: int) -> bytes:
    return struct.pack(
        "<HBBHH",
        MAGIC,
        VERSION,
        flags & 0xFF,
        node_count & 0xFFFF,
        sequence_id & 0xFFFF,
    )


def _unpack_header(data: bytes, offset: int = 0):
    magic, version, flags, node_count, sequence_id = struct.unpack_from(
        "<HBBHH", data, offset
    )
    if magic != MAGIC:
        raise ValueError(f"bad magic: 0x{magic:04X}")
    if version != VERSION:
        raise ValueError(f"unsupported version: 0x{version:02X}")
    return flags, node_count, sequence_id, offset + 8


def pack_core_node(n: CoreNode) -> bytes:
    tc = TYPE_CODES.get(n.type_name, 0)
    return struct.pack(
        "<HBB fff BBBB f",
        n.node_id & 0xFFFF,
        n.level & 0xFF,
        tc & 0xFF,
        float(n.x),
        float(n.y),
        float(n.z),
        n.r & 0xFF,
        n.g & 0xFF,
        n.b & 0xFF,
        n.flags & 0xFF,
        float(n.param0),
    )


def unpack_core_node(data: bytes, offset: int) -> Tuple[CoreNode, int]:
    node_id, level, tc, x, y, z, r, g, b, flags, param0 = struct.unpack_from(
        "<HBB fff BBBB f", data, offset
    )
    return (
        CoreNode(
            node_id=node_id,
            level=level,
            type_name=TYPE_NAMES.get(tc, f"type_{tc}"),
            x=x,
            y=y,
            z=z,
            r=r,
            g=g,
            b=b,
            flags=flags,
            param0=param0,
        ),
        offset + 24,
    )


def pack_embodied_node(n: EmbodiedNode) -> bytes:
    px, py, pz = n.pos
    vx, vy, vz = n.vel
    return struct.pack(
        "<HBB fff fff f I",
        n.node_id & 0xFFFF,
        n.risk_state & 0xFF,
        n.sub_system & 0xFF,
        float(px),
        float(py),
        float(pz),
        float(vx),
        float(vy),
        float(vz),
        float(n.phase_angle),
        n.reserved & 0xFFFFFFFF,
    )


def unpack_embodied_node(data: bytes, offset: int) -> Tuple[EmbodiedNode, int]:
    (
        node_id,
        risk,
        sub,
        px,
        py,
        pz,
        vx,
        vy,
        vz,
        phase,
        reserved,
    ) = struct.unpack_from("<HBB fff fff f I", data, offset)
    return (
        EmbodiedNode(
            node_id=node_id,
            risk_state=risk,
            sub_system=sub,
            pos=(px, py, pz),
            vel=(vx, vy, vz),
            phase_angle=phase,
            reserved=reserved,
        ),
        offset + 32,
    )


def pack_packet(pkt: PlodPacket, with_crc: bool = True) -> bytes:
    embodied = bool(pkt.flags & FLAG_EMBODIED_PROFILE)
    nodes = pkt.embodied_nodes if embodied else pkt.core_nodes
    node_count = len(nodes)

    flags = pkt.flags
    if pkt.edges:
        flags |= FLAG_TOPOLOGY_INLINE
    if pkt.we_blob:
        flags |= FLAG_WE_PRESENT

    body = bytearray()
    body += _pack_header(node_count, flags, pkt.sequence_id)

    if embodied:
        for n in pkt.embodied_nodes:
            body += pack_embodied_node(n)
    else:
        for n in pkt.core_nodes:
            body += pack_core_node(n)

    if flags & FLAG_TOPOLOGY_INLINE:
        body += struct.pack("<H", len(pkt.edges) & 0xFFFF)
        for a, b in pkt.edges:
            body += struct.pack("<HH", a & 0xFFFF, b & 0xFFFF)

    if flags & FLAG_WE_PRESENT:
        blob = pkt.we_blob or b""
        body += struct.pack("<I", len(blob))
        body += blob

    if with_crc:
        crc = zlib.crc32(bytes(body)) & 0xFFFFFFFF
        body += struct.pack("<I", crc)

    return bytes(body)


def unpack_packet(data: bytes, expect_crc: bool = True) -> PlodPacket:
    flags, node_count, sequence_id, off = _unpack_header(data)
    embodied = bool(flags & FLAG_EMBODIED_PROFILE)

    core_nodes: List[CoreNode] = []
    embodied_nodes: List[EmbodiedNode] = []

    if embodied:
        for _ in range(node_count):
            node, off = unpack_embodied_node(data, off)
            embodied_nodes.append(node)
    else:
        for _ in range(node_count):
            node, off = unpack_core_node(data, off)
            core_nodes.append(node)

    edges: List[Tuple[int, int]] = []
    if flags & FLAG_TOPOLOGY_INLINE:
        (edge_count,) = struct.unpack_from("<H", data, off)
        off += 2
        for _ in range(edge_count):
            a, b = struct.unpack_from("<HH", data, off)
            edges.append((a, b))
            off += 4

    we_blob = None
    if flags & FLAG_WE_PRESENT:
        (blen,) = struct.unpack_from("<I", data, off)
        off += 4
        we_blob = data[off : off + blen]
        off += blen

    if expect_crc:
        if off + 4 > len(data):
            raise ValueError("missing CRC trailer")
        (crc_read,) = struct.unpack_from("<I", data, off)
        crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
        if crc_read != crc_calc:
            raise ValueError(f"CRC mismatch: got 0x{crc_read:08X}, expected 0x{crc_calc:08X}")

    return PlodPacket(
        sequence_id=sequence_id,
        flags=flags,
        core_nodes=core_nodes,
        embodied_nodes=embodied_nodes,
        edges=edges,
        we_blob=we_blob,
    )


def _self_test() -> None:
    # Core profile: 3 nodes + edges (like a tiny triangle)
    core = PlodPacket(
        sequence_id=1,
        flags=0,
        core_nodes=[
            CoreNode(1, 1, "end", 0.0, 1.0, 0.0),
            CoreNode(2, 1, "end", -1.0, 0.0, 0.0),
            CoreNode(3, 1, "end", 1.0, 0.0, 0.0),
        ],
        edges=[(1, 2), (1, 3), (2, 3)],
    )
    raw = pack_packet(core)
    back = unpack_packet(raw)
    assert len(back.core_nodes) == 3
    assert back.edges == [(1, 2), (1, 3), (2, 3)]
    assert abs(back.core_nodes[0].y - 1.0) < 1e-6

    # Embodied profile: 2 nodes
    emb = PlodPacket(
        sequence_id=7,
        flags=FLAG_EMBODIED_PROFILE | FLAG_FORWARD_FOCUS,
        embodied_nodes=[
            EmbodiedNode(
                node_id=10,
                risk_state=0,
                sub_system=0x20,
                pos=(1.0, 0.0, 0.5),
                vel=(0.1, 0.0, 0.0),
                phase_angle=0.25,
            ),
            EmbodiedNode(
                node_id=11,
                risk_state=1,
                sub_system=0x10,
                pos=(1.2, 0.1, 0.8),
                vel=(0.0, 0.05, 0.0),
                phase_angle=-0.1,
            ),
        ],
    )
    raw2 = pack_packet(emb)
    back2 = unpack_packet(raw2)
    assert len(back2.embodied_nodes) == 2
    assert back2.embodied_nodes[1].risk_state == 1
    assert back2.flags & FLAG_EMBODIED_PROFILE

    print("self-test OK")
    print(f"  core packet size:     {len(raw)} bytes")
    print(f"  embodied packet size: {len(raw2)} bytes")


def _demo_size() -> None:
    """Show SE-Frame size for N embodied nodes (Spec §7 style)."""
    n = 80
    nodes = [
        EmbodiedNode(
            i,
            risk_state=0,
            sub_system=0x30,
            pos=(float(i) * 0.01, 0.0, 0.0),
        )
        for i in range(n)
    ]
    pkt = PlodPacket(
        sequence_id=0,
        flags=FLAG_EMBODIED_PROFILE,
        embodied_nodes=nodes,
    )
    raw = pack_packet(pkt, with_crc=True)
    print(f"Embodied SE-Frame: {n} nodes")
    print(f"  packed size = {len(raw)} bytes ({len(raw)/1024:.2f} KB)")
    print(f"  (header 8 + {n}*32 + crc 4 = {8 + n*32 + 4} without topology)")


def main() -> None:
    ap = argparse.ArgumentParser(description="P-LOD Spec v1.0 reference codec")
    ap.add_argument("--demo", action="store_true", help="print 80-node embodied frame size")
    args = ap.parse_args()
    _self_test()
    if args.demo:
        _demo_size()


if __name__ == "__main__":
    main()
