# P-LOD Protocol Specification v1.0 / v1.1

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> **Engineering Note on Terminology:** SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

```text
Original Data → SE Extractor → Encoder → Binary Frame → Decoder → Emergence Engine → Validator (TCS / RFS)
```

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

---

## Frame payload layout (v1.1)

```text
+----------+----------------+---------------------------+-------+
| Header   | SE Node Table  | Constraint Table (optional)| CRC32 |
| 8 bytes  | N × node       | M × constraint entry       | 4 B   |
+----------+----------------+---------------------------+-------+
```

### Header
`MAGIC=0x504C`, VERSION `0x10`/`0x11`, FLAGS, `SE_NODE_COUNT`, `SEQUENCE_ID`.

FLAGS bit2 = EMBODIED, bit4 = EXTENDED_META. Implementations MAY use profile docs to signal Constraint Table presence after nodes.

### SE nodes
Core 24B or Embodied 32B (+ optional 8B meta: `resonance_freq`, `causal_depth`).

**`causal_depth` (semantic):** recommended assignment is structural importance from **node ablation** —  
$$\mathrm{causal\_depth}(i)\;\propto\;\Delta E\quad\text{(reconstruction error increase if node }i\text{ is removed)}.$$

Values $\ge 200$ mark **Causal Anchors**. Demo reference: `examples/horizon_compression_demo.py`.

### Constraint Table (optional, v1.1 Extended)

Independent of the node array. Each **Constraint Entry**:

| Offset | Field | Type | Notes |
|--------|-------|------|-------|
| 0 | `constraint_type` | uint8 | see table below |
| 1 | `flags` | uint8 | reserved 0 |
| 2..3 | `node_a` | uint16 | 0 = global / N/A |
| 4..5 | `node_b` | uint16 | second target |
| 6..9 | `param0` | float32 | primary scalar (e.g. max distance, radius) |
| 10..13 | `param1` | float32 | optional secondary |
| 14..15 | `reserved` | uint16 | 0 |

**Entry size: 16 bytes.**

| Type | Code | Meaning |
|------|------|--------|
| Distance | `0x01` | Max spatial/topological separation A–B |
| Boundary / Safety | `0x02` | WE must not exit envelope (`param0` = radius or half-extent) |
| Temporal Link | `0x03` | Causal/temporal bound between time anchors |
| Symmetry | `0x04` | Optional symmetry relation (profile-defined `param*`) |

Preceding the table: `uint16 constraint_count` (when profile indicates constraints present).

Reference engine applies Distance + Boundary under compute budgets `constrained` / `high_fidelity`.

---

## Official Reference Emergence Engine

| Profile | Status |
|---------|--------|
| **`plod.ref.linear_spline.v1`** | **Normative frozen baseline** (stdlib-only, transparent mid/quarter points) |
| `plod.ref.linear_spline.v2` | Budgeted + constraint projection (engineering track) |

File: [`examples/reference_emergence_engine.py`](../examples/reference_emergence_engine.py)

**TCS** ≥ 0.99 → Protocol Compliance PASS. **RFS** vs Ground Truth: see [`examples/eval_reconstruction_fidelity.py`](../examples/eval_reconstruction_fidelity.py).

---

## Metrics

| Metric | Role |
|--------|------|
| TCS | Protocol topology compliance |
| RFS | $1 - \mathrm{normalized\ Chamfer}$ (or domain equivalent) |
| CR | Raw bytes / SE-Frame bytes |

TCS ≠ RFS.

---

## Golden vectors

`tests/generate_vectors.py` · `tests/run_compliance_tests.py`

---

*Structural State Representation and Progressive Realization Protocol — Prior Art under MIT.*
