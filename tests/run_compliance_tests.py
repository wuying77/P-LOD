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
    fr = decode_frame(data)
    expect(fr.version == 0x11, "version")
    expect(len(fr.nodes) == 4, "4 nodes")
    print("[PASS] golden_core_v11.plod")


def test_golden_invalid_crc() -> None:
    data = (VEC / "golden_invalid_crc.plod").read_bytes()
    try:
        decode_frame(data)
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        expect("CRC" in str(e) or "crc" in str(e).lower(), str(e))
    print("[PASS] golden_invalid_crc.plod")


def test_trailing_garbage() -> None:
    good = (VEC / "minimal_valid.plod").read_bytes()
    try:
        decode_frame(good + b"\x00\x01")
        raise AssertionError("expected trailing garbage reject")
    except ProtocolError:
        pass
    print("[PASS] trailing garbage")


def test_unknown_version() -> None:
    data = bytearray((VEC / "minimal_valid.plod").read_bytes())
    data[2] = 0x99
    # CRC will also fail after version poke; either is Fail Loudly
    try:
        decode_frame(bytes(data))
        raise AssertionError("expected reject")
    except ProtocolError:
        pass
    print("[PASS] unknown VERSION")


def test_bad_constraint_index() -> None:
    nodes = [SENode(0, (0.0, 0.0, 0.0)), SENode(1, (1.0, 0.0, 0.0))]
    try:
        encode_frame(nodes, constraints=[Constraint(0x01, 0, 99, 1.0)])
        raise AssertionError("expected bad constraint index")
    except ProtocolError:
        pass
    print("[PASS] bad constraint index")


def test_reject_node_id_ffff() -> None:
    try:
        encode_frame([SENode(GLOBAL_NA, (0.0, 0.0, 0.0))])
        raise AssertionError("expected reject 0xFFFF")
    except ProtocolError:
        pass
    print("[PASS] reject node_id=0xFFFF")


def test_embodied_meta() -> None:
    data = (VEC / "embodied_32b.plod").read_bytes()
    fr = decode_frame(data)
    expect(bool(fr.flags & FLAG_IS_EMBODIED_PROFILE), "embodied flag")
    print("[PASS] embodied_32b.plod")


def test_minimal_valid() -> None:
    data = (VEC / "minimal_valid.plod").read_bytes()
    fr = decode_frame(data)
    expect(fr.version == 0x10, "v1.0 wire")
    print("[PASS] minimal_valid.plod")


def test_v1_deterministic_samples() -> None:
    nodes = [
        SENode(1, (0.0, 0.0, 0.0)),
        SENode(2, (4.0, 0.0, 0.0)),
    ]
    pts = emerge_v1(nodes)
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


def test_canonical_node_order() -> None:
    """Semantic equality ⇒ wire byte equality (node_id order independent)."""
    a = [
        SENode(3, (3.0, 0.0, 0.0)),
        SENode(1, (1.0, 0.0, 0.0)),
        SENode(2, (2.0, 0.0, 0.0)),
    ]
    b = [
        SENode(1, (1.0, 0.0, 0.0)),
        SENode(2, (2.0, 0.0, 0.0)),
        SENode(3, (3.0, 0.0, 0.0)),
    ]
    ba, bb = encode_frame(a), encode_frame(b)
    expect(ba == bb, "canonical encoding: shuffled node order must match bytes")
    print("[PASS] canonical node order → identical wire bytes + CRC")


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
        test_canonical_node_order,
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
