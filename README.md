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
    → SE Extractor
    → P-LOD Encoder
    → P-LOD Binary Frame
    → P-LOD Decoder
    → Emergence Engine (compute budget: coarse | constrained | high_fidelity)
    → Validator (TCS = compliance · RFS = fidelity vs Ground Truth)
```

$$
\mathrm{SE} = \mathrm{Nodes} + \mathrm{Edges} + \mathrm{Constraints}
$$

---

## Quick start

```bash
cd examples
python reference_emergence_engine.py --budget coarse
python reference_emergence_engine.py --budget constrained
python reference_emergence_engine.py --budget high_fidelity

# Golden vectors
cd ../tests
python generate_vectors.py
python run_compliance_tests.py
```

---

## Docs

| Doc | Role |
|-----|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | Wire format, Constraint Table, budgets, TCS/RFS |
| [ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md) | Domains + Benchmarks A–D |
| [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md) | Prior Art |
| [reference_emergence_engine.py](examples/reference_emergence_engine.py) | Normative emergence (Source of Truth for TCS) |

---

## Metrics

| Score | Role |
|-------|------|
| **TCS** | Protocol compliance (topology / constraints) |
| **RFS** | Reconstruction fidelity vs original Ground Truth |

---

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
