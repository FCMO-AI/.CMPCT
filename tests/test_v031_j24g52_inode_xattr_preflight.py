"""J24G52 acceptance court: explicit inode-level xattr consistency in signed r24 archives.

The independent negative witness is J24G51 / PR #780. This test runs a
different prospective product-acceptance criterion; the old negative remains
unaltered in its own branch. No fixed benchmark corpus identity is used.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import msgpack
import pytest
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_FILE, K_HARDLINK, MAGIC, VERSION
from cmpct.reader import CMPCT
from cmpct.validation import ValidationError, preflight_archive, validate_hardlink_inode_xattrs

OWNER = "a-owner.bin"
ALIAS = "z-alias.bin"
PLAIN_B = "b-copy.bin"
PLAIN_C = "c-copy.bin"
KEY = "com.fcmo.cmpct.j24g52" if sys.platform == "darwin" else "user.cmpct_j24g52"
SIGNED = {OWNER: b"owner\x00\xff", ALIAS: b"alias\x00\xfe",
          PLAIN_B: b"independent-B", PLAIN_C: b"independent-C"}


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _sign_archive(original: bytes, attrs: dict[str, bytes], *,
                  chain: bool = False) -> bytes:
    magic, revision, flags, csize, usize, span, digest = HDR.unpack_from(original)
    assert magic == MAGIC and revision == VERSION and flags == 0
    raw_index = zstd.ZstdDecompressor().decompress(
        original[HDR.size:HDR.size + csize], max_output_size=usize + 1)
    assert len(raw_index) == usize and _sha(raw_index) == digest
    index = msgpack.unpackb(raw_index, raw=False)
    by = {row[0]: (i, row) for i, row in enumerate(index["files"])}
    assert len(by) == 4 and set(by) == set(SIGNED)
    assert all(row[1] == K_FILE for _, row in by.values())
    # Use the real Builder's physical content records. Only signed metadata
    # and the logical alias topology change; all four payloads are identical.
    assert len({row[4] for _, row in by.values()}) == 1
    by[ALIAS][1][1] = K_HARDLINK
    by[ALIAS][1][6] = [OWNER]
    index["fsmeta"] = {
        "owner": [0, 0], "owner_overrides": [],
        "xattrs": [[by[name][0], [[KEY, value]]]
                   for name, value in sorted(attrs.items(), key=lambda x: by[x[0]][0])],
    }
    body = original[HDR.size + csize:HDR.size + csize + span]
    assert len(body) == span
    new_raw = msgpack.packb(index, use_bin_type=True)
    compressed = zstd.ZstdCompressor(level=3).compress(new_raw)
    header = HDR.pack(MAGIC, VERSION, flags, len(compressed), len(new_raw),
                      span, _sha(new_raw))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(new_raw), 0, _sha(new_raw))
    return header + compressed + body + compressed + footer


def _physical_pair(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    payload = b"generic-shared-payload\x00\xff" * 128
    for name in SIGNED:
        (source / name).write_bytes(payload)
    original_path = tmp_path / "firstparty.cmpct"
    Builder(source, workers=1, reproducible=True).build(original_path)
    raw = original_path.read_bytes()
    equal = {**SIGNED, ALIAS: SIGNED[OWNER]}
    good = tmp_path / "compatible.cmpct"
    bad = tmp_path / "contradictory.cmpct"
    good.write_bytes(_sign_archive(raw, equal))
    bad.write_bytes(_sign_archive(raw, SIGNED))
    evidence_dir = os.environ.get("J24G52_EVIDENCE_DIR")
    if evidence_dir:
        directory = Path(evidence_dir)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "firstparty.cmpct").write_bytes(raw)
        (directory / good.name).write_bytes(good.read_bytes())
        (directory / bad.name).write_bytes(bad.read_bytes())
        (directory / "fingerprints.json").write_text(json.dumps({
            "original_sha256": _sha(raw).hex(),
            "compatible_sha256": _sha(good.read_bytes()).hex(),
            "contradictory_sha256": _sha(bad.read_bytes()).hex(),
            "unchanged_body_sha256": _sha(
                raw[HDR.size + HDR.unpack_from(raw)[3]:
                    HDR.size + HDR.unpack_from(raw)[3] + HDR.unpack_from(raw)[5]]).hex(),
        }, indent=2, sort_keys=True) + "\n")
    return good, bad


def _get_native_xattr(path: Path) -> bytes:
    if sys.platform == "darwin":
        output = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                                check=True, capture_output=True, text=True)
        return bytes.fromhex("".join(output.stdout.split()))
    return os.getxattr(path, KEY, follow_symlinks=False)


def test_hostile_signed_inode_conflict_rejected_before_side_effects(tmp_path):
    good, bad = _physical_pair(tmp_path)
    assert preflight_archive(good)["files"] == 4
    with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
        preflight_archive(bad)
    with CMPCT(bad) as archive:
        with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
            archive.verify()
        destination = tmp_path / "should-not-exist"
        with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
            archive.extractall(destination, metadata=True, require_xattrs=True)
        assert not destination.exists()
        with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
            archive.extractall(destination, metadata=True)
        assert not destination.exists()
        # Skipping metadata is an explicitly weaker, content-only operation.
        archive.extractall(destination, metadata=False)
        assert (destination / OWNER).read_bytes() == (destination / ALIAS).read_bytes()


@pytest.mark.skipif(sys.platform not in ("linux", "darwin"),
                    reason="POSIX inode-level xattr readback only")
def test_equal_inode_xattrs_and_independent_same_content_are_preserved(tmp_path):
    good, bad = _physical_pair(tmp_path)
    assert preflight_archive(good)["files"] == 4
    with CMPCT(good) as archive:
        assert archive.verify() == 4
        destination = tmp_path / "restored"
        archive.extractall(destination, metadata=True, require_xattrs=True)
    assert os.stat(destination / OWNER).st_ino == os.stat(destination / ALIAS).st_ino
    assert os.stat(destination / PLAIN_B).st_ino != os.stat(destination / PLAIN_C).st_ino
    assert _get_native_xattr(destination / OWNER) == SIGNED[OWNER]
    assert _get_native_xattr(destination / ALIAS) == SIGNED[OWNER]
    assert _get_native_xattr(destination / PLAIN_B) == SIGNED[PLAIN_B]
    assert _get_native_xattr(destination / PLAIN_C) == SIGNED[PLAIN_C]


def test_sparse_absence_not_assumed_negative_and_multihop_aliases():
    owner = ["a", K_FILE, 0, 0, 1, None, None]
    mid = ["z", K_HARDLINK, 0, 0, 1, None, ["a"]]
    tail = ["zz", K_HARDLINK, 0, 0, 1, None, ["z"]]
    directory = ["directory", 1, 0, 0, 0, b"", None]
    data = {"files": [owner, mid, tail, directory],
            "fsmeta": {"xattrs": [[0, [[KEY, b"same"]]],
                                   [2, [[KEY, b"same"]]],
                                   [3, [[KEY, b"directory-data"]]]]}}
    validate_hardlink_inode_xattrs(data)
    # A sparse omitted row is NOT an explicit negative requirement in this
    # historical format; no new compatibility restriction is justified.
    del data["fsmeta"]["xattrs"][1]
    validate_hardlink_inode_xattrs(data)
    data["fsmeta"]["xattrs"].append([1, [[KEY, b"different"]]])
    with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
        validate_hardlink_inode_xattrs(data)


def test_str_and_bytes_attribute_names_resolve_to_same_native_key():
    rows = [["a", K_FILE, 0, 0, 1, None, None],
            ["z", K_HARDLINK, 0, 0, 1, None, ["a"]]]
    index = {"files": rows, "fsmeta": {"xattrs": [
        [0, [["user.shared", b"A"]]], [1, [[b"user.shared", b"B"]]]
    ]}}
    with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
        validate_hardlink_inode_xattrs(index)


def test_aliased_chain_is_iterative_not_recursive():
    n = 8192
    rows = [["root", K_FILE, 0, 0, 1, None, None]]
    for i in range(n):
        rows.append([f"alias{i}", K_HARDLINK, 0, 0, 1, None,
                     ["root" if i == 0 else f"alias{i - 1}"]])
    idx = {"files": rows, "fsmeta": {
        "xattrs": [[i, [[KEY, b"same"]]] for i in range(n + 1)]}}
    start = time.perf_counter()
    validate_hardlink_inode_xattrs(idx)
    duration = time.perf_counter() - start
    print("J24G52_CHAIN_8192_SECONDS", duration)
    idx["fsmeta"]["xattrs"][-1][1][0][1] = b"bad"
    with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
        validate_hardlink_inode_xattrs(idx)


def test_duplicate_explicit_key_rejected_but_independent_same_hash_allowed():
    index = {"files": [
        ["a", K_FILE, 0, 0, 1, b"x" * 32, None],
        ["z", K_HARDLINK, 0, 0, 1, b"x" * 32, ["a"]],
        ["independent", K_FILE, 0, 0, 1, b"x" * 32, None]],
        "fsmeta": {"xattrs": [
            [0, [[KEY, b"ok"]]], [1, [[KEY, b"ok"]]], [2, [[KEY, b"different"]]]]
        }}
    validate_hardlink_inode_xattrs(index)
    index["fsmeta"]["xattrs"][0][1].append([KEY, b"bad"])
    with pytest.raises(ValidationError, match="conflicting hardlink inode xattr"):
        validate_hardlink_inode_xattrs(index)
