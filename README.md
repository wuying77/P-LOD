# P-LOD

**Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding**

An open-source hierarchical skeleton-based data compression and emergence framework.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-v0.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)]()
[![Status](https://img.shields.io/badge/status-concept%20v0.1-lightgrey.svg)]()
[![Spec](https://img.shields.io/badge/spec-v1.0%20draft-orange.svg)](docs/SPECIFICATION.md)
[![Prior Art](https://img.shields.io/badge/prior%20art-defensive%20publication-success.svg)](docs/DEFENSIVE_PUBLICATION.md)

> **Banner line:** P-LOD is a free global open-source standard. Published as immutable Prior Art under MIT — no entity may monopolize, patent-troll, or paywall the core protocol.

---

## 防垄断与公有领域声明 / Defensive Publication & Anti-Monopoly Notice

**P-LOD aims to be a Universal Open-Source Standard belonging to all humanity.**

本仓库的核心第一性原理、控制与编码架构（强弱纠缠分离、Level 1–3 渐进骨架、可选上下肢/相位意图线索、可选 90/10 空间算力策略）、**数据帧规范**及**参考代码**，均已通过 GitHub 公开提交历史完成**不可篡改的现有技术存证（Prior Art）**，并以 **MIT License** 彻底开源。

**We state clearly: P-LOD is public technical commons.**  
任何商业实体、机构或中间商试图将本协议核心概念**封包私有化、恶意抢注专利、或设立垄断收费墙**的行为，在法律层面将面对本仓库的公开时间戳；就已披露主题而言，其主张往往因**缺乏新颖性（Novelty）**而难以成立。全球开发者与企业均有权**免费、自由使用与演进**本协议。

**Scientific commons clause:** The Strong/Weak Entanglement decoupling and emergence mechanisms specified in P-LOD are derived from fundamental information theory and the Holographic Principle. Any attempt by commercial entities to monopolize or patent these physical intuitions, as disclosed here, constitutes an obstacle to the human collective cognitive boundary and is intended to be ineffective under global Prior Art practice.

MIT 仍允许基于 P-LOD 的**商业产品**；本声明针对的是把**开放标准本身**变成私人专利护城河。

完整文本：**[docs/DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md)**  
规范开篇：见 [docs/SPECIFICATION.md §0](docs/SPECIFICATION.md)

---

## Theoretical Foundation & Reading Guide

### Three Levels of Understanding (分层阅读指南)

To bridge physical intuition with rigid software engineering, P-LOD is designed for three reader profiles:

1. **Level 1 — Engineers & Developers**  
   Focus on the byte-level protocol ([`docs/SPECIFICATION.md`](docs/SPECIFICATION.md)) and Python reference code ([`examples/plod_spec_codec.py`](examples/plod_spec_codec.py), [`examples/horizon_compression_demo.py`](examples/horizon_compression_demo.py)). Goal: implement encode/decode and measure size collapse with zero non-stdlib dependencies for the codec path.

2. **Level 2 — Scientists & Systems Architects**  
   Explore compute-for-bandwidth, 90/10 spatial allocation, gait/phase decoupling, multi-domain blueprints (LLM memory, metaverse, generative video) in [`docs/ROADMAP_AND_APPLICATIONS.md`](docs/ROADMAP_AND_APPLICATIONS.md).

3. **Level 3 — Philosophers & Seekers**  
   Read Strong/Weak Entanglement, horizon-scale compression, and Motherfield Cosmology as information-law metaphors (holographic bounds, sparse structure vs local emergence). Theory essays may live on the author’s Substack / Medium; this repo is the **timestamped engineering anchor** that maps those ideas to wire formats and demos.

| Profile | Start here |
|---------|------------|
| Engineer | Spec + `plod_spec_codec.py` + `horizon_compression_demo.py` |
| Architect | Roadmap + Embodied profile in Spec |
| Theory reader | Defensive publication + Roadmap §4 + primary essays (external) |

---

## What is P-LOD?

P-LOD stores only the **minimal strong-entanglement skeleton** (key points + topology + discrete state labels) and regenerates the remaining details (**weak entanglement**) at runtime through deterministic / procedural rules.

> **Store Skeleton, Compute Details** — trade local compute for bandwidth and storage.

Three progressive levels:

| Level | Content | Typical size | Goal |
|-------|---------|--------------|------|
| **Level 1** | Extreme structural skeleton | very few points | Maximum compression, identity preserved |
| **Level 2** | + key attributes & color control points | ~30–40 points | ~80% perceptual fidelity |
| **Level 3** | + local smoothing / transition points | more points | Higher surface continuity |

Applicable to 2D images, 3D models, point clouds, **text / books**, **video**, and other data with clear topological structure.

**Wire / frame standard:** [docs/SPECIFICATION.md](docs/SPECIFICATION.md) (v1.0 core + v1.1 extended metas)  
**Applications & engineering roadmap:** [docs/ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md)

---

## Architecture Overview

![P-LOD architecture overview](docs/plod_architecture.png)

One-page summary of the framework:

- **Strong-entanglement skeleton** vs **weak-entanglement emergence**
- Tunable trade-off (minimal storage ↔ perceptual fidelity)
- Point field definition (id, position, type labels, connections)
- Three progressive levels
- Cross-media compression examples (image / text / video)

### Mind map

- **Markdown (searchable):** [docs/mindmap.md](docs/mindmap.md)
- **Visual:** ![P-LOD mind map](docs/plod_mindmap.png)

---

## English Abstract

We present **P-LOD** (Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding), a hierarchical data representation and compression framework. The core idea is to identify the minimal set of points that most critically determine the identity, topology, and primary visual or semantic features of the data—termed the *strong-entanglement skeleton*—and store only this skeleton together with discrete state labels and essential attributes. All remaining details (*weak entanglement*) are discarded at storage time and regenerated at runtime through deterministic or procedural rules.

This design enables a tunable trade-off between storage size and reconstruction fidelity. The proposal is released as prior art under the MIT License for free research, implementation, and improvement by the global community.

**Keywords**: data compression, level of detail, skeleton extraction, procedural generation, hierarchical representation, point-based modeling, progressive encoding, defensive publication, compute-for-bandwidth, holographic encoding

---

## 中文简介

P-LOD（渐进式强纠缠点阵与弱纠缠涌现编码）是一种面向结构化与半结构化数据的层级压缩与表示框架。

核心思路：只永久存储对整体可识别性与可重构性贡献最高的最小点集及其拓扑与关键属性（强纠缠骨架）；其余细节（弱纠缠）在调用时由规则实时涌现生成。通过 Level 1 → 2 → 3 的渐进方式，在极小存储体积与可接受还原度之间取得平衡。

**一句话原则：** 存骨架，算细节（Store Skeleton, Compute Details）；用端侧算力换带宽与存储。

开源防守见上方专节与 [docs/DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md)。分层阅读见 **Theoretical Foundation & Reading Guide**。

- 技术说明：[docs/whitepaper_zh.md](docs/whitepaper_zh.md)
- 协议规范：[docs/SPECIFICATION.md](docs/SPECIFICATION.md)
- 应用与路线图：[docs/ROADMAP_AND_APPLICATIONS.md](docs/ROADMAP_AND_APPLICATIONS.md)
- 思维导图：[docs/mindmap.md](docs/mindmap.md)

---

## Quick Start / Demo

### 3D skeleton view (JSON)

```bash
cd examples
pip install -r requirements.txt
python parse_plod.py
```

### Spec v1.0 binary codec (stdlib only)

```bash
cd examples
python plod_spec_codec.py
python plod_spec_codec.py --demo
python test_plod_spec_codec.py
```

### Horizon compression demo (stdlib only)

```bash
cd examples
python horizon_compression_demo.py
```

Simulates ~10,000 high-entropy 3D samples, extracts ≤80 SE nodes, packs Embodied SE-Frame + v1.1 `causal_depth` / `resonance_freq` metas, and prints the size collapse.

---

## Examples

### 0. Character-level intuition (easiest way to understand P-LOD)

**Point-array compression = keep only the key nodes that define the identity of the shape; throw away all intermediate fill; reconnect on demand.**

#### English letter **A** → 5 points

```
      1
     / \
    2   3
   /     \
  4-------5
```

| Point | Role |
|-------|------|
| 1 | Apex |
| 2 | Upper-left corner |
| 3 | Upper-right corner |
| 4 | Bottom-left end |
| 5 | Bottom-right end |

All pixels along the strokes between these nodes are **weak entanglement** — not stored.  
At reconstruction time, straight lines connect `1-2-4`, `1-3-5`, and `2-3`. The letter **A** reappears.

#### Chinese character **王** → 9 points

```
1----2----3
     |
4----5----6
     |
7----8----9
```

Same idea: thousands of pixels → **9 structural points**.

---

### 0.5 GitHub Octocat logo

- **Level 1** (~13 points): [`examples/github_logo_level1.json`](examples/github_logo_level1.json)
- **Level 2** (~22 points): [`examples/github_logo_level2.json`](examples/github_logo_level2.json)

### 1. 3D Humanoid

- [`examples/humanoid_level1.json`](examples/humanoid_level1.json)
- [`examples/humanoid_level2.json`](examples/humanoid_level2.json)
- [`examples/humanoid_level3.json`](examples/humanoid_level3.json)

### 2. 2D Cosmic Meditation Image

![Cosmic Meditation – original illustration](examples/cosmic_meditation.png)

| Version | Size | vs Original |
|---------|------|-------------|
| Original PNG | **5.48 MB** | 1× |
| P-LOD Level 1 | **2.6 KB** | **≈ 2,190×** |
| P-LOD Level 2 | **3.2 KB** | **≈ 1,735×** |
| P-LOD Level 3 | **4.4 KB** | **≈ 1,267×** |

### 3. Text / Books & 4. Video

See size tables in prior revisions of this README and the conceptual estimates in [`docs/ROADMAP_AND_APPLICATIONS.md`](docs/ROADMAP_AND_APPLICATIONS.md).

---

## Point Fields

| Field | Description |
|-------|-------------|
| `id` | Unique point identifier |
| `position` | 2D or 3D coordinates (or sequential index for text/video) |
| `rgb` | Color (or other attributes for non-image data) |
| `type` | Discrete state label |
| `level` | Lowest level this point belongs to |
| `params` | Optional generation parameters |
| `connections` | Topology links |
| `resonance_freq` | v1.1 optional meta (float32) |
| `causal_depth` | v1.1 optional meta (uint8; ≥200 = causal anchor) |

---

## Repository Structure

```
P-LOD/
├── README.md
├── LICENSE
├── docs/
│   ├── DEFENSIVE_PUBLICATION.md
│   ├── SPECIFICATION.md
│   ├── ROADMAP_AND_APPLICATIONS.md
│   ├── whitepaper_zh.md
│   ├── mindmap.md
│   ├── plod_architecture.png
│   └── plod_mindmap.png
└── examples/
    ├── requirements.txt
    ├── parse_plod.py
    ├── plod_spec_codec.py
    ├── test_plod_spec_codec.py
    ├── horizon_compression_demo.py   # 视界压缩 / 全息降维 demo
    ├── humanoid_level1.json
    ├── …
```

---

## Status & Future Directions

**Current status:** Concept / Prior Art **v0.1** + Spec **v1.0** (+ **v1.1 extended metas**) + Python codec + horizon demo.

P-LOD continues from embodied AI toward LLM structured memory, metaverse lightweight rendering, generative streaming, automated SE extraction, EDL profiles, and drift anchors — details in [`docs/ROADMAP_AND_APPLICATIONS.md`](docs/ROADMAP_AND_APPLICATIONS.md).

Contributions welcome.

---

## Credits

| Role | Name |
|------|------|
| **总架构师 / Lead Architect** | wuying77 |
| **策划 / Planning** | Gemini |
| **编辑 / Editing** | Grok |

---

## License

MIT License © 2026 wuying77 & P-LOD Contributors

Released as **prior art** and a **public technical commons**.  
See [docs/DEFENSIVE_PUBLICATION.md](docs/DEFENSIVE_PUBLICATION.md).
