#!/usr/bin/env python3
"""Generate golden P-LOD test vectors (stdlib only)."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4
FLAG_UNKNOWN = 1 << 5

OUT = Path(__file__).resolve().parent / "vectors"

# Core 24B: id u16, level u8, type u8, xyz f32*3, rgb u8*3, flags u8, param0 f32
CORE_FMT = "<HBB3f3BBf"  # 11 fields, 24 bytes


def header(ver: int, flags: int, n: int, seq: int = 1) -> bytes:
    return struct.pack("<HBBHH", MAGIC, ver, flags & 0xFF, n & 0xFFFF, seq & 0xFFFF)


def core_node(nid: int, x: float, y: float, z: float) -> bytes:
    return struct.pack(CORE_FMT, nid, 1, 0, x, y, z, 0, 0, 0, 0, 0.0)


def embodied_node(nid: int, x: float, y: float, z: float, depth: int = 128) -> bytes:
    body = struct.pack(
        "<HBB3f3ff",
        nid,
        0,
        0x30,
        x,
        y,
        z,
        0.0,
        0.0,
        0.0,
        0.0,
    )
    body += struct.pack("<fBxxx", 1.0 + 0.01 * nid, depth & 0xFF)
    return body


def with_crc(payload: bytes, corrupt: bool = False) -> bytes:
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    if corrupt:
        crc ^= 0xFFFFFFFF
    return payload + struct.pack("<I", crc)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    n = 8
    payload = bytearray(header(0x10, 0, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    (OUT / "minimal_valid.plod").write_bytes(with_crc(bytes(payload)))

    n = 16
    flags = FLAG_EMBODIED | FLAG_EXTENDED_META
    payload = bytearray(header(0x11, flags, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += embodied_node(
            i + 1, math.cos(ang), math.sin(ang), 0.1 * math.sin(ang), 100 + i * 5
        )
    (OUT / "embodied_32b.plod").write_bytes(with_crc(bytes(payload)))

    payload = bytearray(header(0x10, 0, 8))
    for i in range(8):
        ang = 2 * math.pi * i / 8
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    (OUT / "invalid_crc.plod").write_bytes(with_crc(bytes(payload), corrupt=True))

    payload = bytearray(header(0x10, FLAG_UNKNOWN, 4))
    for i in range(4):
        payload += core_node(i + 1, float(i), 0.0, 0.0)
    (OUT / "unknown_extension.plod").write_bytes(with_crc(bytes(payload)))

    print(f"Wrote vectors to {OUT}")
    for p in sorted(OUT.glob("*.plod")):
        print(f"  {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
