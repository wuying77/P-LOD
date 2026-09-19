# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding**

An open-source hierarchical skeleton-based data compression and emergence framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-v0.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)]()
[![Spec](https://img.shields.io/badge/spec-v1.0%2Fv1.1-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)

**Status:** Prior Art Protocol Specification v1.0/v1.1 & Normative Reference Implementation. Open for global research, inter-operability testing, and benchmark verification.

> **Banner:** P-LOD is published as immutable Prior Art under MIT — a public technical commons for research and interoperable implementation.

> **Engineering Note on Terminology:**  
> In the P-LOD specification, *"Strong Entanglement (SE)"* and *"Weak Entanglement (WE)"* are a **protocol-level metaphor** for non-linear dependency coupling between persistent structural anchors and reconstructible procedural details. This is an **information-theoretic abstraction** and **does not constitute a claim of quantum entanglement**.

---

## Defensive Publication

Public technical commons · Prior Art · MIT. Full text: [docs/DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md).

---

## Reading Guide

1. **Engineers** — [SPEC](docs/SPECIFICATION.md), [`plod_spec_codec.py`](examples/plod_spec_codec.py), [`reference_emergence_engine.py`](examples/reference_emergence_engine.py) (**TCS = protocol compliance**), [`horizon_compression_demo.py`](examples/horizon_compression_demo.py)
2. **Architects** — [ROADMAP](docs/ROADMAP_AND_APPLICATIONS.md) (applications + **Benchmark A–D**, RFS metrics)
3. **Theory readers** — metaphors & essays; this repo is the engineering timestamp

| Metric | Meaning |
|--------|--------|
| **TCS** | Topological Consistency — *protocol compliance* (reference engine) |
| **RFS** | Reconstruction Fidelity — *vs Ground Truth* (Chamfer / PSNR / SSIM / task rate; Benchmark Suite) |

---

## What is P-LOD?

Store the **minimal SE skeleton**; regenerate **WE detail** at runtime.

> **Store Skeleton, Compute Details**

- Spec: [docs/SPECIFICATION.md](docs/SPECIFICATION.md)  
- Reference emergence (normative for **TCS**): [examples/reference_emergence_engine.py](examples/reference_emergence_engine.py)  
- Roadmap & benchmarks: [docs/ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md)

---

## Architecture

![P-LOD architecture overview](docs/plod_architecture.png)

---

## Quick Start

```bash
cd examples
python plod_spec_codec.py --demo
python horizon_compression_demo.py
python reference_emergence_engine.py
```

Reference engine reports **TCS** (compliance). **RFS** requires Ground Truth and is defined in the Benchmark Suite — not implied by TCS alone.

---

## Status & Roadmap

Open protocol + normative reference for inter-op and compliance testing.  
**v2.0 core objective:** Automatic SE extraction from raw data.  
**Near-term validation:** Benchmarks A (3D Chamfer/Hausdorff), B (PSNR/SSIM/LPIPS), C (temporal video), D (embodied SE-only mission rate).

---

## Credits

| Role | Name |
|------|------|
| Lead Architect | wuying77 |
| Planning | Gemini |
| Editing | Grok |

## License

MIT © 2026 wuying77 & P-LOD Contributors · [DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md)
