# P-LOD Protocol Specification v1.0 (Core Standard)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.  
**License:** MIT  
**Defensive publication:** [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

**Scope:** Byte-oriented and structural rules so independent implementations can encode, decode, and interoperate.

> **Engineering Note on Terminology:**  
> In the P-LOD specification, the terms *"Strong Entanglement (SE)"* and *"Weak Entanglement (WE)"* represent a **protocol-level metaphor** for non-linear dependency coupling between persistent structural anchors and reconstructible procedural details. It is an **information-theoretic abstraction** and **does not constitute a claim of quantum entanglement**.

**Codec reference:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py)  
**Emergence reference (normative):** [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py)  
**Horizon demo:** [`examples/horizon_compression_demo.py`](../examples/horizon_compression_demo.py)

---

## 0. Legal & Public Domain Status (Defensive Publication)

This specification and its associated algorithms constitute a **Defensive Publication** under the MIT License with public version-control timestamps (Prior Art).

**P-LOD is a public technical commons.** Implementers may build interoperable codecs freely. See [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md).

---

## 1. Goals

1. Define a clear **container + SE payload** for multi-language decoders.
2. Quantify why sparse skeletons can be orders of magnitude smaller than dense media.
3. Separate Core profile vs optional Embodied profile.

Illustrative sizes (e.g. ~2.51 KB) are **worked examples under stated assumptions**, not universal constants.

---

## 2. Frame Architecture Overview

| Layer | Name | Role |
|-------|------|------|
| **SE-Frame** | Strong-Entanglement Frame | Low-entropy topological skeleton (structure / identity / mission-critical logic) |
| **WE-Stream** | Weak-Entanglement Stream | Optional reconstructible detail |

**Design rule:** Mission-critical decisions MUST be possible from the **SE-Frame alone**.

---

## 3. Header (Core, 8 bytes)

Little-endian.

| Offset | Field | Type | Description |
|--------|-------|------|-------------|
| 0..1 | `MAGIC` | uint16 | `0x504C` |
| 2 | `VERSION` | uint8 | `0x10` v1.0; `0x11` v1.1 metas |
| 3 | `FLAGS` | uint8 | see below |
| 4..5 | `SE_NODE_COUNT` | uint16 | |
| 6..7 | `SEQUENCE_ID` | uint16 | |

**FLAGS:** bit0 WE_PRESENT, bit1 TOPOLOGY_INLINE, bit2 EMBODIED_PROFILE, bit3 FORWARD_FOCUS, bit4 EXTENDED_META.

---

## 4–5. Core / Embodied nodes & v1.1 metas

- Core suggested binary node: **24 bytes**
- Embodied node: **32 bytes** (pos, vel, phase, risk, sub_system)
- v1.1 optional **8-byte** meta: `resonance_freq` (float32), `causal_depth` (uint8), pad×3

Full layouts remain as previously published in this repository.

---

## 6. Weak-Entanglement Stream

Out of band relative to structural truth. Optional CRC32 trailer allowed.

---

## 7. Worked size example (illustrative)

80 × 32 B + header + CRC ≈ **2.51 KB**; + v1.1 metas ≈ **~3.1 KB**.

---

## 8. Progressive levels

Level 1 extreme skeleton → Level 2 attributes → Level 3 local transitions.

---

## 9. Official Reference Emergence Engine (Normative)

[`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) is the **normative reference** for SE decode + deterministic WE emergence (Source of Truth for **protocol compliance**).

Profile: `plod.ref.linear_spline.v1` · Default seed: `0x504C4F44`.

### 9.1 Metrics: Compliance (TCS) vs Fidelity (RFS)

| Metric | Full name | Answers | Pass rule |
|--------|-----------|---------|-----------|
| **TCS** | Topological Consistency Score | Does the third-party engine respect **protocol topology constraints** (e.g. emerged samples stay in the SE-bounded region defined by the reference)? | **TCS ≥ 0.99 → Protocol Compliance PASS** |
| **RFS** | Reconstruction Fidelity Score | How close is the emerged state to **original Ground Truth**? | Domain-specific (see below); **not** substituted by TCS |

**TCS is not RFS.** A system can be protocol-compliant (high TCS) while still looking different from a particular dense capture (low RFS), and vice versa.

**Suggested RFS measures (for experimental suites, not wire format):**

| Domain | Suggested RFS indicators |
|--------|--------------------------|
| 3D mesh / point cloud | Chamfer Distance, Hausdorff Distance |
| Image / video | PSNR, SSIM, LPIPS |
| Embodied / robotics | Task-completion / mission-success rate from SE-only control |

Reference engine log format (compliance runs without GT):

```text
TCS = 1.0000 | P-LOD Protocol Compliance Test: PASS
(Note: TCS verifies protocol compliance. Reconstruction Fidelity (RFS) is measured against original Ground Truth).
```

### 9.2 Third-party “P-LOD Compliant”

SHALL parse SE correctly; meet TCS ≥ 0.99 under the reference definition (or publish an alternate open profile); MUST NOT require WE for SE-only safety decisions.

---

## 10. Compliance checklist

Core decode rules + Section 9 for emergence claims.

---

## 11. Versioning

v1.0 wire · v1.1 additive metas · reference profile ids version independently.

---

## 12. References

| Resource | Path |
|----------|------|
| README | [../README.md](../README.md) |
| Roadmap + Benchmark Suite | [ROADMAP_AND_APPLICATIONS.md](ROADMAP_AND_APPLICATIONS.md) |
| Reference engine | [`../examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) |

---

*P-LOD Spec v1.0/v1.1 — Prior Art under MIT. TCS = compliance; RFS = fidelity to Ground Truth.*
