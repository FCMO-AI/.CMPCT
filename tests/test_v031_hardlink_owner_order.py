"""Revision-24 Builder-to-extractor hardlink dependency regression."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT

BENCHMARKS = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARKS))
from v031_hardlink_owner_order_court import case  # noqa: E402


@pytest.mark.skipif(os.name != "posix", reason="hardlink inode identity requires POSIX")
@pytest.mark.parametrize(
    "alias,late", [("a!.bin", True), ("a-.bin", True), ("a..bin", True),
                   ("a0.bin", False), ("z.bin", False)],
)
def test_builder_valid_hardlink_archive_extracts_regardless_of_index_order(tmp_path, alias, late):
    result = case(tmp_path, alias, predicted_late_owner=late)
    assert result["verify"] == 2
    assert result["baseline"] == {"outcome": "ACCEPT", "exact": True, "same_inode": True}
    assert result["dependency_first"] == {"exact": True, "same_inode": True}


@pytest.mark.skipif(os.name != "posix", reason="hardlink inode identity requires POSIX")
def test_hardlink_chain_resolves_regular_root_not_alias_creation_order(tmp_path):
    source = tmp_path / "source"
    (source / "a").mkdir(parents=True)
    owner = source / "a" / "owner.bin"
    owner.write_bytes(b"hardlink-chain" * 1024)
    os.link(owner, source / "a!.bin")
    os.link(owner, source / "z.bin")
    archive = tmp_path / "source.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.by["a!.bin"][1] == K_HARDLINK
        assert reader.by["z.bin"][1] == K_HARDLINK
        # Independent valid in-memory chain, deliberately backward with respect to index order.
        reader.by["a!.bin"][6] = ["z.bin"]
        reader.by["z.bin"][6] = ["a/owner.bin"]
        reader.extractall(tmp_path / "output")
    nodes = [tmp_path / "output" / name for name in ["a!.bin", "z.bin", "a/owner.bin"]]
    assert all(path.read_bytes() == owner.read_bytes() for path in nodes)
    assert len({os.stat(path).st_ino for path in nodes}) == 1


@pytest.mark.skipif(os.name != "posix", reason="hardlink graph requires POSIX")
def test_hardlink_cycle_is_rejected_without_publishing_alias(tmp_path):
    source = tmp_path / "source"
    (source / "a").mkdir(parents=True)
    owner = source / "a" / "owner.bin"
    owner.write_bytes(b"cyclic-alias" * 100)
    os.link(owner, source / "a!.bin")
    os.link(owner, source / "z.bin")
    archive = tmp_path / "source.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        reader.by["a!.bin"][6] = ["z.bin"]
        reader.by["z.bin"][6] = ["a!.bin"]
        with pytest.raises(IOError, match="cyclic hardlink target"):
            reader.extractall(tmp_path / "output")
    assert not (tmp_path / "output" / "a!.bin").exists()
    assert not (tmp_path / "output" / "z.bin").exists()
