"""Source-byte oracle for unsupported or inconsistent sparse filesystem seeks.

Reader.verify() authenticates archive consistency; it cannot by itself prove that
the builder acquired the correct source bytes before creating the archive.
All simulated bad SEEK offsets below are synthetic and deliberately nonconforming.
"""
from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
from unittest import mock

import pytest

from cmpct.builder import Builder
from cmpct.codec import _sparse_data_extents
from cmpct.reader import CMPCT

EPOCH = 1_729_468_800_000_000
REQUIRES_SPARSE = pytest.mark.skipif(
    os.name != "posix" or not all(hasattr(os, name) for name in
    ("SEEK_DATA", "SEEK_HOLE", "pread")),
    reason="requires POSIX sparse SEEK_DATA/SEEK_HOLE and pread",
)


def _source_file(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    p = root / "sparse.bin"
    with p.open("wb") as f:
        f.truncate(2 << 20)
        f.seek(1 << 20)
        f.write(b"NONZERO-ORIGINAL-SOURCE-" * 300)
    os.utime(p, ns=(EPOCH, EPOCH))
    p.chmod(0o644)
    if not hasattr(p.stat(), "st_blocks") or p.stat().st_blocks * 512 >= p.stat().st_size * .75:
        pytest.skip("host filesystem does not provide a sparse source for this test")
    return p


FAULTS = (
    "unsupported_ENOTSUP", "unsupported_EINVAL", "unsupported_ENODEV",
    "unsupported_EOPNOTSUPP", "data_at_eof", "data_past_eof",
    "hole_at_data", "hole_before_data", "hole_past_eof",
)


def _invalid_seek(real_lseek, size: int, fault: str):
    calls = 0

    def fake(fd, offset, whence):
        nonlocal calls
        calls += 1
        assert calls < 100, "non-progressing SEEK must never spin"
        if whence == os.SEEK_DATA:
            if fault.startswith("unsupported_"):
                raise OSError(getattr(errno, fault.split("_", 1)[1]), "synthetic unsupported seek")
            if fault == "data_at_eof":
                return size
            if fault == "data_past_eof":
                return size + 1
            if fault in ("hole_at_data", "hole_before_data", "hole_past_eof"):
                return 1 << 20
        if whence == os.SEEK_HOLE:
            if fault == "hole_at_data":
                return 1 << 20
            if fault == "hole_before_data":
                return (1 << 20) - 1
            if fault == "hole_past_eof":
                return size + 1
        return real_lseek(fd, offset, whence)

    return fake


@REQUIRES_SPARSE
@pytest.mark.parametrize("fault", FAULTS)
def test_invalid_sparse_seek_roundtrips_source_bytes(tmp_path: Path, fault: str):
    source = _source_file(tmp_path / "source")
    original_sha = hashlib.sha256(source.read_bytes()).digest()
    real = os.lseek
    archive = tmp_path / "result.cmpct"

    with mock.patch("os.lseek", side_effect=_invalid_seek(real, source.stat().st_size, fault)):
        assert _sparse_data_extents(source, source.stat().st_size) is None
        Builder(source.parent, workers=1, reproducible=True,
                reproducible_epoch_ns=EPOCH).build(archive)

    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        rebuilt_sha = hashlib.sha256(reader.read("sparse.bin")).digest()
    assert rebuilt_sha == original_sha


@REQUIRES_SPARSE
def test_valid_sparse_seek_preserves_original_data_and_holes(tmp_path: Path):
    source = _source_file(tmp_path / "source")
    archive = tmp_path / "result.cmpct"
    Builder(source.parent, workers=1, reproducible=True,
            reproducible_epoch_ns=EPOCH).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() == 1
        assert reader.read("sparse.bin") == source.read_bytes()
