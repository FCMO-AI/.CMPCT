"""O50 joint-source conformance: O47 physical alias ownership × O48 no-loss admission.

Independent integration test; original O47/O48 tests remain unchanged.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.reader import CMPCT


_PAYLOAD = bytes((i * 17 + (i >> 7) * 9 + 3) & 255 for i in range(16384))


def _make_tree(root: Path) -> Path:
    src = root / "source"
    src.mkdir()
    (src / "owner.bin").write_bytes(_PAYLOAD)
    os.link(src / "owner.bin", src / "alias.bin")
    (src / "independent.bin").write_bytes(_PAYLOAD)
    assert os.path.samefile(src / "owner.bin", src / "alias.bin")
    assert not os.path.samefile(src / "owner.bin", src / "independent.bin")
    (src / "nested").mkdir()
    (src / "nested" / "plain.txt").write_bytes(b"exact-lossless\x00")
    if os.name != "nt":
        os.symlink("owner.bin", src / "symbolic")
    return src


def _assert_archive(src: Path, archive: Path, output: Path) -> tuple[str, int]:
    Builder(src, workers=1, reproducible=True, reproducible_epoch_ns=0).build(archive)
    with CMPCT(archive) as reader:
        assert reader.verify() >= 2
        rows = reader.index["files"]
        hardlinks = [r for r in rows if r[1] == K_HARDLINK]
        regular = [r for r in rows if r[1] == K_FILE]
        assert len(hardlinks) == 1, [(r[0], r[1]) for r in rows]
        assert len(regular) == 3, [(r[0], r[1]) for r in rows]
        assert hardlinks[0][0] in {"alias.bin", "owner.bin"}
        assert hardlinks[0][6][0] in {"alias.bin", "owner.bin"}
        assert hardlinks[0][0] != hardlinks[0][6][0]
        for name in ("owner.bin", "alias.bin", "independent.bin"):
            assert reader.read(name) == _PAYLOAD
        reader.extractall(output, metadata=False)
    assert os.path.samefile(output / "owner.bin", output / "alias.bin")
    assert not os.path.samefile(output / "owner.bin", output / "independent.bin")
    for name in ("owner.bin", "alias.bin", "independent.bin"):
        assert (output / name).read_bytes() == _PAYLOAD
    assert (output / "nested" / "plain.txt").read_bytes() == b"exact-lossless\x00"
    if os.name != "nt":
        assert os.readlink(output / "symbolic") == "owner.bin"
    return hashlib.sha256(archive.read_bytes()).hexdigest(), archive.stat().st_size


@pytest.mark.skipif(os.name == "nt" or not hasattr(os, "mkfifo"),
                    reason="mixed regular-hardlink/FIFO conflict requires POSIX FIFO")
def test_mixed_physical_alias_with_fifo_rejects_without_clobbering(tmp_path: Path):
    """A valid link group must not hide an unsupported sibling or publish a partial tree."""
    source = _make_tree(tmp_path)
    fifo = source / "zz-special"
    os.mkfifo(fifo, mode=0o600)
    existing = tmp_path / "existing.cmpct"
    sentinel = b"PREEXISTING-ARCHIVE-MUST-REMAIN-UNCHANGED"
    existing.write_bytes(sentinel)
    with pytest.raises(OSError, match="unsupported filesystem entry"):
        Builder(source, workers=1, reproducible=True, reproducible_epoch_ns=0).build(existing)
    assert existing.read_bytes() == sentinel
    fresh = tmp_path / "fresh.cmpct"
    with pytest.raises(OSError, match="unsupported filesystem entry"):
        Builder(source, workers=1, reproducible=True, reproducible_epoch_ns=0).build(fresh)
    assert not fresh.exists()

    fifo.unlink()
    digest_1 = _assert_archive(source, tmp_path / "pass-1.cmpct", tmp_path / "out-1")
    digest_2 = _assert_archive(source, tmp_path / "pass-2.cmpct", tmp_path / "out-2")
    assert digest_1 == digest_2


def test_no_specials_joint_supported_tree_exact_on_all_hosts(tmp_path: Path):
    """Ordinary success path preserves hardlink topology on all three host systems."""
    src = _make_tree(tmp_path)
    first = _assert_archive(src, tmp_path / "first.cmpct", tmp_path / "out-first")
    second = _assert_archive(src, tmp_path / "second.cmpct", tmp_path / "out-second")
    assert first == second
