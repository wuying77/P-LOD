"""P-LOD Security Envelope (PLSE) — outer AEAD wrapper around a Core wire frame.

Architecture
------------
Core ``encode_frame`` / ``decode_frame`` remain pure, deterministic, key-free.
Confidentiality and authenticity are provided **only** by this outer envelope:

    [ Core P-LOD Plain Frame ]
            │ AEAD (AES-256-GCM)
            ▼
    [ magic | key_id | nonce | ciphertext||tag ]

Wire layout (little-endian where numeric):
    magic      : 4 bytes  b"PLSE"
    key_id     : uint32
    nonce      : 12 bytes
    body       : ciphertext || 16-byte GCM tag

Optional dependency: ``cryptography``
(``pip install 'plod-protocol[security]'``).
"""

from __future__ import annotations

import os
import struct
from typing import Optional

MAGIC = b"PLSE"
NONCE_SIZE = 12
TAG_SIZE = 16
_HEADER_SIZE = 4 + 4 + NONCE_SIZE  # magic + key_id + nonce


class SecurityError(Exception):
    """Envelope parse / authentication failure."""


def _aead():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as e:
        raise ImportError(
            "P-LOD Security Envelope requires the optional 'cryptography' package.\n"
            "  pip install 'plod-protocol[security]'\n"
            "  # or: pip install cryptography"
        ) from e
    return AESGCM


def pack_security_envelope(
    raw_frame: bytes,
    key: bytes,
    key_id: int = 1,
    *,
    nonce: Optional[bytes] = None,
) -> bytes:
    """AEAD-encrypt a canonical Core P-LOD frame into a PLSE envelope."""
    if len(key) != 32:
        raise SecurityError("AES-256-GCM key must be exactly 32 bytes")
    if not (0 <= key_id <= 0xFFFFFFFF):
        raise SecurityError("key_id must fit in uint32")
    if nonce is None:
        nonce = os.urandom(NONCE_SIZE)
    if len(nonce) != NONCE_SIZE:
        raise SecurityError(f"nonce must be {NONCE_SIZE} bytes")

    AESGCM = _aead()
    aad = MAGIC + struct.pack("<I", key_id)
    ct_and_tag = AESGCM(key).encrypt(nonce, raw_frame, aad)
    return MAGIC + struct.pack("<I", key_id) + nonce + ct_and_tag


def unpack_security_envelope(envelope_bytes: bytes, key: bytes) -> bytes:
    """Authenticate and decrypt a PLSE envelope → canonical Core P-LOD frame."""
    if len(key) != 32:
        raise SecurityError("AES-256-GCM key must be exactly 32 bytes")
    if len(envelope_bytes) < _HEADER_SIZE + TAG_SIZE:
        raise SecurityError("envelope too short")

    magic = envelope_bytes[:4]
    if magic != MAGIC:
        raise SecurityError(f"bad envelope magic {magic!r}, expected {MAGIC!r}")

    (key_id,) = struct.unpack_from("<I", envelope_bytes, 4)
    nonce = envelope_bytes[8 : 8 + NONCE_SIZE]
    body = envelope_bytes[8 + NONCE_SIZE :]
    if len(body) < TAG_SIZE:
        raise SecurityError("missing ciphertext/tag")

    AESGCM = _aead()
    aad = MAGIC + struct.pack("<I", key_id)
    try:
        return AESGCM(key).decrypt(nonce, body, aad)
    except Exception as e:
        raise SecurityError("AEAD authentication failed (tamper or wrong key)") from e
