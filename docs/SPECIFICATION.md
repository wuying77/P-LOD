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

---

*(Wire layout, constraint table, CRC-32/ISO-HDLC, security bounds, and extended sections remain as previously specified in this document body on main.)*
