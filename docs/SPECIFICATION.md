# P-LOD Protocol Specification v1.0 / v1.1

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> **Engineering Note on Terminology:**  
> *"Strong Entanglement (SE)"* and *"Weak Entanglement (WE)"* are **protocol-level metaphors** for non-linear dependency coupling between persistent structural anchors and reconstructible procedural details. They are **information-theoretic abstractions** and **do not constitute a claim of quantum entanglement**.

**Pipeline (structural realization):**

```text
Original Data → SE Extractor → P-LOD Encoder → P-LOD Binary Frame
       → P-LOD Decoder → Emergence Engine (budgeted) → Validator (TCS / RFS)
```

**References:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py) · [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) · [`tests/run_compliance_tests.py`](../tests/run_compliance_tests.py)

---

## 0. Legal (Defensive Publication)

Public technical commons under MIT with Prior Art timestamps. Full text: [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md).

---

## 1. Structural definition of SE

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

| Component | Role |
|-----------|------|
| **Nodes** | Discrete structural anchors (positions, labels, metas) |
| **Edges** | Topology links (explicit edge list or ordered-id chain in reference profile) |
| **Constraints** | Hard / soft rules the WE emergencer must respect |

WE detail is *progressive realization* under a **compute budget**, not a second stored dense volume.

---

## 2. Frame overview

| Layer | Role |
|-------|------|
| SE-Frame | Structural state (nodes + edges + optional constraint table) |
| WE-Stream | Optional emergent detail |

Mission-critical decisions MUST be possible from **SE alone**.

---

## 3. Header (8 bytes)

`MAGIC=0x504C`, `VERSION` `0x10`/`0x11`, `FLAGS`, `SE_NODE_COUNT`, `SEQUENCE_ID`.

FLAGS: WE_PRESENT, TOPOLOGY_INLINE, EMBODIED_PROFILE, FORWARD_FOCUS, EXTENDED_META, …

---

## 4–5. Nodes (Core 24B / Embodied 32B) + v1.1 metas

Core / Embodied layouts as previously specified. v1.1 meta: `resonance_freq` (f32), `causal_depth` (u8).

---

## 5.7 Constraint Table (v1.1 Extended Specification)

Optional section after nodes (before CRC). When present, FLAG bit or profile documents `CONSTRAINT_TABLE`.

**Logical record** (reference encoding; portable across languages):

| Field | Type | Description |
|-------|------|-------------|
| `ctype` | uint8 | Constraint class |
| `node_a` | uint16 | Primary node id (0 = global) |
| `node_b` | uint16 | Secondary node id |
| `value` | float32 | Class-specific scalar |

**Constraint classes:**

| Code | Name | Semantics |
|------|------|-----------|
| `0x01` | **Distance Constraint** | Upper bound on topological/spatial separation between A and B |
| `0x02` | **Boundary / Safety Constraint** | WE samples must not exit the given safety/physical envelope (e.g. max radius) |
| `0x03` | **Temporal Link** | Causal / temporal evolution bound between time-indexed anchors |

Reference Emergence Engine 2.0 applies Distance + Boundary projection under `budget=constrained|high_fidelity`.

---

## 6. WE stream & CRC

WE optional. CRC32 trailer optional but recommended for golden vectors.

---

## 7. Size examples

~2.51 KB class for 80×32B embodied + header + CRC; +metas ≈ 3.1 KB.

---

## 8. Progressive levels

L1 skeleton → L2 attributes → L3 transitions.

---

## 9. Official Reference Emergence Engine (Normative)

[`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py) — **Source of Truth** for protocol compliance.

### 9.1 Compute budgets

| Budget | Intent | Behavior |
|--------|--------|----------|
| `coarse` | ~1 ms class | Midpoint linear emergence only |
| `constrained` | ~10 ms class | Midpoints + **Constraint Table** projection |
| `high_fidelity` | ~50 ms class | Dense samples + smoothstep + constraints + micro-jitter |

### 9.2 Metrics

| Metric | Meaning | Pass |
|--------|---------|------|
| **TCS** | Protocol topological consistency | ≥ 0.99 |
| **RFS** | Fidelity vs Ground Truth | Domain metrics (Roadmap Benchmarks A–D) |

TCS ≠ RFS.

---

## 10. Golden vectors

`tests/generate_vectors.py` · `tests/run_compliance_tests.py` · `tests/vectors/*.plod`

- `minimal_valid.plod` — valid core SE  
- `embodied_32b.plod` — embodied + metas  
- `invalid_crc.plod` — CRC failure path  
- `unknown_extension.plod` — unknown flag forward-compat  

---

## 11–12. Compliance & versioning

v1.0 wire · v1.1 metas + Constraint Table semantics · Reference profile `plod.ref.linear_spline.v2`

---

*Structural State Representation and Progressive Realization Protocol — Prior Art under MIT.*
