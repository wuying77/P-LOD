#!/usr/bin/env python3
"""P-LOD golden-vector compliance tests (stdlib only). Auto-generates vectors if missing."""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
VEC = HERE / "vectors"
MAGIC = 0x504C
FLAG_EMBODIED = 1 << 2
FLAG_EXTENDED_META = 1 << 4
CORE_FMT = "<HBB3f3BBf"
CORE_SIZE = struct.calcsize(CORE_FMT)


def ensure_vectors() -> None:
    if not (VEC / "minimal_valid.plod").exists():
        import generate_vectors as gv

        gv.main()


def parse_frame(data: bytes):
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    if magic != MAGIC:
        raise ValueError(f"bad magic {magic:#x}")
    embodied = bool(flags & FLAG_EMBODIED)
    ext = bool(flags & FLAG_EXTENDED_META)
    off = 8
    nodes = []
    for _ in range(count):
        if embodied:
            nid, risk, sub, px, py, pz, vx, vy, vz, phase = struct.unpack_from("<HBB3f3ff", data, off)
            off += 32
            node = {"id": nid, "pos": (px, py, pz)}
        else:
            nid, level, tcode, px, py, pz, r, g, b, nfl, p0 = struct.unpack_from(CORE_FMT, data, off)
            off += CORE_SIZE
            node = {"id": nid, "pos": (px, py, pz)}
        if ext:
            freq, depth = struct.unpack_from("<fB", data, off)
            off += 8
            node["causal_depth"] = depth
        nodes.append(node)
    crc_stored = struct.unpack_from("<I", data, off)[0]
    crc_calc = zlib.crc32(data[:off]) & 0xFFFFFFFF
    return {"flags": flags, "count": count, "nodes": nodes, "crc_ok": crc_stored == crc_calc}


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    sys.path.insert(0, str(HERE))
    ensure_vectors()
    failed = 0

    def run(name, fn):
        nonlocal failed
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")

    def t_min():
        r = parse_frame((VEC / "minimal_valid.plod").read_bytes())
        expect(r["crc_ok"] and r["count"] == 8, "minimal")

    def t_emb():
        r = parse_frame((VEC / "embodied_32b.plod").read_bytes())
        expect(r["crc_ok"] and (r["flags"] & FLAG_EMBODIED) and r["count"] == 16, "embodied")

    def t_bad():
        r = parse_frame((VEC / "invalid_crc.plod").read_bytes())
        expect(not r["crc_ok"], "bad crc")

    def t_unk():
        r = parse_frame((VEC / "unknown_extension.plod").read_bytes())
        expect(r["crc_ok"] and r["count"] == 4, "unknown")

    for n, f in [
        ("minimal_valid.plod", t_min),
        ("embodied_32b.plod", t_emb),
        ("invalid_crc.plod", t_bad),
        ("unknown_extension.plod", t_unk),
    ]:
        run(n, f)
    print()
    print("RESULT: all compliance vector tests PASS" if not failed else f"RESULT: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
