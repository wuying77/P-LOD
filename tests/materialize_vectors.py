#!/usr/bin/env python3
"""Expand committed *.plod.b64 golden sidecars into binary *.plod files."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DIR = HERE / "vectors"


def materialize(vec_dir: Path) -> None:
    vec_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(vec_dir.glob("*.plod.b64"))
    if not files:
        raise SystemExit(f"No *.plod.b64 files in {vec_dir}")
    for b64_path in files:
        raw = base64.b64decode(b64_path.read_text().strip())
        out = Path(str(b64_path)[: -len(".b64")])
        out.write_bytes(raw)
        print(f"  {out.name}: {len(raw)} bytes")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    print(f"Materializing golden vectors into {args.dir}")
    materialize(args.dir)


if __name__ == "__main__":
    main()
