"""Backward-compatible entry: examples/plod_spec_codec.py → plod.spec.codec

Normative implementation lives in src/plod/spec/codec.py (dev) or the installed
``plod`` package (wheel). Set ``PLOD_FORCE_INSTALLED=1`` to skip adding ``src/``
to ``sys.path`` so CI can prove the published wheel is the code under test.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if (
    os.environ.get("PLOD_FORCE_INSTALLED", "") not in ("1", "true", "TRUE", "yes")
    and _SRC.is_dir()
    and str(_SRC) not in sys.path
):
    sys.path.insert(0, str(_SRC))

from plod.spec.codec import *  # noqa: F401,F403
from plod.spec.codec import (  # noqa: F401
    FLAG_HAS_CONSTRAINT_TABLE,
    FLAG_HAS_EXTENDED_META,
    FLAG_IS_EMBODIED_PROFILE,
    GLOBAL_NA,
    KNOWN_FLAGS,
    MAGIC,
    VERSION_V10,
    VERSION_V11,
    Constraint,
    DecodedFrame,
    ProtocolError,
    SENode,
    decode_frame,
    encode_frame,
)

if __name__ == "__main__":
    from plod.spec.codec import demo

    demo()
