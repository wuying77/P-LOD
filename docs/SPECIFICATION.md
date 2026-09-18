# P-LOD Protocol Specification v1.0 (Core Standard)

**Status:** Draft standard (aligned with concept / prior art v0.1)  
**License:** MIT  
**Defensive publication:** [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

**Scope:** Byte-oriented and structural rules so independent implementations can encode, decode, and interoperate.

**Reference implementation:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) (Python, stdlib only).  
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

When `FLAGS.EMBODIED_PROFILE = 1`, nodes use an autonomy-oriented layout.

### 5.1 SE-Node memory layout (32 bytes)

```
[Node_ID: 2B] [Risk_State: 1B] [Sub_System: 1B]     # 4 bytes
[Pos_X: 4B] [Pos_Y: 4B] [Pos_Z: 4B]                 # 12 bytes  (total 16)
[Vel_X: 4B] [Vel_Y: 4B] [Vel_Z: 4B]                 # 12 bytes  (total 28)
[Phase_Angle: 4B]                                   # 4 bytes   (total 32)
```

Little-endian. Struct layout equivalent: `uint16, uint8, uint8, float32×3, float32×3, float32`.

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

### 5.6 Extended Vector Metas (v1.1, optional, forward-compatible)

When `FLAGS.EXTENDED_META = 1` (recommended with `VERSION = 0x11`), **each** SE node (Core 24B or Embodied 32B) is immediately followed by an **8-byte** meta block:

| Offset | Field | Type | Description |
|--------|-------|------|-------------|
| 0..3 | `resonance_freq` | float32 | Operational resonance of the node in the topological field (phase alignment / impedance matching under noise) |
| 4 | `causal_depth` | uint8 | Causal impact weight in \([0, 255]\). Values \(\ge 200\) mark **Causal Anchors**: removing them permanently alters identity or trajectory topology |
| 5..7 | `pad` | uint8×3 | Must be zero in v1.1; reserved for future sub-fields |

**Compatibility rules:**

- v1.0 decoders that ignore unknown flag bits MAY skip packets with `EXTENDED_META` if they do not implement v1.1, or skip 8 bytes per node when the bit is set.
- Core 24B / Embodied 32B layouts are **unchanged**; metas are strictly additive.
- Reference illustration: `examples/horizon_compression_demo.py`.

---

## 6. Weak-Entanglement Stream

WE is **out of band relative to structural truth**:

- Omitted entirely (structure-only asset)
- Pointer / URL / content-hash in an extension trailer
- Inline blob after SE (discouraged for huge media; fine for small procedural seeds)

Decoders MUST still accept and use SE if WE is missing or fails.

Emergence rules (noise, shaders, language model fill, video interpolators) are **not** frozen in v1.0 wire format; they are bound by `type`, `params`, and external profile documents.

Optional **CRC32** (IEEE, zlib-compatible) MAY be appended as a 4-byte little-endian trailer over the packet bytes excluding the CRC itself.

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

Verified by `python examples/plod_spec_codec.py --demo`.

With v1.1 metas: add \(80 \times 8 = 640\) bytes → still on the order of **~3.1 KB** for the same node count.

### 7.2 Repo media examples (JSON skeletons)

Human-readable JSON in `examples/` (Cosmic Meditation, humanoid, etc.) demonstrates the **same sparsity principle** with different node counts and domains. See README size tables.

### 7.3 Horizon compression demo

`python examples/horizon_compression_demo.py` generates ~10k high-entropy samples, extracts ≤80 SE nodes, and packs an Embodied frame with `causal_depth` metas.

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

1. Recognizes `MAGIC = 0x504C` and `VERSION = 0x10` (and MAY accept `0x11`)
2. Reads `SE_NODE_COUNT` and parses the SE payload without requiring WE
3. Honors `level` and basic `type` for progressive display
4. Ignores unknown flag bits and reserved fields safely

A system is **Embodied v1.0 compliant** if it additionally:

1. Sets / accepts `EMBODIED_PROFILE`
2. Implements Risk_State and Sub_System semantics above
3. Documents forward vs peripheral compute policy

**v1.1 extended meta compliance:** when `EXTENDED_META` is set, parse or skip the 8-byte block per node without breaking SE topology.

---

## 10. Versioning

- **v1.0** — core header, Core 24B / Embodied 32B nodes, WE optional, CRC optional
- **v1.1** — additive Extended Vector Metas (`resonance_freq`, `causal_depth`); no breaking change to v1.0 node bodies
- Breaking wire changes require major VERSION bump
- JSON examples may lead the binary layout during early adoption

---

## 11. References in this repository

| Resource | Path |
|----------|------|
| Overview | [README.md](../README.md) |
| Defensive publication | [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md) |
| Roadmap & applications | [ROADMAP_AND_APPLICATIONS.md](ROADMAP_AND_APPLICATIONS.md) |
| Chinese whitepaper | [whitepaper_zh.md](whitepaper_zh.md) |
| Mind map | [mindmap.md](mindmap.md) |
| JSON examples | [`examples/`](../examples/) |
| 3D JSON demo | [`examples/parse_plod.py`](../examples/parse_plod.py) |
| Spec v1.0 codec | [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) |
| Horizon compression demo | [`examples/horizon_compression_demo.py`](../examples/horizon_compression_demo.py) |
| Codec tests | [`examples/test_plod_spec_codec.py`](../examples/test_plod_spec_codec.py) |

---

*P-LOD Protocol Specification v1.0 + v1.1 extended metas — drafted for open implementation. Prior art under MIT.*
