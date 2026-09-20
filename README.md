# P-LOD

**P-LOD (Progressive Structural State Representation):** A deterministic, RFC-style protocol and framework for **discovering, encoding, and dynamically emerging minimal independent structures** from high-entropy states.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/release-v0.1.0-blue.svg)](docs/RELEASE_v0.1.0.md)
[![Spec](https://img.shields.io/badge/spec-v1.1%20RFC-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)
[![CI](https://img.shields.io/badge/CI-compliance-success.svg)](.github/workflows/ci.yml)

**Status:** **Protocol v0.1.0** (GitHub Release) · **Python package `plod-protocol` 0.1.1**

> SE / WE are protocol-level information-theoretic metaphors — **not** quantum entanglement.

$$
S^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{s.t.} \quad D\bigl(X, G(S)\bigr) \le \epsilon
$$

**Release notes:** [docs/RELEASE_v0.1.0.md](docs/RELEASE_v0.1.0.md) · **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

## Single public codec (Source of Truth)

**Normative Implementation:** [`src/plod/spec/codec.py`](src/plod/spec/codec.py) — sole normative `encode_frame` / `decode_frame`.  
**Public Package API:** `plod.encode_frame` / `plod.decode_frame` / `plod.emerge`.  
**Compatibility Layer:** [`examples/plod_spec_codec.py`](examples/plod_spec_codec.py).

---

## Quick Start & Installation

Install from a local checkout (PyPI name: **`plod-protocol`**):

```bash
pip install -e .
# or, after release:
# pip install plod-protocol
```

### 1-Minute Minimal Usage

```python
from plod import encode_frame, decode_frame, SENode, emerge

# 1. Minimal independent structure (SE nodes)
nodes = [
    SENode(node_id=1, pos=(10.0, 20.0, 30.0), causal_depth=255),
    SENode(node_id=2, pos=(15.0, 25.0, 35.0), causal_depth=220),
]

# 2. Binary protocol encode
frame_bytes = encode_frame(nodes)

# 3. Binary protocol decode
decoded = decode_frame(frame_bytes)

# 4. Normative emergence (plod.ref.linear_spline.v1)
emerged = emerge(decoded.nodes, profile="v1")
print(f"P-LOD active — reconstructed {len(emerged)} spatial samples from {len(decoded.nodes)} SE nodes.")
```

### Developer demos (repo checkout)

```bash
export PYTHONPATH=src
python tests/materialize_vectors.py
python examples/plod_spec_codec.py --demo
python examples/reference_emergence_engine.py --profile v1
python examples/horizon_compression_demo.py
python tests/run_compliance_tests.py
```

> **Profile v2:** `plod.ref.linear_spline.v2` is an experimental placeholder (currently identical to normative v1).

---

## Rate–Distortion Performance & Minimal Degrees of Freedom

Synthetic volume $|X|=10\,000$ points; ablation-ranked SE; emergence `plod.ref.linear_spline.v1`.

| N_SE | SE-Frame (B) | Compression | Chamfer D | D/diag | RFS |
|-----:|-------------:|------------:|----------:|------:|----:|
| 4 | 172 | **1396×** | 0.3466 | 0.0770 | 0.9230 |
| 8 | 332 | 723× | 0.2969 | 0.0660 | 0.9340 |
| 16 | 652 | 368× | 0.2327 | 0.0517 | 0.9483 |
| 32 | 1292 | 186× | 0.1910 | 0.0424 | 0.9576 |
| 64 | 2572 | 93× | 0.1580 | 0.0351 | 0.9649 |
| 128 | 4812 | 50× | 0.1361 | 0.0303 | 0.9697 |

![Rate–Distortion curve](docs/rate_distortion_curve.svg)

Regenerate: `python examples/eval_rate_distortion.py`  
Formal $S^*$: [Spec §0](docs/SPECIFICATION.md).

---

## Docs

| Path | Role |
|------|------|
| [RELEASE_v0.1.0.md](docs/RELEASE_v0.1.0.md) | Official release notes |
| [CHANGELOG.md](CHANGELOG.md) | Package changelog |
| [SPECIFICATION.md](docs/SPECIFICATION.md) | $S^*$ math + wire format |
| [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md) | Prior Art |

## Credits

Lead Architect: **wuying77** · Planning: **Gemini** · Editing: **Grok**

## License

MIT © 2026 wuying77 & P-LOD Contributors
