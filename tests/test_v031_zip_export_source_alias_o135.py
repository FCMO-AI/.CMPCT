"""O135 source-exact ZIP export inode-alias court.

Run the *original* PR #284 package and the O135 candidate in separate child Python
processes with O135_PRODUCT_SRC pointed to each checkout. The parent's assertions
inspect physical source SHA independently of exporter exit status: a fatal SIGBUS
is not mistaken for safe rejection. Do not weaken baseline expectations to green CI.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "tests" / "conformance" / "v24-direct-codecs.json"
GOLDEN_BLOB_SHA = "d10b7dab9126d39e819a74279c186363a163f2ef"

CHILD = r"""
import os
from pathlib import Path
import sys
import resource
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
source, target, expected_root = [Path(x).resolve() if i == 2 else Path(x) for i,x in enumerate(sys.argv[1:])]
from cmpct.reader import CMPCT
import cmpct.reader as reader_module
actual = Path(reader_module.__file__).resolve()
expected = expected_root / "cmpct" / "reader.py"
if actual != expected:
    print("O135_WRONG_READER", actual, expected, flush=True)
    sys.exit(79)
try:
    with CMPCT(source) as archive:
        archive.export_zip(target)
except (OSError, IOError) as exc:
    print("O135_MANAGED_REFUSAL", type(exc).__name__, str(exc), flush=True)
    sys.exit(31)
print("O135_EXPORT_SUCCESS", flush=True)
"""

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.parametrize("codec", ["raw.bin", "deflate.txt"])
@pytest.mark.parametrize("target_kind", ["disjoint", "same", "hardlink", "symlink"])
def test_source_archive_vs_zip_destination_inode(tmp_path, codec, target_kind):
    expectation = os.environ.get("O135_EXPECT")
    src_root = os.environ.get("O135_PRODUCT_SRC")
    assert expectation in ("original", "candidate"), "explicit engine attribution required"
    assert src_root, "explicit package source path required"
    src_root = Path(src_root).resolve()
    assert (src_root / "cmpct" / "reader.py").is_file()

    # The independent revision-24 golden vectors are pre-existing and were
    # hand-generated without Builder. Neither engine gets to regenerate them.
    doc = json.loads(VECTORS.read_text(encoding="utf-8"))
    vectors = {r["name"]: r for r in doc["vectors"]}
    vector = vectors[codec]
    archive_bytes = base64.b64decode(vector["archive_base64"], validate=True)
    assert _sha(archive_bytes) == vector["archive_sha256"]

    archive_path = tmp_path / "source.cmpct"
    archive_path.write_bytes(archive_bytes)
    target = tmp_path / "output.zip"
    if target_kind == "same":
        target = archive_path
    elif target_kind == "hardlink":
        os.link(archive_path, target)
    elif target_kind == "symlink":
        os.symlink(archive_path, target)

    initial_archive_hash = _sha(archive_path.read_bytes())
    assert initial_archive_hash == vector["archive_sha256"]
    if target_kind in ("same", "hardlink", "symlink"):
        assert os.stat(archive_path).st_ino == os.stat(target).st_ino
        assert os.stat(archive_path).st_dev == os.stat(target).st_dev

    env = dict(os.environ)
    env["PYTHONPATH"] = os.fspath(src_root) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, "-c", CHILD, str(archive_path), str(target), str(src_root)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=12,
    )
    after = _sha(archive_path.read_bytes())
    observation = {
        "engine": expectation,
        "codec": codec,
        "target_kind": target_kind,
        "exit_code": completed.returncode,
        "archive_source_hash_before": initial_archive_hash,
        "archive_source_hash_after": after,
        "stdout": completed.stdout[-300:],
        "stderr": completed.stderr[-300:],
    }
    print("O135_OBSERVATION=" + json.dumps(observation, sort_keys=True), flush=True)

    if target_kind == "disjoint":
        assert completed.returncode == 0, observation
        assert after == initial_archive_hash, observation
        assert target.exists(), observation
        with zipfile.ZipFile(target) as z:
            assert z.namelist() == [codec], observation
            assert z.testzip() is None, observation
            assert _sha(z.read(codec)) == vector["logical_sha256"], observation
    elif expectation == "original":
        # Source destruction is the negative being measured. A fatal signal,
        # Python exception or successful return are not used as its proxy.
        assert after != initial_archive_hash, observation
    else:
        assert completed.returncode == 31, observation
        assert "O135_MANAGED_REFUSAL" in completed.stdout, observation
        assert "aliases its own CMPCT source archive" in completed.stdout, observation
        assert after == initial_archive_hash, observation
        assert target.exists(), "static aliases must be rejected without unlinking them"
