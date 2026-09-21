"""Canonical wire encoding: order-independent bytes."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from plod_spec_codec import Constraint, SENode, encode_frame  # noqa: E402
from plod.emergence.reference import emerge  # noqa: E402


def test_node_order_does_not_change_bytes():
    a = [
        SENode(node_id=3, pos=(3.0, 0.0, 0.0)),
        SENode(node_id=1, pos=(1.0, 0.0, 0.0)),
        SENode(node_id=2, pos=(2.0, 0.0, 0.0)),
    ]
    b = [
        SENode(node_id=1, pos=(1.0, 0.0, 0.0)),
        SENode(node_id=2, pos=(2.0, 0.0, 0.0)),
        SENode(node_id=3, pos=(3.0, 0.0, 0.0)),
    ]
    assert encode_frame(a) == encode_frame(b)


def test_constraint_order_does_not_change_bytes():
    nodes = [
        SENode(node_id=0, pos=(0.0, 0.0, 0.0)),
        SENode(node_id=1, pos=(1.0, 0.0, 0.0)),
    ]
    c1 = [Constraint(0x02, 0, 1, 1.0), Constraint(0x01, 0, 1, 2.5)]
    c2 = [Constraint(0x01, 0, 1, 2.5), Constraint(0x02, 0, 1, 1.0)]
    assert encode_frame(nodes, constraints=c1) == encode_frame(nodes, constraints=c2)


def test_emerge_v1_equals_v2_placeholder():
    nodes = [
        SENode(node_id=1, pos=(0.0, 0.0, 0.0)),
        SENode(node_id=2, pos=(4.0, 0.0, 0.0)),
    ]
    assert emerge(nodes, profile="v1") == emerge(nodes, profile="v2")
