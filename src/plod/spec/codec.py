"""P-LOD Spec v1.1 public codec (stdlib only). Normative: plod.spec.codec"""
from __future__ import annotations
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_SRC = "".join(
    (_HERE / name).read_text(encoding="utf-8")
    for name in ("_codec_part1.py", "_codec_part2.py", "_codec_part3.py")
)
exec(compile(_SRC, str(_HERE / "codec.py"), "exec"), globals())
