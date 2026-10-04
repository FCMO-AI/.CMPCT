import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'docs' / 'V030_RELEASE_LOCK.json'
HELPER = 'tools/materialize_performance_base_native.py'


def test_historical_native_materializer_is_release_fingerprinted():
    manifest = json.loads(LOCK.read_text())
    assert HELPER in manifest['fingerprint_globs'], (
        'release-critical historical-engine ownership helper must be part of candidate identity'
    )
