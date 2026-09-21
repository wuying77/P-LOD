# P-LOD Security Envelope (PLSE)

**Status:** Optional extension (`feature/security-envelope` · `plod-protocol[security]`)  
**Principle:** Core wire format stays **deterministic and key-free**. Encryption is an **outer envelope only**.

## Why not encrypt inside the Core header?

Injecting AES-GCM nonces/tags into the v1.1 Core frame would destroy:

- Deterministic `encode_frame` (same SE → same bytes)
- Golden vectors & CI integrity locks
- Content-addressed storage
- Defensive Publication / Prior Art clarity

## Layering

```text
SE Nodes  →  encode_frame()  →  Core Plain Frame (CRC-32)
                                      │
                                      │  pack_security_envelope(key)
                                      ▼
                               PLSE Envelope (AEAD)
```

| Layer | Responsibility |
|-------|----------------|
| Core (`src/plod/spec/codec.py`) | Structure, CRC-32, golden vectors |
| Security (`src/plod/security/envelope.py`) | AES-256-GCM confidentiality + authenticity |

## Envelope layout

| Field | Size | Notes |
|-------|------|--------|
| magic | 4 | `PLSE` |
| key_id | 4 | uint32 LE |
| nonce | 12 | GCM nonce |
| body | variable | ciphertext \|\| 16-byte tag |

AAD (authenticated, not encrypted): `magic || key_id`.

## API

```python
from plod import encode_frame, decode_frame, SENode
from plod.security import pack_security_envelope, unpack_security_envelope

raw = encode_frame([SENode(1, (0, 0, 0))])
env = pack_security_envelope(raw, key)  # key: 32 bytes
plain = unpack_security_envelope(env, key)
assert plain == raw
```

Install: `pip install 'plod-protocol[security]'`
