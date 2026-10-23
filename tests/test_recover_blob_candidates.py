"""Physical salvage enumerates candidates; it does not authenticate recovered content.

The comparison scanner is intentionally copied from the inherited v0.31 behavior.
It is an independent compatibility oracle for framing offsets and declared metadata.
"""
import binascii
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import BHDR, BMAGIC, CODEC_RAW
from cmpct.reader import CMPCT
from cmpct.transactions import recover_blob_records

WINDOW = 1024 * 1024
DECLARED_KEYS = ("offset", "codec", "usize", "csize", "crc32", "sha256")


def _legacy_scan(data):
    out = []
    p = 0
    while True:
        i = data.find(BMAGIC, p)
        if i < 0:
            break
        if i + BHDR.size <= len(data):
            try:
                m, c, fl, res, us, cs, ml, rcrc, rh = BHDR.unpack_from(data, i)
                if i + BHDR.size + ml + cs <= len(data):
                    out.append({
                        "offset": i, "codec": c, "usize": us,
                        "csize": cs, "crc32": rcrc, "sha256": bytes(rh).hex()
                    })
            except Exception:
                pass
        p = i + 1
    return out


def _record(payload, *, declared_sha=None, declared_crc=None, codec=CODEC_RAW):
    return (BHDR.pack(
        BMAGIC, codec, 0, 0, len(payload), len(payload), 0,
        binascii.crc32(payload) & 0xffffffff if declared_crc is None else declared_crc,
        hashlib.sha256(payload).digest() if declared_sha is None else declared_sha,
    ) + payload)


def _check_parity(path):
    expected = _legacy_scan(path.read_bytes())
    actual = recover_blob_records(path)
    assert [{k: row[k] for k in DECLARED_KEYS} for row in actual] == expected
    assert all(row["verification"] == "unverified" for row in actual)
    assert all(row["generation_membership"] == "unknown" for row in actual)
    return actual


@pytest.mark.parametrize("offset", [
    0, 1, WINDOW - BHDR.size, WINDOW - BHDR.size + 1,
    WINDOW - 4, WINDOW - 1, WINDOW, WINDOW + 1, 2 * WINDOW - 11,
])
def test_original_framing_parity_for_window_edge_positions(tmp_path, offset):
    # A physically valid frame begins at each representative boundary position.
    path = tmp_path / "boundary.cmpct"
    path.write_bytes(b"x" * offset + _record(b"hello boundary") + b"tail")
    got = _check_parity(path)
    assert len(got) == 1 and got[0]["offset"] == offset


def test_adjacent_nested_and_truncated_header_candidates(tmp_path):
    # Deliberate false candidates inside payloads, a forged wrong-hash header and
    # incomplete near-EOF data all retain the old source scanner's permissive truth.
    inner = _record(b"inner")
    outer = _record(inner + b"suffix")
    forged = _record(b"forged", declared_sha=b"\\x42" * 32, declared_crc=0)
    path = tmp_path / "hostile.cmpct"
    path.write_bytes(
        b"before" + outer + _record(b"adjacent") + forged
        + b"padding" * 3 + BMAGIC + b"\\x00" * (BHDR.size - len(BMAGIC) - 1)
    )
    rows = _check_parity(path)
    assert len(rows) >= 3
    assert any(r["sha256"] == (b"\\x42" * 32).hex() for r in rows)
    assert all(r["verification"] == "unverified" for r in rows)


def test_framed_unknown_codec_stays_unverified_candidate(tmp_path):
    # This scanner must not quietly grant decoder support from a framing coincidence.
    path = tmp_path / "unknown.cmpct"
    path.write_bytes(_record(b"raw?", codec=255))
    rows = _check_parity(path)
    assert len(rows) == 1
    assert rows[0]["codec"] == 255
    assert rows[0]["verification"] == "unverified"


def test_real_revision24_corrupt_raw_and_forged_uncommitted_tail(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    payload = random.Random(1337).randbytes(8192)
    (source / "source.bin").write_bytes(payload)
    archive = tmp_path / "source.cmpct"
    Builder(source, workers=1).build(archive)
    with CMPCT(archive) as reader:
        assert reader.read("source.bin") == payload
    rows = _check_parity(archive)
    assert rows
    raw = next(row for row in rows if row["codec"] == CODEC_RAW and row["usize"] == len(payload))
    bad = bytearray(archive.read_bytes())
    off = raw["offset"] + BHDR.size
    bad[off + 53] ^= 0x01
    forged = _record(b"uncommitted", declared_sha=b"\\x42" * 32, declared_crc=0)
    corrupt = tmp_path / "corrupt.cmpct"
    corrupt.write_bytes(bytes(bad) + forged)
    with CMPCT(corrupt) as reader:
        with pytest.raises(Exception):
            reader.read("source.bin")
    scan = _check_parity(corrupt)
    assert raw["sha256"] in {row["sha256"] for row in scan}
    assert (b"\\x42" * 32).hex() in {row["sha256"] for row in scan}
    # The scanner makes no claim that either physically framed candidate has verified data.
    assert all(row["verification"] == "unverified" for row in scan)


def test_cli_output_preserves_legacy_keys_and_explicit_trust_tier(tmp_path):
    path = tmp_path / "single.cmpct"
    path.write_bytes(_record(b"source"))
    run = subprocess.run(
        [sys.executable, "-m", "cmpct.cli", "recover-blobs", str(path)],
        capture_output=True, text=True, check=True,
    )
    rows = json.loads(run.stdout)
    assert rows == recover_blob_records(path)
    assert set(DECLARED_KEYS).issubset(rows[0])
    assert rows[0]["verification"] == "unverified"
    assert rows[0]["generation_membership"] == "unknown"


@pytest.mark.skipif(os.name != "posix", reason="POSIX child process ru_maxrss semantics")
def test_sparse_128mib_scan_stays_below_full_materialization_rss(tmp_path):
    # This checks the installed real scanner, not a duplicated synthetic implementation.
    # Results measure additional peak RSS after all package imports in a fresh child.
    path = tmp_path / "sparse.cmpct"
    with path.open("wb") as out:
        out.seek(128 * 1024 * 1024 - 1)
        out.write(b"\\x00")
    code = (
        "import resource,sys,json;"
        "from cmpct.transactions import recover_blob_records;"
        "before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;"
        "rows=recover_blob_records(sys.argv[1]);"
        "after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;"
        "print(json.dumps({'before_kib':before,'after_kib':after,'delta_kib':after-before,'rows':len(rows)}))"
    )
    run = subprocess.run([sys.executable, "-c", code, str(path)],
                         text=True, capture_output=True, check=True)
    measured = json.loads(run.stdout)
    assert measured["rows"] == 0
    assert measured["delta_kib"] < 24 * 1024, measured
