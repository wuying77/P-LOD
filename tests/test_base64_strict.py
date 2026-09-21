"""Strict Base64 negative tests for golden-vector materialization."""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))


def test_invalid_base64_rejected():
    bad = "not!!valid@@base64==="
    with pytest.raises(Exception):
        base64.b64decode(bad, validate=True)


def test_materialize_rejects_corrupt_sidecar(tmp_path):
    sidecar = tmp_path / "broken.plod.b64"
    sidecar.write_text("@@@@\n")
    from materialize_vectors import materialize

    with pytest.raises(SystemExit):
        materialize(tmp_path)
