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

Practical extractors implement a **greedy ε-minimal search** (see `examples/horizon_compression_demo.py --epsilon`): start from an ablation-ranked pool and strip lowest-impact nodes while $D \le \epsilon$, reporting $N^*(\epsilon)$.

### Node removal loss & `causal_depth`

$$
\Delta E_i = D\bigl(X, G(S \setminus \{p_i\})\bigr) - D\bigl(X, G(S)\bigr)
$$

$$
C_i = \mathrm{round}\left( 255 \cdot \mathrm{clamp}\left( \frac{\Delta E_i}{\max_j(\Delta E_j)}, 0, 1 \right) \right)
$$

- $C_i \ge 200$ → **High-Causal-Depth Anchor** (relative rank)
- low $C_i$ → emergent redundancy at runtime

**Structural isomorphism note.** Volume→surface collapse is an **information-structural isomorphism**, not a claim of quantum gravity physics.

### Strict Definition: $\epsilon$-Essential Nodes and Structural Redundancy Throttle

#### 1. $\epsilon$-Essential Degree of Freedom

$$
p_i \text{ is } \epsilon\text{-essential} \iff \min_{\hat{S} \subseteq (S \setminus \{p_i\})} D\bigl(X, G(\hat{S})\bigr) > \epsilon
$$

| Term | Meaning |
|------|--------|
| **High-Causal-Depth Anchor** ($C_i \ge 200$) | *Relative* impact rank under $\Delta E_i$ |
| **$\epsilon$-Essential Node** | *Absolute* irreducible DoF for a chosen $\epsilon$ |

#### 2. Structural Redundancy Throttle

$$
\mathcal{R}_\epsilon(X) = \bigl\{ p_j \in X \;\big|\; D\bigl(X, G(X \setminus \{p_j\})\bigr) \le \epsilon \bigr\}
\qquad
S^* \approx X \setminus \mathcal{R}_\epsilon(X)
$$

#### 3. Adversarial Degeneracy & No-Structure Reject

Under pure unstructured noise, the absolute ablation field collapses (`max ΔE / E_full` near zero). Reference extractors **SHOULD** emit:

```text
STATUS: STRUCTURAL_CONFIDENCE_LOW
REASON: No stable independent structure detected. Frame skipped or baseline pass-through.
```
rather than minting a spurious SE skeleton. See `examples/horizon_compression_demo.py` and `examples/eval_adversarial_noise.py`.

### Structural Description Cost & Recursive Compression

Total information footprint is not only wire bytes, but joint **Structural Description Cost**:

$$
\mathcal{L}_{\mathrm{total}}(X) = \mathcal{L}(S^*) + \mathcal{L}(G)
$$

| Term | Meaning |
|------|--------|
| $\mathcal{L}(S^*)$ | Cardinality / wire entropy of the $\epsilon$-essential SE skeleton |
| $\mathcal{L}(G)$ | Complexity of the deterministic emergence profile (e.g. frozen `linear_spline.v1`) |

**Recursive structural compression** (roadmap / multi-scale):

$$
X \longrightarrow S_1 \longrightarrow S_2 \longrightarrow \cdots \longrightarrow S_k \longrightarrow (S^*, C, G)
$$

each stage applying $\epsilon_i$-constrained ablation to the previous skeleton, bounded by minimizing $\mathcal{L}(S^*)+\mathcal{L}(G)$.

---

## 1. Frame layout

```text
+----------+------------------+---------------------------+--------+
| Header   | SE Node Table    | Constraint Table (optional)| CRC32  |
| 8 bytes  | N × node_size    | 2 + M × 16 bytes          | 4 B    |
+----------+------------------+---------------------------+--------+
```

Derived Edge Rule (`plod.ref.linear_spline.v1`): sort by `node_id`, consecutive + ring; $t \in \{0.25,0.50,0.75\}$.

---

## 2–11. Wire format, CRC, metrics, security, profiles

Unchanged from v1.1 core: Header FLAGS (`0x01` CT / `0x02` Embodied / `0x04` Meta), Core 24B / Embodied 32B, Extended Meta with **`resonance_freq` = Profile-Defined Placeholder**, Constraint Table (`0xFFFF` global), CRC-32/ISO-HDLC, TCS-AABB / RFS, TLV future path.

```bash
python examples/horizon_compression_demo.py --epsilon 0.08
python examples/eval_adversarial_noise.py
python examples/eval_rate_distortion.py
python tests/run_compliance_tests.py
```

---

*P-LOD Spec v1.1 — self-contained. Prior Art under MIT.*
