# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation (v0.1.0+).  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

**Sole public codec:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py).

---

## 0. Mathematical Formulation: Minimal Independent Structure

### Ideal program (information-theoretic)

$$
S^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{subject to} \quad D_{\mathrm{sym}}\bigl(X, G(S)\bigr) \le \epsilon
$$

### Candidate Space and Two-Stage Minimization Protocol (normative engineering form)

Exhaustive search over all subsets of $X$ is intractable. P-LOD formalizes discovery as a **two-stage** discrete optimization over a finite **candidate manifold** $P(X)$:

1. **Candidate Generation Operator**

$$
P(X) = \mathrm{CandidateSelect}(X, K_{\mathrm{pool}})
$$

where $P(X)$ is a bounded candidate set ($\lvert P(X)\rvert \le K_{\mathrm{pool}}$, reference demos use $K_{\mathrm{pool}} \le 120$) obtained via spatial density / entropy proxies (e.g. cell centroids). **$P(X)$ is not claimed to equal $X$**; it is the explicit finite search domain of the reference extractor.

2. **Greedy $\epsilon$-Minimal Optimization over $P(X)$**

$$
S_\epsilon^* = \arg\min_{S \subseteq P(X)} \lvert S\rvert \quad \text{subject to} \quad D_{\mathrm{sym}}\bigl(X, G(S)\bigr) \le \epsilon
$$

Reference Stage-B solver: **dynamic greedy marginal elimination** — each round recompute

$$
D_i = D_{\mathrm{sym}}\bigl(X, G(S \setminus \{p_i\})\bigr)
$$

for all remaining $p_i$, drop $p^* = \arg\min_i D_i$ while $D^* \le \epsilon$, and stop when every single removal would exceed $\epsilon$.

**$\epsilon$-minimality certificate (over the final $S_\epsilon^*$):**

$$
\forall p_i \in S_\epsilon^*,\quad D_{\mathrm{sym}}\bigl(X, G(S_\epsilon^* \setminus \{p_i\})\bigr) > \epsilon
$$

### Distortion $D_{\mathrm{sym}}$

Normalized **symmetric Chamfer** between the observation $X$ and the emergence $G(S)$:

$$
D_{\mathrm{sym}}(X, G(S)) = \frac{1}{2}\Bigl[ D_{\mathrm{mean}}(X \to G(S)) + D_{\mathrm{mean}}(G(S) \to X) \Bigr] \big/ \mathrm{bbox\_diag}(X)
$$

This jointly penalizes **under-coverage** of $X$ and **hallucinated** mass in $G(S)$. Normative $G$ for claims: `plod.ref.linear_spline.v1`.

### High-Causal-Depth vs $\epsilon$-Essential

| Term | Meaning |
|------|--------|
| **High-Causal-Depth Anchor** ($C_i \ge 200$) | Relative rank under leave-one-out $\Delta E_i$ |
| **$\epsilon$-Essential** | Absolute: removing the node forces $D_{\mathrm{sym}} > \epsilon$ |

### No-structure reject

If the ablation field on $P(X)$ is degenerate (e.g. pure noise), extractors **SHOULD** report `STRUCTURAL_CONFIDENCE_LOW` rather than emit a spurious skeleton.

### Structural Description Cost & Recursion

$$
\mathcal{L}_{\mathrm{total}}(X) = \mathcal{L}(S_\epsilon^*) + \mathcal{L}(G)
$$

Recursive multi-scale reduction remains a roadmap item: $X \to S_1 \to \cdots \to (S_\epsilon^*, C, G)$.

---

## 1–11. Wire format (unchanged v1.1 core)

Header 8B · Core 24B / Embodied 32B · Extended Meta (`resonance_freq` = **Profile-Defined Placeholder**) · Constraint Table · CRC-32/ISO-HDLC · TCS-AABB / RFS · Derived Edge Rule for `linear_spline.v1`.

```bash
python examples/horizon_compression_demo.py --ablation-mode exact --epsilon 0.10
python examples/eval_rate_distortion.py --mode fast
python examples/eval_structural_stability.py
python tests/run_compliance_tests.py
```

---

*P-LOD Spec v1.1 — self-contained. Prior Art under MIT.*
