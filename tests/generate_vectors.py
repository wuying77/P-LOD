#!/usr/bin/env python3
"""Generate golden P-LOD test vectors (stdlib only). Run from repo root or tests/."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4
FLAG_UNKNOWN = 1 << 5  # reserved/unknown for forward-compat test

OUT = Path(__file__).resolve().parent / "vectors"


def header(ver: int, flags: int, n: int, seq: int = 1) -> bytes:
    return struct.pack("<HBBHH", MAGIC, ver, flags & 0xFF, n & 0xFFFF, seq & 0xFFFF)


def core_node(nid: int, x: float, y: float, z: float) -> bytes:
    return struct.pack("<HBB3f3Bf", nid, 1, 0, x, y, z, 0, 0, 0, 0, 0.0)


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

    # minimal_valid: 8 core nodes, no embodied, no meta — small valid SE
    n = 8
    payload = bytearray(header(0x10, 0, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    (OUT / "minimal_valid.plod").write_bytes(with_crc(bytes(payload)))

    # embodied_32b: 16 embodied + extended meta
    n = 16
    flags = FLAG_EMBODIED | FLAG_EXTENDED_META
    payload = bytearray(header(0x11, flags, n))
    for i in range(n):
        ang = 2 * math.pi * i / n
        payload += embodied_node(
            i + 1, math.cos(ang), math.sin(ang), 0.1 * math.sin(ang), 100 + i * 5
        )
    (OUT / "embodied_32b.plod").write_bytes(with_crc(bytes(payload)))

    # invalid_crc: same as minimal but bad CRC
    payload = bytearray(header(0x10, 0, n))
    for i in range(8):
        ang = 2 * math.pi * i / 8
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    # rewrite with correct n
    payload = bytearray(header(0x10, 0, 8))
    for i in range(8):
        ang = 2 * math.pi * i / 8
        payload += core_node(i + 1, math.cos(ang), math.sin(ang), 0.0)
    (OUT / "invalid_crc.plod").write_bytes(with_crc(bytes(payload), corrupt=True))

    # unknown_extension: unknown flag bit set; still parseable core nodes
    flags = FLAG_UNKNOWN
    payload = bytearray(header(0x10, flags, 4))
    for i in range(4):
        payload += core_node(i + 1, float(i), 0.0, 0.0)
    (OUT / "unknown_extension.plod").write_bytes(with_crc(bytes(payload)))

    print(f"Wrote vectors to {OUT}")
    for p in sorted(OUT.glob("*.plod")):
        print(f"  {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
