#!/usr/bin/env python3
"""v1.1 codec unit tests: encode↔decode, NaN, duplicate id, truncated frame."""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from plod_spec_codec import (
    GLOBAL_NA,
    ProtocolError,
    SENode,
    Constraint,
    decode_frame,
    encode_frame,
)


def _ok(name: str) -> None:
    print(f"[PASS] {name}")


def test_roundtrip() -> None:
    nodes = [
        SENode(1, (0.1, 0.2, 0.3), resonance_freq=1.5, causal_depth=210),
        SENode(2, (1.0, 0.0, 0.0), vel=(0.1, 0.0, 0.0), phase=0.5),
    ]
    cons = [Constraint(0x01, 1, 2, 3.0, 0.0)]
    blob = encode_frame(nodes, constraints=cons, embodied=True, extended_meta=True)
    fr = decode_frame(blob)
    assert len(fr.nodes) == 2
    assert fr.nodes[0].causal_depth == 210
    assert abs(fr.nodes[0].resonance_freq - 1.5) < 1e-6
    assert len(fr.constraints) == 1
    _ok("encode↔decode roundtrip")


def test_reject_nan_pos() -> None:
    try:
        encode_frame([SENode(1, (float("nan"), 0.0, 0.0))])
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        assert "non-finite" in str(e).lower() or "nan" in str(e).lower()
    _ok("reject NaN pos")


def test_reject_inf_vel() -> None:
    try:
        encode_frame(
            [SENode(1, (0.0, 0.0, 0.0), vel=(float("inf"), 0.0, 0.0))],
            embodied=True,
        )
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        assert "non-finite" in str(e).lower() or "vel" in str(e).lower()
    _ok("reject Inf vel")


def test_reject_nan_constraint() -> None:
    try:
        encode_frame(
            [SENode(1, (0.0, 0.0, 0.0))],
            constraints=[Constraint(0x02, GLOBAL_NA, GLOBAL_NA, float("nan"))],
        )
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        assert "non-finite" in str(e).lower() or "param" in str(e).lower()
    _ok("reject NaN constraint param")


def test_reject_duplicate_id() -> None:
    try:
        encode_frame([SENode(7, (0.0, 0.0, 0.0)), SENode(7, (1.0, 0.0, 0.0))])
        raise AssertionError("expected ProtocolError")
    except ProtocolError as e:
        assert "duplicate" in str(e).lower()
    _ok("reject duplicate node_id")


def test_reject_truncated() -> None:
    blob = encode_frame([SENode(1, (0.0, 0.0, 0.0))])
    try:
        decode_frame(blob[:12])
        raise AssertionError("expected ProtocolError")
    except ProtocolError:
        pass
    _ok("reject truncated frame")


def main() -> int:
    failed = 0
    for fn in (
        test_roundtrip,
        test_reject_nan_pos,
        test_reject_inf_vel,
        test_reject_nan_constraint,
        test_reject_duplicate_id,
        test_reject_truncated,
    ):
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"[FAIL] {fn.__name__}: {e}")
    print()
    print("RESULT: codec unit tests PASS" if not failed else f"RESULT: {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
