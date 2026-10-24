"""O9 genuine authenticated journal × signed-symlink prewrite composition court.

Both behaviors are independently tested in O7 and O3. This test exercises
their *intersection* through the actual Builder, transaction writer and Reader,
without a simulated parser or disabled safety policy. Not atomic extraction.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import preflight_archive

PAYLOAD = b"O9-REAL-SIGNED-JOURNAL-AND-SYMLINK\x00" * 8


def _journal(tmp_path: Path, target: str) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a-first.bin").write_bytes(PAYLOAD)
    (source / "b-extra.bin").write_bytes(b"O9-JOURNAL-RENAMED-CONTENT" * 8)
    try:
        os.symlink(target, source / "z-link")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"host cannot build signed symlink: {exc}")
    archive = tmp_path / "signed-journal.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        prev = reader.latest_footer_pos
        assert reader.read("z-link").decode("utf-8", "surrogateescape") == target
    _append_generation(
        archive,
        {"blobs": [], "ops": [["ren", "b-extra.bin", "c-renamed.bin"]]},
        prev,
    )
    assert preflight_archive(archive)["delta_depth"] == 1
    return archive


@pytest.mark.parametrize("target", ("../outside", "/absolute/outside"))
def test_authenticated_journal_unsafe_link_rejected_before_both_regular_members(
    tmp_path: Path, target: str,
) -> None:
    archive = _journal(tmp_path, target)
    dest = tmp_path / "out"
    with CMPCT(archive) as reader:
        assert reader.delta_depth == 1
        assert reader.read("a-first.bin") == PAYLOAD
        assert reader.read("c-renamed.bin") == b"O9-JOURNAL-RENAMED-CONTENT" * 8
        assert reader.read("z-link").decode("utf-8", "surrogateescape") == target
        with pytest.raises(OSError, match="unsafe.*symlink target|unsafe symlink target"):
            reader.extractall(dest, safe_symlinks=True, metadata=False)
    assert not (dest / "a-first.bin").exists(), "base member published before reject"
    assert not (dest / "c-renamed.bin").exists(), "journal member published before reject"
    assert not os.path.lexists(dest / "z-link"), "unsafe signed symlink published"


def test_authenticated_journal_valid_relative_symlink_materializes(
    tmp_path: Path,
) -> None:
    archive = _journal(tmp_path, "a-first.bin")
    dest = tmp_path / "out"
    with CMPCT(archive) as reader:
        assert reader.delta_depth == 1
        reader.extractall(dest, safe_symlinks=True, metadata=False)
    assert (dest / "a-first.bin").read_bytes() == PAYLOAD
    assert (dest / "c-renamed.bin").read_bytes() == b"O9-JOURNAL-RENAMED-CONTENT" * 8
    assert (dest / "z-link").is_symlink()
    assert os.readlink(dest / "z-link") == "a-first.bin"
