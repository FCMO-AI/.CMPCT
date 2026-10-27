#!/usr/bin/env python3
"""J24K02 independent *receipt* referee, without importing CMPCT's Reader or validator.

Independently decodes authenticated wire metadata, verifies immutable physical owners,
and checks exact recorded selective bytes. It authenticates experiment receipts, not an
independent execution of the Python Reader. Optional deliberate receipt mutations
prove this referee is not a decorative green check.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from pathlib import Path
import sys

import msgpack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from conformance.generate_v24_pack_golden import BHDR, FTR, HDR, zstd_codec  # noqa: E402

LABELS = ("oversized-slice", "past-physical-end", "huge-offset", "negative-offset", "missing-owner", "negative-length", "noninteger-owner", "boolean-offset")
FIXTURE = ROOT / "tests/conformance/v24-pack.json"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def inspect(wire: bytes, decompress):
    header = HDR.unpack_from(wire)
    magic, version, flags, ci, ui, span, wanted_digest = header
    assert (magic, version, flags) == (b"CMPCT24\0", 24, 0)
    index_bytes = decompress(wire[HDR.size:HDR.size+ci], ui)
    assert hashlib.sha256(index_bytes).digest() == wanted_digest
    index = msgpack.unpackb(index_bytes, raw=False)
    tail_pos = HDR.size+ci+span
    assert wire[tail_pos:tail_pos+ci] == wire[HDR.size:HDR.size+ci]
    assert FTR.unpack_from(wire, tail_pos+ci) == (
        b"CMPTF24\0", 0, 1, 0, 0, ci, ui, 0, wanted_digest
    )
    assert len(wire) == tail_pos+ci+FTR.size
    physical = wire[HDR.size+ci:tail_pos]
    bm, codec, flags, reserved, usize, csize, ml, crc, sha = BHDR.unpack_from(physical)
    assert bm == b"CMA4" and flags == reserved == 0 and ml == 0
    assert len(physical) == BHDR.size+csize
    encoded = physical[BHDR.size:]
    unpacked = encoded if codec == 0 else decompress(encoded, usize)
    assert len(unpacked) == usize
    assert binascii.crc32(unpacked) & 0xffffffff == crc
    assert hashlib.sha256(unpacked).digest() == sha
    assert index["blobs"] == [[0, usize, csize, codec, 0]]
    return index, physical, unpacked, codec


def adjudicate(receipt: dict) -> int:
    assert receipt["schema"] == "cmpct-j24k02-pack-selective-repair-v1"
    assert receipt["source"] == "installed-Python-Reader"
    assert receipt["decision"] == "CANDIDATE_GUARD_PASS"
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert golden["schema"] == "cmpct-v24-independent-pack-golden-v1"
    originals = {v["name"]: v for v in golden["vectors"]}
    assert set(originals) == {"pack-raw", "pack-zstd"}
    assert len(receipt["controls"]) == 2 and len(receipt["attacks"]) == 16
    _, decompress = zstd_codec()
    checks = 0
    seen_controls = set()
    for item in receipt["controls"]:
        name = item["vector"]
        assert name in originals and name not in seen_controls
        seen_controls.add(name)
        vec = originals[name]
        wire = base64.b64decode(vec["archive_base64"], validate=True)
        assert len(wire) == vec["archive_bytes"]
        assert digest(wire) == vec["archive_sha256"] == item["archive_sha256"]
        idx, physical, raw, codec = inspect(wire, decompress)
        assert codec == item["physical_codec"] == vec["physical_codec"]
        assert digest(raw) == vec["packed_blob_sha256"]
        assert item["verify"] == item["members"] == len(idx["files"]) == 4
        assert item["range_checks"] == 16
        rows = {row[0]: row for row in idx["files"]}
        for filename, expected in vec["files"].items():
            logical = bytes.fromhex(expected["hex"])
            row = rows[filename]
            if row[1] == 0 and row[6][0] == 4:
                assert raw[row[6][2]:row[6][2] + row[6][3]] == logical
        checks += 14

    seen = set()
    for item in receipt["attacks"]:
        key = (item["vector"], item["label"])
        assert key not in seen
        seen.add(key)
        assert item["vector"] in originals and item["label"] in LABELS
        vec = originals[item["vector"]]
        baseline = base64.b64decode(vec["archive_base64"], validate=True)
        index0, physical0, raw0, codec0 = inspect(baseline, decompress)
        changed = base64.b64decode(item["archive_base64"], validate=True)
        assert digest(changed) == item["archive_sha256"]
        assert item["original_archive_sha256"] == digest(baseline) == vec["archive_sha256"]
        index, physical, raw, codec = inspect(changed, decompress)
        assert physical == physical0 and raw == raw0
        assert codec == codec0 == item["physical_codec"]
        rows0 = {row[0]: row for row in index0["files"]}
        rows = {row[0]: row for row in index["files"]}
        assert set(rows0) == set(rows)
        for name in rows:
            if name != "omega.bin":
                assert rows[name] == rows0[name]
        base = rows0["omega.bin"]
        target = rows["omega.bin"]
        assert target[:6] == base[:6]
        assert target[6][0] == base[6][0] == 4
        assert target[6] == item["storage"]
        actual_len = target[4]
        assert item["logical_bytes"] == actual_len == vec["files"]["omega.bin"]["size"]
        ident, owner, off, length = target[6]
        assert ident == 4
        if item["label"] == "oversized-slice":
            assert (owner, off, length) == (0, base[6][2], actual_len+1)
        elif item["label"] == "past-physical-end":
            assert (owner, off, length) == (0, len(raw)-actual_len+1, actual_len)
        elif item["label"] == "huge-offset":
            assert (owner, off, length) == (0, (1 << 64)-1, actual_len)
        elif item["label"] == "negative-offset":
            assert (owner, off, length) == (0, -1, actual_len)
        elif item["label"] == "missing-owner":
            assert (owner, off, length) == (len(index["blobs"]), base[6][2], actual_len)
        elif item["label"] == "negative-length":
            assert (owner, off, length) == (0, base[6][2], -1)
        elif item["label"] == "noninteger-owner":
            assert (owner, off, length) == ("0", base[6][2], actual_len)
        elif item["label"] == "boolean-offset":
            assert type(off) is bool and off is True
            assert owner == 0 and length == actual_len
        assert item["preflight_rejected"] is True
        assert item["decode_calls"] == 0
        assert item["rejected_queries"] == ["OSError", "OSError", "OSError"]
        checks += 25
    assert seen == {(v,l) for v in originals for l in LABELS}
    assert checks == 428
    return checks


def main():
    if len(sys.argv) not in (2,3):
        raise SystemExit("usage: referee.py receipt.json [--hostile-selftest]")
    receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    checks = adjudicate(receipt)
    print(f"J24K02 independent authenticated wire/receipt referee: {checks} PASS")
    if len(sys.argv) == 3:
        assert sys.argv[2] == "--hostile-selftest"
        from copy import deepcopy
        probes = [
            lambda r: r["attacks"][0]["rejected_queries"].__setitem__(0, "ACCEPTED"),
            lambda r: r["attacks"][1]["storage"].__setitem__(2, 0),
            lambda r: r["attacks"][2].__setitem__("archive_sha256", "0"*64),
            lambda r: r["attacks"][3].__setitem__("archive_base64", "AA=="),
            lambda r: r["attacks"][4].__setitem__("decode_calls", 1),
            lambda r: r["attacks"][5].__setitem__("preflight_rejected", False),
            lambda r: r["controls"][0].__setitem__("verify", 3),
            lambda r: r.__setitem__("decision", "UNMEASURED"),
        ]
        refused = 0
        for mutate in probes:
            hostile = deepcopy(receipt)
            mutate(hostile)
            try:
                adjudicate(hostile)
            except (AssertionError, ValueError, KeyError, IndexError, TypeError):
                refused += 1
        assert refused == len(probes)
        print(f"J24K02 hostile receipt challenges rejected: {refused}/{len(probes)}")


if __name__ == "__main__":
    main()
