"""Strict Base64 negative tests — Failure Mode Isolation (format layer)."""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

FIXTURE = ROOT / "tests" / "fixtures" / "invalid_base64.plod.b64"


def test_invalid_base64_rejected():
    bad = FIXTURE.read_text().strip()
    with pytest.raises(Exception):
        base64.b64decode(bad, validate=True)


def test_materialize_rejects_corrupt_sidecar(tmp_path):
    sidecar = tmp_path / "broken.plod.b64"
    sidecar.write_text(FIXTURE.read_text())
    from materialize_vectors import materialize

    with pytest.raises(SystemExit) as ei:
        materialize(tmp_path)
    assert "Invalid base64" in str(ei.value) or "Invalid" in str(ei.value)


def test_format_error_not_crc_confusion():
    """Base64 failure must surface before any Core CRC check."""
    bad = FIXTURE.read_text().strip()
    with pytest.raises(Exception) as ei:
        base64.b64decode(bad, validate=True)
    msg = str(ei.value).lower()
    assert "crc" not in msg
