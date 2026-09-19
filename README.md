# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec](https://img.shields.io/badge/spec-v1.1%20RFC-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)
[![CI](https://img.shields.io/badge/CI-compliance-success.svg)](.github/workflows/ci.yml)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

---

## Single public codec (Source of Truth)

**[`examples/plod_spec_codec.py`](examples/plod_spec_codec.py)** — sole `encode_frame` / `decode_frame`.  
Golden vectors, tests, and the reference engine call **only** this module. No parallel binary packers.

| FLAGS | Mask |
|-------|------|
| `HAS_CONSTRAINT_TABLE` | `0x01` |
| `IS_EMBODIED_PROFILE` | `0x02` |
| `HAS_EXTENDED_META` | `0x04` |

---

## Emergence profiles

| CLI | Profile |
|-----|--------|
| `--profile v1` **(default)** | `plod.ref.linear_spline.v1` normative frozen baseline |
| `--profile v2` | experimental budgets / jitter / Distance+Boundary |

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

**TCS-AABB** is a containment **proxy**; full compliance also needs edge validity, constraint compliance, and sample coverage (see Spec §8).

---

## Architecture (current → package roadmap)

**Today (reference tree):**

```text
examples/plod_spec_codec.py   # codec (SoT)
examples/plod_metrics.py      # TCS-AABB / RFS
examples/reference_emergence_engine.py
tests/                        # golden vectors + CI
docs/SPECIFICATION.md
```

**Future package layout (non-breaking target):**

```text
src/plod/
  codec.py      # from plod_spec_codec
  metrics.py    # from plod_metrics
  profiles.py   # v1 / v2 emergence
```

Migration will re-export the same APIs so existing imports remain stable.

---

## Docs

| Path | Role |
|------|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | Wire format, version matrix, constraints, future TLV |
| [ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md) | Benchmarks |
| [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md) | Prior Art |

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
