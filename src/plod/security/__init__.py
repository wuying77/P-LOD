"""Optional outer Security Envelope (AEAD). Does not alter Core wire canon."""

from .envelope import (
    MAGIC,
    NONCE_SIZE,
    TAG_SIZE,
    SecurityError,
    pack_security_envelope,
    unpack_security_envelope,
)

__all__ = [
    "MAGIC",
    "NONCE_SIZE",
    "TAG_SIZE",
    "SecurityError",
    "pack_security_envelope",
    "unpack_security_envelope",
]
