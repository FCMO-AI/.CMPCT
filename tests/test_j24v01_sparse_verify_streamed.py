"""J24V01: genuine Builder sparse owner, immutable r24 sparse golden, bounded verifier.

Distinct from #255/#571 sparse extraction and #610 hardlink alias admission.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.codec import K_FILE, S_SPARSE
from cmpct.reader import CMPCT


def test_frozen_r24_sparse_sha_unchanged_and_uncached(tmp_path: Path):
    path = Path(__file__).with_name("conformance") / "v24-sparse.json"
    record = json.loads(path.read_text())
    archive = tmp_path / "golden.cmpct"
    archive.write_bytes(base64.b64decode(record["archive"]["base64"]))
    name = record["member"]["path"]
    with CMPCT(archive) as ar:
        assert ar.by[name][6][0] == S_SPARSE
        read_digest = hashlib.sha256(ar.read(name)).hexdigest()
        assert read_digest == record["member"]["sha256"]
    with CMPCT(archive) as ar:
        original = ar._blob
        calls = []
        def without_retention(idx, *, retain=True):
            calls.append((idx, retain))
            assert retain is False
            return original(idx, retain=retain)
        ar._blob = without_retention
        assert ar.verify() == 1
        assert calls and all(not retain for _, retain in calls)
        assert not ar.cache
        row = ar.by[name]
        valid_hash = row[5]
        row[5] = bytes(32)
        try:
            with pytest.raises(IOError, match="SHA-256 verification failure"):
                ar.verify()
        finally:
            row[5] = valid_hash
        original_storage = row[6]
        row[6] = [S_SPARSE, [[0, 1, [original_storage[1][0][2][0]]]]]
        try:
            with pytest.raises(IOError, match="sparse extent length failure"):
                ar.verify()
        finally:
            row[6] = original_storage
        assert ar.verify() == 1


@pytest.mark.skipif(sys.platform != "linux", reason="Linux SEEK_DATA/SEEK_HOLE sparse owner and VmHWM")
def test_real_256m_sparse_verification_does_not_materialize_holes(tmp_path: Path):
    source = tmp_path / "tree"
    source.mkdir()
    huge = source / "large.bin"
    logical_size = 256 * 1024 * 1024
    with huge.open("wb") as fh:
        fh.write(b"J24V01" * 512)
        fh.seek(logical_size - 4096)
        fh.write(b"V" * 4096)
    archive = tmp_path / "large.cmpct"
    Builder(source).build(archive)
    with CMPCT(archive) as ar:
        row = ar.by["large.bin"]
        assert row[1] == K_FILE and row[6][0] == S_SPARSE, "genuine sparse admission required"
        assert row[4] == logical_size
        # No eager logical member read: actual post-exec VmHWM is measured in the fresh verifier child, not pytest.
    script = """
import json,resource,sys
from pathlib import Path
from cmpct.reader import CMPCT
with CMPCT(sys.argv[1]) as reader:
    count=reader.verify()
    # Linux ru_maxrss can inherit the PARENT's pre-exec high-water through fork/exec.
    # /proc/self/status:VmHWM belongs to THIS exec'd verifier and includes native RSS.
    hwm_line=next((line for line in Path('/proc/self/status').read_text().splitlines()
                   if line.startswith('VmHWM:')), None)
    if hwm_line is None:
        raise RuntimeError('post-exec VmHWM missing: cannot claim bounded verification')
    parts=hwm_line.split()
    if len(parts) != 3 or parts[2] != 'kB':
        raise RuntimeError('invalid post-exec VmHWM: '+repr(hwm_line))
    peak=int(parts[1])
    if peak <= 0:
        raise RuntimeError('nonpositive post-exec VmHWM')
    print(json.dumps({'verified':count,'peak_kib':peak,
        'inherited_ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
"""
    proc = subprocess.run([sys.executable, "-c", script, str(archive)],
                          capture_output=True, text=True, check=True, timeout=50)
    result = json.loads(proc.stdout)
    assert result["verified"] == 1
    # The published read() path first allocated a 256-MiB bytearray, then copied it to
    # bytes. Preserve the strict original 128-MiB ceiling; only the Linux process-local
    # peak attribution was corrected (ru_maxrss could carry the parent pre-exec peak).
    assert result["peak_kib"] < 128 * 1024, result
