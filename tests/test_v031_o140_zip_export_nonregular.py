"""O140 source-exact installed product court: ZIP export refuses nonregular destinations.

Independently distinguish a deadlocking FIFO open from an earlier Reader failure using
a flushed sentinel; test both the direct ZIP32 route and stdlib ZipFile route on exact
revision-24 golden source bytes. Child processes are killed after three seconds.
No builder fixture, no hostname-specific expected archive, no relaxed product claims.
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
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "conformance" / "v24-direct-codecs.json"
GOLDEN_BLOB_SHA = "d10b7dab9126d39e819a74279c186363a163f2ef"

CHILD = r"""
import os
from pathlib import Path
import sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
except ImportError:
    pass
source, target, root, route = sys.argv[1:5]
root = Path(root).resolve()
from cmpct.reader import CMPCT
import cmpct.reader as rm
actual = Path(rm.__file__).resolve()
expected = root / 'cmpct' / 'reader.py'
if actual != expected:
    print('O140_WRONG_READER', actual, expected, flush=True)
    sys.exit(79)
try:
    with CMPCT(Path(source)) as archive:
        print('O140_READER_OPENED', flush=True)
        archive._zip64_offset_fallback_required = lambda: route == 'stdlib'
        print('O140_ROUTE_' + route, flush=True)
        archive.export_zip(Path(target))
except (OSError, IOError) as exc:
    print('O140_MANAGED_REFUSAL', type(exc).__name__, str(exc), flush=True)
    sys.exit(31)
print('O140_EXPORT_SUCCESS', flush=True)
"""

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("codec", ["raw.bin", "deflate.txt"])
@pytest.mark.parametrize("route", ["direct", "stdlib"])
@pytest.mark.parametrize("target_kind", [
    "new", "regular", "fifo", "symlink_fifo", "directory", "source_alias"
])
def test_zip_export_nonregular_destination(tmp_path, codec, route, target_kind):
    engine = os.environ.get("O140_ENGINE")
    package_root = os.environ.get("O140_PRODUCT_SRC")
    assert engine in ("original", "candidate"), "engine attribution required"
    assert package_root, "source-install location required"
    package_root = Path(package_root).resolve()
    assert (package_root / "cmpct" / "reader.py").is_file()
    assert hasattr(os, "mkfifo"), "POSIX FIFO support required"

    vectors = json.loads(GOLDEN.read_text(encoding="utf-8"))["vectors"]
    v = next(row for row in vectors if row["name"] == codec)
    data = base64.b64decode(v["archive_base64"], validate=True)
    assert _sha(data) == v["archive_sha256"]
    archive_path = tmp_path / "source.cmpct"
    archive_path.write_bytes(data)
    before = _sha(archive_path.read_bytes())
    target = tmp_path / "target.zip"
    fifo = tmp_path / "unconnected.fifo"

    if target_kind == "regular":
        target.write_bytes(b"old existing content")
    elif target_kind == "fifo":
        os.mkfifo(target)
    elif target_kind == "symlink_fifo":
        os.mkfifo(fifo)
        os.symlink(fifo.name, target)
    elif target_kind == "directory":
        target.mkdir()
    elif target_kind == "source_alias":
        target = archive_path

    old_stat = os.lstat(target) if target.exists() or target.is_symlink() else None
    if target_kind in ("fifo", "symlink_fifo"):
        assert stat.S_ISFIFO(os.stat(target).st_mode)
    if target_kind == "source_alias":
        assert os.stat(archive_path).st_ino == os.stat(target).st_ino

    env = dict(os.environ)
    env["PYTHONPATH"] = os.fspath(package_root) + os.pathsep + env.get("PYTHONPATH", "")
    command = [sys.executable, "-c", CHILD, str(archive_path), str(target), str(package_root), route]
    timeout = False
    try:
        r = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                           text=True, timeout=3.0)
        stdout = r.stdout
        stderr = r.stderr
        exit_code = r.returncode
    except subprocess.TimeoutExpired as e:
        timeout = True
        stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        exit_code = "TIMEOUT_3_SECONDS"
    after = _sha(archive_path.read_bytes())
    observation = {
        "engine": engine, "codec": codec, "route": route, "target_kind": target_kind,
        "timeout": timeout, "exit": exit_code, "source_hash_before": before,
        "source_hash_after": after, "stdout": stdout[-700:],
        "stderr": stderr[-700:],
    }
    print("O140_OBSERVATION=" + json.dumps(observation, sort_keys=True), flush=True)

    assert "O140_READER_OPENED" in stdout, observation
    assert "O140_ROUTE_" + route in stdout, observation
    assert before == after, "source CMPCT must never be modified"

    if target_kind in ("new", "regular"):
        assert not timeout and exit_code == 0, observation
        with zipfile.ZipFile(target, "r") as z:
            assert z.namelist() == [codec], observation
            assert z.testzip() is None, observation
            assert _sha(z.read(codec)) == v["logical_sha256"], observation
    elif target_kind in ("fifo", "symlink_fifo") and engine == "original":
        assert timeout, "original exporter unexpectedly did not block: " + str(observation)
    else:
        assert not timeout and exit_code == 31, observation
        assert "O140_MANAGED_REFUSAL" in stdout, observation
        if target_kind in ("fifo", "symlink_fifo") and engine == "candidate":
            assert "nonregular" in stdout.lower(), observation
        if target_kind == "source_alias":
            assert "aliases its own CMPCT source archive" in stdout, observation

    if target_kind in ("fifo", "symlink_fifo", "directory", "source_alias"):
        assert os.lstat(target).st_ino == old_stat.st_ino, observation
        assert os.lstat(target).st_mode == old_stat.st_mode, observation
