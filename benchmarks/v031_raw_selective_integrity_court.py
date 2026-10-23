"""Exact-source r24 RAW read_range integrity-tier falsifier (RESEARCH, not product)."""
from __future__ import annotations
import binascii
import hashlib
import json
import pathlib
import statistics
import tempfile
import time

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import BHDR, CODEC_RAW, S_BLOB
from cmpct.validation import preflight_archive

SIZES = (65536, 524288, 1048576)

def digest(x):
    return hashlib.sha256(x).hexdigest()

def classify(path, position, expected):
    with CMPCT(path) as reader:
        ranged = reader.read_range("probe.bin", position, 1)
        range_state = "ACCEPT_TAMPERED" if ranged == bytes([expected]) else "UNEXPECTED"
        try:
            result = reader.read("probe.bin")[position:position + 1]
            full_state = "ACCEPT_TAMPERED" if result == bytes([expected]) else "UNEXPECTED"
        except (OSError, ValueError):
            full_state = "REJECT"
        try:
            reader.verify()
            verified = "ACCEPT"
        except (OSError, ValueError):
            verified = "REJECT"
    try:
        preflight_archive(path)
        structural = "ACCEPT"
    except Exception as e:
        structural = "REJECT_" + type(e).__name__
    return dict(range=range_state, full_read=full_state, verify=verified,
                structural_preflight=structural)

def corruption_case(size):
    data = hashlib.shake_256(b"cmpct-r24-raw-integrity-20261023:" +
                            str(size).encode()).digest(size)
    with tempfile.TemporaryDirectory(prefix="cmpct-raw-") as temp:
        root = pathlib.Path(temp)
        source = root / "source"
        source.mkdir()
        (source / "probe.bin").write_bytes(data)
        archive = root / "source.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            row = reader.by["probe.bin"]
            assert row[6][0] == S_BLOB
            off, us, cs, codec, ml = reader.blobs[row[6][1]]
            assert codec == CODEC_RAW and us == cs == size
            header = reader.record_base + off
            payload = header + BHDR.size + ml
            assert reader.read("probe.bin") == data
            assert reader.verify() == 1
            original = archive.read_bytes()
            stored_crc = BHDR.unpack_from(original, header)[-2]
            stored_sha = BHDR.unpack_from(original, header)[-1]
        cases = []
        for pos in (0, size // 2, size - 1):
            for repair_crc in (False, True):
                changed = bytearray(original)
                changed[payload + pos] ^= 0x80
                new_crc = binascii.crc32(
                    memoryview(changed)[payload:payload + size]) & 0xffffffff
                assert stored_crc != new_crc
                if repair_crc:
                    fields = list(BHDR.unpack_from(changed, header))
                    fields[-2] = new_crc
                    BHDR.pack_into(changed, header, *fields)
                assert BHDR.unpack_from(changed, header)[-1] == stored_sha
                corrupt = root / "corrupt.cmpct"
                corrupt.write_bytes(changed)
                actual = classify(corrupt, pos, data[pos] ^ 0x80)
                expected = {
                    "range": "ACCEPT_TAMPERED",
                    "full_read": "ACCEPT_TAMPERED" if repair_crc else "REJECT",
                    "verify": "REJECT",
                    "structural_preflight": "ACCEPT",
                }
                assert actual == expected, (size, pos, repair_crc, actual)
                cases.append(dict(size=size, position=pos, crc_repaired=repair_crc,
                                  archive_sha256=digest(changed), **actual))
        return dict(size=size, source_sha256=digest(data),
                    archive_sha256=digest(original), cases=cases)

def crc_cost_probe(size, rounds=11):
    data = hashlib.shake_256(
        b"cmpct-r24-raw-selective-cost:" + str(size).encode()).digest(size)
    with tempfile.TemporaryDirectory(prefix="cmpct-raw-cost-") as temp:
        root = pathlib.Path(temp)
        source = root / "source"
        source.mkdir()
        (source / "probe.bin").write_bytes(data)
        archive = root / "source.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            off, us, cs, codec, ml = reader.blobs[reader.by["probe.bin"][6][1]]
            assert codec == CODEC_RAW and us == size
            header = reader.record_base + off
            start = header + BHDR.size + ml
            stored_crc = BHDR.unpack_from(reader.mm, header)[-2]
            direct, charged = [], []
            for i in range(rounds):
                for mode in ("ABBA" if i % 2 == 0 else "BAAB"):
                    t0 = time.perf_counter_ns()
                    if mode == "A":
                        got = reader.read_range("probe.bin", size // 2, 1)
                    else:
                        actual_crc = binascii.crc32(
                            memoryview(reader.mm)[start:start + size]) & 0xffffffff
                        assert actual_crc == stored_crc
                        got = reader.mm[start + size // 2:start + size // 2 + 1]
                    delta_ms = (time.perf_counter_ns() - t0) / 1e6
                    assert got == data[size // 2:size // 2 + 1]
                    (direct if mode == "A" else charged).append(delta_ms)
        return dict(size=size, direct_slice_ms=direct, crc_whole_blob_ms=charged,
                    direct_median_ms=statistics.median(direct),
                    crc_median_ms=statistics.median(charged))

def main():
    cases = [corruption_case(size) for size in SIZES]
    all_cases = [row for group in cases for row in group["cases"]]
    assert len(all_cases) == 18
    assert all(row["range"] == "ACCEPT_TAMPERED" and
               row["verify"] == "REJECT" for row in all_cases)
    timings = [crc_cost_probe(size) for size in SIZES]
    print(json.dumps({
        "schema": "cmpct-v031-raw-selective-court-v1",
        "decision": "RAW_RANGE_BYPASSES_CRC_AND_SHA",
        "baseline": "canonical installed revision-24 Reader",
        "cases": cases,
        "cost_micro_ABBA": timings,
        "scope_limit": "physical corruption cases; CRC-only full read is not SHA verify; "
                       "microcosts do not certify a release-performance gate.",
    }, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
