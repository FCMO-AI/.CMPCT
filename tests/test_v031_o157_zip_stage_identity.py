"""O157 exact-source installed-product ZIP stage close/reopen identity falsifier.

This is a NEGATIVE research court: a passing pivot test documents a real bug.
No product-source modification or weakened original O149/O150 tests.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import zipfile

from cmpct.reader import CMPCT


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def setup_case(root: Path) -> tuple[Path, Path, Path, bytes, bytes, bytes]:
    vecs = json.loads(Path(os.environ["CMPCT_FIXTURE_JSON"]).read_text())
    vec = next(v for v in vecs["vectors"] if v["name"] == "raw.bin")
    archive_bytes = base64.b64decode(vec["archive_base64"])
    assert len(archive_bytes) == vec["archive_bytes"]
    assert sha(archive_bytes) == vec["archive_sha256"]
    source = root / "source.cmpct"
    source.write_bytes(archive_bytes)
    target = root / "requested.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("previous.txt", b"healthy pre-existing ZIP")
    prior_target = target.read_bytes()
    with zipfile.ZipFile(target) as zf:
        assert zf.read("previous.txt") == b"healthy pre-existing ZIP"
    victim = root / "unrelated-victim.dat"
    sentinel = b"UNRELATED REGULAR FILE: NEVER AN AUTHORIZED ZIP TARGET\n" * 13
    victim.write_bytes(sentinel)
    assert source.stat().st_ino != victim.stat().st_ino
    assert target.stat().st_ino != victim.stat().st_ino
    return source, target, victim, archive_bytes, prior_target, sentinel


def report(case: str, **parts) -> None:
    print("O157_CASE=" + json.dumps({"case": case, "engine": os.environ["O157_ENGINE"], **parts}, sort_keys=True), flush=True)


def test_unpivoted_export_is_valid_and_preserves_unrelated_file(tmp_path: Path) -> None:
    source, target, victim, archive_bytes, prior_target, sentinel = setup_case(tmp_path)
    with CMPCT(source) as ar:
        assert ar.read("raw.bin") == bytes(range(64))
        assert ar.export_zip(target) == target
    assert source.read_bytes() == archive_bytes
    assert victim.read_bytes() == sentinel
    assert not target.is_symlink()
    assert target.read_bytes() != prior_target
    with zipfile.ZipFile(target) as zf:
        assert zf.namelist() == ["raw.bin"]
        assert zf.read("raw.bin") == bytes(range(64))
        assert zf.testzip() is None
    assert not any(".cmpct-zip-" in p.name for p in tmp_path.iterdir())
    report("unpivoted", result="exact_zip_and_victim_preserved",
           archive_sha=sha(archive_bytes), victim_before_sha=sha(sentinel),
           victim_after_sha=sha(victim.read_bytes()), target_after_sha=sha(target.read_bytes()))


def test_post_exclusive_creation_stage_pivot_overwrites_unrelated_regular_file(
    tmp_path: Path, monkeypatch
) -> None:
    """Deterministically interleave a directory writer after stage fd close.

    The test ONLY unlinks a freshly-created private staging filename and
    substitutes a symlink. It never writes the unrelated victim's bytes.
    Any observed victim change must arise from CMPCT's own subsequent writer.
    """
    source, target, victim, archive_bytes, prior_target, sentinel = setup_case(tmp_path)
    original_close = os.close
    attacked = []
    assert not any(".cmpct-zip-" in p.name for p in tmp_path.iterdir())

    def stage_close_interleaving(fd: int) -> None:
        if not attacked:
            stage_paths = [
                p for p in tmp_path.iterdir()
                if ".cmpct-zip-" in p.name and p.name.endswith(".tmp")
            ]
            if stage_paths:
                assert len(stage_paths) == 1, stage_paths
                stage = stage_paths[0]
                before = os.lstat(stage)
                opened = os.fstat(fd)
                assert stat.S_ISREG(before.st_mode)
                assert before.st_dev == opened.st_dev
                assert before.st_ino == opened.st_ino
                assert stage.resolve() != victim.resolve()
                # Simulates a cooperating/hostile actor with write permission to
                # the output DIRECTORY, after CMPCT has created its private file.
                original_close(fd)
                stage.unlink()
                stage.symlink_to(victim)
                assert stage.is_symlink()
                assert stage.resolve() == victim.resolve()
                attacked.append({"stage_basename": stage.name,
                                 "old_stage_inode": before.st_ino,
                                 "victim_inode": victim.stat().st_ino})
                return
        original_close(fd)

    with CMPCT(source) as ar:
        assert ar.read("raw.bin") == bytes(range(64))
        with monkeypatch.context() as patch:
            patch.setattr(os, "close", stage_close_interleaving)
            ar.export_zip(target)

    assert len(attacked) == 1, "no real post-creation stage interleaving occurred"
    # NEGATIVE witness: success means the installed exporter wrote THROUGH the
    # substituted stage symlink, rather than retaining exclusive-fd custody.
    after = victim.read_bytes()
    assert after != sentinel, "falsified: external victim survived the stage pivot"
    assert zipfile.is_zipfile(victim), "victim changed but was not a ZIP"
    with zipfile.ZipFile(victim) as zf:
        assert zf.namelist() == ["raw.bin"]
        assert zf.read("raw.bin") == bytes(range(64))
        assert zf.testzip() is None
    assert target.is_symlink(), "stage path replacement did not publish an alias"
    assert target.resolve() == victim.resolve()
    assert target.read_bytes() == after
    assert source.read_bytes() == archive_bytes
    assert not any(".cmpct-zip-" in p.name for p in tmp_path.iterdir())

    report("post_close_symlink_pivot", result="unrelated_regular_victim_modified_by_exporter",
           archive_sha=sha(archive_bytes), victim_before_sha=sha(sentinel),
           victim_after_sha=sha(after), victim_before_bytes=len(sentinel),
           victim_after_bytes=len(after), target_prior_sha=sha(prior_target),
           target_is_symlink=target.is_symlink(), stage_witness=attacked[0])
