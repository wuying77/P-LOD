# P-LOD Protocol Specification v1.0 (Core Standard)

**Status:** Draft standard (aligned with concept / prior art v0.1)  
**License:** MIT  
**Scope:** Byte-oriented and structural rules so independent implementations can encode, decode, and interoperate.

This document turns the P-LOD *idea* into a **parseable specification**.  
Philosophy and examples remain in the [README](../README.md) and [whitepaper](whitepaper_zh.md).

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

```
+-----------------------------------------------------------------------+
| P-LOD PACKET CONTAINER                                                |
+-----------------------------------------------------------------------+
| [Header]  |  [Strong-Entanglement Frame (SE-Frame)]  |  [WE pointer / |
|  fixed    |  variable (nodes + topology)             |   optional blob]|
+-----------------------------------------------------------------------+
```

**Design rule:** Mission-critical decisions (recognition of structure, collision topology, plot anchors, keyframe graph) MUST be possible from the **SE-Frame alone**. WE is never required for structural correctness.

---

## 3. Header (Core, 8 bytes)

Binary layout is little-endian unless otherwise noted.

| Offset | Field | Type | Description |
|--------|-------|------|-------------|
| 0..1 | `MAGIC` | uint16 | `0x504C` (`'P' 'L'`) |
| 2 | `VERSION` | uint8 | `0x10` = v1.0 |
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
| 4..7 | Reserved | Must be 0 in v1.0 |

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
| `type` | yes | Discrete label: `solid`, `hollow`, `semi-hollow`, `joint`, `end`, `control`, `emitter`, … |
| `rgb` / attrs | optional | Color or domain attributes |
| `params` | optional | Generation hints for WE emergence |
| `connections` | optional | Topology (may be packet-global edge list) |

### 4.2 Suggested binary core node (24 bytes)

| Offset | Field | Type | Notes |
|--------|-------|------|-------|
| 0..1 | `node_id` | uint16 | |
| 2 | `level` | uint8 | 1..3 |
| 3 | `type_code` | uint8 | Enum (implementation table) |
| 4..7 | `x` | float32 | or normalized fixed-point in a profile |
| 8..11 | `y` | float32 | |
| 12..15 | `z` | float32 | use 0 for 2D |
| 16..18 | `r,g,b` | uint8×3 | optional; 0 if unused |
| 19 | `flags` | uint8 | node-local flags |
| 20..23 | `param0` | float32 | optional scalar / packed hint |

Topology MAY follow as: `uint16 edge_count` + `edge_count × (uint16 a, uint16 b)`.

---

## 5. Embodied Profile (Optional) — 32-byte SE-Node

When `FLAGS.EMBODIED_PROFILE = 1`, nodes use an autonomy-oriented layout (Gemini draft, refined).

### 5.1 SE-Node memory layout (32 bytes)

```
[Node_ID: 2B] [Risk_State: 1B] [Sub_System: 1B]
[Pos_X: 4B] [Pos_Y: 4B] [Pos_Z: 4B]
[Vel_X: 4B] [Vel_Y: 4B] [Vel_Z: 4B]
[Phase_Angle: 4B] [Reserved: 4B]
```

### 5.2 Risk state machine (`Risk_State`)

| Value | Name | Meaning |
|-------|------|--------|
| `0x00` | `SAFE` / hollow-white | Background / non-threatening topology |
| `0x01` | `WATCH` / half-hollow | Intention or threshold rising |
| `0x02` | `CRITICAL` / solid-black | Actuation priority / collision lock |

### 5.3 Sub-system tag (`Sub_System`)

| Value | Meaning |
|-------|--------|
| `0x10` | Upper body / CoM-related |
| `0x20` | Lower body / gait phase |
| `0x30` | Peripheral spatial array |
| other | Reserved / vendor |

### 5.4 Phase angle

`Phase_Angle` as float32 in \([-\pi, \pi]\) (or normalized fixed-point in constrained profiles).  
Intended for gait / inclination decoupling (upper vs lower kinematics) so intention can be flagged **before** full body cross into a lane.

### 5.5 Spatial compute policy (normative for embodied compliance)

Implementations claiming **P-LOD Embodied v1.0** SHOULD document a priority policy equivalent to:

- **~90%** compute budget on nodes in the **forward trajectory cone** (e.g. \(|\theta| \le 30°\) from travel axis), higher sample rate.
- **~10%** on peripheral / rear topology until a node enters `WATCH` or `CRITICAL`, then boost.

Exact angles and Hz are deployment parameters; the **ratio intent** is part of the profile.

---

## 6. Weak-Entanglement Stream

WE is **out of band relative to structural truth**:

- Omitted entirely (structure-only asset)
- Pointer / URL / content-hash in an extension trailer
- Inline blob after SE (discouraged for huge media; fine for small procedural seeds)

Decoders MUST still accept and use SE if WE is missing or fails.

Emergence rules (noise, shaders, language model fill, video interpolators) are **not** frozen in v1.0 wire format; they are bound by `type`, `params`, and external profile documents.

---

## 7. Worked size example (illustrative)

### 7.1 Sparse SE-Frame arithmetic

Assumptions for one embodied-style frame:

| Item | Size |
|------|------|
| Header | 8 bytes |
| 80 SE nodes × 32 bytes | 2,560 bytes |
| CRC32 (optional trailer) | 4 bytes |
| **Total** | **2,572 bytes ≈ 2.51 KB** |

Under these assumptions, a dense raw cloud on the order of ~5 MB/frame can be reduced to a ~2.5 KB SE-Frame if the application truly only needs the topological skeleton for the decision loop.  
**This is an engineering identity under stated node counts — not a universal constant for every image or movie.**

### 7.2 Repo media examples (JSON skeletons)

Human-readable JSON in `examples/` (Cosmic Meditation, humanoid, etc.) demonstrates the **same sparsity principle** with different node counts and domains. See README size tables.

---

## 8. Progressive levels (normative semantics)

| Level | SE content | Intent |
|-------|------------|--------|
| **1** | Extreme skeleton | Identity + critical topology |
| **2** | + attributes / color / major events | ~high perceptual or semantic coverage |
| **3** | + local transitions / denser anchors | Smoother reconstruction |

Packets MAY carry only Level 1 nodes; higher levels are additive deltas or full supersets (encoder choice). Flag or `level` field on nodes distinguishes membership.

---

## 9. Compliance checklist

A decoder is **Core v1.0 compliant** if it:

1. Recognizes `MAGIC = 0x504C` and `VERSION = 0x10`
2. Reads `SE_NODE_COUNT` and parses the SE payload without requiring WE
3. Honors `level` and basic `type` for progressive display
4. Ignores unknown flag bits and reserved fields safely

A system is **Embodied v1.0 compliant** if it additionally:

1. Sets / accepts `EMBODIED_PROFILE`
2. Implements Risk_State and Sub_System semantics above
3. Documents forward vs peripheral compute policy

---

## 10. Versioning

- **v1.0** — this document (draft locked for community review)
- Breaking wire changes require VERSION bump
- JSON examples may lead the binary layout during v0.x → v1.x transition

---

## 11. References in this repository

| Resource | Path |
|----------|------|
| Overview | [README.md](../README.md) |
| Chinese whitepaper | [whitepaper_zh.md](whitepaper_zh.md) |
| Mind map | [mindmap.md](mindmap.md) |
| JSON examples | [`examples/`](../examples/) |
| Demo parser | [`examples/parse_plod.py`](../examples/parse_plod.py) |

---

*P-LOD Protocol Specification v1.0 — drafted for open implementation. Prior art under MIT.*
