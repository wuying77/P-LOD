# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation (v0.1.0 milestone).  
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

| Symbol | Meaning |
|--------|--------|
| $\lvert S\rvert$ | Cardinality of the independent SE node set |
| $G$ | Emergence map (normative: `plod.ref.linear_spline.v1`) |
| $D(\cdot,\cdot)$ | Normalized topological distortion (e.g. symmetric Chamfer / bbox diagonal) |
| $\epsilon \ge 0$ | Target reconstruction tolerance |

### Node removal loss & `causal_depth`

Leave-one-out removal loss:

$$
\Delta E_i = D\bigl(X, G(S \setminus \{p_i\})\bigr) - D\bigl(X, G(S)\bigr)
$$

Quantized causal depth $C_i \in [0,255]$:

$$
C_i = \mathrm{round}\left( 255 \cdot \mathrm{clamp}\left( \frac{\Delta E_i}{\max_j(\Delta E_j)}, 0, 1 \right) \right)
$$

- $C_i \ge 200$ → **High-Causal-Depth Anchor** (relativized rank of structural impact under ablation)
- low $C_i$ → emergent redundancy synthesized by $G(S)$ at runtime, not necessarily serialized on the wire

Practical extractors approximate $S^*$ by ablation-ranked candidates; exhaustive search is NP-hard.

**Structural isomorphism note.** Volume→surface collapse is an **information-structural isomorphism**, not a claim of quantum gravity physics.

### Strict Definition: $\epsilon$-Essential Nodes and Structural Redundancy Throttle

Relative ranking ($C_i$) is not the same as absolute irreplaceability. P-LOD separates the two.

#### 1. $\epsilon$-Essential Degree of Freedom

Given $X$, $G$, $D$, and tolerance $\epsilon \ge 0$, a candidate $p_i \in S$ is **$\epsilon$-essential** iff its removal forces reconstruction error to breach $\epsilon$:

$$
p_i \text{ is } \epsilon\text{-essential} \iff \min_{\hat{S} \subseteq (S \setminus \{p_i\})} D\bigl(X, G(\hat{S})\bigr) > \epsilon
$$

| Term | Meaning |
|------|--------|
| **High-Causal-Depth Anchor** ($C_i \ge 200$) | *Relative* impact rank under $\Delta E_i$ |
| **$\epsilon$-Essential Node** | *Absolute* irreducible degree of freedom for a chosen $\epsilon$ |

A node may be high-$C_i$ yet not $\epsilon$-essential for a loose $\epsilon$; conversely, under a tight $\epsilon$, more nodes become $\epsilon$-essential.

#### 2. Structural Redundancy Throttle

Non-$\epsilon$-essential candidates (under a fixed extractor / $G$ / $\epsilon$):

$$
\mathcal{R}_\epsilon(X) = \bigl\{ p_j \in X \;\big|\; D\bigl(X, G(X \setminus \{p_j\})\bigr) \le \epsilon \bigr\}
$$

Idealized wire payload (conceptual throttle; practical codecs emit ranked top-$k$ SE tables):

$$
S^* \approx X \setminus \mathcal{R}_\epsilon(X)
$$

Redundant nodes are suppressed on the wire; the decoder reconstructs via $G(S^*)$.

#### 3. Adversarial Degeneracy Criterion (Zero-Causal Noise Limit)

Under pure unstructured noise $W \sim \mathcal{N}(\mu, \Sigma)$ (or i.i.d. uniform scatter without topology):

$$
\forall p_i \in W,\quad \Delta E_i \to 0 \quad\implies\quad C_i \approx 0
$$

and typically $\nexists\, p_i \in W$ that is $\epsilon$-essential for moderate $\epsilon$. Reference: `examples/eval_adversarial_noise.py`.

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

| VERSION | Wire name | Allowed | Forbidden |
|---------|-----------|---------|-----------|
| `0x10` | v1.0 | Header + Core/Embodied nodes + CRC | Constraint Table; Extended Meta |
| `0x11` | v1.1 | Full optional CT + Meta | — |
| other | — | — | **MUST** `ProtocolError` |

---

## 3. Core Node (24 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 (`0..65534`) |
| 2 | 1 | `level` | uint8 (`1..3`) |
| 3 | 1 | `type_code` | uint8 |
| 4–15 | 12 | `x,y,z` | float32 × 3 |
| 16–18 | 3 | `r,g,b` | uint8 × 3 |
| 19 | 1 | `node_flags` | uint8 |
| 20–23 | 4 | `param0` | float32 |

---

## 4. Embodied Node (32 bytes)

| Offset | Size | Field | Type |
|-------:|-----:|-------|------|
| 0–1 | 2 | `node_id` | uint16 |
| 2 | 1 | `risk_state` | 0=SAFE, 1=WATCH, 2=CRITICAL |
| 3 | 1 | `sub_system` | uint8 |
| 4–15 | 12 | `pos` | float32 × 3 |
| 16–27 | 12 | `vel` | float32 × 3 |
| 28–31 | 4 | `phase` | float32 |

---

## 5. Extended Meta (8 bytes) — v1.1 only

| Offset | Size | Field | Notes |
|-------:|-----:|-------|-------|
| 0–3 | 4 | `resonance_freq` | **Profile-Defined Placeholder / Demo Parameter** |
| 4 | 1 | `causal_depth` | $C_i$ as defined in §0 |
| 5–7 | 3 | pad | must be 0 |

**`resonance_freq` semantics:** The baseline reference profiles (`plod.ref.linear_spline.v1` / v2) **do not** require extracting a physical vacuum or modal resonance from point clouds. The field exists for (1) fixed Extended Meta layout, (2) forward-compatible profile experiments, and (3) demo numerical fill. Third-party profiles **MAY** assign domain-specific meaning; until then treat values as **opaque placeholders**, not measured physics.

---

## 6. Constraint Table — v1.1 only

`uint16 count` + `count × 16` byte entries. Global/N/A = `0xFFFF`.

| Type | Code | Profile handling |
|------|------|------------------|
| Distance | `0x01` | v2 may enforce; v1 stores |
| Boundary | `0x02` | v2 may enforce; v1 stores |
| Temporal Link | `0x03` | Pass-through in v1/v2 ref |
| Symmetry | `0x04` | Pass-through in v1/v2 ref |

---

## 7. CRC-32/ISO-HDLC

Coverage: Header + Nodes + Constraints; excludes trailing CRC. LE uint32.

---

## 8. Metrics

**TCS-AABB** = containment proxy. **RFS** = `1 - min(1, CD/bbox_diag)`.  
Full compliance = edge validity + constraint compliance + sample coverage.

---

## 9. Security

Unique `node_id`; finite floats; no silent truncation; reject unknown VERSION / bad CRC / trailing garbage.

---

## 10. Profiles & CLI

```bash
python examples/reference_emergence_engine.py --profile v1
python examples/eval_rate_distortion.py
python examples/eval_adversarial_noise.py
```

---

## 11. Future Extension Strategy (v1.2 / v2.0+)

Reserved FLAGS bits 3–7; optional TLV after Constraint Table; new constraint codes ≥ `0x10` pass-through.

---

*P-LOD Spec v1.1 — self-contained. Prior Art under MIT.*
