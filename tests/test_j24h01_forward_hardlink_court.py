"""J24H01: observational (not promotion) court for signed forward hardlinks.

Source: preregistered docs/v031-research/2026-10-27-j24h01-forward-hardlink-extract-prereg.md
No product code, frozen workload, source-owner, or evaluator is changed here.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

import msgpack
import pytest

from cmpct.core import Builder, CMPCT
from cmpct.codec import (
    HDR, FTR, MAGIC, FMAGIC, VERSION, K_FILE, K_HARDLINK,
    sha, zc, zd,
)
from cmpct.validation import preflight_archive


CONTENT = b"J24H01 independent authenticated hardlink owner\x00" * 19


def _builder_control(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    (src / "a-alias").write_bytes(CONTENT)
    os.link(src / "a-alias", src / "z-owner")
    archive = tmp_path / "builder.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    assert preflight_archive(archive)["files"] == 2
    with CMPCT(archive) as reader:
        index = reader.index
        by = {r[0]: r for r in index["files"]}
        assert by["a-alias"][1] == K_FILE
        assert by["z-owner"][1] == K_HARDLINK
        assert by["z-owner"][6] == ["a-alias"]
        assert reader.read("a-alias") == reader.read("z-owner") == CONTENT
        assert reader.verify() == 2
        destination = tmp_path / "control-restored"
        reader.extractall(destination)
    assert (destination / "a-alias").read_bytes() == CONTENT
    assert (destination / "z-owner").read_bytes() == CONTENT
    assert os.stat(destination / "a-alias").st_ino == os.stat(destination / "z-owner").st_ino
    return archive


def _signed_forward_archive(source: Path, destination: Path, *, chain: bool) -> dict:
    """Rebuild both authenticated r24 indexes; keep the *actual* Builder data records."""
    wire = source.read_bytes()
    magic, version, flags, old_cs, old_us, data_size, digest = HDR.unpack_from(wire, 0)
    assert magic == MAGIC and version == VERSION
    old_ic = wire[HDR.size:HDR.size + old_cs]
    old_ib = zd(old_ic, old_us)
    assert hashlib.sha256(old_ib).digest() == digest
    data_begin = HDR.size + old_cs
    data_end = data_begin + data_size
    physical_data = wire[data_begin:data_end]
    assert len(physical_data) == data_size
    assert wire[data_end:data_end + old_cs] == old_ic
    footer = FTR.unpack_from(wire, data_end + old_cs)
    assert footer[0] == FMAGIC and footer[-1] == digest

    index = msgpack.unpackb(old_ib, raw=False)
    index = copy.deepcopy(index)
    by = {r[0]: r for r in index["files"]}
    physical = by["a-alias"]
    alias = by["z-owner"]
    assert physical[1] == K_FILE and alias[1] == K_HARDLINK
    # Only logical aliases change. The exact verified physical blob survives byte-for-byte.
    physical[0] = "z-owner"
    alias[0] = "a-alias"
    alias[6] = ["b-alias" if chain else "z-owner"]
    if chain:
        extra = copy.deepcopy(alias)
        extra[0] = "b-alias"
        extra[6] = ["z-owner"]
        index["files"].append(extra)
    index["files"].sort(key=lambda row: row[0])
    assert [r[0] for r in index["files"]] == (
        ["a-alias", "b-alias", "z-owner"] if chain else ["a-alias", "z-owner"]
    )
    # Reproducible Builder encoded empty owner/xattr override maps; no index-relative
    # filesystem metadata can become stale after the row reorder.
    assert index.get("fsmeta", {}).get("owner_overrides", []) == []
    assert index.get("fsmeta", {}).get("xattrs", []) == []
    new_ib = msgpack.packb(index, use_bin_type=True)
    new_ic = zc(new_ib, 12)
    new_hash = sha(new_ib)
    new_header = HDR.pack(MAGIC, VERSION, flags, len(new_ic), len(new_ib), data_size, new_hash)
    new_footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(new_ic), len(new_ib), 0, new_hash)
    destination.write_bytes(new_header + new_ic + physical_data + new_ic + new_footer)
    assert source.read_bytes()[data_begin:data_end] == physical_data
    return {
        "chain": chain,
        "physical_data_sha256": hashlib.sha256(physical_data).hexdigest(),
        "authenticated_index_sha256": new_hash.hex(),
        "archive_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }


@pytest.mark.parametrize("chain", [False, True], ids=["direct-forward", "two-hop-forward"])
def test_signed_forward_hardlink_is_readable_but_not_extractable(tmp_path: Path, chain: bool):
    original = _builder_control(tmp_path)
    mutated = tmp_path / ("forward-chain.cmpct" if chain else "forward-direct.cmpct")
    receipt = _signed_forward_archive(original, mutated, chain=chain)
    # This is a fully rebuilt, SHA-bound *different* valid index, not an on-disk
    # corruption test. Both index copies and footer must match.
    result = preflight_archive(mutated)
    assert result["files"] == (3 if chain else 2)
    with CMPCT(mutated) as reader:
        assert reader.read("z-owner") == CONTENT
        assert reader.read("a-alias") == CONTENT
        assert reader.read_range("a-alias", 7, 15) == CONTENT[7:22]
        if chain:
            assert reader.read("b-alias") == CONTENT
        receipt["verified_logical_rows"] = reader.verify()
        assert receipt["verified_logical_rows"] == (3 if chain else 2)
        with pytest.raises(IOError, match="hardlink target not yet extracted") as err:
            reader.extractall(tmp_path / "forward-restored")
        receipt["extract_error"] = str(err.value)
    # This asserts the *observed* defect. If a product fix makes extraction work,
    # retire/update the research court prospectively; never silently invert history.
    assert not (tmp_path / "forward-restored" / "a-alias").exists()
    print("J24H01_RECEIPT=" + json.dumps(receipt, sort_keys=True))


def test_first_party_alias_rename_creates_unextractable_but_verified_generation(tmp_path: Path):
    """J24H01b: the ordinary transactional writer can produce a forward reference."""
    from cmpct.transactions import append_rename

    src = tmp_path / "initial-src"
    src.mkdir()
    (src / "b-owner").write_bytes(CONTENT)
    os.link(src / "b-owner", src / "z-alias")
    archive = tmp_path / "transactional.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    assert preflight_archive(archive)["files"] == 2
    with CMPCT(archive) as before:
        assert before.by["b-owner"][1] == K_FILE
        assert before.by["z-alias"][1] == K_HARDLINK
        assert before.by["z-alias"][6] == ["b-owner"]
        assert before.verify() == 2
        baseline_out = tmp_path / "baseline-out"
        before.extractall(baseline_out)
    assert (baseline_out / "b-owner").read_bytes() == CONTENT
    assert (baseline_out / "z-alias").read_bytes() == CONTENT
    assert os.stat(baseline_out / "b-owner").st_ino == os.stat(baseline_out / "z-alias").st_ino

    original_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    append_rename(archive, "z-alias", "a-alias")
    result = preflight_archive(archive)
    assert result["files"] == 2
    with CMPCT(archive) as after:
        assert after.delta_depth >= 1
        assert sorted(after.by) == ["a-alias", "b-owner"]
        assert after.by["a-alias"][1] == K_HARDLINK
        assert after.by["a-alias"][6] == ["b-owner"]
        assert after.read("a-alias") == after.read("b-owner") == CONTENT
        assert after.read_range("a-alias", 7, 15) == CONTENT[7:22]
        assert after.verify() == 2
        with pytest.raises(IOError, match="hardlink target not yet extracted") as err:
            after.extractall(tmp_path / "renamed-out")
        receipt = {
            "case": "first-party-append-rename-forward-alias",
            "original_builder_sha256": original_sha,
            "after_writer_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "generation_depth": after.delta_depth,
            "preflight_file_count": result["files"],
            "reader_verify_count": 2,
            "extract_error": str(err.value),
        }
    assert not (tmp_path / "renamed-out" / "a-alias").exists()
    print("J24H01B_RECEIPT=" + json.dumps(receipt, sort_keys=True))
