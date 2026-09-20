#!/usr/bin/env python3
"""Golden vectors via normative codec (src/plod/spec/codec.py)."""

from __future__ import annotations

import argparse
import base64
import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from plod_spec_codec import (  # noqa: E402
    GLOBAL_NA,
    SENode,
    Constraint,
    encode_frame,
    VERSION_V10,
    VERSION_V11,
)


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    path.with_name(path.name + ".b64").write_text(
        base64.b64encode(data).decode("ascii") + "\n"
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Generate P-LOD golden vectors")
    ap.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "vectors",
        help="Output directory for *.plod (+ *.plod.b64 sidecars)",
    )
    args = ap.parse_args(argv)
    out: Path = args.output
    out.mkdir(parents=True, exist_ok=True)

    nodes = [
        SENode(i, (math.cos(2 * math.pi * i / 4), math.sin(2 * math.pi * i / 4), 0.0))
        for i in range(4)
    ]
    cons = [
        Constraint(0x01, 0, 1, 2.5),
        Constraint(0x02, GLOBAL_NA, GLOBAL_NA, 1.75),
    ]
    good = encode_frame(nodes, constraints=cons, version=VERSION_V11)
    _write(out / "golden_core_v11.plod", good)

    bad = bytearray(good)
    crc = struct.unpack_from("<I", bad, len(bad) - 4)[0] ^ 0xA5A5A5A5
    struct.pack_into("<I", bad, len(bad) - 4, crc)
    _write(out / "golden_invalid_crc.plod", bytes(bad))

    nodes8 = [
        SENode(
            i + 1,
            (math.cos(2 * math.pi * i / 8), math.sin(2 * math.pi * i / 8), 0.0),
        )
        for i in range(8)
    ]
    minimal = encode_frame(nodes8, version=VERSION_V10)
    _write(out / "minimal_valid.plod", minimal)
    inv = bytearray(minimal)
    crc = struct.unpack_from("<I", inv, len(inv) - 4)[0] ^ 0xA5A5A5A5
    struct.pack_into("<I", inv, len(inv) - 4, crc)
    _write(out / "invalid_crc.plod", bytes(inv))

    emb = [
        SENode(
            i + 1,
            (
                math.cos(2 * math.pi * i / 16),
                math.sin(2 * math.pi * i / 16),
                0.1 * math.sin(2 * math.pi * i / 16),
            ),
            risk_state=0,
            sub_system=0x30,
            resonance_freq=1.0 + 0.01 * i,
            causal_depth=min(255, 100 + i * 5),
        )
        for i in range(16)
    ]
    _write(
        out / "embodied_32b.plod",
        encode_frame(emb, embodied=True, extended_meta=True, version=VERSION_V11),
    )

    unk = bytearray(
        encode_frame(
            [SENode(i + 1, (float(i), 0.0, 0.0)) for i in range(4)], version=VERSION_V10
        )
    )
    unk[3] = unk[3] | 0x20
    payload = bytes(unk[:-4])
    new_crc = zlib.crc32(payload) & 0xFFFFFFFF
    unk = bytearray(payload + struct.pack("<I", new_crc))
    _write(out / "unknown_extension.plod", bytes(unk))

    print(f"Wrote vectors to {out}")
    for p in sorted(out.glob("*.plod")):
        print(f"  {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
