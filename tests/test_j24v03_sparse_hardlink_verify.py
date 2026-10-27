"""J24V03: signed sparse hardlinks reuse bounded verification without alias-size amnesty.

Source-locked to J24V01. Independent r24 primary+tail indexes are reauthenticated
while preserving the original physical records byte-for-byte.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import msgpack
import pytest

from cmpct.builder import Builder
from cmpct.codec import (
    FMAGIC, FTR, HDR, K_DIR, K_FILE, K_HARDLINK, MAGIC,
    S_SPARSE, sha, zc, zd,
)
from cmpct.reader import CMPCT


def _golden_wire() -> bytes:
    record = json.loads((Path(__file__).with_name("conformance") / "v24-sparse.json").read_text())
    return base64.b64decode(record["archive"]["base64"])


def _alias(owner, name, target, declared=None):
    return [name, K_HARDLINK, owner[2], owner[3],
            owner[4] if declared is None else declared, None, [target]]


def _signed_index(tmp_path: Path, rows_factory) -> Path:
    wire = _golden_wire()
    magic, version, flags, cs, us, ds, digest = HDR.unpack_from(wire)
    assert magic == MAGIC and version == 24
    raw_index = zd(wire[HDR.size:HDR.size + cs], us)
    assert sha(raw_index) == digest
    index = msgpack.unpackb(raw_index, raw=False)
    assert len(index["files"]) == 1
    owner = index["files"][0]
    assert owner[1] == K_FILE and owner[6][0] == S_SPARSE and owner[4] == 64
    index["files"] = rows_factory(list(owner))
    new_index = msgpack.packb(index, use_bin_type=True)
    compressed = zc(new_index, 12)
    physical = wire[HDR.size + cs:HDR.size + cs + ds]
    assert len(physical) == ds
    target = tmp_path / "signed-alias.cmpct"
    target.write_bytes(
        HDR.pack(MAGIC, version, flags, len(compressed), len(new_index), ds, sha(new_index))
        + compressed + physical + compressed
        + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(new_index), 0, sha(new_index))
    )
    result = target.read_bytes()
    assert result[HDR.size + len(compressed):HDR.size + len(compressed) + ds] == physical
    assert result[HDR.size:HDR.size + len(compressed)] == result[-FTR.size - len(compressed):-FTR.size]
    assert hashlib.sha256(physical).digest() == hashlib.sha256(
        wire[HDR.size + cs:HDR.size + cs + ds]
    ).digest()
    return target


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("chain", [False, True])
def test_signed_sparse_aliases_verify_without_materializing_any_member(tmp_path: Path, reverse: bool, chain: bool):
    def rows(owner):
        result = [owner, _alias(owner, "alias-a", owner[0])]
        if chain:
            result.append(_alias(owner, "alias-b", "alias-a"))
        return result[::-1] if reverse else result

    path = _signed_index(tmp_path, rows)
    with CMPCT(path) as reader:
        expected = len(reader.files)
        assert reader.by["sparse.bin"][6][0] == S_SPARSE
        def no_whole_read(name):
            raise AssertionError(f"whole-read materialization forbidden: {name}")
        reader.read = no_whole_read
        assert reader.verify() == expected
        assert not reader.cache, "sparse decoded payload must not persist in Reader cache"
    with CMPCT(path) as reader:
        # Independently exercise genuine reconstructed owner bytes.
        value = reader.read("sparse.bin")
        assert len(value) == 64
        assert hashlib.sha256(value).hexdigest() == (
            "0ead4c6bf7ab3c32f8452985937a48186b64c7e482c4fd4ecfca28bd44443ca9"
        )
        assert reader.read("alias-a") == value


@pytest.mark.parametrize("case", ["outer-size", "middle-size", "missing", "cycle", "nonregular"])
def test_resigned_hostile_aliases_fail_closed(tmp_path: Path, case: str):
    def rows(owner):
        middle = _alias(owner, "alias-a", owner[0], 65 if case == "middle-size" else 64)
        outer = _alias(owner, "alias-b", "alias-a", 63 if case == "outer-size" else 64)
        if case == "missing":
            middle[6] = ["absent-target"]
        elif case == "cycle":
            middle[6] = ["alias-b"]
        values = [owner, middle, outer]
        if case == "nonregular":
            values.append(["directory", K_DIR, owner[2], owner[3], 0, None, []])
            middle[6] = ["directory"]
        return values

    path = _signed_index(tmp_path, rows)
    with CMPCT(path) as reader:
        with pytest.raises(IOError, match="hardlink"):
            reader.verify()


@pytest.mark.parametrize("reverse", [False, True])
def test_deep_signed_chain_resolution_is_linear_without_recursion(tmp_path: Path, reverse: bool):
    n = 1024
    def rows(owner):
        result = [owner]
        prev = owner[0]
        for i in range(n):
            name = f"link-{i:05d}"
            result.append(_alias(owner, name, prev))
            prev = name
        return result[::-1] if reverse else result
    path = _signed_index(tmp_path, rows)
    with CMPCT(path) as reader:
        counts = {"lookups": 0}
        real_by = reader.by
        class Counting(dict):
            def get(self, name, default=None):
                counts["lookups"] += 1
                return super().get(name, default)
        reader.by = Counting(real_by)
        reader.read = lambda name: (_ for _ in ()).throw(AssertionError("materialized"))
        assert reader.verify() == n + 1
        assert counts["lookups"] <= n + 2, counts
        assert not reader.cache


@pytest.mark.skipif(sys.platform != "linux", reason="Linux sparse Builder + own VmHWM")
def test_real_sparse_hardlink_64m_uses_bounded_peak_memory(tmp_path: Path):
    source = tmp_path / "tree"
    source.mkdir()
    owner = source / "a-owner.bin"
    logical = 64 * 1024 * 1024
    with owner.open("wb") as fp:
        fp.write(b"J24V03" * 512)
        fp.seek(logical - 4096)
        fp.write(b"P" * 4096)
    os.link(owner, source / "z-alias.bin")
    archive = tmp_path / "genuine.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert len(reader.files) == 2, reader.files
        kinds = {row[1] for row in reader.files}
        assert kinds == {K_FILE, K_HARDLINK}, kinds
        physical = next(row for row in reader.files if row[1] == K_FILE)
        assert physical[6][0] == S_SPARSE, "real sparse admission required"
        assert physical[4] == logical

    process_code = """
import json,sys,time
from cmpct.reader import CMPCT
start = time.perf_counter()
with CMPCT(sys.argv[1]) as reader:
    def no_materialized_read(name):
        raise AssertionError("whole-read called for sparse alias: " + name)
    reader.read = no_materialized_read
    verified = reader.verify()
    assert not reader.cache
with open("/proc/self/status", encoding="ascii") as fh:
    line = next(x for x in fh if x.startswith("VmHWM:"))
peak_kib = int(line.split()[1])
print(json.dumps({"verified": verified, "peak_kib": peak_kib, "wall_ms": round(1000*(time.perf_counter()-start), 3)}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", process_code, str(archive)],
        capture_output=True, text=True, check=True, timeout=50,
    )
    result = json.loads(proc.stdout)
    assert result["verified"] == 2
    assert result["peak_kib"] < 128 * 1024, result
    print("J24V03_REAL_SPARSE_HARDLINK", json.dumps(result, sort_keys=True))
