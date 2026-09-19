#!/usr/bin/env python3
"""RFC compliance + v1 deterministic golden samples."""

from __future__ import annotations

import struct
import sys
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
    SENode,
    Constraint,
    decode_frame,
    encode_frame,
)
from reference_emergence_engine import emerge_v1  # noqa: E402


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
    fr = decode_frame(data)
    expect(len(fr.nodes) == 4, "4 nodes")
    expect(fr.constraints[1].node_a == GLOBAL_NA, "0xFFFF")
    print("[PASS] golden_core_v11.plod")


def test_golden_invalid_crc() -> None:
    try:
        decode_frame((VEC / "golden_invalid_crc.plod").read_bytes())
        raise AssertionError("expected ProtocolError")
    except ProtocolError:
        pass
    print("[PASS] golden_invalid_crc.plod")


def test_trailing_garbage() -> None:
    try:
        decode_frame((VEC / "golden_core_v11.plod").read_bytes() + b"\x00\x00")
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        expect("trailing" in str(e).lower(), str(e))
    print("[PASS] trailing garbage")


def test_unknown_version() -> None:
    data = bytearray((VEC / "minimal_valid.plod").read_bytes())
    data[2] = 0x99
    try:
        decode_frame(bytes(data))
        raise AssertionError("expected ProtocolError")
    except ProtocolError:
        pass
    print("[PASS] unknown VERSION")


def test_bad_constraint_index() -> None:
    try:
        encode_frame(
            [SENode(1, (0.0, 0.0, 0.0)), SENode(2, (1.0, 0.0, 0.0))],
            constraints=[Constraint(0x01, 99, 2, 1.0)],
        )
        raise AssertionError("expected ProtocolError")
    except ProtocolError:
        pass
    print("[PASS] bad constraint index")


def test_reject_node_id_ffff() -> None:
    try:
        encode_frame([SENode(0xFFFF, (0.0, 0.0, 0.0))])
        raise AssertionError("expected ProtocolError")
    except ProtocolError:
        pass
    print("[PASS] reject node_id=0xFFFF")


def test_embodied_meta() -> None:
    fr = decode_frame((VEC / "embodied_32b.plod").read_bytes())
    expect(len(fr.nodes) == 16, "16")
    print("[PASS] embodied_32b.plod")


def test_minimal_valid() -> None:
    fr = decode_frame((VEC / "minimal_valid.plod").read_bytes())
    expect(len(fr.nodes) == 8, "8")
    print("[PASS] minimal_valid.plod")


def test_v1_deterministic_samples() -> None:
    """A(0,0,0)–B(4,0,0) must yield exactly (1,0,0), (2,0,0), (3,0,0) on that edge."""
    nodes = [SENode(1, (0.0, 0.0, 0.0)), SENode(2, (4.0, 0.0, 0.0))]
    pts = emerge_v1(nodes)
    # edges: 1→2 and 2→1 (ring); take samples on edge 1→2 = first three
    edge_ab = pts[:3]
    expected = [(1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (3.0, 0.0, 0.0)]
    for got, exp in zip(edge_ab, expected):
        expect(
            abs(got[0] - exp[0]) < 1e-9
            and abs(got[1] - exp[1]) < 1e-9
            and abs(got[2] - exp[2]) < 1e-9,
            f"expected {exp} got {got}",
        )
    print("[PASS] v1 deterministic samples A(0,0,0)–B(4,0,0) → (1,0,0)(2,0,0)(3,0,0)")


def main() -> int:
    ensure_vectors()
    failed = 0
    for fn in (
        test_golden_core_v11,
        test_golden_invalid_crc,
        test_trailing_garbage,
        test_unknown_version,
        test_bad_constraint_index,
        test_reject_node_id_ffff,
        test_embodied_meta,
        test_minimal_valid,
        test_v1_deterministic_samples,
    ):
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"[FAIL] {fn.__name__}: {e}")
    print()
    print("RESULT: all compliance vector tests PASS" if not failed else f"RESULT: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
