# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian** for all multi-byte integers and IEEE-754 floats.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

**Public codec:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py)

---

## 1. Frame layout

```text
+----------+------------------+---------------------------+--------+
| Header   | SE Node Table    | Constraint Table (optional)| CRC32  |
| 8 bytes  | N × node_size    | 2 + M × 16 bytes          | 4 B    |
+----------+------------------+---------------------------+--------+
```

`node_size` = 24 (Core) or 32 (Embodied), plus **+8** if `HAS_EXTENDED_META`.

### Implicit Edge Derivation Note (Derived Edge Rule)

Wire format carries **Nodes + Constraints only** (no Edge Table).

For **`plod.ref.linear_spline.v1`**:

1. Sort nodes by `node_id` ascending.
2. Edges: consecutive pairs + ring close `(last → first)`.
3. Samples at **t ∈ {0.25, 0.50, 0.75}** on each edge (no seed, jitter, smoothstep).

---

## 2. Header (8 bytes)

| Offset | Size | Field | Type | Description |
|-------:|-----:|-------|------|-------------|
| 0 | 2 | `MAGIC` | uint16 | Must be `0x504C` |
| 2 | 1 | `VERSION` | uint8 | `0x10` (v1.0) or `0x11` (v1.1) |
| 3 | 1 | `FLAGS` | uint8 | Bitmask (§2.1) |
| 4 | 2 | `SE_NODE_COUNT` | uint16 | Number of nodes `N` |
| 6 | 2 | `SEQUENCE_ID` | uint16 | Stream index `0..65535` |

### 2.1 FLAGS

| Bit | Mask | Name |
|----:|------|------|
| 0 | `0x01` | `HAS_CONSTRAINT_TABLE` |
| 1 | `0x02` | `IS_EMBODIED_PROFILE` |
| 2 | `0x04` | `HAS_EXTENDED_META` |
| 3–7 | — | Reserved (write 0; ignore on read) |

v1.0 frames **MUST NOT** set Constraint Table or Extended Meta flags.

---

## 3. Core Node (24 bytes) — `IS_EMBODIED_PROFILE = 0`

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 (`0..65534`; **`0xFFFF` forbidden**) |
| 2 | 1 | `level` | uint8 (`1..3`) |
| 3 | 1 | `type_code` | uint8 |
| 4–15 | 12 | `x, y, z` | float32 × 3 |
| 16–18 | 3 | `r, g, b` | uint8 × 3 |
| 19 | 1 | `node_flags` | uint8 |
| 20–23 | 4 | `param0` | float32 |

---

## 4. Embodied Node (32 bytes) — `IS_EMBODIED_PROFILE = 1`

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 (`0..65534`) |
| 2 | 1 | `risk_state` | uint8: `0=SAFE`, `1=WATCH`, `2=CRITICAL` |
| 3 | 1 | `sub_system` | uint8 |
| 4–15 | 12 | `pos_x, pos_y, pos_z` | float32 × 3 |
| 16–27 | 12 | `vel_x, vel_y, vel_z` | float32 × 3 |
| 28–31 | 4 | `phase` | float32 |

---

## 5. Extended Meta (8 bytes per node) — if `HAS_EXTENDED_META`

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–3 | 4 | `resonance_freq` | float32 |
| 4 | 1 | `causal_depth` | uint8 (`≥200` = Causal Anchor) |
| 5–7 | 3 | `pad` | must be `0x00` |

---

## 6. Constraint Table — if `HAS_CONSTRAINT_TABLE`

Preceded by `uint16 constraint_count` (`M`).

Each **Constraint Entry (16 bytes)**:

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 1 | `constraint_type` | uint8 |
| 1 | 1 | `cflags` | uint8 (must be 0) |
| 2–3 | 2 | `node_a` | uint16 (`0xFFFF` = global/N/A) |
| 4–5 | 2 | `node_b` | uint16 (`0xFFFF` = global/N/A) |
| 6–9 | 4 | `param0` | float32 |
| 10–13 | 4 | `param1` | float32 |
| 14–15 | 2 | `reserved` | uint16 (must be 0) |

| Type | Code |
|------|------|
| Distance | `0x01` |
| Boundary / Safety | `0x02` |
| Temporal Link | `0x03` |
| Symmetry | `0x04` |

---

## 7. CRC-32/ISO-HDLC

Polynomial `0x04C11DB7`, init/final XOR `0xFFFFFFFF`, reflected; stored LE uint32.  
Coverage: Header + Nodes + Constraints; **excludes** CRC field.

---

## 8. Metrics

| Name | Meaning |
|------|--------|
| **TCS-AABB** | Bounding-box containment proxy |
| **RFS** | `1 - min(1, CD/bbox_diag)`, CD = symmetric Chamfer |

```text
TCS-AABB: 1.0000 | Status: AABB Containment PASS (Note: Containment Proxy Verification).
```

---

## 9. Security & encoding rules

- `MAX_SE_NODES` = 65535; `MAX_FRAME_SIZE` = 16 MiB
- Unique `node_id`; never `0xFFFF` for nodes
- All floats finite (no NaN/±Inf)
- Encoders **MUST NOT** silently truncate; out-of-range → `ProtocolError`
- Decoders reject CRC fail, trailing garbage, truncated tables

---

## 10. Profiles

| Profile | Role |
|---------|------|
| **`plod.ref.linear_spline.v1`** | Normative frozen baseline |
| `plod.ref.linear_spline.v2` | Experimental |

---

*P-LOD Spec v1.1 — self-contained RFC-style standard. Prior Art under MIT.*
