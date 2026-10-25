"""O121 source-exact installed Reader S_PACK/S_VZIP output-leaf FIFO falsifier.

A passing negative test proves availability exposure; it is not product safety.
All true blocking work occurs in bounded, killable child processes.
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
import zipfile

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.codec import S_PACK, S_VZIP

DEADLINE = 8
MODES = {"pack": S_PACK, "vzip": S_VZIP}
LEAVES = ("fresh", "regular", "fifo", "symlink_fifo")


@pytest.fixture(scope="module", params=tuple(MODES))
def genuine_archive(request, tmp_path_factory):
    mode = request.param
    root = tmp_path_factory.mktemp("o121-" + mode)
    source = root / "source"
    source.mkdir()
    member = "payload.txt" if mode == "pack" else "payload.zip"
    src = source / member
    if mode == "pack":
        original = hashlib.shake_256(b"O121-pack-bytes-fixed").digest(8192)
        src.write_bytes(original)
    else:
        entry = zipfile.ZipInfo("inner.txt", date_time=(2020, 1, 2, 3, 4, 6))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        with zipfile.ZipFile(src, "w") as archive:
            archive.writestr(entry, b"O121-ZIP-entry\n" * 512, compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=6)
        original = src.read_bytes()
    archive = root / "original.cmpct"
    Builder(source, workers=1).build(archive)
    with CMPCT(archive) as reader:
        rows = [row for row in reader.files if row[0] == member]
        assert len(rows) == 1, (mode, rows)
        actual_storage = rows[0][6][0]
        assert actual_storage == MODES[mode], (
            "Genuine Builder storage prerequisite not satisfied; no product outcome",
            mode, actual_storage, MODES[mode])
        assert reader.read(member) == original
        assert reader.verify() == 1
    manifest = {"mode": mode, "storage": actual_storage, "member": member,
                "source_sha": hashlib.sha256(original).hexdigest(),
                "archive_sha": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "source_size": len(original)}
    print("O121_ARCHIVE=" + json.dumps(manifest, sort_keys=True), flush=True)
    return root, archive, src, original, manifest


def _extract_child(archive: Path, dest: Path, member: str):
    child = (
        "from cmpct.core import CMPCT\n"
        "from pathlib import Path\n"
        "import hashlib,sys\n"
        "archive=Path(sys.argv[1]); dest=Path(sys.argv[2]); member=sys.argv[3]\n"
        "with CMPCT(archive) as r:\n"
        "    print('O121_CHILD_INDEX_OPENED',flush=True)\n"
        "    r.extractall(dest,metadata=False)\n"
        "print('O121_CHILD_RETURNED',flush=True)\n"
        "print('O121_CHILD_DIGEST='+hashlib.sha256((dest/member).read_bytes()).hexdigest(),flush=True)\n"
    )
    began = time.perf_counter()
    try:
        proc = subprocess.run([sys.executable, "-c", child, str(archive), str(dest), member],
                              cwd=str(dest.parent), capture_output=True, text=True,
                              timeout=DEADLINE, check=False)
        return {"kind": "exit", "rc": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "elapsed": round(time.perf_counter()-began, 6)}
    except subprocess.TimeoutExpired as exc:
        out, err = exc.stdout or b"", exc.stderr or b""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        return {"kind": "timeout", "rc": None, "stdout": out, "stderr": err,
                "elapsed": round(time.perf_counter()-began, 6)}


@pytest.mark.parametrize("leaf", LEAVES)
def test_o121_genuine_reader_storage_output(genuine_archive, leaf):
    assert os.name == "posix" and hasattr(os, "mkfifo"), "POSIX FIFO prerequisite"
    root, archive, src, original, manifest = genuine_archive
    mode, member = manifest["mode"], manifest["member"]
    dest = root / ("dest-" + leaf)
    dest.mkdir()
    target = dest / member
    external = None
    if leaf == "regular":
        target.write_bytes(b"pre-existing regular output")
    elif leaf == "fifo":
        os.mkfifo(target)
    elif leaf == "symlink_fifo":
        external = root / "external_fifo"
        if not external.exists():
            os.mkfifo(external)
        os.symlink(external, target)
        assert stat.S_ISFIFO(os.stat(target).st_mode)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    source_sha = hashlib.sha256(src.read_bytes()).hexdigest()
    assert archive_sha == manifest["archive_sha"]
    assert source_sha == manifest["source_sha"]
    outcome = _extract_child(archive, dest, member)
    assert "O121_CHILD_INDEX_OPENED" in outcome["stdout"], (mode, leaf, outcome)
    bad_leaf = leaf in ("fifo", "symlink_fifo")
    if bad_leaf:
        assert outcome["kind"] == "timeout", ("O121 prediction disproved", mode, leaf, outcome)
        if leaf == "fifo":
            assert stat.S_ISFIFO(os.lstat(target).st_mode)
        else:
            assert stat.S_ISLNK(os.lstat(target).st_mode)
            assert stat.S_ISFIFO(os.lstat(external).st_mode)
        observation = "direct_fifo_timeout"
    else:
        assert outcome["kind"] == "exit" and outcome["rc"] == 0, (mode, leaf, outcome)
        assert "O121_CHILD_RETURNED" in outcome["stdout"], outcome
        assert "O121_CHILD_DIGEST="+source_sha in outcome["stdout"], outcome
        assert stat.S_ISREG(os.lstat(target).st_mode)
        assert target.read_bytes() == original
        observation = "exact_regular"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha
    assert hashlib.sha256(src.read_bytes()).hexdigest() == source_sha
    print("O121_CASE=" + json.dumps({
        **manifest, "leaf": leaf, "outcome": observation, "child_kind": outcome["kind"],
        "child_rc": outcome["rc"], "wall_seconds": outcome["elapsed"],
        "deadline_seconds": DEADLINE}, sort_keys=True), flush=True)
