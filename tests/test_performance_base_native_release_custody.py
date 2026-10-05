import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'docs' / 'V030_RELEASE_LOCK.json'
HELPER = 'tools/materialize_performance_base_native.py'


def test_historical_native_materializer_is_release_fingerprinted():
    manifest = json.loads(LOCK.read_text())
    if manifest.get('publication_mode') == 'rolling-pre1-checkpoint':
        assert manifest.get('required_receipts') == []
        assert manifest.get('dominance_target', {}).get('required_for_release') is False
        assert manifest.get('prior_strict_contract_parent') == 'cd2886bda7580a56e1efab8132b0b9477c52bd55'
        return
    assert HELPER in manifest['fingerprint_globs'], (
        'release-critical historical-engine ownership helper must be part of candidate identity'
    )
