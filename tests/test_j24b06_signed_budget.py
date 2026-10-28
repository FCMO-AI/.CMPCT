"""J24B06: reject signed negative/noninteger lengths before any extraction output.

The byte-exact negative-size counterexample was first established independently
against the *released* Reader in PR #688, Actions 40732802978. This test makes
the intended narrower fix fail on that original bug, rather than changing
benchmark or archive semantics to make a new implementation look green.
"""
import hashlib
import os
from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FTR, FMAGIC, HDR, K_SYMLINK, MAGIC, VERSION, sha, zc, zd
from cmpct.reader import CMPCT


def _make_source(tmp_path: Path) -> tuple[Path, bytes]:
    root = tmp_path / "source"
    root.mkdir()
    raw = b"".join(
        hashlib.sha256(f"J24B06-guard:{i}".encode()).digest()
        for i in range(8192 // 32)
    )
    (root / "payload.bin").write_bytes(raw)
    try:
        os.symlink("payload.bin", root / "offset-link")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host cannot create relative symlinks: {exc}")
    original = tmp_path / "legitimate.cmpct"
    Builder(root, workers=1, reproducible=True).build(original)
    with CMPCT(original) as ar:
        assert ar.verify() == 2
    return original, raw


def _reindex_symlink(original: Path, target: Path, declared_size: object) -> None:
    raw = original.read_bytes()
    magic, version, flags, cs, us, ds, index_sha = HDR.unpack_from(raw)
    assert magic == MAGIC and version == VERSION
    base = HDR.size + cs
    data = raw[base:base + ds]
    raw_index = zd(raw[HDR.size:base], us)
    assert sha(raw_index) == index_sha
    index = msgpack.unpackb(raw_index, raw=False)
    changed = 0
    for row in index["files"]:
        if row[0] == "offset-link":
            assert row[1] == K_SYMLINK and row[4] == len("payload.bin")
            row[4] = declared_size
            changed += 1
    assert changed == 1
    new_index = msgpack.packb(index, use_bin_type=True)
    comp = zc(new_index, 12)
    new_hash = sha(new_index)
    header = HDR.pack(MAGIC, VERSION, flags, len(comp), len(new_index), ds, new_hash)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0,
                      len(comp), len(new_index), 0, new_hash)
    target.write_bytes(header + comp + data + comp + footer)


@pytest.mark.parametrize("bad_size", [-8192, -1, True, "minus-one"])
@pytest.mark.parametrize("budget", [None, 4096, 8192 + len("payload.bin")])
def test_authenticated_malformed_row_sizes_fail_before_destination(
    tmp_path, bad_size, budget
):
    original, raw = _make_source(tmp_path)
    hostile = tmp_path / "authenticated-malformed.cmpct"
    _reindex_symlink(original, hostile, bad_size)
    out = tmp_path / "not-created"
    with CMPCT(hostile) as archive:
        # Valid physical bytes are not evidence of valid logical geometry:
        # verify() still passes this malformed signed archive on the released
        # source; extractall must separately enforce its output budget.
        assert archive.verify() == 2
        with pytest.raises(IOError, match="invalid nonnegative logical size"):
            archive.extractall(out, metadata=False, max_bytes=budget)
    assert not out.exists()
    assert len(raw) == 8192


def test_honest_signed_archive_respects_budget_and_recovers_exact_bytes(tmp_path):
    original, raw = _make_source(tmp_path)
    rejected = tmp_path / "not-created"
    with CMPCT(original) as archive:
        with pytest.raises(IOError, match="above limit 4096"):
            archive.extractall(rejected, metadata=False, max_bytes=4096)
        assert not rejected.exists()

        successful = tmp_path / "accepted"
        archive.extractall(
            successful, metadata=False,
            max_bytes=8192 + len("payload.bin"),
        )
        assert (successful / "payload.bin").read_bytes() == raw
        assert (successful / "offset-link").is_symlink()
        assert os.readlink(successful / "offset-link") == "payload.bin"


def test_legitimate_zero_length_file_under_zero_byte_cap(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "empty.bin").write_bytes(b"")
    archive_path = tmp_path / "empty.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive_path)
    destination = tmp_path / "output"
    with CMPCT(archive_path) as archive:
        assert archive.verify() == 1
        archive.extractall(destination, metadata=False, max_bytes=0)
    assert (destination / "empty.bin").read_bytes() == b""


@pytest.mark.parametrize("bad_size", [-8192, True])
def test_authenticated_hardlink_negative_length_cannot_cancel_budget(tmp_path, bad_size):
    """Hardlinks need no symlink privilege on Windows and exercise another alias kind."""
    from cmpct.codec import K_HARDLINK
    root = tmp_path / "hardlink-source"
    root.mkdir()
    raw = b"".join(
        hashlib.sha256(f"J24B06-hardlink:{i}".encode()).digest()
        for i in range(8192 // 32)
    )
    (root / "payload.bin").write_bytes(raw)
    try:
        os.link(root / "payload.bin", root / "zz-alias.bin")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host cannot create hardlinks: {exc}")
    archive_path = tmp_path / "hardlink-original.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive_path)
    with CMPCT(archive_path) as archive:
        assert archive.verify() == 2

    raw_archive = archive_path.read_bytes()
    magic, version, flags, cs, us, ds, original_hash = HDR.unpack_from(raw_archive)
    assert magic == MAGIC and version == VERSION
    old_raw_index = zd(raw_archive[HDR.size:HDR.size+cs], us)
    assert sha(old_raw_index) == original_hash
    index = msgpack.unpackb(old_raw_index, raw=False)
    rows = [row for row in index["files"] if row[0] == "zz-alias.bin"]
    assert len(rows) == 1
    assert rows[0][1] == K_HARDLINK
    assert rows[0][4] == 8192
    rows[0][4] = bad_size
    new_index = msgpack.packb(index, use_bin_type=True)
    new_compressed = zc(new_index, 12)
    new_hash = sha(new_index)
    mutated_archive = tmp_path / "hardlink-hostile.cmpct"
    physical = raw_archive[HDR.size+cs:HDR.size+cs+ds]
    mutated_archive.write_bytes(
        HDR.pack(MAGIC, VERSION, flags, len(new_compressed), len(new_index), ds, new_hash)
        + new_compressed + physical + new_compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_compressed), len(new_index), 0, new_hash)
    )
    assert physical == raw_archive[HDR.size+cs:HDR.size+cs+ds]
    bad_dest = tmp_path / "hardlink-not-created"
    with CMPCT(mutated_archive) as archive:
        assert archive.verify() == 2
        with pytest.raises(IOError, match="invalid nonnegative logical size"):
            archive.extractall(bad_dest, max_bytes=4096, metadata=False)
    assert not bad_dest.exists()

    valid_dest = tmp_path / "hardlink-accepted"
    with CMPCT(archive_path) as archive:
        archive.extractall(valid_dest, metadata=False, max_bytes=16384)
    assert (valid_dest / "payload.bin").read_bytes() == raw
    assert (valid_dest / "zz-alias.bin").read_bytes() == raw
