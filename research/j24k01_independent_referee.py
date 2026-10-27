#!/usr/bin/env python3
"""J24K01 independent *receipt* referee, without importing CMPCT's Reader or validator.

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

LABELS = ("oversized-slice", "past-physical-end", "huge-offset")
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
    assert receipt["schema"] == "cmpct-j24k01-pack-selective-court-v1"
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert golden["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert golden["format_revision"] == 24
    originals = {v["name"]: v for v in golden["vectors"]}
    assert set(originals) == {"pack-raw", "pack-zstd"}
    assert len(receipt["controls"]) == 2 and len(receipt["mutations"]) == 6
    _, decompress = zstd_codec()
    checks = 0
    for item in receipt["controls"]:
        vec = originals[item["vector"]]
        wire = base64.b64decode(vec["archive_base64"], validate=True)
        assert len(wire) == vec["archive_bytes"]
        assert digest(wire) == vec["archive_sha256"] == item["archive_sha256"]
        idx, physical, raw, codec = inspect(wire, decompress)
        assert codec == vec["physical_codec"] == item["physical_codec"]
        assert digest(raw) == vec["packed_blob_sha256"]
        assert item["verify"] == item["members"] == len(idx["files"]) == 4
        expected = bytes.fromhex(vec["files"]["omega.bin"]["hex"])
        assert item["omega_sha256"] == digest(expected)
        rows = {r[0]: r for r in idx["files"]}
        assert rows["omega.bin"][6][0] == 4
        s = rows["omega.bin"][6]
        assert raw[s[2]:s[2]+s[3]] == expected
        checks += 12
    seen = set()
    for item in receipt["mutations"]:
        key = (item["vector"], item["label"])
        assert key not in seen
        seen.add(key)
        assert item["label"] in LABELS
        vector = originals[item["vector"]]
        baseline = base64.b64decode(vector["archive_base64"], validate=True)
        baseline_index, base_physical, base_pack, base_codec = inspect(baseline, decompress)
        candidate = base64.b64decode(item["archive_base64"], validate=True)
        assert digest(candidate) == item["archive_sha256"]
        assert item["original_archive_sha256"] == vector["archive_sha256"] == digest(baseline)
        mutated_index, physical, pack, codec = inspect(candidate, decompress)
        assert physical == base_physical and pack == base_pack
        assert codec == base_codec == item["physical_codec"]
        orig_rows = {r[0]: r for r in baseline_index["files"]}
        rows = {r[0]: r for r in mutated_index["files"]}
        assert set(orig_rows) == set(rows)
        for name in rows:
            if name != "omega.bin":
                assert rows[name] == orig_rows[name]
        old = orig_rows["omega.bin"]
        row = rows["omega.bin"]
        assert row[:6] == old[:6]
        assert item["storage"] == row[6]
        assert row[6][0:2] == old[6][0:2] == [4,0]
        size = row[4]
        assert item["logical_size"] == size == vector["files"]["omega.bin"]["size"]
        if item["label"] == "oversized-slice":
            assert row[6][2] == old[6][2]
            assert row[6][3] == size+1
        elif item["label"] == "past-physical-end":
            assert row[6][2] == len(pack)-size+1
            assert row[6][3] == old[6][3] == size
        else:
            assert row[6][2] == (1 << 64)-1
            assert row[6][3] == size
        assert "pack slice exceeds blob" in item["preflight"]
        assert "packed file size failure" in item["whole_read"]
        observation = item["selective"]
        assert observation["status"] == "ACCEPTED", (key, observation)
        actual = pack[row[6][2]:row[6][2]+size]
        assert bytes.fromhex(observation["hex"]) == actual
        assert observation["length"] == len(actual)
        assert observation["sha256"] == digest(actual)
        if item["label"] == "oversized-slice":
            assert actual == bytes.fromhex(vector["files"]["omega.bin"]["hex"])
        elif item["label"] == "past-physical-end":
            assert len(actual) == size-1
        else:
            assert actual == b""
        checks += 27
    assert seen == {(v, l) for v in originals for l in LABELS}
    assert checks == 186
    return checks


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: independent_referee.py court.json [--hostile-selftest]")
    record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    checks = adjudicate(record)
    print(f"J24K01 independent wire/receipt referee: {checks} PASS")
    if len(sys.argv) == 3:
        assert sys.argv[2] == "--hostile-selftest"
        from copy import deepcopy
        probes = [
            lambda d: d["mutations"][0]["selective"].__setitem__("length", 0),
            lambda d: d["mutations"][1]["selective"].__setitem__("hex", "00"),
            lambda d: d["mutations"][2]["storage"].__setitem__(2, 0),
            lambda d: d["mutations"][3].__setitem__("archive_sha256", "0"*64),
            lambda d: d["mutations"][4]["selective"].__setitem__("sha256", "0"*64),
            lambda d: d["controls"][0].__setitem__("verify", 3),
            lambda d: d["mutations"][5].__setitem__("preflight", "accepted"),
        ]
        refused = 0
        for corrupt in probes:
            mutated = deepcopy(record)
            corrupt(mutated)
            try:
                adjudicate(mutated)
            except (AssertionError, ValueError, KeyError):
                refused += 1
        assert refused == len(probes)
        print(f"J24K01 hostile receipt challenges: {refused}/{len(probes)} rejected")


if __name__ == "__main__":
    main()
