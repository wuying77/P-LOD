# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

---

## Frame layout (v1.1)

```text
+----------+------------------+---------------------------+--------+
| Header   | SE Node Table    | Constraint Table (optional)| CRC32  |
| 8 bytes  | N × node_size    | 2 + M × 16 bytes          | 4 B    |
+----------+------------------+---------------------------+--------+
```

### Implicit Edge Derivation Note (Derived Edge Rule)

The P-LOD v1.1 **wire format serializes Nodes and Constraints without an explicit Edge Table**.

For the normative profile **`plod.ref.linear_spline.v1`**:

1. Sort SE nodes by `node_id` ascending.
2. Form edges `(id_i → id_{i+1})` for consecutive sorted ids.
3. Close a ring with `(id_last → id_first)`.
4. Emit deterministic linear samples at **t ∈ {0.25, 0.50, 0.75}** on each edge (no seed, jitter, or smoothstep).

Advanced profiles (v1.2 / v2.0+) **MAY** introduce explicit edge sections or alternate topology rules; such profiles **MUST** publish a distinct `Profile_ID`.

---

## Header (8 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0 | 2 | `MAGIC` | uint16 = `0x504C` |
| 2 | 1 | `VERSION` | uint8 `0x10` / `0x11` |
| 3 | 1 | `FLAGS` | uint8 bitmask |
| 4 | 2 | `SE_NODE_COUNT` | uint16 |
| 6 | 2 | `SEQUENCE_ID` | uint16 |

### FLAGS

| Bit | Mask | Name |
|----:|------|------|
| 0 | `0x01` | `HAS_CONSTRAINT_TABLE` |
| 1 | `0x02` | `IS_EMBODIED_PROFILE` |
| 2 | `0x04` | `HAS_EXTENDED_META` |
| 3–7 | — | Reserved (write 0; ignore on read) |

---

## Nodes, Extended Meta, Constraints

- Core 24B / Embodied 32B as previously specified.
- Extended Meta 8B: `resonance_freq` (f32), `causal_depth` (u8), pad×3 = 0.
- Constraint entry 16B; **global/N/A = `0xFFFF`** (not 0).
- **`node_id` values MUST be unique** within a frame; duplicates → `ProtocolError`.

All float fields (`pos`, `vel`, `phase`, `param0`, `resonance_freq`, constraint `param0`/`param1`) **MUST** be finite; NaN/±Inf → `ProtocolError`.

---

## CRC-32/ISO-HDLC

Coverage: Header + Nodes + Constraints; excludes trailing CRC. Stored LE uint32.

---

## Metrics (normative naming)

| Name | Meaning |
|------|--------|
| **TCS-AABB** (`containment_score`) | Bounding-box containment proxy: emerged samples inside expanded SE AABB |
| **RFS** | `1 - min(1, CD / bbox_diag)` with symmetric Chamfer CD |

Report text example:

```text
TCS-AABB = 1.0000 | Status: Protocol AABB Containment PASS
(Note: Verifies emerged points fall within SE anchor bounding bounds; not a full graph-topology invariant.)
```

---

## Security & Bounds

`MAX_SE_NODES` = 65535 · `MAX_FRAME_SIZE` = 16 MiB · reject CRC fail, trailing garbage, non-finite floats, duplicate ids.

---

## Reference profiles

| Profile | Role |
|---------|------|
| **`plod.ref.linear_spline.v1`** | Normative frozen baseline (Derived Edge Rule + t∈{0.25,0.5,0.75}) |
| `plod.ref.linear_spline.v2` | Experimental budgets / jitter / constraint projection |

Codec: [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py)

---

*P-LOD Spec v1.1 — Prior Art under MIT.*
