"""Prospective candidate custody must include historical-engine materialization dependencies.

V030_RELEASE_LOCK.json is immutable published evidence, not an editable v0.31 candidate manifest.
"""
from tools import check_v031_candidate_fingerprint as candidate

HELPER = "tools/materialize_performance_base_native.py"


def test_historical_native_materializer_is_prospectively_fingerprinted() -> None:
    manifest = candidate.load_manifest()
    _identity, rows = candidate.fingerprint(manifest)
    assert HELPER in rows, "historical-engine helper must invalidate v0.31 candidate receipts"
