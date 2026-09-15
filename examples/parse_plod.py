#!/usr/bin/env python3
"""P-LOD minimal demo: visualize 3D humanoid Level 1 skeleton."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# Load Level 1 humanoid
data = json.loads(Path(__file__).with_name("humanoid_level1.json").read_text())
points = {p["id"]: p for p in data["levels"]["1"]}

fig = plt.figure(figsize=(6, 6))
ax = fig.add_subplot(111, projection="3d")

# Draw points
for p in points.values():
    x, y, z = p["position"]
    ax.scatter(x, y, z, s=80)
    ax.text(x, y, z, f"  {p['id']}", fontsize=9)

# Draw topology edges
for a, b in data["topology"]:
    xa, ya, za = points[a]["position"]
    xb, yb, zb = points[b]["position"]
    ax.plot([xa, xb], [ya, yb], [za, zb], "-", linewidth=2)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("P-LOD Humanoid Level 1 (6 strong-entanglement points)")
plt.tight_layout()
plt.show()
