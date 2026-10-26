"""J24F01 Builder-independent r24 S_CHUNKS/S_CDC physical publication court.

A passing test validates only the frozen archive and tested POSIX output
arrangement. Child deadlines are availability guards, not throughput benchmarks.
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

import pytest

from cmpct.core import CMPCT
from cmpct.codec import BHDR, S_CHUNKS, S_CDC

DEADLINE = 7
MODES = (("fixed.bin", S_CHUNKS), ("cdc.bin", S_CDC))
LEAVES = ("fresh", "regular", "fifo", "symlink_fifo", "symlink_regular",
          "hardlink_regular", "corrupt")


@pytest.fixture(scope="module", params=MODES, ids=("chunks-frozen", "cdc-frozen"))
def frozen_archive(request, tmp_path_factory):
    assert os.name == "posix" and hasattr(os, "mkfifo"), "POSIX fixture prerequisite"
    golden = Path(os.environ["CMPCT_GOLDEN_PATH"])
    assert golden.is_file(), "golden source unavailable"
    doc = json.loads(golden.read_text(encoding="utf-8"))
    assert doc["schema"] == "cmpct-v24-golden-chunk-maps-v1"
    assert doc["format_revision"] == 24
    name, storage = request.param
    vec, = [v for v in doc["vectors"] if v["name"] == name]
    assert vec["storage_kind"] == storage
    raw = base64.b64decode(vec["archive_base64"], validate=True)
    assert len(raw) == vec["archive_bytes"]
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == vec["archive_sha256"]
    root = tmp_path_factory.mktemp("j24f01-" + name)
    archive = root / "frozen.cmpct"
    archive.write_bytes(raw)
    with CMPCT(archive) as reader:
        matching = [x for x in reader.files if x[0] == name]
        assert len(matching) == 1, (name, reader.files)
        assert matching[0][6][0] == storage, (name, matching[0][6][0])
        expected = reader.read(name)
        assert len(expected) == vec["logical_size"]
        assert hashlib.sha256(expected).hexdigest() == vec["logical_sha256"]
        assert reader.verify() == 1
        # Corrupt the *last* physical chunk: earlier chunks must already have
        # entered the staging file before this checksum refusal occurs.
        # A first-chunk error would not exercise partial-staging cleanup.
        mapping = matching[0][6][1]
        chunk_ids = list(mapping) if storage == S_CHUNKS else [int(x[1]) for x in mapping]
        assert len(chunk_ids) == len(vec["chunk_codecs"]) == 3
        tail_idx = chunk_ids[-1]
        off, us, cs, codec, meta_len = reader.blobs[tail_idx]
        assert codec == vec["chunk_codecs"][-1] == 0
        assert cs > 0 and all(reader.blobs[i][1] > 0 for i in chunk_ids[:-1])
        payload_at = reader.record_base + off + BHDR.size + meta_len
        assert 0 <= payload_at < payload_at + cs <= len(raw), (name, payload_at, cs)
    print("J24F01_ARCHIVE=" + json.dumps({
        "mode": name, "storage": storage, "archive_sha": digest,
        "logical_sha": vec["logical_sha256"], "size": len(expected),
        "physical_payload_offset": payload_at, "physical_payload_len": cs}, sort_keys=True),
        flush=True)
    return root, archive, name, storage, expected, digest, payload_at, cs


def _run_child(archive: Path, dest: Path, name: str):
    script = (
        "import hashlib,sys\n"
        "from pathlib import Path\n"
        "from cmpct.core import CMPCT\n"
        "a,d,n=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]\n"
        "with CMPCT(a) as r:\n"
        "    print('J24F01_INDEX_OPENED',flush=True)\n"
        "    r.extractall(d,metadata=False)\n"
        "print('J24F01_EXTRACTED',flush=True)\n"
        "print('J24F01_SHA='+hashlib.sha256((d/n).read_bytes()).hexdigest(),flush=True)\n"
    )
    begun = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(archive), str(dest), name],
            cwd=str(dest.parent), text=True, capture_output=True, timeout=DEADLINE,
            check=False)
        return {"kind": "exit", "code": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr, "wall_seconds": round(time.perf_counter()-begun, 6)}
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        return {"kind": "timeout", "code": None, "stdout": stdout, "stderr": stderr,
                "wall_seconds": round(time.perf_counter()-begun, 6)}


@pytest.mark.parametrize("leaf", LEAVES)
def test_j24f01_fixed_chunk_publication(frozen_archive, leaf):
    root, archive, name, storage, expected, archive_sha, payload_at, payload_len = frozen_archive
    dest = root / ("dest-" + leaf)
    dest.mkdir()
    target = dest / name
    external = None
    sentinel = b"J24F01-before-publication-external-sentinel\n"
    old_stat = None
    tested_archive = archive

    if leaf == "regular" or leaf == "corrupt":
        target.write_bytes(sentinel)
        old_stat = os.lstat(target)
    elif leaf == "fifo":
        os.mkfifo(target)
    elif leaf == "symlink_fifo":
        external = root / "external.fifo"
        if not external.exists():
            os.mkfifo(external)
        os.symlink(external, target)
        assert stat.S_ISFIFO(os.stat(target).st_mode)
    elif leaf == "symlink_regular":
        external = root / "external-regular"
        external.write_bytes(sentinel)
        os.symlink(external, target)
    elif leaf == "hardlink_regular":
        external = root / "external-hardlink"
        external.write_bytes(sentinel)
        os.link(external, target)
        old_stat = os.lstat(target)
        assert os.lstat(external).st_ino == old_stat.st_ino

    if leaf == "corrupt":
        tampered = bytearray(archive.read_bytes())
        tampered[payload_at + payload_len // 2] ^= 1
        tested_archive = root / "corrupt-payload.cmpct"
        tested_archive.write_bytes(tampered)
        assert hashlib.sha256(tested_archive.read_bytes()).hexdigest() != archive_sha

    result = _run_child(tested_archive, dest, name)
    assert result["kind"] == "exit", ("unexpected hang", name, leaf, result)
    assert "J24F01_INDEX_OPENED" in result["stdout"], ("no real Reader open", name, leaf, result)
    if leaf == "corrupt":
        assert result["code"] != 0, ("corrupt physical chunk unexpectedly published", name, result)
        last_error = next((x.strip().lower() for x in reversed(result["stderr"].splitlines()) if x.strip()), "")
        assert any(x in last_error for x in ("zstd", "deflate", "integrity", "corrupt", "checksum", "decode")), ("not a codec/integrity refusal", name, last_error)
        assert target.read_bytes() == sentinel
        assert os.lstat(target).st_ino == old_stat.st_ino
        assert not list(dest.glob(f".{name}.cmpct-part-*")), "staging leak after rejection"
        conclusion = "corrupt_refused_without_publication"
    else:
        assert result["code"] == 0, (name, leaf, result)
        assert "J24F01_EXTRACTED" in result["stdout"], result
        assert "J24F01_SHA="+hashlib.sha256(expected).hexdigest() in result["stdout"], result
        assert stat.S_ISREG(os.lstat(target).st_mode)
        assert target.read_bytes() == expected
        if leaf == "fifo":
            assert not stat.S_ISFIFO(os.lstat(target).st_mode)
        if leaf in ("symlink_fifo", "symlink_regular"):
            assert not stat.S_ISLNK(os.lstat(target).st_mode)
        if leaf == "symlink_fifo":
            assert stat.S_ISFIFO(os.lstat(external).st_mode)
        if leaf in ("symlink_regular", "hardlink_regular"):
            assert external.read_bytes() == sentinel
        if leaf == "hardlink_regular":
            assert os.lstat(external).st_ino == old_stat.st_ino
            assert os.lstat(target).st_ino != old_stat.st_ino
        conclusion = "exact_atomic_leaf_replace"

    assert hashlib.sha256(archive.read_bytes()).hexdigest() == archive_sha
    print("J24F01_CASE=" + json.dumps({
        "mode": name, "storage": storage, "leaf": leaf, "result": conclusion,
        "archive_sha": archive_sha, "logical_sha": hashlib.sha256(expected).hexdigest(),
        "child": result["kind"], "exit_code": result["code"],
        "seconds": result["wall_seconds"], "deadline": DEADLINE}, sort_keys=True), flush=True)
