# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

**Sole public codec:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py).

---

## 0. Dual-Layer Mathematical Specification: Oracle vs Reference Extractor

P-LOD **rigorously separates** the theoretical information limit from its polynomial-time reference implementation.

### 1. Theoretical Global Oracle ($S_{\epsilon,X}^*$)

Absolute minimum degree of freedom over the full observation domain $X$:

$$
S_{\epsilon,X}^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{subject to} \quad D_{\mathrm{sym}}\bigl(X, G(S)\bigr) \le \epsilon
$$

This program is combinatorial and generally intractable for large $\lvert X\rvert$. It is the **ideal information limit**, not the claim of a single demo run.

### 2. Reference Candidate-Constrained Extractor ($\hat{S}_{\epsilon,P}^*$)

Engineering form used by the reference stack:

$$
P(X) = \mathrm{CandidateSelect}(X, K_{\mathrm{pool}})
$$

$$
\hat{S}_{\epsilon,P}^* = \mathrm{GreedyMarginalElimination}\bigl(P(X), G, D_{\mathrm{sym}}, \epsilon\bigr)
$$

Each greedy iteration removes

$$
p^* = \arg\min_{p_i \in S} D_{\mathrm{sym}}\bigl(X, G(S \setminus \{p_i\})\bigr)
$$

while $D^* \le \epsilon$, and stops when every single removal would exceed $\epsilon$.

**Certificate of $\epsilon$-minimality over the returned set** (not global optimality over $X$):

$$
\forall p_i \in \hat{S}_{\epsilon,P}^*,\quad D_{\mathrm{sym}}\bigl(X, G(\hat{S}_{\epsilon,P}^* \setminus \{p_i\})\bigr) > \epsilon
$$

### 3. Distortion $D_{\mathrm{sym}}$

Normalized **symmetric Chamfer** between $X$ and $G(S)$ (under-coverage + hallucination). Normative $G$: `plod.ref.linear_spline.v1`.

### 4. Empirical validation hooks

| Script | Role |
|--------|------|
| `examples/eval_oracle_vs_greedy.py` | On small $\lvert P\rvert$, compare greedy $\lvert\hat{S}\rvert$ to exhaustive oracle $\lvert S_{\mathrm{oracle}}\rvert$ → ratio $\rho$ |
| `examples/eval_pool_sufficiency.py` | Sweep $K_{\mathrm{pool}}$; look for plateau in $N^*(\epsilon)$ |
| `examples/eval_rate_distortion.py` | $\epsilon \mapsto N^*(\epsilon)$ curve |
| `examples/eval_structural_stability.py` | Multi-seed $SS_i$ |

High-Causal-Depth ($C_i\ge200$) remains a **relative** ablation rank; $\epsilon$-essential is the absolute certificate above.

---

## 1–11. Wire format (v1.1 core)

Header · Core 24B / Embodied 32B · Extended Meta (`resonance_freq` = Profile-Defined Placeholder) · Constraints · CRC-32/ISO-HDLC · TCS-AABB / RFS.

```bash
python examples/eval_oracle_vs_greedy.py --pool 12 --epsilon 0.15 --mode fast
python examples/eval_pool_sufficiency.py --epsilon 0.12 --mode fast
python tests/run_compliance_tests.py
```

---

*P-LOD Spec v1.1 — Oracle vs Extractor dual-layer. Prior Art under MIT.*
