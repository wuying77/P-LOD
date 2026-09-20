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
Encoders **MUST NOT** silently truncate integer fields; out-of-range values raise `ProtocolError`.

---

## 0. Mathematical Formulation: Minimal Independent Structure ($S^*$)

P-LOD shifts data reduction from legacy lossy compression toward the discovery of **Minimal Independent Structures**. Given a high-entropy observational frame $X \in \mathbb{R}^{N \times d}$ and an emergence engine $G: \mathcal{S} \to \mathcal{X}$, the optimal Strong-Entanglement skeleton $S^*$ is the constrained discrete program:

$$
S^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{subject to} \quad D\bigl(X, G(S)\bigr) \le \epsilon
$$

where:

| Symbol | Meaning |
|--------|--------|
| $\lvert S\rvert$ | Cardinality of the independent SE node set |
| $G$ | Emergence map (normative: `plod.ref.linear_spline.v1`) |
| $D(\cdot,\cdot)$ | Normalized topological distortion (e.g. symmetric Chamfer / bbox diagonal) |
| $\epsilon \ge 0$ | Target reconstruction tolerance |

This is the information-theoretic statement behind the informal 「王」-character 9-point example: store only non-degenerate topological anchors; reconstruct fillable structure at read time.

### Node removal loss & `causal_depth`

To decide whether $p_i \in X$ is a non-degenerate structural anchor, define leave-one-out removal loss:

$$
\Delta E_i = D\bigl(X, G(S \setminus \{p_i\})\bigr) - D\bigl(X, G(S)\bigr)
$$

Quantized causal depth $C_i \in [0,255]$:

$$
C_i = \mathrm{round}\left( 255 \cdot \mathrm{clamp}\left( \frac{\Delta E_i}{\max_j(\Delta E_j)}, 0, 1 \right) \right)
$$

- $C_i \ge 200$ → **Causal Anchor** (essential degree of freedom)
- low $C_i$ → emergent redundancy synthesized by $G(S)$ at runtime, not serialized on the wire

Practical extractors (see `examples/horizon_compression_demo.py`) approximate $S^*$ by ablation-ranked candidates; exhaustive combinatorial search is NP-hard.

**Structural isomorphism note.** The volume→surface collapse of classical holographic ideas is treated here as an **information-structural isomorphism** (high-entropy bulk → low-cardinality skeleton), not as a claim of quantum gravity physics.

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

### Constraint type codes & `param0` / `param1` meanings

| Type | Code | `param0` | `param1` | Profile handling |
|------|------|----------|----------|------------------|
| **Distance** | `0x01` | Max distance A–B | Reserved (0) | **v2** enforced under constrained/high_fidelity; **v1** stored |
| **Boundary / Safety** | `0x02` | Max radius / half-extent | Reserved (0) | **v2** enforced; **v1** stored |
| **Temporal Link** | `0x03` | Max Δt / causal lag | Optional weight | **Pass-through** in v1/v2 ref |
| **Symmetry** | `0x04` | Plane/axis parameter | Optional axis | **Pass-through** in v1/v2 ref |

---

## 7. CRC-32/ISO-HDLC

Coverage: Header + Nodes + Constraints; excludes trailing CRC. LE uint32.

---

## 8. Metrics

| Name | Role |
|------|------|
| **TCS-AABB** | Containment **proxy** — emerged samples inside expanded SE AABB |
| **RFS** | `1 - min(1, CD/bbox_diag)` |

Full compliance = Edge validity + Constraint compliance + Sample coverage (v1: $t \in \{0.25,0.50,0.75\}$).

---

## 9. Security

Unique `node_id` ∈ `0..65534`; finite floats; no silent truncation; reject unknown VERSION / bad CRC / trailing garbage.

---

## 10. Profiles & CLI

| Profile | Role |
|---------|------|
| **`plod.ref.linear_spline.v1`** | Normative frozen baseline |
| `plod.ref.linear_spline.v2` | Experimental budgets / jitter / Distance+Boundary |

```bash
python examples/reference_emergence_engine.py --profile v1
python examples/eval_rate_distortion.py
```

---

## 11. Future Extension Strategy (v1.2 / v2.0+)

Reserved FLAGS bits 3–7; optional **TLV** sections after Constraint Table; new constraint codes ≥ `0x10` pass-through; VERSION bumps only on incompatible layouts.

---

*P-LOD Spec v1.1 — self-contained. Prior Art under MIT.*
