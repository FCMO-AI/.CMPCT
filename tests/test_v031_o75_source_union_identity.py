"""O75 source-exact composition guard: test-only proof of immutable owner blobs.

These pins are deliberately narrow and scoped to the O75 integration experiment.
They are not version/format law and must not silently be carried into a moving
canonical source after an authorized owner changes a pinned file.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Immutable O266 candidate-identity source, not a restatement of its contents.
IDENTITY_OWNER = {
    ".github/workflows/tests.yml": "7c8eff1885a3d4bf13d1d1100679de65138018c1",
    "docs/V031_CANDIDATE_FINGERPRINT.json": "f806d96dba4750dead6746e078e596e848e6f201",
    "tests/test_performance_base_native_release_custody.py": "ee030beb056ded21b16fe04f0e6e6427af3d62c0",
    "tests/test_public_attribution.py": "4cf80b7559fdb0d260501819083f54255c80db1e",
    "tests/test_v030_ci_topology_split_receipts.py": "90ae3a44bf08122f1e4b237868b3d07bb55c76e6",
    "tests/test_v030_release_fingerprint_surface.py": "5594b7a3a6ff072054688c3d8f2d2a96651603fa",
    "tests/test_v031_candidate_fingerprint.py": "636aab739c2a19c127cab6568008f019f0f95215",
    "tools/check_v031_candidate_fingerprint.py": "4a8c0748b03f621add78810057d9f708f8050e06",
}

# O66 Builder source and historical comparison fixtures must not be altered
# while importing evidence/CI-only files from another owner.
PRODUCT_AND_PARENT = {
    "src/cmpct/builder.py": "382e60983bf1e8e7595ea7112f3a5553dc33dcc0",
    "src/cmpct/codec.py": "dc3446b0eed82edfba9380e3885a20aa45577899",
    "tests/fixtures/o50_o47_parent_builder.py": "6f60dfe63742ff4b777f959a15d6fb828ae29610",
    "tests/test_v031_builder_parent_parity_o50.py": "20faf26980693342439c7730f62bd0bab8daca0f",
    ".github/workflows/v031-o66-o63-historical-custody-union.yml": "4d3ae3cde7ddab3f59888f0cf3dfaa3261967a78",
}

HISTORICAL_LOCK = {
    "docs/V030_RELEASE_LOCK.json": "988a7b05ad4e0833fac0453de74133b38f890f87",
}


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _assert_exact_sources(source: dict[str, str]) -> None:
    for relative, expected in source.items():
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink(), f"source missing or symlink: {relative}"
        got = git_blob_sha(path.read_bytes())
        assert got == expected, f"source owner unexpectedly changed: {relative}: {got} != {expected}"


def test_o75_original_o266_source_is_exact() -> None:
    _assert_exact_sources(IDENTITY_OWNER)


def test_o75_original_o66_product_and_historical_comparator_are_untouched() -> None:
    _assert_exact_sources(PRODUCT_AND_PARENT)


def test_o75_published_v030_release_lock_is_immutable() -> None:
    _assert_exact_sources(HISTORICAL_LOCK)
