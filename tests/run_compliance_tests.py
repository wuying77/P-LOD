#!/usr/bin/env python3
"""
P-LOD golden-vector compliance tests (stdlib only).

Usage (from repo root):
  python tests/generate_vectors.py
  python tests/run_compliance_tests.py
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VEC = Path(__file__).resolve().parent / "vectors"

MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4


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
            if off + 24 > len(data) - 4:
                raise ValueError("truncated core")
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                "<HBB3f3Bf", data, off
            )
            off += 24
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
        "unknown_flags": flags & ~0x1F,
    }


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_minimal_valid() -> None:
    data = (VEC / "minimal_valid.plod").read_bytes()
    r = parse_frame(data)
    expect(r["crc_ok"], "minimal_valid CRC must pass")
    expect(r["count"] == 8, "expect 8 nodes")
    expect(not (r["flags"] & FLAG_EMBODIED), "core profile")
    print("[PASS] minimal_valid.plod")


def test_embodied_32b() -> None:
    data = (VEC / "embodied_32b.plod").read_bytes()
    r = parse_frame(data)
    expect(r["crc_ok"], "embodied CRC must pass")
    expect(r["flags"] & FLAG_EMBODIED, "embodied flag")
    expect(r["flags"] & FLAG_EXTENDED_META, "extended meta")
    expect(r["count"] == 16, "16 nodes")
    expect("causal_depth" in r["nodes"][0], "meta present")
    print("[PASS] embodied_32b.plod")


def test_invalid_crc() -> None:
    data = (VEC / "invalid_crc.plod").read_bytes()
    r = parse_frame(data)
    expect(not r["crc_ok"], "invalid_crc must fail CRC")
    print("[PASS] invalid_crc.plod (CRC correctly rejected)")


def test_unknown_extension() -> None:
    data = (VEC / "unknown_extension.plod").read_bytes()
    r = parse_frame(data)
    expect(r["crc_ok"], "unknown_extension still CRC-valid")
    expect(r["count"] == 4, "4 nodes")
    # decoder must not crash on unknown flag bits
    print("[PASS] unknown_extension.plod (forward-compat)")


def main() -> int:
    if not VEC.exists() or not list(VEC.glob("*.plod")):
        print("Vectors missing — run: python tests/generate_vectors.py")
        return 1
    tests = [
        test_minimal_valid,
        test_embodied_32b,
        test_invalid_crc,
        test_unknown_extension,
    ]
    failed = 0
    for t in tests:
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
