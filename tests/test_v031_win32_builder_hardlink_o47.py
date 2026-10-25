"""O47 authentic Win32 source-hardlink admission regression (r24, no format edits)."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.reader import CMPCT


PAYLOAD = bytes((i * 13 + (i >> 6) * 17 + 23) & 255 for i in range(65536))


def _source(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    (source / "owner.bin").write_bytes(PAYLOAD)
    os.link(source / "owner.bin", source / "alias.bin")
    (source / "copy.bin").write_bytes(PAYLOAD)
    assert os.path.samefile(source / "owner.bin", source / "alias.bin")
    assert not os.path.samefile(source / "owner.bin", source / "copy.bin")
    return source


def test_exact_physical_hardlink_and_independent_samebyte_copy(tmp_path: Path):
    """Detect O46's previously green-byte, red-inode output on Windows."""
    source = _source(tmp_path)
    results = []
    for repeat in range(2):
        archive = tmp_path / f"r24-{repeat}.cmpct"
        destination = tmp_path / f"extracted-{repeat}"
        Builder(source, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
        with CMPCT(archive) as reader:
            assert reader.verify() >= 2
            rows = reader.index["files"]
            hardlinks = [row for row in rows if row[1] == K_HARDLINK]
            regular = [row for row in rows if row[1] == K_FILE]
            assert len(hardlinks) == 1, [(row[0], row[1]) for row in rows]
            assert len(regular) == 2, [(row[0], row[1]) for row in rows]
            assert hardlinks[0][0] in ("alias.bin", "owner.bin")
            assert hardlinks[0][6][0] in ("alias.bin", "owner.bin")
            assert hardlinks[0][0] != hardlinks[0][6][0]
            for name in ("alias.bin", "owner.bin", "copy.bin"):
                assert reader.read(name) == PAYLOAD
            reader.extractall(destination, metadata=False)
        assert os.path.samefile(destination / "alias.bin", destination / "owner.bin")
        assert not os.path.samefile(destination / "copy.bin", destination / "owner.bin")
        assert all((destination / name).read_bytes() == PAYLOAD
                   for name in ("alias.bin", "owner.bin", "copy.bin"))
        results.append((hashlib.sha256(archive.read_bytes()).hexdigest(),
                        archive.stat().st_size))
    assert results[0] == results[1], results


def test_scandir_is_not_physical_ownership_metadata_on_win32(tmp_path: Path):
    """The exact CPython API boundary that O47 corrects, no mocked stat."""
    source = _source(tmp_path)
    actual = os.stat(source / "owner.bin", follow_symlinks=False)
    assert actual.st_nlink >= 2
    with os.scandir(source) as entries:
        fast = next(e.stat(follow_symlinks=False)
                    for e in entries if e.name == "owner.bin")
    if os.name == "nt":
        # Documented CPython behavior: Win32 DirEntry.stat() omits these
        # identifiers even when os.stat() reports a physically linked inode.
        assert fast.st_nlink == fast.st_dev == fast.st_ino == 0
    else:
        assert fast.st_nlink >= 2
    assert stat.S_ISREG(actual.st_mode)
