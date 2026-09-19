#!/usr/bin/env python3
"""Golden vectors via sole public codec examples/plod_spec_codec.py."""

from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from plod_spec_codec import (  # noqa: E402
    GLOBAL_NA,
    SENode,
    Constraint,
    encode_frame,
    VERSION_V10,
    VERSION_V11,
)

OUT = Path(__file__).resolve().parent / "vectors"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # golden_core_v11: 4 core nodes + distance + global boundary
    nodes = [
        SENode(i, (math.cos(2 * math.pi * i / 4), math.sin(2 * math.pi * i / 4), 0.0))
        for i in range(4)
    ]
    cons = [
        Constraint(0x01, 0, 1, 2.5),
        Constraint(0x02, GLOBAL_NA, GLOBAL_NA, 1.75),
    ]
    good = encode_frame(nodes, constraints=cons, version=VERSION_V11)
    (OUT / "golden_core_v11.plod").write_bytes(good)

    bad = bytearray(good)
    # corrupt CRC only
    crc = struct.unpack_from("<I", bad, len(bad) - 4)[0] ^ 0xA5A5A5A5
    struct.pack_into("<I", bad, len(bad) - 4, crc)
    (OUT / "golden_invalid_crc.plod").write_bytes(bytes(bad))

    # minimal_valid: 8 core nodes, v1.0 wire (no CT / meta)
    nodes8 = [
        SENode(
            i + 1,
            (math.cos(2 * math.pi * i / 8), math.sin(2 * math.pi * i / 8), 0.0),
        )
        for i in range(8)
    ]
    minimal = encode_frame(nodes8, version=VERSION_V10)
    (OUT / "minimal_valid.plod").write_bytes(minimal)
    inv = bytearray(minimal)
    crc = struct.unpack_from("<I", inv, len(inv) - 4)[0] ^ 0xA5A5A5A5
    struct.pack_into("<I", inv, len(inv) - 4, crc)
    (OUT / "invalid_crc.plod").write_bytes(bytes(inv))

    # embodied + meta
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
    (OUT / "embodied_32b.plod").write_bytes(
        encode_frame(emb, embodied=True, extended_meta=True, version=VERSION_V11)
    )

    # unknown reserved flag bit: build minimal then set bit 5 on FLAGS
    unk = bytearray(encode_frame([SENode(i + 1, (float(i), 0.0, 0.0)) for i in range(4)], version=VERSION_V10))
    unk[3] = unk[3] | 0x20
    # recompute CRC over body without old CRC
    payload = bytes(unk[:-4])
    # FLAGS changed → must refresh CRC
    new_crc = zlib.crc32(payload) & 0xFFFFFFFF
    unk = bytearray(payload + struct.pack("<I", new_crc))
    (OUT / "unknown_extension.plod").write_bytes(bytes(unk))

    print(f"Wrote vectors to {OUT}")
    for p in sorted(OUT.glob("*.plod")):
        print(f"  {p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
