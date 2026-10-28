"""J24I01: source-exact prospective candidate identity across the B06 safety composition.

This is a separate, narrow *integration* witness, not a substitute for the
installed signed-wire hostile court or release performance gate. It is a
deliberately cheap falsifier of missing-source candidate fingerprints.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile

from tools.check_v031_candidate_fingerprint import fingerprint, load_manifest


ROOT = Path(__file__).resolve().parents[1]
RELEASE_LOCK_BLOB = "988a7b05ad4e0833fac0453de74133b38f890f87"
B06_SOURCE_BLOBS = {
    "src/cmpct/reader.py": "20f6e257a07a61a4c1aebe23ae23e4109d6c41c8",
    "tests/test_j24b06_signed_budget.py": "594d93e6884df7924bd52a83a1ceab20bb5ff727",
    ".github/workflows/v031-j24b06-budget-guard.yml": "49ed0795353182cb5b2f956ea3a0f9718dd3e90d",
}


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def test_b06_exact_source_and_immutable_released_lock():
    assert git_blob_id((ROOT / "docs/V030_RELEASE_LOCK.json").read_bytes()) == RELEASE_LOCK_BLOB
    for path, expected_sha in B06_SOURCE_BLOBS.items():
        assert git_blob_id((ROOT / path).read_bytes()) == expected_sha, path


def test_prospective_candidate_identity_includes_b06_code_and_test():
    manifest = load_manifest()
    _, paths = fingerprint(manifest, root=ROOT)
    for path in B06_SOURCE_BLOBS:
        assert path in paths, ("new safety source omitted from prospective identity", path)


def test_source_and_test_changes_invalidate_candidate_identity():
    # Isolate a tiny synthetic mirror; do not change actual checkout or
    # weaken/change the normative v0.31 full-manifest source-identity gate.
    selected = list(B06_SOURCE_BLOBS)
    small_manifest = {"fingerprint_globs": selected, "required_paths": selected}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24i01-custody-") as td:
        root = Path(td)
        for path in selected:
            src = ROOT / path
            dst = root / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        before, paths = fingerprint(small_manifest, root=root)
        assert paths == sorted(selected)
        for path in selected:
            f = root / path
            original = f.read_bytes()
            assert original
            f.write_bytes(original + b"\\n# J24I01 source-custody mutation test\\n")
            altered, _ = fingerprint(small_manifest, root=root)
            assert altered != before, path
            f.write_bytes(original)
            restored, _ = fingerprint(small_manifest, root=root)
            assert restored == before, path
