#!/usr/bin/env python3
"""RFC-aligned golden-vector compliance tests (stdlib only)."""
from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
VEC = HERE / "vectors"

MAGIC = 0x504C
HAS_CONSTRAINT_TABLE = 0x01
IS_EMBODIED_PROFILE = 0x02
HAS_EXTENDED_META = 0x04
GLOBAL_NA = 0xFFFF
CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = 24
EMBODIED_SIZE = 32
META_SIZE = 8
CONSTRAINT_SIZE = 16
MAX_FRAME_SIZE = 16 * 1024 * 1024


class ProtocolError(Exception):
    pass


def ensure_vectors() -> None:
    if not (VEC / "golden_core_v11.plod").exists():
        sys.path.insert(0, str(HERE))
        import generate_vectors as gv

        gv.main()


def parse_frame(data: bytes) -> dict:
    if len(data) < 12:
        raise ProtocolError("frame too short")
    if len(data) > MAX_FRAME_SIZE:
        raise ProtocolError("MAX_FRAME_SIZE exceeded")

    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ProtocolError(f"bad MAGIC {magic:#x}")

    embodied = bool(flags & IS_EMBODIED_PROFILE)
    has_meta = bool(flags & HAS_EXTENDED_META)
    has_ct = bool(flags & HAS_CONSTRAINT_TABLE)
    base = EMBODIED_SIZE if embodied else CORE_SIZE
    per = base + (META_SIZE if has_meta else 0)

    off = 8
    nodes = []
    for _ in range(count):
        if off + base > len(data) - 4:
            raise ProtocolError("truncated node table")
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from(
                "<HBB3f3ff", data, off
            )
            off += EMBODIED_SIZE
            node = {"id": nid, "pos": (px, py, pz)}
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(
                CORE_FMT, data, off
            )
            off += CORE_SIZE
            node = {"id": nid, "pos": (px, py, pz)}
        for v in node["pos"]:
            if math.isnan(v) or math.isinf(v):
                raise ProtocolError("NaN/Inf coordinate")
        if has_meta:
            if off + META_SIZE > len(data) - 4:
                raise ProtocolError("truncated meta")
            freq, depth = struct.unpack_from("<fB", data, off)
            off += META_SIZE
            node["causal_depth"] = depth
            node["resonance_freq"] = freq
        nodes.append(node)

    constraints = []
    if has_ct:
        if off + 2 > len(data) - 4:
            raise ProtocolError("truncated constraint count")
        (m,) = struct.unpack_from("<H", data, off)
        off += 2
        for _ in range(m):
            if off + CONSTRAINT_SIZE > len(data) - 4:
                raise ProtocolError("truncated constraint entry")
            ctype, cflags, a, b, p0, p1, reserved = struct.unpack_from("<BBHHffH", data, off)
            off += CONSTRAINT_SIZE
            constraints.append({"type": ctype, "a": a, "b": b, "p0": p0, "p1": p1})

    if off + 4 > len(data):
        raise ProtocolError("missing CRC")
    crc_stored = struct.unpack_from("<I", data, off)[0]
    crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
    crc_ok = crc_stored == crc_calc

    return {
        "version": ver,
        "flags": flags,
        "count": count,
        "seq": seq,
        "nodes": nodes,
        "constraints": constraints,
        "crc_ok": crc_ok,
        "payload_end": off,
        "header_magic_ok": magic == MAGIC,
        "offsets": {"nodes_start": 8, "payload_end": off},
    }


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_golden_core_v11() -> None:
    data = (VEC / "golden_core_v11.plod").read_bytes()
    # Byte-level header assertions
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    expect(magic == MAGIC, "MAGIC @0")
    expect(ver == 0x11, "VERSION")
    expect(flags & HAS_CONSTRAINT_TABLE, "HAS_CONSTRAINT_TABLE")
    expect(not (flags & IS_EMBODIED_PROFILE), "core profile")
    expect(count == 4, "SE_NODE_COUNT")

    r = parse_frame(data)
    expect(r["crc_ok"], "CRC-32/ISO-HDLC must pass")
    expect(len(r["nodes"]) == 4, "4 nodes")
    expect(r["nodes"][0]["id"] == 0, "node_id 0 is valid")
    expect(len(r["constraints"]) == 2, "2 constraints")
    expect(r["constraints"][0]["type"] == 0x01, "distance type")
    expect(r["constraints"][1]["a"] == GLOBAL_NA, "global marker 0xFFFF")
    expect(r["constraints"][1]["b"] == GLOBAL_NA, "global marker 0xFFFF b")
    print("[PASS] golden_core_v11.plod (offsets, FLAGS, 0xFFFF, CRC)")


def test_golden_invalid_crc() -> None:
    data = (VEC / "golden_invalid_crc.plod").read_bytes()
    r = parse_frame(data)
    expect(not r["crc_ok"], "CRC must fail")
    print("[PASS] golden_invalid_crc.plod")


def test_minimal_valid() -> None:
    r = parse_frame((VEC / "minimal_valid.plod").read_bytes())
    expect(r["crc_ok"] and r["count"] == 8, "minimal")
    print("[PASS] minimal_valid.plod")


def test_embodied_32b() -> None:
    data = (VEC / "embodied_32b.plod").read_bytes()
    flags = data[3]
    expect(flags & IS_EMBODIED_PROFILE, "embodied flag bit1")
    expect(flags & HAS_EXTENDED_META, "meta flag bit2")
    r = parse_frame(data)
    expect(r["crc_ok"] and r["count"] == 16, "embodied parse")
    expect("causal_depth" in r["nodes"][0], "meta")
    print("[PASS] embodied_32b.plod")


def test_invalid_crc_legacy() -> None:
    r = parse_frame((VEC / "invalid_crc.plod").read_bytes())
    expect(not r["crc_ok"], "legacy bad crc")
    print("[PASS] invalid_crc.plod")


def test_unknown_extension() -> None:
    r = parse_frame((VEC / "unknown_extension.plod").read_bytes())
    expect(r["crc_ok"] and r["count"] == 4, "forward-compat unknown FLAGS bit")
    print("[PASS] unknown_extension.plod")


def main() -> int:
    ensure_vectors()
    failed = 0
    for fn in (
        test_golden_core_v11,
        test_golden_invalid_crc,
        test_minimal_valid,
        test_embodied_32b,
        test_invalid_crc_legacy,
        test_unknown_extension,
    ):
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"[FAIL] {fn.__name__}: {e}")
    print()
    if failed:
        print(f"RESULT: {failed} failed")
        return 1
    print("RESULT: all compliance vector tests PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
