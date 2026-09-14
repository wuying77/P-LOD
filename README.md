# P-LOD: Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding

**An Open-Source Hierarchical Skeleton-Based Data Compression and Emergence Framework**

---

## English Abstract

We present **P-LOD** (Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding), a hierarchical data representation and compression framework for structured and semi-structured data. The core idea is to identify the minimal set of points that most critically determine the identity, topology, and primary visual or semantic features of the data—termed the *strong-entanglement skeleton*—and store only this skeleton together with discrete state labels and essential attributes. All remaining details (*weak entanglement*) are discarded at storage time and regenerated at runtime through deterministic or procedural rules.

Three progressive levels are defined:
- **Level 1**: Extreme structural skeleton.
- **Level 2**: Key attributes and color control points.
- **Level 3**: Local smoothing and transition points.

This design enables a tunable trade-off between storage size and reconstruction fidelity. The proposal is released as prior art under the MIT License for free research, implementation, and improvement by the global community.

**Keywords**: `data compression`, `level of detail`, `skeleton extraction`, `procedural generation`, `hierarchical representation`, `point-based modeling`, `progressive encoding`

---

## 渐进式强纠缠点阵与弱纠缠涌现编码（P-LOD）技术白皮书

### 摘要
本文提出一种面向结构化与半结构化数据的渐进式压缩与表示框架——渐进式强纠缠点阵与弱纠缠涌现编码（P-LOD）。核心思想是：将数据中对整体可识别性与可重构性贡献最高的最小点集及其拓扑与关键属性定义为“强纠缠骨架”，在存储阶段仅保留该骨架；其余细节（弱纠缠）在调用/渲染阶段由确定性或程序化规则实时涌现生成。通过定义 Level 1（极致结构）、Level 2（关键属性与色彩）、Level 3（局域平滑与过渡）的层级增量方式，实现存储体积与重构精度之间的可调节平衡。

---

### 1. 核心定义

- **强纠缠（Strong Entanglement）**：对数据整体可识别性、拓扑完整性与主要特征贡献最高的最小点集合，及其拓扑与关键属性。
- **弱纠缠（Weak Entanglement）**：可由强纠缠骨架 + 预设生成规则推导或程序化生成的细节，在存储阶段剔除，调用时涌现。
- **层级点阵（Progressive Point Array）**：
  - **Level 1**：仅保留决定数据基本身份与拓扑的最少关键点。
  - **Level 2**：增加主要属性点（关节、颜色控制点），提升可识别度与色彩还原。
  - **Level 3**：增加局域平滑与过渡点，提升表面连续性与细节自然度。

---

### 2. 数据结构设计（JSON 示例）

#### 极简 Level 1 文件示例（3D 人形，仅 6 个点，体积 < 1 KB）

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
