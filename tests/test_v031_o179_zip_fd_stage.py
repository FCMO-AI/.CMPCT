"""O179: fd-bound ZIP stage protects unrelated victims before publication.

A separate positive test. Original O157/O157b negative witnesses remain untouched.
Requires a genuine authenticated revision-24 vector from the independent O143 court.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import zipfile

import pytest
from cmpct.reader import CMPCT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def setup(root: Path):
    vecs = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in vecs["vectors"] if v["name"] == "raw.bin")
    archive_bytes = base64.b64decode(vec["archive_base64"])
    assert len(archive_bytes) == vec["archive_bytes"]
    assert digest(archive_bytes) == vec["archive_sha256"]
    src = root / "source.cmpct"
    src.write_bytes(archive_bytes)
    dest = root / "existing.zip"
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr("previous.txt", b"valid prior ZIP - preserve on failure")
    prior = dest.read_bytes()
    victim = root / "unrelated.dat"
    sentinel = b"UNRELATED VICTIM: NEVER AUTHORIZED" * 23
    victim.write_bytes(sentinel)
    assert src.stat().st_ino != victim.stat().st_ino
    return src, dest, victim, archive_bytes, prior, sentinel


def no_stage_left(root: Path):
    return not [p for p in root.iterdir() if ".cmpct-zip-" in p.name]


@pytest.mark.parametrize("force_stdlib", [False, True], ids=["fast", "zipfile"])
def test_clean_export_writes_exact_bytes_via_original_fd(tmp_path, monkeypatch, force_stdlib):
    src, dest, victim, original, prior, sentinel = setup(tmp_path)
    if force_stdlib:
        monkeypatch.setattr(CMPCT, "_zip64_offset_fallback_required", lambda self: True)
    with CMPCT(src) as ar:
        assert ar.read("raw.bin") == bytes(range(64))
        assert ar.export_zip(dest) == dest
    assert src.read_bytes() == original
    assert victim.read_bytes() == sentinel
    assert dest.read_bytes() != prior
    with zipfile.ZipFile(dest) as z:
        assert z.namelist() == ["raw.bin"]
        assert z.read("raw.bin") == bytes(range(64))
        assert z.testzip() is None
    assert no_stage_left(tmp_path)
    print("O179_CASE=" + json.dumps({"case":"clean_" + ("zipfile" if force_stdlib else "fast"),
        "result":"exact_valid_zip_no_victim_mutation","source_sha":digest(original),
        "victim_before_sha":digest(sentinel),"victim_after_sha":digest(victim.read_bytes()),
        "dest_after_sha":digest(dest.read_bytes())},sort_keys=True),flush=True)


@pytest.mark.skipif(os.name == "nt", reason="O157 POSIX same-directory symlink/hardlink interleaving")
@pytest.mark.parametrize("pivot", ["symlink", "hardlink"])
def test_attacker_substitutes_stage_before_writer_but_victim_survives(tmp_path, monkeypatch, pivot):
    src, dest, victim, original, prior, sentinel = setup(tmp_path)
    real_fdopen = os.fdopen
    intervened = []
    def redirect_stage(fd, *args, **kwargs):
        # The only modified action is the attacker mutating the stage directory
        # entry. The authentically installed writer is still responsible for all
        # bytes written and for detecting the lost original inode.
        if not intervened:
            stages = [p for p in tmp_path.iterdir()
                      if ".cmpct-zip-" in p.name and p.name.endswith(".tmp")]
            assert len(stages) == 1, stages
            stage = stages[0]
            created = os.fstat(fd)
            named = os.lstat(stage)
            assert stat.S_ISREG(named.st_mode)
            assert (named.st_dev,named.st_ino) == (created.st_dev,created.st_ino)
            assert victim.read_bytes() == sentinel
            stage.unlink()
            if pivot == "symlink":
                stage.symlink_to(victim)
            else:
                os.link(victim, stage)
            assert stage.stat().st_ino == victim.stat().st_ino
            intervened.append({"pivot":pivot,"stage_original_inode":created.st_ino,
                                "victim_inode":victim.stat().st_ino})
        return real_fdopen(fd, *args, **kwargs)
    with CMPCT(src) as ar:
        with monkeypatch.context() as m:
            m.setattr(os, "fdopen", redirect_stage)
            with pytest.raises(IOError,match="staging pathname lost exclusive file identity"):
                ar.export_zip(dest)
    assert len(intervened) == 1
    assert victim.read_bytes() == sentinel, "O157 unrelated victim overwritten"
    assert src.read_bytes() == original
    assert dest.read_bytes() == prior, "O143 pre-existing ZIP destroyed"
    assert not dest.is_symlink()
    with zipfile.ZipFile(dest) as z:
        assert z.read("previous.txt") == b"valid prior ZIP - preserve on failure"
    assert no_stage_left(tmp_path)
    print("O179_CASE=" + json.dumps({"case":"stage_" + pivot,"result":"victim_and_prior_zip_preserved_after_rejected_pivot",
        "source_sha":digest(original),"prior_zip_sha":digest(prior),
        "after_zip_sha":digest(dest.read_bytes()),"victim_before_sha":digest(sentinel),
        "victim_after_sha":digest(victim.read_bytes()),"interleaving":intervened[0]},sort_keys=True),flush=True)
