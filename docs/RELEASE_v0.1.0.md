# P-LOD v0.1.0 — Official RFC Standard Release

**Minimal Independent Structure Framework**

First public milestone of the P-LOD protocol: a deterministic, RFC-style wire format and reference stack for discovering, encoding, and emerging **minimal independent structures** from high-entropy data.

$$
S^* = \arg\min_{S \subseteq X} \lvert S\rvert \quad \text{s.t.} \quad D\bigl(X, G(S)\bigr) \le \epsilon
$$

---

## Highlights

| Area | What shipped |
|------|----------------|
| **Theory** | Spec §0: $S^*$, node ablation $\Delta E_i$, quantized `causal_depth` |
| **Wire** | Spec v1.1: 8B header, Core 24B / Embodied 32B, Constraints, CRC-32/ISO-HDLC |
| **Codec** | Sole SoT: `examples/plod_spec_codec.py` (strict range / NaN / unique id) |
| **Emergence** | `plod.ref.linear_spline.v1` frozen baseline; v2 experimental |
| **Evidence** | Rate–distortion sweep on 10 000-pt volume |
| **CI** | Python 3.10 / 3.11 / 3.12 compliance matrix |

---

## Rate–Distortion (measured)

Ablation-ranked SE → `plod.ref.linear_spline.v1` reconstruction:

| N_SE | SE-Frame | Compression | D/diag | RFS |
|-----:|---------:|------------:|-------:|----:|
| 4 | 172 B | **1396×** | 0.077 | 0.923 |
| 16 | 652 B | 368× | 0.052 | 0.948 |
| 64 | 2572 B | 93× | 0.035 | 0.965 |
| 128 | 4812 B | 50× | 0.030 | 0.970 |

Curve: [`docs/rate_distortion_curve.svg`](rate_distortion_curve.svg)

Reproduce:

```bash
python examples/eval_rate_distortion.py
```

---

## Quick start

```bash
python examples/plod_spec_codec.py --demo
python examples/reference_emergence_engine.py --profile v1
python examples/horizon_compression_demo.py
python tests/run_compliance_tests.py
```

---

## License & Prior Art

MIT · Defensive publication — see [`DEFENSIVE_PUBLICATION.md`](DEFENSIVE_PUBLICATION.md).

**Credits:** Lead Architect **wuying77** · Planning **Gemini** · Editing **Grok**
