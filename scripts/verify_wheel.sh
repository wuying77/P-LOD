#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Building Distribution Package ==="
python -m pip install --upgrade build twine >/dev/null
python -m build
python -m twine check dist/*

echo "=== Testing Clean Wheel Installation ==="
rm -rf /tmp/plod_wheel_env
python -m venv /tmp/plod_wheel_env
# shellcheck disable=SC1091
source /tmp/plod_wheel_env/bin/activate
pip install --upgrade pip >/dev/null
pip install dist/*.whl

echo "=== Executing Clean Environment Smoke Test ==="
python -c "import plod; print('Installed version:', plod.__version__); assert plod.__version__ == '0.1.1'"
python -c "
from plod import encode_frame, decode_frame, emerge, SENode
nodes = [SENode(node_id=1, pos=(0.0, 0.0, 0.0)), SENode(node_id=2, pos=(1.0, 0.0, 0.0))]
f = encode_frame(nodes)
d = decode_frame(f)
assert len(d.nodes) == 2
pts = emerge(d.nodes, profile='v1')
assert len(pts) >= 1
print('Core API smoke PASS')
"

echo "=== All Clean Installation Checks Passed! ==="
