#!/usr/bin/env python3
"""Generate RFC-aligned golden P-LOD vectors (stdlib only). Little-Endian."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

MAGIC = 0x504C
# Spec v1.1 FLAGS
HAS_CONSTRAINT_TABLE = 0x01
IS_EMBODIED_PROFILE = 0x02
HAS_EXTENDED_META = 0x04

GLOBAL_NA = 0xFFFF
CORE_FMT = "<HBB3f3BBf"  # 24 bytes
OUT = Path(__file__).resolve().parent / "vectors"


def header(ver: int, flags: int, n: int, seq: int = 1) -> bytes:
    return struct.pack("<HBBHH", MAGIC, ver, flags & 0xFF, n & 0xFFFF, seq & 0xFFFF)


def core_node(nid: int, x: float, y: float, z: float) -> bytes:
    return struct.pack(CORE_FMT, nid, 1, 0, x, y, z, 0, 0, 0, 0, 0.0)


def constraint_entry(ctype: int, a: int, b: int, p0: float, p1: float = 0.0) -> bytes:
    return struct.pack("<BBHHffH", ctype & 0xFF, 0, a & 0xFFFF, b & 0xFFFF, p0, p1, 0)


def with_crc(payload: bytes, corrupt: bool = False) -> bytes:
    # CRC-32/ISO-HDLC via zlib (poly 0x04C11DB7, init/xor 0xFFFFFFFF, reflected)
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    if corrupt:
        crc ^= 0xA5A5A5A5
    return payload + struct.pack("<I", crc)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- golden_core_v11.plod: Header + 4 core nodes + 2 constraints + CRC ---
    n = 4
    flags = HAS_CONSTRAINT_TABLE  # core profile, no meta
    payload = bytearray(header(0x11, flags, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += core_node(i, math.cos(ang), math.sin(ang), 0.0)  # node_id 0..3 valid

    # constraint_count = 2
    payload += struct.pack("<H", 2)
    # Distance between node 0 and 1
    payload += constraint_entry(0x01, 0, 1, 2.5)
    # Global boundary (node_a = node_b = 0xFFFF)
    payload += constraint_entry(0x02, GLOBAL_NA, GLOBAL_NA, 1.75)

    (OUT / "golden_core_v11.plod").write_bytes(with_crc(bytes(payload)))
    (OUT / "golden_invalid_crc.plod").write_bytes(with_crc(bytes(payload), corrupt=True))

    # Keep legacy names for older tests / demos
    n = 8
    payload = bytearray(header(0x10, 0, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    (OUT / "minimal_valid.plod").write_bytes(with_crc(bytes(payload)))
    (OUT / "invalid_crc.plod").write_bytes(with_crc(bytes(payload), corrupt=True))

    # Embodied + extended meta (FLAGS bit1 + bit2)
    n = 16
    flags = IS_EMBODIED_PROFILE | HAS_EXTENDED_META
    payload = bytearray(header(0x11, flags, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        body = struct.pack(
            "<HBB3f3ff",
            i + 1,
            0,
            0x30,
            math.cos(ang),
            math.sin(ang),
            0.1 * math.sin(ang),
            0.0,
            0.0,
            0.0,
            0.0,
        )
        body += struct.pack("<fBxxx", 1.0 + 0.01 * i, (100 + i * 5) & 0xFF)
        payload += body
    (OUT / "embodied_32b.plod").write_bytes(with_crc(bytes(payload)))

    # Unknown reserved flag bit (bit 5) — must still parse
    payload = bytearray(header(0x10, 0x20, 4))
    for i in range(4):
        payload += core_node(i + 1, float(i), 0.0, 0.0)
    (OUT / "unknown_extension.plod").write_bytes(with_crc(bytes(payload)))

    print(f"Wrote vectors to {OUT}")
    for p in sorted(OUT.glob("*.plod")):
        print(f"  {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
