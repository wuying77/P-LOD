# P-LOD Protocol Specification v1.0 (Core Standard)

**Status:** Draft standard (aligned with concept / prior art v0.1)  
**License:** MIT  
**Defensive publication:** [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

**Scope:** Byte-oriented and structural rules so independent implementations can encode, decode, and interoperate.

**Codec reference:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py)  
**Emergence reference (normative):** [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py)  
**Horizon demo:** [`examples/horizon_compression_demo.py`](../examples/horizon_compression_demo.py)

---

## 0. Legal & Public Domain Status (Defensive Publication)

This specification and its associated algorithms constitute a **Defensive Publication** designed to protect the open-source data, spatial computing, and embodied AI ecosystem from predatory patenting and institutional monopolization.

By publishing this protocol under the **MIT License** with immutable cryptographic timestamps on public version control, all theoretical models, field layouts, and operational parameters described herein are permanently established as **Prior Art**.

Any subsequent patent applications asserting ownership or exclusivity over the foundational concepts of P-LOD—including strong/weak entanglement decoupling, progressive Level 1–3 point-array encoding, SE-Frame / WE-Stream separation, sparse topological skeletons, or regional compute-allocation policies disclosed in this repository—shall be opposed as lacking **novelty** under applicable global patent practice, to the extent prior art is recognized.

**Scientific commons clause.** The Strong/Weak Entanglement decoupling and emergence mechanisms specified in P-LOD are derived from fundamental information theory and the Holographic Principle (as interpretive framing for sparse boundary encoding). Any attempt by commercial entities to monopolize or patent these physical intuitions, as disclosed here, constitutes an obstacle to the human collective cognitive boundary and is intended to be rendered ineffective under global Prior Art practice.

**P-LOD is a public technical commons.** Implementers may build interoperable codecs freely under MIT. Attempts to enclose the same disclosed subject matter behind exclusive patents or intermediary tolls are contrary to the purpose of this publication.

Full statement: [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md).

---

## 1. Goals

1. Define a clear **container + strong-entanglement payload** so any language (C/C++, Rust, Python, embedded) can implement a decoder.
2. Quantify why sparse skeletons can be orders of magnitude smaller than dense media.
3. Separate:
   - **Core profile** — general media / spatial data (images, meshes, text anchors, video skeletons)
   - **Embodied profile** (optional) — autonomy / robotics extensions (risk state, limb tags, compute policy)

P-LOD is **not** a claim that every 5 MB file becomes exactly 2.6 KB.  
2.6 KB is a **worked example** of a sparse strong-entanglement frame under stated assumptions.

---

## 2. Frame Architecture Overview

A P-LOD packet has two logical layers:

| Layer | Name | Role |
|-------|------|------|
| **SE-Frame** | Strong-Entanglement Frame | Deterministic, low-entropy topological skeleton. Required for identity, safety-critical logic, structure. |
| **WE-Stream** | Weak-Entanglement Stream | Optional. High-entropy detail for reconstruction / display only. May be absent, external, or generated locally. |

**Design rule:** Mission-critical decisions MUST be possible from the **SE-Frame alone**. WE is never required for structural correctness.

---

## 3. Header (Core, 8 bytes)

Binary layout is little-endian unless otherwise noted.

| Offset | Field | Type | Description |
|--------|-------|------|-------------|
| 0..1 | `MAGIC` | uint16 | `0x504C` (`'P' 'L'`) |
| 2 | `VERSION` | uint8 | `0x10` = v1.0 core wire; `0x11` = v1.1 with extended metas present |
| 3 | `FLAGS` | uint8 | Bit flags (see below) |
| 4..5 | `SE_NODE_COUNT` | uint16 | Number of SE nodes in this packet |
| 6..7 | `SEQUENCE_ID` | uint16 | Temporal / stream sequence number |

### FLAGS (uint8)

| Bit | Name | Meaning |
|-----|------|--------|
| 0 | `WE_PRESENT` | 1 = weak stream / pointer follows SE payload |
| 1 | `TOPOLOGY_INLINE` | 1 = edge list included after nodes |
| 2 | `EMBODIED_PROFILE` | 1 = nodes use embodied 32-byte layout (Section 5) |
| 3 | `FORWARD_FOCUS` | Hint: encoder prioritized forward cone (embodied) |
| 4 | `EXTENDED_META` | 1 = each SE node is followed by v1.1 Extended Vector Meta (8 bytes) |
| 5..7 | Reserved | Must be 0 unless a later minor version defines them |

---

## 4. Core SE-Node (General Profile)

When `EMBODIED_PROFILE = 0`, each node is a **variable logical record**.  
On the wire, v1.0 recommends a fixed **24-byte core node** for simple binary codecs; JSON examples in the repo remain the human-readable reference.

### 4.1 Logical fields (must be representable)

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique node id within the packet / asset |
| `position` | yes | 2D, 3D, or 1D sequential index (text/video time) |
| `level` | yes | 1 / 2 / 3 (progressive LOD) |
| `type` | yes | Discrete label |
| `rgb` / attrs | optional | Color or domain attributes |
| `params` | optional | Generation hints for WE emergence |
| `connections` | optional | Topology |

### 4.2 Suggested binary core node (24 bytes)

| Offset | Field | Type |
|--------|-------|------|
| 0..1 | `node_id` | uint16 |
| 2 | `level` | uint8 |
| 3 | `type_code` | uint8 |
| 4..15 | `x,y,z` | float32 × 3 |
| 16..18 | `r,g,b` | uint8 × 3 |
| 19 | `flags` | uint8 |
| 20..23 | `param0` | float32 |

---

## 5. Embodied Profile (Optional) — 32-byte SE-Node

When `FLAGS.EMBODIED_PROFILE = 1`, nodes use an autonomy-oriented layout.

### 5.1 SE-Node memory layout (32 bytes)

```
[Node_ID: 2B] [Risk_State: 1B] [Sub_System: 1B]
[Pos_X: 4B] [Pos_Y: 4B] [Pos_Z: 4B]
[Vel_X: 4B] [Vel_Y: 4B] [Vel_Z: 4B]
[Phase_Angle: 4B]
```

### 5.2–5.5 Risk state, Sub_System, Phase, 90/10 policy

Unchanged from prior draft (see repository history / README embodied notes). Summary:

- Risk: `SAFE=0`, `WATCH=1`, `CRITICAL=2`
- Sub_System: upper `0x10`, lower `0x20`, peripheral `0x30`
- ~90% compute forward cone / ~10% periphery until escalation

### 5.6 Extended Vector Metas (v1.1, optional)

When `FLAGS.EXTENDED_META = 1`, each SE node is followed by 8 bytes:

| Offset | Field | Type |
|--------|-------|------|
| 0..3 | `resonance_freq` | float32 |
| 4 | `causal_depth` | uint8 (\(\ge 200\) = Causal Anchor) |
| 5..7 | pad | 0 |

---

## 6. Weak-Entanglement Stream

WE is out of band relative to structural truth. Decoders MUST accept SE without WE.

Optional CRC32 trailer (zlib-compatible) MAY follow the SE payload.

---

## 7. Worked size example (illustrative)

| Item | Size |
|------|------|
| Header | 8 B |
| 80 × 32 B embodied nodes | 2,560 B |
| CRC32 | 4 B |
| **Total (no meta)** | **2,572 B ≈ 2.51 KB** |
| + 80 × 8 B v1.1 meta | **~3.1 KB** |

---

## 8. Progressive levels (normative semantics)

| Level | SE content | Intent |
|-------|------------|--------|
| **1** | Extreme skeleton | Identity + critical topology |
| **2** | + attributes / color / major events | High coverage |
| **3** | + local transitions | Smoother reconstruction |

---

## 9. Official Reference Emergence Engine (Normative)

### 9.1 Status

The file **[`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py)** is the **official normative reference implementation** of P-LOD SE decoding + deterministic WE emergence for Spec **v1.0 / v1.1**.

It is the **Source of Truth** (benchmark base) for compliance discussions:

- Algorithm is transparent, published, and **stdlib-only** (no vendor SDK required to audit behavior).
- Profile id: `plod.ref.linear_spline.v1`
- Default seed: `0x504C4F44` (`PLOD`)

### 9.2 What “P-LOD Compliant” means for third parties

Any third-party implementation (C++ / CUDA / Rust / WebAssembly / proprietary GPU paths) that claims **P-LOD Compliant** for emergence SHALL:

1. Correctly parse SE-Frames per Sections 3–5 (including optional v1.1 metas).
2. Produce WE detail whose **Topological Consistency Score (TCS)** against the same SE input is **≥ 0.99** when evaluated with the reference TCS definition in the reference engine, **or** document an alternate profile id and publish its own open test vectors.
3. Not require WE for safety-critical decisions driven only by SE topology.

Accelerated or proprietary engines may differ in surface appearance; **topological / structural agreement with the reference engine is the compliance bar**, not pixel-identical marketing renders.

### 9.3 Reference profile behavior (summary)

`plod.ref.linear_spline.v1`:

- Builds a deterministic edge chain over ordered node ids (plus ring close).
- Emits Level-2 midpoints and Level-3 quarter points along each edge.
- Applies seed-locked micro-jitter scaled down for high `causal_depth` (anchors stay stiff).
- Reports `P-LOD Standard Compliance Test PASS` when TCS ≥ 0.99.

### 9.4 Running the reference

```bash
cd examples
python reference_emergence_engine.py
python reference_emergence_engine.py --nodes 80
```

---

## 10. Compliance checklist

A decoder is **Core v1.0 compliant** if it:

1. Recognizes `MAGIC = 0x504C` and `VERSION = 0x10` (and MAY accept `0x11`)
2. Reads `SE_NODE_COUNT` and parses SE without requiring WE
3. Honors progressive `level` semantics
4. Ignores unknown flag bits safely

**Emergence-compliant** systems additionally meet Section 9 against the official reference engine (or an openly documented alternate profile).

---

## 11. Versioning

- **v1.0** — core header, Core 24B / Embodied 32B, WE optional, CRC optional
- **v1.1** — Extended Vector Metas; additive only
- Reference emergence engine tracks v1.0/v1.1 wire; profile id versions independently (`plod.ref.*.vN`)

---

## 12. References in this repository

| Resource | Path |
|----------|------|
| Overview | [README.md](../README.md) |
| Defensive publication | [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md) |
| Roadmap | [ROADMAP_AND_APPLICATIONS.md](ROADMAP_AND_APPLICATIONS.md) |
| Spec codec | [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) |
| **Reference emergence engine** | [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) |
| Horizon demo | [`examples/horizon_compression_demo.py`](../examples/horizon_compression_demo.py) |

---

*P-LOD Protocol Specification v1.0 + v1.1 — open implementation. Prior art under MIT. Reference emergence engine is normative for compliance tests.*
