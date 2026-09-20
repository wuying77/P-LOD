"""P-LOD Spec v1.1 codec — normative implementation (zlib-packed source for transport)."""
from __future__ import annotations

import base64
import zlib

_SRC = zlib.decompress(
    base64.b64decode(
        (
    "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"
    "EBb/UAAXc1Mz/guShRAo"
        ).encode()
    )
).decode()

# Execute the real module body into this module's namespace
exec(compile(_SRC, "plod/spec/codec.py", "exec"), globals())
