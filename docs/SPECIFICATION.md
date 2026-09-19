# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

**Sole public codec:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) (`encode_frame` / `decode_frame`).

---

## 1. Frame layout

```text
+----------+------------------+---------------------------+--------+
| Header   | SE Node Table    | Constraint Table (optional)| CRC32  |
| 8 bytes  | N × node_size    | 2 + M × 16 bytes          | 4 B    |
+----------+------------------+---------------------------+--------+
```

### Implicit Edge Derivation (Derived Edge Rule)

No Edge Table on the wire. For **`plod.ref.linear_spline.v1`**: sort by `node_id`, consecutive edges + ring close; samples at **t ∈ {0.25, 0.50, 0.75}**.

---

## 2. Header (8 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 2 | `MAGIC` | uint16 = `0x504C` |
| 2 | 1 | `VERSION` | uint8 |
| 3 | 1 | `FLAGS` | uint8 |
| 4 | 2 | `SE_NODE_COUNT` | uint16 |
| 6 | 2 | `SEQUENCE_ID` | uint16 |

### FLAGS

| Bit | Mask | Name |
|----:|------|------|
| 0 | `0x01` | `HAS_CONSTRAINT_TABLE` |
| 1 | `0x02` | `IS_EMBODIED_PROFILE` |
| 2 | `0x04` | `HAS_EXTENDED_META` |
| 3–7 | — | Reserved |

### Version Compatibility Matrix

| VERSION | Wire name | Allowed payload | Forbidden |
|---------|-----------|-----------------|-----------|
| `0x10` | **v1.0** | Header + Core or Embodied SE Node Table + CRC | Constraint Table; Extended Meta; flags bit0/bit2 must be 0 |
| `0x11` | **v1.1** | Full: Core/Embodied, optional Extended Meta, optional Constraint Table | — |
| other | — | — | **MUST reject** with `ProtocolError` |

---

## 3. Core Node (24 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 (`0..65534`; `0xFFFF` forbidden) |
| 2 | 1 | `level` | uint8 (`1..3`) |
| 3 | 1 | `type_code` | uint8 |
| 4–15 | 12 | `x, y, z` | float32 × 3 |
| 16–18 | 3 | `r, g, b` | uint8 × 3 |
| 19 | 1 | `node_flags` | uint8 |
| 20–23 | 4 | `param0` | float32 |

---

## 4. Embodied Node (32 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 (`0..65534`) |
| 2 | 1 | `risk_state` | `0=SAFE`, `1=WATCH`, `2=CRITICAL` |
| 3 | 1 | `sub_system` | uint8 |
| 4–15 | 12 | `pos_x,y,z` | float32 × 3 |
| 16–27 | 12 | `vel_x,y,z` | float32 × 3 |
| 28–31 | 4 | `phase` | float32 |

---

## 5. Extended Meta (8 bytes) — v1.1 only

| Offset | Size | Field |
|-------:|-----:|-------|
| 0–3 | 4 | `resonance_freq` float32 |
| 4 | 1 | `causal_depth` uint8 |
| 5–7 | 3 | pad = 0 |

---

## 6. Constraint Table — v1.1 only

`uint16 count` + `count × 16` byte entries.

| Offset | Size | Field |
|-------:|-----:|-------|
| 0 | 1 | `constraint_type` |
| 1 | 1 | `cflags` (0) |
| 2–3 | 2 | `node_a` (`0xFFFF` = global/N/A) |
| 4–5 | 2 | `node_b` |
| 6–9 | 4 | `param0` float32 |
| 10–13 | 4 | `param1` float32 |
| 14–15 | 2 | reserved (0) |

### Constraint Semantics

| Type | Code | `plod.ref.linear_spline.v1` | Notes |
|------|------|------------------------------|--------|
| **Distance** | `0x01` | **Enforced** when profile applies constraints (v2 constrained/high_fidelity budgets; optional on wire for v1 storage) | Max separation A–B via `param0` |
| **Boundary / Safety** | `0x02` | **Enforced** under the same rule | Envelope / max radius `param0` |
| **Temporal Link** | `0x03` | **Pass-through (ignored)** by v1 baseline engine | Reserved for advanced temporal profiles |
| **Symmetry** | `0x04` | **Pass-through (ignored)** by v1 baseline engine | Reserved for symmetry-aware profiles |

Decoders **MUST** still parse and retain unknown/pass-through constraint rows when present (for forward compatibility). The **v1 normative emergencer** does not alter geometry based on types `0x03`/`0x04`.

---

## 7. CRC-32/ISO-HDLC

Coverage: Header + Nodes + Constraints; excludes trailing CRC. LE uint32.

---

## 8. Metrics

**TCS-AABB** = bounding-box containment proxy.  
**RFS** = `1 - min(1, CD/bbox_diag)` (symmetric Chamfer).

```text
TCS-AABB: 1.0000 | Status: AABB Containment PASS (Note: Containment Proxy Verification).
```

---

## 9. Security

Unique `node_id`; finite floats; no silent truncation; reject unknown VERSION, bad CRC, trailing garbage.

---

## 10. Profiles

| Profile | Role |
|---------|------|
| **`plod.ref.linear_spline.v1`** | Normative frozen baseline |
| `plod.ref.linear_spline.v2` | Experimental (budgets / jitter / Distance+Boundary projection) |

CLI:

```bash
python examples/reference_emergence_engine.py --profile v1
python examples/reference_emergence_engine.py --profile v2 --budget constrained
```

---

*P-LOD Spec v1.1 — self-contained. Prior Art under MIT.*
