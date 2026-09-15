# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding**

An open-source hierarchical skeleton-based data compression and emergence framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-concept%20v0.1-blue)]()

---

## What is P-LOD?

P-LOD stores only the **minimal strong-entanglement skeleton** (key points + topology + discrete state labels) and regenerates the remaining details (**weak entanglement**) at runtime through deterministic / procedural rules.

Three progressive levels:

| Level | Content | Typical size | Goal |
|-------|---------|--------------|------|
| **Level 1** | Extreme structural skeleton | very few points | Maximum compression, identity preserved |
| **Level 2** | + key attributes & color control points | ~30–40 points | ~80% perceptual fidelity |
| **Level 3** | + local smoothing / transition points | more points | Higher surface continuity |

Applicable to 2D images, 3D models, point clouds, and other data with clear topological structure.

---

## English Abstract

We present **P-LOD** (Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding), a hierarchical data representation and compression framework. The core idea is to identify the minimal set of points that most critically determine the identity, topology, and primary visual or semantic features of the data—termed the *strong-entanglement skeleton*—and store only this skeleton together with discrete state labels and essential attributes. All remaining details (*weak entanglement*) are discarded at storage time and regenerated at runtime through deterministic or procedural rules.

This design enables a tunable trade-off between storage size and reconstruction fidelity. The proposal is released as prior art under the MIT License for free research, implementation, and improvement by the global community.

**Keywords**: data compression, level of detail, skeleton extraction, procedural generation, hierarchical representation, point-based modeling, progressive encoding

---

## 中文简介

P-LOD（渐进式强纠缠点阵与弱纠缠涌现编码）是一种面向结构化与半结构化数据的层级压缩与表示框架。

核心思路：只永久存储对整体可识别性与可重构性贡献最高的最小点集及其拓扑与关键属性（强纠缠骨架）；其余细节（弱纠缠）在调用时由规则实时涌现生成。通过 Level 1 → 2 → 3 的渐进方式，在极小存储体积与可接受还原度之间取得平衡。

完整技术说明见：[docs/whitepaper_zh.md](docs/whitepaper_zh.md)

---

## Quick Example (Level 1 Humanoid – 6 points)

```json
{
  "format": "P-LOD",
  "version": "0.1",
  "dimension": 3,
  "levels": {
    "1": [
      { "id": "H", "position": [0.0, 1.6, 0.0], "rgb": [255, 220, 180], "type": "semi-hollow", "level": 1 },
      { "id": "T", "position": [0.0, 0.9, 0.0], "rgb": [30, 144, 255], "type": "hollow", "level": 1 },
      { "id": "L_H", "position": [-0.65, 0.45, 0.0], "rgb": [255, 220, 180], "type": "end", "level": 1 },
      { "id": "R_H", "position": [0.65, 0.45, 0.0], "rgb": [255, 220, 180], "type": "end", "level": 1 },
      { "id": "L_F", "position": [-0.2, 0.0, 0.0], "rgb": [50, 50, 50], "type": "end", "level": 1 },
      { "id": "R_F", "position": [0.2, 0.0, 0.0], "rgb": [50, 50, 50], "type": "end", "level": 1 }
    ]
  },
  "topology": [
    ["H", "T"], ["T", "L_H"], ["T", "R_H"], ["T", "L_F"], ["T", "R_F"]
  ]
}
```

More examples: [examples/](examples/)

---

## Point Fields

| Field | Description |
|-------|-------------|
| `id` | Unique point identifier |
| `position` | 2D or 3D coordinates |
| `rgb` | Color |
| `type` | Discrete state label (`solid` / `hollow` / `semi-hollow` / `joint` / `end` / `control` / `emitter` …) |
| `level` | Lowest level this point belongs to |
| `params` | Optional generation parameters |
| `connections` | Topology links |

---

## Repository Structure

```
P-LOD/
├── README.md
├── LICENSE
├── docs/
│   └── whitepaper_zh.md
├── examples/
│   ├── humanoid_level1.json
│   └── humanoid_level2.json
└── (more to come)
```

---

## Status & Roadmap

Current status: **Concept / Prior Art v0.1**

Open problems:
- Automatic extraction of strong-entanglement points
- Objective quality metrics
- High-entropy data handling
- Reference implementations (CPU / GPU / shader)

Contributions, discussions, and implementations are welcome.

---

## License

MIT License © 2026 wuying77 & P-LOD Contributors

This work is released as prior art. Anyone may freely research, implement, modify, and distribute it.
