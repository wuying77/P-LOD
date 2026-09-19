# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding — A Structural State Representation and Progressive Realization Protocol.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spec](https://img.shields.io/badge/spec-v1.1%20RFC-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)
[![CI](https://img.shields.io/badge/CI-compliance-success.svg)](.github/workflows/ci.yml)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.

> **Engineering Note:** SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

---

## Single public codec (Spec v1.1)

**[`examples/plod_spec_codec.py`](examples/plod_spec_codec.py)** is the only pack/decode implementation that tests and engines must use.

| FLAGS | Mask |
|-------|------|
| `HAS_CONSTRAINT_TABLE` | `0x01` |
| `IS_EMBODIED_PROFILE` | `0x02` |
| `HAS_EXTENDED_META` | `0x04` |

- Global/N/A node marker: **`0xFFFF`**
- CRC-32/ISO-HDLC; mismatch / trailing garbage / bad VERSION → **`ProtocolError`**

---

## Emergence profiles

| Profile | Role |
|---------|------|
| **`plod.ref.linear_spline.v1`** | **Normative frozen baseline** — pure linear mid/quarter points; no seed, jitter, or smoothstep |
| `plod.ref.linear_spline.v2` | Experimental — budgets, jitter, constraint projection |

---

## Quick start

```bash
python examples/plod_spec_codec.py --demo
python examples/reference_emergence_engine.py --profile v1
python examples/horizon_compression_demo.py
python examples/eval_reconstruction_fidelity.py

python tests/generate_vectors.py
python tests/run_compliance_tests.py
```

Shared metrics: [`examples/plod_metrics.py`](examples/plod_metrics.py) (symmetric Chamfer → RFS; AABB TCS).

---

## Pipeline

```text
Original → SE Extractor (ablation causal_depth) → Encoder (plod_spec_codec)
  → Binary Frame → decode_frame() → Emergence (v1/v2) → Validator (TCS / RFS)
```

$$
\mathrm{causal\_depth}_i = \mathrm{round}\big(255 \cdot \mathrm{clamp}(\Delta E_i / \max_j \Delta E_j,\,0,\,1)\big)
$$

---

## Docs

| Path | Role |
|------|------|
| [SPECIFICATION.md](docs/SPECIFICATION.md) | RFC-style wire format |
| [ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md) | Benchmarks A–D |
| [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md) | Prior Art |

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
