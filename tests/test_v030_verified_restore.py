from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pytest

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VERIFIED


def _decoded_for_regular(rel: str, payload: bytes, *, digest: bytes | None = None) -> dict:
    expected = hashlib.sha256(payload).digest() if digest is None else digest
    entry = [rel, "f", 0o644, 0, 0, 0, [], [len(payload), expected]]
    return {
        "raw": b"test-manifest",
        "manifest": {"v": 1, "profile": "cmpct-r25-filesystem-manifest-v1", "entries": [entry]},
        "regular": {rel: (len(payload), expected)},
        "hardlinks": {},
    }


def test_generic_restorer_still_rehashes_untrusted_staging(tmp_path: Path) -> None:
    staging = tmp_path / "generic"
    staging.mkdir()
    payload = b"abcd"
    (staging / "model.bin").write_bytes(payload)
    decoded = _decoded_for_regular("model.bin", payload, digest=b"\x00" * 32)

    with pytest.raises(RuntimeError, match="identity mismatch"):
        FS.restore_manifest_tree(staging, decoded)


def test_verified_restorer_skips_only_redundant_digest_pass(tmp_path: Path) -> None:
    staging = tmp_path / "verified"
    staging.mkdir()
    payload = b"abcd"
    target = staging / "model.bin"
    target.write_bytes(payload)
    decoded = _decoded_for_regular("model.bin", payload, digest=b"\x00" * 32)

    # This helper is intentionally provenance-sensitive: the release streamer, not this helper, owns content
    # authentication.  Same-size bytes therefore reach metadata restoration here, while the generic entry point
    # above still rejects them.  The shipping call-order contract below prevents use before authenticated stream.
    VERIFIED.restore_verified_manifest_tree(staging, decoded)
    assert target.read_bytes() == payload


def test_verified_restorer_still_rejects_shape_drift(tmp_path: Path) -> None:
    staging = tmp_path / "shape"
    staging.mkdir()
    (staging / "model.bin").write_bytes(b"abc")
    decoded = _decoded_for_regular("model.bin", b"abcd")

    with pytest.raises(RuntimeError, match="shape mismatch"):
        VERIFIED.restore_verified_manifest_tree(staging, decoded)


def test_shipping_extract_authenticates_before_verified_restore_and_publish() -> None:
    source = inspect.getsource(PRODUCT.extract)
    streamed = source.index("POLICY.extract_verified_into_staging")
    restored = source.index("VERIFIED_RESTORE.restore_verified_manifest_tree")
    published = source.index("C._publish_tree")

    assert streamed < restored < published
    assert "FS.restore_manifest_tree(content_root" not in source
