# P-LOD Extended Applications & Engineering Roadmap

**Status:** Companion to [SPECIFICATION.md](SPECIFICATION.md)  
**License:** MIT · [DEFENSIVE_PUBLICATION.md](DEFENSIVE_PUBLICATION.md)

> SE/WE are protocol metaphors, not quantum entanglement.

---

## 1. Principle

**Store Skeleton, Compute Details.**  
$$\mathrm{SE} = \mathrm{Nodes}+\mathrm{Edges}+\mathrm{Constraints}$$

### Reference engine freeze

- **`plod.ref.linear_spline.v1`** — **normative frozen baseline** for compliance (TCS).
- Budgeted / constraint-aware paths may version as v2+ without breaking v1 claims.

### SE extraction — ablation (v1.2 core benchmark **landed in repo demos**)

Automatic SE selection via:

$$\mathrm{Score}(p)=w_1\mathrm{Density}+w_2\mathrm{Curvature}+w_3\Delta E_{\mathrm{ablation}}$$

$$\mathrm{causal\_depth}(i)\propto \Delta E\text{ when node }i\text{ is removed}$$

Reference demo: [`examples/horizon_compression_demo.py`](../examples/horizon_compression_demo.py).  
Fidelity bench: [`examples/eval_reconstruction_fidelity.py`](../examples/eval_reconstruction_fidelity.py).

Further production-grade extractors (GNN, video, text graphs) remain **v2.0** research targets.

---

## 2. Application blueprints

LLM memory · Metaverse · Generative video · Embodied AI (unchanged intent).

---

## 3. Benchmark Suite A–D

| ID | Domain | Primary RFS-style metrics |
|----|--------|---------------------------|
| A | 3D geometry | Chamfer, Hausdorff |
| B | Image/video stills | PSNR, SSIM, LPIPS |
| C | Temporal video | continuity, latency |
| D | Embodied | SE-only mission success rate |

Always report **TCS** (compliance) separately from **RFS** (fidelity).

---

## 4. Document control

| Tag | Notes |
|-----|--------|
| +ablation | causal_depth via node ablation in horizon demo |
| +rfs-eval | eval_reconstruction_fidelity.py |
| +constraint-section | Spec Constraint Table 16B entries |
| +freeze-v1 | linear_spline.v1 normative frozen baseline |
