# CHANGELOG

## [0.1.1] - 2026-09-20

### Added
- Canonical `src/plod` package structure and clean PyPI distribution metadata (`plod-protocol`).
- Strict protocol decoder validation for unknown flags and out-of-range `risk_state`.
- Explicit emergence profile whitelist (`v1` / `v2`); unknown profiles raise `ValueError`.
- Fail-loudly public imports (no silent empty/zero fallbacks).
- Ground-truth structure recovery benchmarks (Precision / Recall / F1).
- Dynamic marginal elimination path for ε-minimal extraction experiments.

### Changed
- Python package distribution version set to **0.1.1** (protocol milestone remains GitHub Release **v0.1.0**).
- Normative Source of Truth documented as `src/plod/spec/codec.py`; `examples/` is compatibility only.
- `requires-python` raised to `>=3.10` (aligned with CI matrix).

## [0.1.0] - 2026-09-20

### Added
- Initial Prior Art protocol specification v1.0/v1.1 and normative reference implementation.
