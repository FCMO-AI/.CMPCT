"""O108 authentic installed Reader FIFO matrix: direct S_BLOB/S_SPARSE vs staged S_CDC.

A scientific PASS on direct-write FIFO means a defect reproduced, not safe extraction.
Every blocking candidate runs in a killable child. One physical original revision-24
archive per storage class is held constant for all four destination arrangements.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.codec import S_BLOB, S_CDC, S_SPARSE

DEADLINE = 8
MODES = {"blob": S_BLOB, "cdc": S_CDC, "sparse": S_SPARSE}
LEAVES = ("fresh", "regular", "fifo", "symlink_fifo")
READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"


@pytest.fixture(scope="module", params=tuple(MODES))
def original_archive(request, tmp_path_factory):
    mode = request.param
    root = tmp_path_factory.mktemp("o108-" + mode)
    source = root / "source"
    source.mkdir()
    src = source / "payload.bin"
    if mode == "blob":
        original = hashlib.shake_256(b"O108-blob-source").digest(4096)
        src.write_bytes(original)
    elif mode == "cdc":
        # Just past the Builder's 4*CHUNK CDC admission, deterministic high entropy.
        original = hashlib.shake_256(b"O108-cdc-source").digest(4 * 256 * 1024 + 32768)
        src.write_bytes(original)
    else:
        # Physical hole verified by Linux st_blocks, not zero-filled normal bytes.
        with src.open("wb") as f:
            f.truncate(6 * 1024 * 1024)
            f.seek(3 * 1024 * 1024)
            f.write(b"O108-sparse-extents" * 16)
        st = src.stat()
        assert hasattr(st, "st_blocks") and st.st_blocks * 512 < st.st_size * .75, (
            "sparse filesystem prerequisite absent", st.st_blocks, st.st_size)
        original = src.read_bytes()
    archive = root / "original.cmpct"
    Builder(source, workers=1).build(archive)
    with CMPCT(archive) as reader:
        rows = [r for r in reader.files if r[0] == "payload.bin"]
        assert len(rows) == 1
        assert rows[0][6][0] == MODES[mode], (mode, rows[0][6][0], MODES[mode])
        assert reader.read("payload.bin") == original
        assert reader.verify() == 1
    print("O108_ARCHIVE=" + json.dumps({
        "mode": mode, "archive_sha": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "payload_sha": hashlib.sha256(original).hexdigest(), "bytes": len(original),
        "storage": rows[0][6][0]}, sort_keys=True), flush=True)
    return mode, root, archive, original


def _child(archive, output):
    code = (
        "from cmpct.core import CMPCT\n"
        "from pathlib import Path\n"
        "import hashlib,sys\n"
        "a=Path(sys.argv[1]);dst=Path(sys.argv[2])\n"
        "with CMPCT(a) as r:\n"
        "    print('O108_CHILD_INDEX_OPENED',flush=True)\n"
        "    r.extractall(dst,metadata=False)\n"
        "print('O108_CHILD_RETURNED',flush=True)\n"
        "print('O108_CHILD_DIGEST='+hashlib.sha256((dst/'payload.bin').read_bytes()).hexdigest(),flush=True)\n"
    )
    start=time.perf_counter()
    try:
        r=subprocess.run([sys.executable,"-c",code,str(archive),str(output)],
                         cwd=str(output.parent),text=True,capture_output=True,
                         timeout=DEADLINE,check=False)
        return {"kind":"exit","rc":r.returncode,"stdout":r.stdout,"stderr":r.stderr,
                "wall_s":round(time.perf_counter()-start,6)}
    except subprocess.TimeoutExpired as exc:
        out=exc.stdout or b""
        err=exc.stderr or b""
        if isinstance(out,bytes):out=out.decode("utf-8","replace")
        if isinstance(err,bytes):err=err.decode("utf-8","replace")
        return {"kind":"timeout","rc":None,"stdout":out,"stderr":err,
                "wall_s":round(time.perf_counter()-start,6)}


@pytest.mark.parametrize("leaf",LEAVES)
def test_o108_storage_by_destination(original_archive,leaf):
    assert os.name=="posix" and hasattr(os,"mkfifo"),"POSIX FIFO scope only"
    mode,root,archive,original=original_archive
    dst=root/("dest-"+leaf)
    dst.mkdir()
    path=dst/"payload.bin"
    fifo_target=None
    if leaf=="regular":
        path.write_bytes(b"preexisting-regular-control")
    elif leaf=="fifo":
        os.mkfifo(path)
    elif leaf=="symlink_fifo":
        fifo_target=root/"external-waiting-fifo"
        if not fifo_target.exists():
            os.mkfifo(fifo_target)
        os.symlink(fifo_target,path)
        assert stat.S_ISFIFO(os.stat(path).st_mode)
    before_archive_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    before_source_sha=hashlib.sha256((root/"source"/"payload.bin").read_bytes()).hexdigest()

    r=_child(archive,dst)
    assert "O108_CHILD_INDEX_OPENED" in r["stdout"],(mode,leaf,r)
    should_timeout=mode in ("blob","sparse") and leaf in ("fifo","symlink_fifo")
    if should_timeout:
        assert r["kind"]=="timeout",("hypothesis falsified or unexpected error",mode,leaf,r)
        if leaf=="fifo":
            assert stat.S_ISFIFO(os.lstat(path).st_mode)
        else:
            assert stat.S_ISLNK(os.lstat(path).st_mode)
            assert stat.S_ISFIFO(os.lstat(fifo_target).st_mode)
        outcome="direct_write_fifo_timeout"
    else:
        assert r["kind"]=="exit" and r["rc"]==0,(mode,leaf,r)
        assert "O108_CHILD_RETURNED" in r["stdout"],r
        assert "O108_CHILD_DIGEST="+hashlib.sha256(original).hexdigest() in r["stdout"],r
        assert stat.S_ISREG(os.lstat(path).st_mode),(mode,leaf,"not a regular destination")
        assert path.read_bytes()==original
        if leaf=="symlink_fifo":
            assert stat.S_ISFIFO(os.lstat(fifo_target).st_mode)
        outcome="exact_regular"
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==before_archive_sha
    assert hashlib.sha256((root/"source"/"payload.bin").read_bytes()).hexdigest()==before_source_sha
    record={"mode":mode,"leaf":leaf,"outcome":outcome,"archive_sha":before_archive_sha,
            "source_sha":before_source_sha,"wall_seconds":r["wall_s"],
            "deadline_seconds":DEADLINE,
            "child_result":r["kind"],"child_rc":r["rc"]}
    print("O108_CASE="+json.dumps(record,sort_keys=True),flush=True)
