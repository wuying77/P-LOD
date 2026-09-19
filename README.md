# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec](https://img.shields.io/badge/spec-v1.1%20RFC-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)
[![CI](https://img.shields.io/badge/CI-compliance-success.svg)](.github/workflows/ci.yml)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

---

## Single public codec

**[`examples/plod_spec_codec.py`](examples/plod_spec_codec.py)** is the **only** encode/decode path (`encode_frame` / `decode_frame`). Golden vectors, tests, and the reference engine all call this module — no parallel pack/unpack implementations.

| FLAGS | Mask |
|-------|------|
| `HAS_CONSTRAINT_TABLE` | `0x01` |
| `IS_EMBODIED_PROFILE` | `0x02` |
| `HAS_EXTENDED_META` | `0x04` |

---

## Emergence profiles

| CLI | Profile | Role |
|-----|---------|------|
| `--profile v1` (default) | `plod.ref.linear_spline.v1` | Normative frozen baseline |
| `--profile v2` | `plod.ref.linear_spline.v2` | Experimental budgets / jitter |

---

## Quick start (copy-paste)

```bash
python examples/plod_spec_codec.py --demo
python examples/reference_emergence_engine.py --profile v1
python examples/reference_emergence_engine.py --profile v2 --budget constrained
python examples/horizon_compression_demo.py
python examples/eval_reconstruction_fidelity.py

python tests/generate_vectors.py
python tests/run_compliance_tests.py
python examples/test_plod_spec_codec.py
```

---

## Docs

| Path | Role |
|------|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | Wire format, version matrix, constraint semantics |
| [ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md) | Benchmarks |
| [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md) | Prior Art |

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
