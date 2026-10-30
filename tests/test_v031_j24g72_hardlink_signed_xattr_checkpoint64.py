"""J24G72 physical intersection: hardlink owner/alias xattrs across checkpoint64.

The previous #815 physical hardlink test has no xattrs; #810/#813 signed-xattr
physical courts lack hardlinks. This test does not patch product code.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import pytest

from cmpct import _xattrs
from cmpct.builder import Builder
from cmpct.codec import K_HARDLINK
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, append_rename
from cmpct.validation import preflight_archive


@pytest.mark.skipif(sys.platform not in ("linux", "darwin"), reason="POSIX physical xattr provider required")
def test_hardlink_signed_xattrs_and_64th_checkpoint(tmp_path: Path):
    assert _xattrs.can_list() and _xattrs.can_set(), "physical xattr provider required"
    key = "com.fcmo.cmpct.j24g72" if sys.platform == "darwin" else "user.cmpct_j24g72"
    value = b"signed hardlink physical identity"
    tree = tmp_path / "source"
    tree.mkdir()
    owner = tree / "a.dat"
    raw = b"physical-hardlink-signed-xattr" * 128
    owner.write_bytes(raw)
    alias = tree / "h.dat"
    os.link(owner, alias)
    assert owner.stat().st_ino == alias.stat().st_ino and owner.stat().st_nlink >= 2
    _xattrs.setxattr(owner, key, value, follow_symlinks=False)
    assert _xattrs.getxattr(alias, key, follow_symlinks=False) == value
    (tree / "neutral.dat").write_bytes(b"independent" * 23)

    def attrs(index):
        names = index["files"]
        result = {}
        for ordinal, items in index.get("fsmeta", {}).get("xattrs", []):
            assert type(ordinal) is int and 0 <= ordinal < len(names)
            name = names[ordinal][0]
            assert name not in result
            result[name] = dict(items)
        return result

    archive = tmp_path / "physical.cmpct"
    Builder(tree, workers=1, reproducible=False).build(archive)
    with CMPCT(archive) as reader:
        assert reader.by["h.dat"][1] == K_HARDLINK
        assert reader.by["h.dat"][6] == ["a.dat"]
        assert reader.read("a.dat") == reader.read("h.dat") == raw
        assert reader.verify() == 3
        assert attrs(reader.index)["a.dat"][key] == value
        assert attrs(reader.index)["h.dat"][key] == value
    preflight_archive(archive)

    current = "neutral.dat"
    for _ in range(63):
        new = "neutral-alt.dat" if current == "neutral.dat" else "neutral.dat"
        append_rename(archive, current, new)
        current = new
    with CMPCT(archive) as reader:
        assert reader.delta_depth == 63
        assert reader.by["h.dat"][1] == K_HARDLINK
        assert attrs(reader.index)["a.dat"][key] == value
        assert attrs(reader.index)["h.dat"][key] == value
        assert reader.verify() == 3
    preflight_archive(archive)
    before = archive.read_bytes()
    with pytest.raises(ValueError, match="hardlink owner"):
        append_delete(archive, "a.dat")
    with pytest.raises(ValueError, match="hardlink owner"):
        append_rename(archive, "a.dat", "renamed.dat")
    assert archive.read_bytes() == before, "hardlink-owner refusal wrote physical bytes"

    append_delete(archive, "h.dat")   # 64th signed generation checkpoints
    with CMPCT(archive) as reader:
        assert reader.delta_depth == 0 and "h.dat" not in reader.by
        assert reader.read("a.dat") == raw
        assert reader.read(current) == b"independent" * 23
        assert reader.verify() == 2
        assert attrs(reader.index)["a.dat"][key] == value
        assert "h.dat" not in attrs(reader.index)
        dest = tmp_path / "restored"
        reader.extractall(dest, require_xattrs=True)
        assert (dest / "a.dat").read_bytes() == raw
        assert _xattrs.getxattr(dest / "a.dat", key, follow_symlinks=False) == value
        assert not (dest / "h.dat").exists()
    preflight_archive(archive)

    # Evidence-only retention of the *physical signed-xattr intersection* artifact.
    # The earlier J24G71 donor sample has no xattrs and is not this specimen.
    evidence_target = os.environ.get("J24G72_XATTR_SAMPLE")
    if evidence_target:
        evidence_path = Path(evidence_target)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, evidence_path)
        evidence_receipt = {
            "schema": "cmpct-j24g72-physical-signed-hardlink-xattr-v1",
            "source_head": os.environ.get("EXPECTED_HEAD", ""),
            "host": sys.platform,
            "physical_archive_bytes": evidence_path.stat().st_size,
            "physical_archive_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            "signed_owner_path": "a.dat",
            "removed_hardlink_alias": "h.dat",
            "unchanged_neutral_path": current,
            "signed_xattr_name": key,
            "signed_xattr_value_hex": value.hex(),
            "generation_64_checkpoint_confirmed": True,
            "reader_preflight_strict_restore": "pass",
            "rejected_owner_mutations_before_checkpoint": 2,
        }

    damaged = tmp_path / "damaged.cmpct"
    shutil.copyfile(archive, damaged)
    with damaged.open("r+b") as handle:
        handle.seek(-1, os.SEEK_END)
        tail = handle.read(1)
        handle.seek(-1, os.SEEK_END)
        handle.write(bytes([tail[0] ^ 1]))
    with CMPCT(damaged) as reader:
        assert reader.delta_depth == 63
        assert reader.by["h.dat"][1] == K_HARDLINK
        assert reader.by["h.dat"][6] == ["a.dat"]
        assert attrs(reader.index)["a.dat"][key] == value
        assert attrs(reader.index)["h.dat"][key] == value
        assert reader.read("a.dat") == reader.read("h.dat") == raw
        assert reader.verify() == 3
    assert hashlib.sha256(archive.read_bytes()).digest() != hashlib.sha256(damaged.read_bytes()).digest()
    if evidence_target:
        corrupted_path = evidence_path.with_name(evidence_path.stem + "-corrupt-last-footer.cmpct")
        shutil.copyfile(damaged, corrupted_path)
        evidence_receipt["corrupt_last_footer_archive_sha256"] = hashlib.sha256(corrupted_path.read_bytes()).hexdigest()
        evidence_receipt["corrupt_last_footer_archive_bytes"] = corrupted_path.stat().st_size
        evidence_receipt["corrupt_footer_recovered_signed_hardlink_generation_63"] = True
        evidence_path.with_suffix(".json").write_text(
            json.dumps(evidence_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

