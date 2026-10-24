"""O6c: simultaneous authenticated journal replay + strict hardlink/tree preflight.

A real Builder supplies the physical payload. We re-sign only the logical r24
checkpoint rows, then append *genuine* transaction generations. This catches
cross-owner interactions separate replay and hardlink courts cannot expose.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_FILE, K_HARDLINK, MAGIC, sha, zc, zd
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import ValidationError, preflight_archive

PAYLOAD = b"O6C-SIGNED-JOURNAL-HARDLINK-OWNER\x00"
COUNT = 68
RENAME_COUNT = 20


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "builder-input"
    root.mkdir()
    (root / "owner.bin").write_bytes(PAYLOAD)
    archive = tmp_path / "builder.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    return archive


def _signed_base(source: Path, dest: Path) -> None:
    data = source.read_bytes()
    magic, revision, flags, csize, usize, dsize, commitment = HDR.unpack_from(data)
    assert magic == MAGIC and revision == 24 and flags == 0
    original = zd(data[HDR.size:HDR.size + csize], usize)
    assert sha(original) == commitment
    index = msgpack.unpackb(original, raw=False)
    assert len(index["files"]) == 1
    original_owner = index["files"][0]
    assert original_owner[0] == "owner.bin" and original_owner[1] == K_FILE
    owner = copy.deepcopy(original_owner)
    regulars = []
    for i in range(COUNT):
        row = copy.deepcopy(owner)
        row[0] = f"f{i:06d}.bin"
        regulars.append(row)
    alias = ["z_alias.bin", K_HARDLINK, owner[2], owner[3], owner[4], None, ["owner.bin"]]
    index["files"] = sorted([owner, alias, *regulars], key=lambda row: row[0])
    plain = msgpack.packb(index, use_bin_type=True)
    zipped = zc(plain, 12)
    physical = data[HDR.size + csize:HDR.size + csize + dsize]
    assert physical and len(physical) == dsize
    dest.write_bytes(
        HDR.pack(MAGIC, revision, flags, len(zipped), len(plain), len(physical), sha(plain))
        + zipped + physical + zipped
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(zipped), len(plain), 0, sha(plain))
    )
    assert dest.read_bytes()[HDR.size+len(zipped):HDR.size+len(zipped)+len(physical)] == physical


def _append(archive: Path, operations: list[list]) -> None:
    with CMPCT(archive) as reader:
        previous = reader.latest_footer_pos
    assert previous > 0
    footer, delta_bytes = _append_generation(
        archive, {"blobs": [], "ops": operations}, previous,
    )
    assert footer > previous and delta_bytes > FTR.size


def _valid_journal(tmp_path: Path) -> Path:
    source = _source(tmp_path)
    target = tmp_path / "signed-journal.cmpct"
    _signed_base(source, target)
    ops = [
        ["ren", f"f{i:06d}.bin", f"g{i:06d}.bin"]
        for i in range(RENAME_COUNT)
    ]
    _append(target, ops)
    return target


def test_signed_journal_indexed_replay_and_hardlink_owner_materialize_exactly(tmp_path: Path) -> None:
    archive = _valid_journal(tmp_path)
    receipt = preflight_archive(archive)
    assert receipt["files"] == COUNT + 2
    assert receipt["delta_depth"] == 1
    with CMPCT(archive) as reader:
        assert reader.read("owner.bin") == PAYLOAD
        assert reader.read("z_alias.bin") == PAYLOAD
        for i in range(RENAME_COUNT):
            assert reader.read(f"g{i:06d}.bin") == PAYLOAD
        extracted = tmp_path / "extracted"
        reader.extractall(extracted)
    assert (extracted / "owner.bin").read_bytes() == PAYLOAD
    assert (extracted / "z_alias.bin").read_bytes() == PAYLOAD
    assert (extracted / "g000000.bin").read_bytes() == PAYLOAD
    assert not (extracted / "f000000.bin").exists()
    assert os.stat(extracted / "z_alias.bin").st_ino == os.stat(extracted / "owner.bin").st_ino


@pytest.mark.parametrize("mutation", [
    [["del", "owner.bin"]],
    [["ren", "g000000.bin", "owner.bin/child.bin"]],
])
def test_signed_journal_indexed_replay_rejects_invalid_hardlink_or_ancestor(
    tmp_path: Path, mutation: list[list],
) -> None:
    archive = _valid_journal(tmp_path)
    _append(archive, mutation)
    # This is an authentic, separately committed second generation. The
    # structural contradiction is signed, not a corrupt checksum shortcut.
    with pytest.raises(ValidationError):
        preflight_archive(archive)
