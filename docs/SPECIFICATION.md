# P-LOD Protocol Specification v1.1 (RFC-style Core Standard)

**P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation.  
**Byte order:** **Little-Endian**.  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

**Normative Implementation:** [`src/plod/spec/codec.py`](../src/plod/spec/codec.py)  
**Public Package API:** `plod.encode_frame` / `plod.decode_frame` / `plod.emerge`  
**Compatibility Entry Point:** [`examples/plod_spec_codec.py`](../examples/plod_spec_codec.py)

> **Profile note:** `plod.ref.linear_spline.v2` is registered as an **experimental** profile identifier (currently identical to the normative `plod.ref.linear_spline.v1` baseline algorithm).

---

## 0. Dual-Layer Math: Oracle vs Reference Extractor

### Theoretical Oracle

$$
S_{\epsilon,X}^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{s.t.} \quad D_{\mathrm{sym}}(X, G(S)) \le \epsilon
$$

### Reference Extractor (engineering)

$$
P(X)=\mathrm{CandidateSelect}(X,K_{\mathrm{pool}})
$$

$$
\hat{S}_{\epsilon,P}^* = \mathrm{GreedyMarginalElimination}(P(X), G, D_{\mathrm{sym}}, \epsilon)
$$

Each round evaluates **full emergence loop**:

$$
S \xrightarrow{G=\texttt{plod.ref.linear\_spline.v1}} G(S) \xrightarrow{D_{\mathrm{sym}}} D_{\mathrm{sym}}(X, G(S))
$$

Reference code path: temporary `SENode` list → `reference_emergence_engine.emerge_v1` → symmetric Chamfer / bbox (`examples/horizon_compression_demo.py`, `--ablation-mode exact`).

**Dynamic marginal elimination** (not fixed rank truncation): remove $p^*=\arg\min_i D_{\mathrm{sym}}(X,G(S\setminus\{p_i\}))$ only while $D^*\le\epsilon$.

### Minimal Structural Description Cost $\mathcal{L}_{\mathrm{PLOD}}$

$$
\mathcal{L}_{\mathrm{PLOD}}(S,G) = \mathcal{L}_{\mathrm{frame}}(S) + \mathcal{L}_{\mathrm{profile}}(G) + \mathcal{L}_{\mathrm{constraints}}
$$

$$
S_\epsilon^* = \arg\min_{S \subseteq P(X)} \mathcal{L}_{\mathrm{PLOD}}(S,G) \quad \text{s.t.} \quad D_{\mathrm{sym}}(X,G(S)) \le \epsilon
$$

where $\mathcal{L}_{\mathrm{frame}}(S)$ is the exact byte size of the serialized v1.1 SE-Frame. For fixed normative profile $G$, minimizing $\lvert S\rvert$ under the distortion constraint is the reference greedy objective; $\mathcal{L}_{\mathrm{profile}}$ is constant across comparisons that share the same profile id.

### `causal_depth`

Ablation-derived **structural sensitivity index** under normative $G$ — local DoF criticality, **not** absolute causal ontology.

### Validation hooks

| Script | Role |
|--------|------|
| `eval_oracle_vs_greedy.py` | $\rho$ vs exhaustive |
| `eval_pool_sufficiency.py` | $N^*(\epsilon,K)$ plateau |
| `eval_synthetic_ground_truth.py` | $R_P$, Precision, Recall, F1 |
| `eval_rate_distortion.py` | $\epsilon\mapsto N^*$ |

---

## Wire format v1.1 (summary)

Header · Core 24B / Embodied 32B · Extended Meta (`resonance_freq` placeholder) · Constraints · CRC-32/ISO-HDLC · TCS-AABB / RFS.

```bash
python examples/horizon_compression_demo.py --ablation-mode exact --epsilon 0.10
python examples/eval_synthetic_ground_truth.py --mode exact --epsilon 0.08
python tests/run_compliance_tests.py
```

---

*P-LOD Spec v1.1 — emergence-closed $D_{\mathrm{sym}}$. Prior Art under MIT.*
