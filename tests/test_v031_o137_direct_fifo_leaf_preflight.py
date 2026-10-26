"""O137: installed CMPCT prewrite rejection of nonregular direct-output leaves.

A hostile FIFO child is always bounded; positive controls preserve regular reuse
and the unchanged verified atomic S_CHUNKS/S_CDC replacement semantics. The
Builder-generated modes are checked explicitly instead of assuming heuristics.
"""
from __future__ import annotations

import base64
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
from cmpct.codec import S_PACK, S_VZIP, S_CHUNKS, S_CDC

pytestmark = pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"),
                                reason="POSIX FIFO required; Windows pipe semantics independent")
MODE = {"pack": S_PACK, "vzip": S_VZIP}
LEAF = ("fresh", "regular", "fifo", "symlink_fifo")
DEADLINE = 5


@pytest.fixture(scope="module", params=("pack", "vzip"))
def genuine_mode(request, tmp_path_factory):
    mode = request.param
    root = tmp_path_factory.mktemp("o137-" + mode)
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
        with zipfile.ZipFile(src, "w") as stream:
            stream.writestr(entry, b"O121-ZIP-entry\n" * 512,
                            compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        original = src.read_bytes()
    archive = root / "original.cmpct"
    Builder(source, workers=1).build(archive)
    with CMPCT(archive) as r:
        assert r.by[member][6][0] == MODE[mode], (mode, r.by[member][6])
        assert r.read(member) == original
        assert r.verify() == 1
    return root, archive, member, original


def child_extract(archive: Path, dest: Path, member: str) -> dict:
    program = (
        "from cmpct.core import CMPCT\n"
        "from pathlib import Path\n"
        "import sys,hashlib\n"
        "with CMPCT(Path(sys.argv[1])) as r:\n"
        "  print('O137_INDEX_OPENED',flush=True)\n"
        "  try:\n"
        "    r.extractall(Path(sys.argv[2]),metadata=False,safe_symlinks=True)\n"
        "  except OSError as exc:\n"
        "    print('O137_REJECTED:'+str(exc),flush=True)\n"
        "    sys.exit(42)\n"
        "print('O137_EXACT:'+hashlib.sha256((Path(sys.argv[2])/sys.argv[3]).read_bytes()).hexdigest(),flush=True)\n"
    )
    start = time.perf_counter()
    try:
        result = subprocess.run([sys.executable, "-c", program, str(archive), str(dest), member],
                                text=True, capture_output=True, timeout=DEADLINE,
                                cwd=dest.parent, check=False)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"Reader hung on preexisting output leaf after {DEADLINE}s: {exc.stdout!r}")
    return {"rc": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "wall_seconds": round(time.perf_counter() - start, 5)}


@pytest.mark.parametrize("leaf", LEAF)
def test_genuine_direct_modes_refuse_fifo_before_write(genuine_mode, leaf):
    root, archive, member, original = genuine_mode
    dest = root / ("dest-" + leaf)
    dest.mkdir()
    target = dest / member
    external = None
    prior = None
    if leaf == "regular":
        prior = b"regular file reused without losing its name"
        target.write_bytes(prior)
    elif leaf == "fifo":
        os.mkfifo(target)
    elif leaf == "symlink_fifo":
        external = root / "external-fifo"
        if not external.exists():
            os.mkfifo(external)
        target.symlink_to(external)
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    observation = child_extract(archive, dest, member)
    assert "O137_INDEX_OPENED" in observation["stdout"], observation
    if leaf in ("fifo", "symlink_fifo"):
        assert observation["rc"] == 42, observation
        if leaf == "fifo":
            assert "nonregular direct-output destination leaf" in observation["stdout"], observation
            assert stat.S_ISFIFO(target.lstat().st_mode)
        else:
            assert "pre-existing destination symlink" in observation["stdout"], observation
            assert target.is_symlink() and stat.S_ISFIFO(external.lstat().st_mode)
    else:
        assert observation["rc"] == 0, observation
        assert "O137_EXACT:" + hashlib.sha256(original).hexdigest() in observation["stdout"]
        assert target.read_bytes() == original
        if prior:
            assert len(original) != len(prior)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha
    print("O137_CASE=" + json.dumps({"storage": int(MODE["pack"] if member.endswith(".txt") else MODE["vzip"]),
                                      "leaf": leaf, **observation}, sort_keys=True), flush=True)


@pytest.mark.parametrize("vector_index", (0, 1))
def test_frozen_independent_chunked_modes_preserve_fifo_replacement(tmp_path, vector_index):
    record = json.loads((Path(__file__).resolve().parents[1] / "tests/conformance/v24-chunk-maps.json").read_text())
    vector = record["vectors"][vector_index]
    assert vector["storage_kind"] in (S_CHUNKS, S_CDC)
    physical = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(physical) == vector["archive_bytes"]
    assert hashlib.sha256(physical).hexdigest() == vector["archive_sha256"]
    archive = tmp_path / "frozen.cmpct"
    archive.write_bytes(physical)
    dest = tmp_path / "output"
    dest.mkdir()
    leaf = dest / vector["name"]
    os.mkfifo(leaf)
    assert stat.S_ISFIFO(leaf.lstat().st_mode)
    with CMPCT(archive) as r:
        assert r.by[vector["name"]][6][0] == vector["storage_kind"]
        r.extractall(dest, metadata=False, safe_symlinks=True)
        assert r.verify() == 1
    assert stat.S_ISREG(leaf.lstat().st_mode)
    assert hashlib.sha256(leaf.read_bytes()).hexdigest() == vector["logical_sha256"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == vector["archive_sha256"]
    print("O137_ATOMIC_GOLDEN_PASS=" + vector["name"], flush=True)


def test_late_nonregular_leaf_rejects_before_earlier_member_mutation(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "a-first.txt").write_bytes(hashlib.shake_256(b"O137-a").digest(8192))
    (src / "z-last.txt").write_bytes(hashlib.shake_256(b"O137-z").digest(8192))
    archive = tmp_path / "two-member.cmpct"
    Builder(src, workers=1).build(archive)
    dest = tmp_path / "output"
    dest.mkdir()
    first = dest / "a-first.txt"
    sentinel = b"O137_OLD_EARLIER_BYTES"
    first.write_bytes(sentinel)
    last = dest / "z-last.txt"
    os.mkfifo(last)
    with CMPCT(archive) as r:
        assert r.by["z-last.txt"][6][0] not in (S_CHUNKS, S_CDC)
    outcome = child_extract(archive, dest, "z-last.txt")
    assert outcome["rc"] == 42 and "nonregular direct-output destination leaf" in outcome["stdout"], outcome
    assert first.read_bytes() == sentinel and stat.S_ISFIFO(last.lstat().st_mode)
    print("O137_PREWRITE_SENTINEL_PRESERVED", flush=True)
