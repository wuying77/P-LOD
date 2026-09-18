#!/usr/bin/env python3
"""Minimal tests for plod_spec_codec (no external deps beyond stdlib)."""

from plod_spec_codec import (
    FLAG_EMBODIED_PROFILE,
    CoreNode,
    EmbodiedNode,
    PlodPacket,
    pack_packet,
    unpack_packet,
)


def test_core_roundtrip():
    pkt = PlodPacket(
        sequence_id=42,
        core_nodes=[
            CoreNode(1, 1, "joint", 0.0, 0.0, 1.0, r=255),
            CoreNode(2, 2, "end", 1.0, 0.0, 0.0),
        ],
        edges=[(1, 2)],
    )
    raw = pack_packet(pkt)
    out = unpack_packet(raw)
    assert out.sequence_id == 42
    assert len(out.core_nodes) == 2
    assert out.core_nodes[0].type_name == "joint"
    assert out.edges == [(1, 2)]


def test_embodied_roundtrip():
    pkt = PlodPacket(
        flags=FLAG_EMBODIED_PROFILE,
        embodied_nodes=[
            EmbodiedNode(1, 2, 0x10, (0.5, 0.5, 0.0), phase_angle=1.57),
        ],
    )
    out = unpack_packet(pack_packet(pkt))
    assert out.embodied_nodes[0].risk_state == 2
    assert abs(out.embodied_nodes[0].phase_angle - 1.57) < 1e-5


if __name__ == "__main__":
    test_core_roundtrip()
    test_embodied_roundtrip()
    print("test_plod_spec_codec: OK")
