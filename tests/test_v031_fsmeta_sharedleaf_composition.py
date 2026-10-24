"""Real CMPCT Reader integration: archive-structure preflight before optional shared-inode publication.

PR #297's fresh-inode fallback and PR #303's bounded authenticated-index fsmeta validation
must not let malformed archival metadata replace a pre-existing destination inode.
These tests deliberately call Reader directly without preflight_archive.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import stat

import msgpack
import pytest

from cmpct.codec import FTR, FMAGIC, HDR, sha, zc
from cmpct.core import Builder, CMPCT
from cmpct.validation import ValidationError


pytestmark = pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "link"),
    reason="POSIX hardlink inode semantics required",
)


def _valid_archive(tmp_path: Path, *, xattr: bool = False) -> Path:
    source = tmp_path / "src"
    source.mkdir()
    (source / "early.bin").write_bytes(b"early-archive-member")
    payload = source / "payload.bin"
    payload.write_bytes(b"THE-AUTHENTIC-ARCHIVE-PAYLOAD" * 256)
    if xattr:
        os.setxattr(payload, "user.cmpct_source_composed", b"source\x00opaque")
    archive = tmp_path / "source.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)
    return archive


def _signed_fsmeta_variant(archive: Path, target: Path, mutate) -> Path:
    """Build valid digest-consistent r24 index copies; preserve original encoded blobs."""
    data = archive.read_bytes()
    magic, ver, flags, comp_len, raw_len, body_len, _ = HDR.unpack_from(data)
    body = data[HDR.size + comp_len:HDR.size + comp_len + body_len]
    with CMPCT(archive) as reader:
        index = deepcopy(reader.index)
    mutate(index["fsmeta"])
    raw = msgpack.packb(index, use_bin_type=True)
    compressed = zc(raw, 12)
    digest = sha(raw)
    target.write_bytes(
        HDR.pack(magic, ver, flags, len(compressed), len(raw), len(body), digest)
        + compressed + body + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, digest)
    )
    return target


def _aliased_destination(tmp_path: Path) -> tuple[Path, Path, Path, tuple]:
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"OLD-EXTERNAL-HARDLINK-CONTENTS" * 4)
    dest = tmp_path / "dest"
    dest.mkdir()
    leaf = dest / "payload.bin"
    os.link(outside, leaf)
    original = outside.stat()
    digest = hashlib.sha256(outside.read_bytes()).digest()
    identity = (original.st_dev, original.st_ino, original.st_size,
                stat.S_IMODE(original.st_mode), original.st_nlink, digest)
    return dest, leaf, outside, identity


def _assert_unchanged(leaf: Path, outside: Path, original: tuple) -> None:
    s = outside.stat()
    assert (s.st_dev, s.st_ino, s.st_size, stat.S_IMODE(s.st_mode),
            s.st_nlink, hashlib.sha256(outside.read_bytes()).digest()) == original
    assert leaf.samefile(outside)
    assert hashlib.sha256(leaf.read_bytes()).digest() == original[-1]


@pytest.mark.parametrize("restore_metadata", [True, False], ids=["metadata-on", "metadata-off"])
@pytest.mark.parametrize(
    "mutation",
    [
        lambda meta: meta.update(xattrs=[[1, [["user.cmpct", "NOT-BYTES"]]]]),
        lambda meta: meta.update(xattrs=[[1, [["user.cmpct", b"A"], ["user.cmpct", b"B"]]]]),
        lambda meta: meta.update(owner_overrides=[[1, 1]]),
    ],
    ids=["invalid-value", "duplicate-xattr", "truncated-owner"],
)
def test_bad_digest_consistent_fsmeta_never_publishes_shared_leaf(
    tmp_path: Path, restore_metadata: bool, mutation
) -> None:
    archive = _valid_archive(tmp_path)
    forged = _signed_fsmeta_variant(archive, tmp_path / "forged.cmpct", mutation)
    dest, leaf, outside, original = _aliased_destination(tmp_path)
    with CMPCT(forged) as reader:
        assert reader.read("payload.bin") == b"THE-AUTHENTIC-ARCHIVE-PAYLOAD" * 256
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.extractall(dest, metadata=restore_metadata, atomic_shared_leaf=True)
    _assert_unchanged(leaf, outside, original)
    assert not (dest / "early.bin").exists(), "metadata refusal must precede first write"
    assert not list(dest.glob(".cmpct-part-*")), "no publication staging may start"


def test_valid_fsmeta_restored_on_fresh_inode_not_external_alias(tmp_path: Path) -> None:
    if not all(hasattr(os, name) for name in ("setxattr", "getxattr")):
        pytest.skip("POSIX xattrs unavailable")
    try:
        archive = _valid_archive(tmp_path, xattr=True)
    except OSError as exc:
        pytest.skip(f"source xattrs unavailable: {exc}")
    dest, leaf, outside, original = _aliased_destination(tmp_path)
    os.setxattr(outside, "user.cmpct_existing_composed", b"outside-only")
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        reader.extractall(dest, metadata=True, atomic_shared_leaf=True)
        assert leaf.read_bytes() == reader.read("payload.bin")
    assert leaf.stat().st_ino != outside.stat().st_ino
    assert os.getxattr(leaf, "user.cmpct_source_composed") == b"source\x00opaque"
    assert os.getxattr(outside, "user.cmpct_existing_composed") == b"outside-only"
    assert outside.stat().st_ino == original[1]
    assert hashlib.sha256(outside.read_bytes()).digest() == original[-1]
    assert (dest / "early.bin").read_bytes() == b"early-archive-member"


def test_valid_fsmeta_without_restore_keeps_outside_inode(tmp_path: Path) -> None:
    archive = _valid_archive(tmp_path)
    dest, leaf, outside, original = _aliased_destination(tmp_path)
    with CMPCT(archive) as reader:
        reader.extractall(dest, metadata=False, atomic_shared_leaf=True)
        assert leaf.read_bytes() == reader.read("payload.bin")
    assert leaf.stat().st_ino != outside.stat().st_ino
    assert outside.stat().st_ino == original[1]
    assert hashlib.sha256(outside.read_bytes()).digest() == original[-1]
