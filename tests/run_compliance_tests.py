#!/usr/bin/env python3
"""P-LOD golden-vector compliance tests (stdlib only)."""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

VEC = Path(__file__).resolve().parent / "vectors"
MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4
CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = struct.calcsize(CORE_FMT)


def parse_frame(data: bytes):
    if len(data) < 12:
        raise ValueError("too short")
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ValueError(f"bad magic {magic:#x}")
    embodied = bool(flags & FLAG_EMBODIED)
    ext = bool(flags & FLAG_EXTENDED_META)
    off = 8
    nodes = []
    for _ in range(count):
        if embodied:
            if off + 32 > len(data) - 4:
                raise ValueError("truncated embodied")
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from(
                "<HBB3f3ff", data, off
            )
            off += 32
            node = {"id": nid, "pos": (px, py, pz)}
        else:
            if off + CORE_SIZE > len(data) - 4:
                raise ValueError("truncated core")
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                CORE_FMT, data, off
            )
            off += CORE_SIZE
            node = {"id": nid, "pos": (px, py, pz)}
        if ext:
            if off + 8 > len(data) - 4:
                raise ValueError("truncated meta")
            freq, depth = struct.unpack_from("<fB", data, off)
            off += 8
            node["resonance_freq"] = freq
            node["causal_depth"] = depth
        nodes.append(node)
    crc_stored = struct.unpack_from("<I", data, off)[0]
    crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
    return {
        "version": ver,
        "flags": flags,
        "count": count,
        "nodes": nodes,
        "crc_ok": crc_stored == crc_calc,
    }


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_minimal_valid() -> None:
    r = parse_frame((VEC / "minimal_valid.plod").read_bytes())
    expect(r["crc_ok"], "CRC")
    expect(r["count"] == 8, "8 nodes")
    print("[PASS] minimal_valid.plod")


def test_embodied_32b() -> None:
    r = parse_frame((VEC / "embodied_32b.plod").read_bytes())
    expect(r["crc_ok"], "CRC")
    expect(bool(r["flags"] & FLAG_EMBODIED), "embodied")
    expect(bool(r["flags"] & FLAG_EXTENDED_META), "meta")
    expect(r["count"] == 16, "16 nodes")
    expect("causal_depth" in r["nodes"][0], "depth")
    print("[PASS] embodied_32b.plod")


def test_invalid_crc() -> None:
    r = parse_frame((VEC / "invalid_crc.plod").read_bytes())
    expect(not r["crc_ok"], "CRC must fail")
    print("[PASS] invalid_crc.plod")


def test_unknown_extension() -> None:
    r = parse_frame((VEC / "unknown_extension.plod").read_bytes())
    expect(r["crc_ok"], "CRC")
    expect(r["count"] == 4, "4 nodes")
    print("[PASS] unknown_extension.plod")


def main() -> int:
    if not VEC.exists() or not list(VEC.glob("*.plod")):
        print("Vectors missing — run: python tests/generate_vectors.py")
        return 1
    failed = 0
    for t in (
        test_minimal_valid,
        test_embodied_32b,
        test_invalid_crc,
        test_unknown_extension,
    ):
        try:
            t()
        except Exception as e:
            failed += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print()
    if failed:
        print(f"RESULT: {failed} failed")
        return 1
    print("RESULT: all compliance vector tests PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
