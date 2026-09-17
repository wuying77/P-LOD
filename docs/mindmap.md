# P-LOD Framework Mind Map

> Progressive Strong-Entanglement Point Array with Weak-Entanglement Emergence Encoding  
> Concept / Prior Art v0.1 · MIT License · [GitHub](https://github.com/wuying77/P-LOD)

Visual companion (if present): [`plod_mindmap.png`](plod_mindmap.png) / architecture overview: [`plod_architecture.png`](plod_architecture.png)

---

## P-LOD Framework

### 1. Core Concept

- **Strong-Entanglement Skeleton**
  - Minimal points that define identity, topology, and primary structure
  - Stored permanently
  - Includes discrete state labels (solid / hollow / joint / end / control / emitter …)
- **Weak-Entanglement Emergence**
  - Intermediate fill, texture, local detail, fine motion, prose padding
  - **Not stored** — regenerated at runtime via procedural rules / shaders / generators
- **Paradigm shift**
  - Traditional compression: pack *all* data tighter (ZIP / JPEG / H.264)
  - P-LOD: discard non-critical data; keep blueprint; grow detail on demand
  - Analogy: **MIDI (sheet music)** vs **MP3 (recorded sound)**
- **Tunable trade-off**
  - Minimal storage (Level 1) ↔ higher perceptual fidelity (Level 2 / 3)

### 2. Hierarchical Levels

- **Level 1 — Extreme structural skeleton**
  - Fewest points
  - Goal: maximum compression + recognizable identity
  - Examples: letter A (5 pts), 王 (9 pts), humanoid (6 pts), Octocat (~13 pts)
- **Level 2 — Key attributes enhancement**
  - + color / attribute control points, major joints, plot/dialogue anchors
  - Target: ~80% perceptual fidelity
- **Level 3 — Local smooth transition**
  - + intermediate / smoothing points
  - Higher surface continuity and denser semantic anchors

### 3. Applications (cross-media)

- **2D / icons / characters**
  - A, 王, GitHub Octocat logo
- **2D illustration**
  - Cosmic Meditation: 5.48 MB PNG → Level 1 **2.6 KB** (~2190×), Level 2 **3.2 KB**, Level 3 **4.4 KB**
- **3D**
  - Humanoid skeleton demo (`examples/parse_plod.py`)
- **Text / books**
  - Alice in Wonderland: full text ~160–180 KB → L1 ~3–5 KB
  - 《西游记》: full text ~1.8–2.5 MB → L1 ~15–30 KB; L2 ~40–80 KB; L3 ~100–200 KB
  - L1 = structure + plot anchors (not full literary prose)
- **Video**
  - 1-hour 1080p typical ~1.5–2.5 GB → L1 conceptual **5–20 MB**
  - Skeleton: scene cuts, motion paths, lighting/state nodes, audio anchors
  - Not a free-form text prompt — a constrained temporal-spatial blueprint

### 4. Technical Specification

- **Point fields**
  - `id` — unique node id
  - `position` — 2D / 3D / sequential index (text·video)
  - `rgb` / attributes — color or semantic tags
  - `type` — discrete state label
  - `level` — lowest level this point belongs to
  - `params` — optional generation parameters
  - `connections` / topology — links between nodes
- **Storage format**
  - JSON point arrays per level (see `examples/*.json`)
- **Runtime**
  - Load skeleton → apply topology → run emergence rules (procedural / shader / lightweight model)
- **Encode side (future)**
  - Strong-point extraction ideally automatic (AI-assisted); currently manual / concept stage

### 5. Project Status

- **Status**: Concept / Prior Art **v0.1**
- **License**: MIT (defensive publication / open use)
- **Repo contents**
  - README, Chinese whitepaper, architecture infographic
  - Examples: humanoid L1–L3, cosmic meditation L1–L3, GitHub logo L1–L2
  - Demo: `examples/parse_plod.py` + `requirements.txt`
- **Open problems**
  - Automatic strong-entanglement extraction
  - Objective quality metrics
  - High-entropy data (chaotic textures, turbulence)
  - Reference CPU / GPU / shader implementations
  - Concrete text / video emergence schemas

---

## One-line summary

**Keep only the DNA of the data. Let the rest emerge when you open it.**
