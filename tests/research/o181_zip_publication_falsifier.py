"""O181: authentic O179 late-publication counterexample, NOT a product repair.

Only the final os.replace call is intercepted. The independent filesystem actor
can replace the stage pathname after the authentic reader's fstat/lstat check.
This court never alters Reader source or earlier O179/O149 frozen witnesses.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import zipfile

import pytest

from cmpct.reader import CMPCT


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def setup_case(root: Path):
    vectors = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    fixture = next(v for v in vectors["vectors"] if v["name"] == "raw.bin")
    source_bytes = base64.b64decode(fixture["archive_base64"])
    assert len(source_bytes) == fixture["archive_bytes"]
    assert sha(source_bytes) == fixture["archive_sha256"]
    src = root / "source.cmpct"
    src.write_bytes(source_bytes)
    dest = root / "previous.zip"
    with zipfile.ZipFile(dest, "w") as z:
        z.writestr("prior.txt", b"preserve until successful publication")
    original_dest = dest.read_bytes()
    victim = root / "unrelated.zip"
    with zipfile.ZipFile(victim, "w") as z:
        z.writestr("unrelated.txt", b"never authorized as exported content")
    victim_original = victim.read_bytes()
    return src, dest, victim, source_bytes, original_dest, victim_original


def zip_members(path: Path):
    with zipfile.ZipFile(path, "r") as z:
        assert z.testzip() is None
        return {name: z.read(name) for name in z.namelist()}


def stage_paths(root: Path):
    return [p for p in root.iterdir()
            if ".cmpct-zip-" in p.name and p.name.endswith(".tmp")]


def record(case: str, *, src: Path, source_bytes: bytes, victim: Path,
           victim_original: bytes, dest: Path, prior: bytes, details: dict):
    assert src.read_bytes() == source_bytes
    assert victim.read_bytes() == victim_original
    assert dest.read_bytes() != prior
    assert not stage_paths(dest.parent)
    data = {
        "case": case,
        "result": ("AUTHENTIC_CLEAN_CONTROL" if case.startswith("clean_")
                   else "POSTCHECK_NAME_SUBSTITUTION_ACCEPTED"),
        "source_sha": sha(source_bytes),
        "victim_before_sha": sha(victim_original),
        "victim_after_sha": sha(victim.read_bytes()),
        "prior_zip_sha": sha(prior),
        "published_zip_sha": sha(dest.read_bytes()),
        **details,
    }
    print("O181_CASE=" + json.dumps(data, sort_keys=True), flush=True)


@pytest.mark.parametrize("stdlib", [False, True], ids=["fast", "stdlib"])
def test_clean_same_source_zip_exact(tmp_path, monkeypatch, stdlib):
    src, dest, victim, source_bytes, prior, victim_original = setup_case(tmp_path)
    if stdlib:
        monkeypatch.setattr(CMPCT, "_zip64_offset_fallback_required", lambda self: True)
    with CMPCT(src) as reader:
        assert reader.read("raw.bin") == bytes(range(64))
        assert reader.export_zip(dest) == dest
    assert zip_members(dest) == {"raw.bin": bytes(range(64))}
    record("clean_" + ("stdlib" if stdlib else "fast"), src=src,
           source_bytes=source_bytes, victim=victim,
           victim_original=victim_original, dest=dest, prior=prior,
           details={"observed":"AUTHENTIC_ZIP", "target_is_symlink":dest.is_symlink()})


@pytest.mark.parametrize("forgery", ["foreign_member", "same_name_wrong_bytes"])
@pytest.mark.parametrize("stdlib", [False, True], ids=["fast", "stdlib"])
def test_regular_attacker_zip_replaces_verified_stage_at_rename(tmp_path, monkeypatch, stdlib, forgery):
    src, dest, victim, source_bytes, prior, victim_original = setup_case(tmp_path)
    if stdlib:
        monkeypatch.setattr(CMPCT, "_zip64_offset_fallback_required", lambda self: True)
    original_replace = os.replace
    seen = []
    def staged_rename(stage, target, *args, **kwargs):
        stage = Path(stage)
        target = Path(target)
        assert target == dest
        assert stage.name.startswith("." + dest.name + ".cmpct-zip-")
        assert len(stage_paths(tmp_path)) == 1
        # Authentic Reader has written and verified a complete correct ZIP.
        assert zip_members(stage) == {"raw.bin":bytes(range(64))}
        correct_inode = stage.stat().st_ino
        assert dest.read_bytes() == prior
        # Deterministic concurrency schedule: another authorized directory writer
        # substitutes the name AFTER Reader's identity check but BEFORE rename.
        stage.unlink()
        forged = ({"attacker.txt": b"not derived from CMPCT contents"}
                  if forgery == "foreign_member"
                  else {"raw.bin": b"X" * 64})
        with zipfile.ZipFile(stage, "w") as foreign:
            for name, data in forged.items():
                foreign.writestr(name, data)
        injected_inode = stage.stat().st_ino
        assert zip_members(stage) == forged
        assert forged != {"raw.bin": bytes(range(64))}
        # A same-number inode allocation after unlink does not make wrong bytes
        # authentic. On Windows, physical file IDs may be recycled after close.
        seen.append({"verified_stage_inode":correct_inode,
                     "foreign_stage_inode":injected_inode})
        return original_replace(stage, target, *args, **kwargs)
    with CMPCT(src) as reader:
        with monkeypatch.context() as m:
            m.setattr(os, "replace", staged_rename)
            assert reader.export_zip(dest) == dest
    assert len(seen) == 1
    assert not dest.is_symlink()
    forged = ({"attacker.txt": b"not derived from CMPCT contents"}
              if forgery == "foreign_member" else {"raw.bin": b"X" * 64})
    assert zip_members(dest) == forged
    assert zip_members(dest) != {"raw.bin": bytes(range(64))}
    case = ("foreign_valid_zip_" if forgery == "foreign_member"
            else "same_name_forged_zip_") + ("stdlib" if stdlib else "fast")
    record(case,
           src=src, source_bytes=source_bytes, victim=victim,
           victim_original=victim_original, dest=dest, prior=prior,
           details={"published_is_regular":True,
                    "expected_member_absent":forgery=="foreign_member",
                    "same_name_wrong_contents":forgery=="same_name_wrong_bytes",
                    "attacker_zip_crc_valid":True, "interleaving":seen[0]})


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory-name alias pivot")
@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_final_rename_can_publish_unrelated_inode_alias(tmp_path, monkeypatch, kind):
    src, dest, victim, source_bytes, prior, victim_original = setup_case(tmp_path)
    original_replace = os.replace
    seen = []
    def staged_rename(stage, target, *args, **kwargs):
        stage=Path(stage);target=Path(target)
        assert target == dest
        assert zip_members(stage) == {"raw.bin":bytes(range(64))}
        assert dest.read_bytes() == prior
        original_inode = os.lstat(stage).st_ino
        stage.unlink()
        if kind == "symlink":
            stage.symlink_to(victim)
        else:
            os.link(victim, stage)
        assert stage.stat().st_ino == victim.stat().st_ino
        assert stage.stat().st_ino != original_inode
        seen.append({"original_stage_inode":original_inode,
                     "victim_inode":victim.stat().st_ino})
        return original_replace(stage, target, *args, **kwargs)
    with CMPCT(src) as reader:
        with monkeypatch.context() as m:
            m.setattr(os,"replace",staged_rename)
            assert reader.export_zip(dest) == dest
    assert len(seen)==1
    assert dest.is_symlink() == (kind=="symlink")
    assert dest.stat().st_ino == victim.stat().st_ino
    assert zip_members(dest) == {
        "unrelated.txt":b"never authorized as exported content"}
    record("late_"+kind,src=src,source_bytes=source_bytes,
           victim=victim,victim_original=victim_original,dest=dest,
           prior=prior,details={"published_victim_inode_alias":True,
                               "target_is_symlink":dest.is_symlink(),
                               "interleaving":seen[0]})
