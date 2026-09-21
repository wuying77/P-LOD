"""PLSE Security Envelope tests (optional cryptography)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

pytest.importorskip("cryptography")

from plod.security.envelope import (  # noqa: E402
    MAGIC,
    NONCE_SIZE,
    SecurityError,
    pack_security_envelope,
    unpack_security_envelope,
)
from plod_spec_codec import SENode, decode_frame, encode_frame  # noqa: E402


def _key() -> bytes:
    return bytes(range(32))


def test_roundtrip_core_frame():
    nodes = [
        SENode(node_id=1, pos=(0.0, 0.0, 0.0)),
        SENode(node_id=2, pos=(1.0, 0.0, 0.0)),
    ]
    raw = encode_frame(nodes)
    env = pack_security_envelope(raw, _key(), key_id=7)
    assert env[:4] == MAGIC
    plain = unpack_security_envelope(env, _key())
    assert plain == raw
    fr = decode_frame(plain)
    assert [n.node_id for n in fr.nodes] == [1, 2]


def test_core_encode_still_deterministic():
    nodes = [SENode(node_id=0, pos=(0.5, 0.25, 0.0))]
    assert encode_frame(nodes) == encode_frame(nodes)


def test_tampered_ciphertext_rejected():
    raw = encode_frame([SENode(node_id=1, pos=(0.0, 0.0, 0.0))])
    env = bytearray(pack_security_envelope(raw, _key(), key_id=1))
    idx = 4 + 4 + NONCE_SIZE
    env[idx] ^= 0x01
    with pytest.raises(SecurityError, match="authentication failed"):
        unpack_security_envelope(bytes(env), _key())


def test_wrong_key_rejected():
    raw = encode_frame([SENode(node_id=1, pos=(0.0, 0.0, 0.0))])
    env = pack_security_envelope(raw, _key(), key_id=1)
    bad = bytes([k ^ 0xFF for k in _key()])
    with pytest.raises(SecurityError, match="authentication failed"):
        unpack_security_envelope(env, bad)


def test_bad_magic_rejected():
    raw = encode_frame([SENode(node_id=1, pos=(0.0, 0.0, 0.0))])
    env = bytearray(pack_security_envelope(raw, _key()))
    env[0] = ord("X")
    with pytest.raises(SecurityError, match="magic"):
        unpack_security_envelope(bytes(env), _key())


def test_explicit_nonce_reproducible():
    raw = b"\x00" * 32
    nonce = b"\x11" * NONCE_SIZE
    e1 = pack_security_envelope(raw, _key(), key_id=3, nonce=nonce)
    e2 = pack_security_envelope(raw, _key(), key_id=3, nonce=nonce)
    assert e1 == e2
    assert unpack_security_envelope(e1, _key()) == raw


def test_random_nonce_differs():
    raw = b"hello-core-bytes"
    e1 = pack_security_envelope(raw, _key(), key_id=1)
    e2 = pack_security_envelope(raw, _key(), key_id=1)
    assert e1 != e2
    assert unpack_security_envelope(e1, _key()) == raw
    assert unpack_security_envelope(e2, _key()) == raw
