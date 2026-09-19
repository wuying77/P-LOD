#!/usr/bin/env python3
"""RFC compliance tests using public examples/plod_spec_codec.decode_frame."""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXAMPLES = ROOT / "examples"
VEC = HERE / "vectors"

sys.path.insert(0, str(EXAMPLES))

from plod_spec_codec import (  # noqa: E402
    FLAG_HAS_CONSTRAINT_TABLE,
    FLAG_HAS_EXTENDED_META,
    FLAG_IS_EMBODIED_PROFILE,
    GLOBAL_NA,
    MAGIC,
    ProtocolError,
    decode_frame,
    encode_frame,
    SENode,
    Constraint,
)


def ensure_vectors() -> None:
    if not (VEC / "golden_core_v11.plod").exists():
        sys.path.insert(0, str(HERE))
        import generate_vectors as gv

        gv.main()


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_golden_core_v11() -> None:
    data = (VEC / "golden_core_v11.plod").read_bytes()
    magic, ver, flags, count, seq = struct.unpack_from("<HBBHH", data, 0)
    expect(magic == MAGIC, "MAGIC")
    expect(ver == 0x11, "VERSION")
    expect(bool(flags & FLAG_HAS_CONSTRAINT_TABLE), "HAS_CONSTRAINT_TABLE")
    fr = decode_frame(data)
    expect(len(fr.nodes) == 4, "4 nodes")
    expect(fr.nodes[0].node_id == 0, "node 0 valid")
    expect(len(fr.constraints) == 2, "2 constraints")
    expect(fr.constraints[1].node_a == GLOBAL_NA, "0xFFFF global")
    print("[PASS] golden_core_v11.plod")


def test_golden_invalid_crc() -> None:
    data = (VEC / "golden_invalid_crc.plod").read_bytes()
    try:
        decode_frame(data)
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        expect("CRC" in str(e).upper() or "crc" in str(e).lower(), str(e))
    print("[PASS] golden_invalid_crc.plod (ProtocolError)")


def test_trailing_garbage() -> None:
    data = (VEC / "golden_core_v11.plod").read_bytes() + b"\x00\x00"
    try:
        decode_frame(data)
        raise AssertionError("expected trailing garbage error")
    except ProtocolError as e:
        expect("trailing" in str(e).lower(), str(e))
    print("[PASS] trailing garbage rejected")


def test_unknown_version() -> None:
    data = bytearray((VEC / "minimal_valid.plod").read_bytes())
    data[2] = 0x99
    # fix CRC for version change so we hit VERSION check first
    body = bytes(data[:-4])
    # actually decode checks version before CRC — but body still has old crc
    # version is checked before CRC in decode_frame
    try:
        decode_frame(bytes(data))
        raise AssertionError("expected unknown version")
    except ProtocolError as e:
        expect("VERSION" in str(e).upper() or "version" in str(e).lower(), str(e))
    print("[PASS] unknown VERSION rejected")


def test_bad_constraint_index() -> None:
    nodes = [SENode(1, (0.0, 0.0, 0.0)), SENode(2, (1.0, 0.0, 0.0))]
    # node_a=99 not in set
    cons = [Constraint(0x01, 99, 2, 1.0)]
    blob = encode_frame(nodes, constraints=cons)
    try:
        decode_frame(blob)
        raise AssertionError("expected bad index")
    except ProtocolError as e:
        expect("node_a" in str(e) or "out of" in str(e).lower(), str(e))
    print("[PASS] illegal constraint node index rejected")


def test_embodied_meta() -> None:
    data = (VEC / "embodied_32b.plod").read_bytes()
    flags = data[3]
    expect(bool(flags & FLAG_IS_EMBODIED_PROFILE), "embodied bit")
    expect(bool(flags & FLAG_HAS_EXTENDED_META), "meta bit")
    fr = decode_frame(data)
    expect(len(fr.nodes) == 16, "16 nodes")
    print("[PASS] embodied_32b.plod")


def test_minimal_valid() -> None:
    fr = decode_frame((VEC / "minimal_valid.plod").read_bytes())
    expect(len(fr.nodes) == 8, "8 nodes")
    print("[PASS] minimal_valid.plod")


def test_unknown_flag_bit() -> None:
    fr = decode_frame((VEC / "unknown_extension.plod").read_bytes())
    expect(len(fr.nodes) == 4, "forward compat")
    print("[PASS] unknown_extension.plod")


def main() -> int:
    ensure_vectors()
    failed = 0
    for fn in (
        test_golden_core_v11,
        test_golden_invalid_crc,
        test_trailing_garbage,
        test_unknown_version,
        test_bad_constraint_index,
        test_embodied_meta,
        test_minimal_valid,
        test_unknown_flag_bit,
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
