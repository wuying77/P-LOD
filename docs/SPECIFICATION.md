# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

**Sole public codec:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py).

---

## 0. Dual-Layer Mathematical Specification: Oracle vs Reference Extractor

### 1. Theoretical Global Oracle ($S_{\epsilon,X}^*$)

$$
S_{\epsilon,X}^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{subject to} \quad D_{\mathrm{sym}}\bigl(X, G(S)\bigr) \le \epsilon
$$

Ideal information limit; generally intractable for large $\lvert X\rvert$.

### 2. Reference Candidate-Constrained Extractor ($\hat{S}_{\epsilon,P}^*$)

$$
P(X) = \mathrm{CandidateSelect}(X, K_{\mathrm{pool}})
$$

$$
\hat{S}_{\epsilon,P}^* = \mathrm{GreedyMarginalElimination}\bigl(P(X), G, D_{\mathrm{sym}}, \epsilon\bigr)
$$

**Dynamic marginal elimination (normative reference loop):** each round, for every remaining $p_i \in S$, evaluate

$$
D_i = D_{\mathrm{sym}}\bigl(X, G(S \setminus \{p_i\})\bigr)
$$

remove $p^* = \arg\min_i D_i$ **only if** $D^* \le \epsilon$; otherwise stop. This is **not** fixed rank-ordered truncation of a static list.

Full chain for every trial deletion:

$$
S \longrightarrow G(S) \longrightarrow D_{\mathrm{sym}}(X, G(S))
$$

with normative $G =$ `plod.ref.linear_spline.v1` when `--ablation-mode exact`.

**$\epsilon$-minimality certificate over the returned set:**

$$
\forall p_i \in \hat{S}_{\epsilon,P}^*,\quad D_{\mathrm{sym}}\bigl(X, G(\hat{S}_{\epsilon,P}^* \setminus \{p_i\})\bigr) > \epsilon
$$

### 3. Distortion $D_{\mathrm{sym}}$

Normalized symmetric Chamfer (under-coverage + hallucination).

### 4. `causal_depth` terminology

**`causal_depth` is an ablation-derived structural sensitivity index** computed under the normative reference generator $G$. It quantifies **local degree-of-freedom criticality** within a given candidate set and ablation experiment. It is **not** a claim of absolute causal inference ontology, interventional causality, or physical causation outside the chosen $(G, D_{\mathrm{sym}}, P(X))$ experiment.

### 5. Empirical validation hooks

| Script | Role |
|--------|------|
| `eval_oracle_vs_greedy.py` | Exhaustive vs greedy $\rho$ on small $\lvert P\rvert$ |
| `eval_pool_sufficiency.py` | $N^*(\epsilon, K_{\mathrm{pool}})$ plateau |
| `eval_rate_distortion.py` | $\epsilon \mapsto N^*$ |
| `eval_structural_stability.py` | Multi-seed $SS_i$ |
| `eval_synthetic_ground_truth.py` | $S_{\mathrm{true}}\to X\to\hat{S}$ Precision/Recall |

---

## 1–11. Wire format (v1.1 core)

Header · Core/Embodied nodes · Extended Meta (`resonance_freq` = Profile-Defined Placeholder) · Constraints · CRC-32/ISO-HDLC · TCS-AABB / RFS.

```bash
python examples/horizon_compression_demo.py --ablation-mode exact --epsilon 0.12
python examples/eval_synthetic_ground_truth.py --mode exact --epsilon 0.12
python tests/run_compliance_tests.py
```

---

*P-LOD Spec v1.1 — dual-layer Oracle vs Extractor. Prior Art under MIT.*
