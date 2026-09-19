# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.  
**Byte order:** **Little-Endian** for all multi-byte integer and IEEE-754 fields.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> **Engineering Note on Terminology:** SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

```text
Original Data → SE Extractor → Encoder → Binary Frame → Decoder → Emergence Engine → Validator (TCS / RFS)
```

**References:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) · [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) · [`tests/run_compliance_tests.py`](../tests/run_compliance_tests.py)

---

## 0. Frame layout (v1.1)

```text
+----------+------------------+---------------------------+--------+
| Header   | SE Node Table    | Constraint Table (optional)| CRC32  |
| 8 bytes  | N × node_size    | 2 + M × 16 bytes          | 4 B    |
+----------+------------------+---------------------------+--------+
```

`node_size` = 24 (Core) or 32 (Embodied), plus **+8** per node if `HAS_EXTENDED_META`.

---

## 1. Header (8 bytes) — Byte-level layout

| Offset | Size | Field | Type | Description |
|-------:|-----:|-------|------|-------------|
| 0 | 2 | `MAGIC` | uint16 | **Must be `0x504C`** (`'P'`, `'L'`) |
| 2 | 1 | `VERSION` | uint8 | `0x10` = v1.0 wire; `0x11` = v1.1 |
| 3 | 1 | `FLAGS` | uint8 | Bitmask — see §2 |
| 4 | 2 | `SE_NODE_COUNT` | uint16 | Number of SE nodes `N` (`0 … 65535`) |
| 6 | 2 | `SEQUENCE_ID` | uint16 | Stream / temporal sequence index |

All multi-byte fields are **Little-Endian**.

---

## 2. FLAGS bitmask (uint8)

| Bit | Mask | Name | Meaning |
|----:|------|------|--------|
| 0 | `0x01` | `HAS_CONSTRAINT_TABLE` | 1 = after Node Table: `uint16 count` + `count × 16` constraint entries |
| 1 | `0x02` | `IS_EMBODIED_PROFILE` | 1 = each node is **32-byte Embodied**; 0 = **24-byte Core** |
| 2 | `0x04` | `HAS_EXTENDED_META` | 1 = each node is followed by **8-byte** Extended Meta |
| 3–7 | — | Reserved | **Must be written as 0** by encoders; decoders **MUST ignore** unknown bits for forward compatibility |

**Decoding rule:** node payload length per entry =

```text
base = 32 if IS_EMBODIED_PROFILE else 24
per_node = base + (8 if HAS_EXTENDED_META else 0)
```

---

## 3. Core SE-Node (24 bytes) — `IS_EMBODIED_PROFILE = 0`

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 2 | `node_id` | uint16 |
| 2 | 1 | `level` | uint8 (1/2/3) |
| 3 | 1 | `type_code` | uint8 |
| 4 | 12 | `x, y, z` | float32 × 3 |
| 16 | 3 | `r, g, b` | uint8 × 3 |
| 19 | 1 | `node_flags` | uint8 |
| 20 | 4 | `param0` | float32 |

---

## 4. Embodied SE-Node (32 bytes) — `IS_EMBODIED_PROFILE = 1`

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 2 | `node_id` | uint16 |
| 2 | 1 | `risk_state` | uint8 |
| 3 | 1 | `sub_system` | uint8 |
| 4 | 12 | `pos_x,y,z` | float32 × 3 |
| 16 | 12 | `vel_x,y,z` | float32 × 3 |
| 28 | 4 | `phase` | float32 |

---

## 5. Extended Meta (8 bytes per node) — if `HAS_EXTENDED_META`

Appended **immediately after** each node body:

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 4 | `resonance_freq` | float32 |
| 4 | 1 | `causal_depth` | uint8 (`≥ 200` = Causal Anchor) |
| 5 | 3 | `pad` | must be `0x00` |

**Semantic (informative):** `causal_depth(i) ∝ ΔE` under node ablation (see horizon demo).

---

## 6. Constraint Table (optional) — if `HAS_CONSTRAINT_TABLE`

Placed **after** the full Node Table (including all Extended Metas).

1. `constraint_count` — **uint16 LE** (`M`)
2. `M` × **Constraint Entry (16 bytes)**:

| Offset | Size | Field | Type | Description |
|-------:|-----:|-------|------|-------------|
| 0 | 1 | `constraint_type` | uint8 | see type table |
| 1 | 1 | `cflags` | uint8 | reserved; write 0 |
| 2 | 2 | `node_a` | uint16 | target A; **`0xFFFF` = global / N/A** |
| 4 | 2 | `node_b` | uint16 | target B; **`0xFFFF` = global / N/A** |
| 6 | 4 | `param0` | float32 | primary scalar |
| 10 | 4 | `param1` | float32 | secondary scalar |
| 14 | 2 | `reserved` | uint16 | must be 0 |

**Global / N/A marker is `0xFFFF` (uint16 max).**  
**Do not use `0` for “global”** — `node_id = 0` is a valid node identifier and must not collide with scope markers.

| Type | Code | Meaning |
|------|------|--------|
| Distance | `0x01` | Max separation A–B (`param0`) |
| Boundary / Safety | `0x02` | Envelope (`param0` radius / half-extent) |
| Temporal Link | `0x03` | Temporal / causal bound |
| Symmetry | `0x04` | Profile-defined symmetry params |

---

## 7. CRC32 (mandatory in compliance profiles)

| Item | Specification |
|------|----------------|
| **Algorithm** | **CRC-32/ISO-HDLC** (same family as zlib / PNG / Ethernet) |
| **Polynomial** | `0x04C11DB7` |
| **Initial value** | `0xFFFFFFFF` |
| **Input reflected** | yes |
| **Output reflected** | yes |
| **Final XOR** | `0xFFFFFFFF` |
| **Wire storage** | Little-Endian **uint32** at end of frame |

**Coverage:** all bytes from offset 0 through the last byte of the Constraint Table (if present), **excluding** the trailing 4-byte CRC field itself.

Equivalent practical check: `zlib.crc32(payload) & 0xFFFFFFFF` on the covered region (Python), matching ISO-HDLC parameters above.

**Decoder rule:** if CRC mismatches → **MUST** reject with `ProtocolError` (must not use the frame).

---

## 8. Official Reference Emergence Engine

| Profile | Status |
|---------|--------|
| **`plod.ref.linear_spline.v1`** | **Normative frozen baseline** |
| `plod.ref.linear_spline.v2` | Budgeted + constraint projection |

**TCS** ≥ 0.99 → Protocol Compliance PASS. **RFS** is separate (fidelity vs Ground Truth).

---

## 9. Golden vectors

| File | Intent |
|------|--------|
| `tests/vectors/golden_core_v11.plod` | Valid v1.1 core nodes + constraint table + CRC |
| `tests/vectors/golden_invalid_crc.plod` | Same payload, deliberately bad CRC |

Generate / refresh: `python tests/generate_vectors.py`  
Assert: `python tests/run_compliance_tests.py`

---

## 10. Security Considerations & Bounds

| Limit | Value |
|-------|------|
| `MAX_SE_NODES` | **65,535** (`uint16` maximum) |
| `MAX_CONSTRAINTS` | **65,535** |
| `MAX_FRAME_SIZE` | **16 MiB** (16 × 1024 × 1024 bytes) |

**Decoder requirements:**

1. Reject frames with `MAGIC ≠ 0x504C`.
2. Reject if declared sizes imply total length **> `MAX_FRAME_SIZE`** or exceed available buffer.
3. Reject on **CRC mismatch**.
4. Reject coordinates that are **NaN** or **±Infinity** (`ProtocolError`); do not propagate into control logic.
5. Unknown `FLAGS` bits **MUST** be ignored (forward compatible); unknown `constraint_type` **MAY** be skipped if the entry size is known (16 B).
6. Decoders **MUST NOT** crash on malformed input; they **MUST** surface a structured error.

---

## 11. Compliance checklist

A decoder is **v1.1 wire-compliant** if it:

1. Parses Header offsets exactly as §1 (LE).
2. Honors FLAGS bits 0–2 as §2.
3. Uses **`0xFFFF`** as global/N/A in constraints (§6).
4. Verifies CRC-32/ISO-HDLC over the full coverage region (§7).
5. Observes §10 bounds and error handling.

---

*P-LOD Spec v1.1 — RFC-style binary standard. Prior Art under MIT.*
