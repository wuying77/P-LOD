# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec](https://img.shields.io/badge/spec-v1.0%2Fv1.1-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.

> **Engineering Note on Terminology:** SE / WE are **protocol-level, information-theoretic metaphors** for structural anchors vs reconstructible detail — **not** quantum entanglement.

---

## Structural pipeline

```text
Original Data
    → SE Extractor (density + curvature + node ablation ΔE)
    → P-LOD Encoder
    → P-LOD Binary Frame  (Nodes + Edges + Constraint Table)
    → P-LOD Decoder
    → Emergence Engine  (plod.ref.linear_spline.v1 frozen baseline)
    → Validator  (TCS = compliance · RFS = fidelity vs Ground Truth)
```

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints},\quad
\mathrm{causal\_depth}(i)\propto \Delta E_{\mathrm{ablation}}
$$

---

## Quick start

```bash
cd examples

# Ablation-based SE extraction + horizon compression
python horizon_compression_demo.py

# RFS / Chamfer / CR report (vs Ground Truth cloud)
python eval_reconstruction_fidelity.py

# Reference emergence (budgets)
python reference_emergence_engine.py --budget constrained

# Golden vectors
cd ../tests
python generate_vectors.py
python run_compliance_tests.py
```

---

## Docs & tools

| Path | Role |
|------|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | Wire format, Constraint Section, causal_depth semantics |
| [ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md) | Benchmarks A–D; ablation marked in-repo |
| [horizon_compression_demo.py](examples/horizon_compression_demo.py) | Node ablation → causal_depth |
| [eval_reconstruction_fidelity.py](examples/eval_reconstruction_fidelity.py) | CR, Chamfer, TCS, RFS |
| [reference_emergence_engine.py](examples/reference_emergence_engine.py) | **plod.ref.linear_spline.v1** normative frozen baseline |

---

## Metrics

| Score | Role |
|-------|------|
| **TCS** | Protocol compliance |
| **RFS** | $1 - \mathrm{normalized\ Chamfer}$ (fidelity to GT) |
| **CR** | Compression ratio |

---

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
