#!/usr/bin/env python3
"""O18 independently test POSIX stage-before-publish C ABI SHA barrier.

A research-only, 1-file subset: sealed r24 index is NOT an external signature.
All source and expected SHA evidence is supplied by the Python oracle, not the
native client's verification decision. Negative retains physical records.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_CDC, S_BLOB, CODEC_RAW
from native_hardlink_owner_o14 import rebuild, wire_parts

BASE = "c2b61c5290382c3df5eb92c6381b83b1ba0e02d0"
CDC_LENGTHS = (1_500_000, 2_100_000)
RAW_LENGTH = 86_016
CHUNK = 65_536
FIXED_TIME = 1_700_000_000_000_000_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def invoke(binary: Path, archive: Path, dest: Path, name: str) -> dict:
    started = time.perf_counter_ns()
    proc = subprocess.run(
        [str(binary), str(archive), str(dest), name],
        capture_output=True, text=True, timeout=90,
    )
    return {
        "exit": proc.returncode, "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(), "wall_ns": time.perf_counter_ns() - started,
    }


def assert_empty(path: Path) -> None:
    assert list(path.iterdir()) == [], [x.name for x in path.iterdir()]


def run_one(binary: Path, home: Path, ordinal: int, length: int) -> dict:
    root = home / f"source-{ordinal}"
    root.mkdir()
    source = random.Random(818000 + ordinal).randbytes(length)
    direct = random.Random(929000 + ordinal).randbytes(RAW_LENGTH)
    (root / "cdc.bin").write_bytes(source)
    (root / "raw.bin").write_bytes(direct)
    for p in root.iterdir():
        os.utime(p, ns=(FIXED_TIME, FIXED_TIME))
    os.utime(root, ns=(FIXED_TIME, FIXED_TIME))
    archive = home / f"original-{ordinal}.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    original = archive.read_bytes()
    with CMPCT(archive) as reader:
        rows = {row[0]: row for row in reader.files}
        assert rows["cdc.bin"][6][0] == S_CDC, rows["cdc.bin"][6]
        assert rows["cdc.bin"][5] == hashlib.sha256(source).digest()
        assert rows["raw.bin"][6][0] == S_BLOB
        assert reader.blobs[int(rows["raw.bin"][6][1])][3] == CODEC_RAW
        assert rows["raw.bin"][5] is None
        assert reader.read("cdc.bin") == source
        assert reader.read("raw.bin") == direct

    okroot = home / f"published-{ordinal}"
    okroot.mkdir()
    good = invoke(binary, archive, okroot, "cdc.bin")
    assert good["exit"] == 0, ("positive CDC", good)
    outcome = json.loads(good["stdout"])
    assert outcome["decision"] == "VERIFIED_CDC_STAGED", outcome
    assert outcome["bytes"] == length and outcome["chunk_bytes"] == CHUNK
    assert outcome["sha256"] == digest(source)
    assert list(okroot.iterdir()) == [okroot / "cdc.bin"]
    assert (okroot / "cdc.bin").read_bytes() == source

    # Source records are untouched. Flip ONLY the existing committed logical
    # row digest then independently recalculate BOTH compressed indexes/footer.
    wrong_digest = bytes([source[0] ^ 0xC3]) * 32
    assert wrong_digest != hashlib.sha256(source).digest()
    changed = {"count": 0}

    def corrupt_index(idx: dict) -> None:
        for row in idx["files"]:
            if row[0] == "cdc.bin":
                assert row[5] == hashlib.sha256(source).digest()
                row[5] = wrong_digest
                changed["count"] += 1

    mutant = rebuild(original, corrupt_index)
    assert changed["count"] == 1
    original_index, original_records, original_flags = wire_parts(original)
    new_index, new_records, new_flags = wire_parts(mutant)
    assert original_records == new_records and original_flags == new_flags
    assert original_index["files"] != new_index["files"]
    assert len(mutant) > 0 and digest(mutant) != digest(original)
    bad_archive = home / f"contradictory-{ordinal}.cmpct"
    bad_archive.write_bytes(mutant)
    with CMPCT(bad_archive) as reader:
        rows_bad = {row[0]: row for row in reader.files}
        assert rows_bad["cdc.bin"][5] == wrong_digest
        # The reference Python Reader MUST independently reject the contradictory
        # logical SHA on full reconstruction. Native C is separately judged by
        # whether it preserves the no-publish barrier under bounded reads.
        try:
            reader.read("cdc.bin")
        except IOError as err:
            assert "integrity" in str(err).lower(), err
        else:
            raise AssertionError("reference Reader accepted contradictory CDC row SHA")

    badroot = home / f"rejected-hash-{ordinal}"
    badroot.mkdir()
    mismatch = invoke(binary, bad_archive, badroot, "cdc.bin")
    assert mismatch["exit"] == 5, (
        "digest mismatch MUST be identified at publication barrier", mismatch
    )
    assert "O18_REJECT status=5" in mismatch["stderr"], mismatch
    assert_empty(badroot)

    rawroot = home / f"rejected-raw-{ordinal}"
    rawroot.mkdir()
    unsupported = invoke(binary, archive, rawroot, "raw.bin")
    assert unsupported["exit"] == 4, (
        "missing RAW row SHA MUST NOT publish", unsupported
    )
    assert_empty(rawroot)

    outer = home / f"outside-canary-{ordinal}"
    canary = b"O18 EXTERNAL CANARY MUST REMAIN EXACT" * 4
    outer.write_bytes(canary)
    hostileroot = home / f"hostile-target-{ordinal}"
    hostileroot.mkdir()
    (hostileroot / "cdc.bin").symlink_to(outer)
    hostile = invoke(binary, archive, hostileroot, "cdc.bin")
    assert hostile["exit"] == 6, ("hostile destination", hostile)
    assert outer.read_bytes() == canary and (hostileroot / "cdc.bin").is_symlink()
    assert list(hostileroot.iterdir()) == [hostileroot / "cdc.bin"]
    assert not (hostileroot / ".cmpct-o18-stage").exists()

    return {
        "source_bytes": length,
        "source_sha256": digest(source),
        "archive_bytes": len(original),
        "archive_sha256": digest(original),
        "contradictory_archive_bytes": len(mutant),
        "contradictory_archive_sha256": digest(mutant),
        "same_records_sha256": digest(original_records),
        "original_index_sha256": digest(
            json.dumps([str(x) for x in original_index["files"]], sort_keys=True).encode()
        ),
        "contradictory_record_commitment": wrong_digest.hex(),
        "positive": good,
        "wrong_index_hash_rejected": mismatch,
        "raw_uncommitted_rejected": unsupported,
        "hostile_preexisting_leaf_rejected": hostile,
        "independent_published_file_sha256": digest((okroot / "cdc.bin").read_bytes()),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: native_signed_index_stage_o18.py CLIENT RESULT.json")
    binary, result = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    assert binary.is_file()
    with tempfile.TemporaryDirectory(prefix="cmpct-o18-") as temp:
        home = Path(temp)
        cases = {
            str(size): run_one(binary, home, i, size)
            for i, size in enumerate(CDC_LENGTHS)
        }
    receipt = {
        "schema": "cmpct-native-signed-index-stage-o18-v1",
        "source_base_sha": BASE,
        "decision": "CDC_STAGED_LOGICAL_SHA_BARRIER_PASS",
        "cases": cases,
        "negative_classes": [
            "resealed authentic-r24-index wrong logical SHA; physical records unchanged",
            "real RAW direct entry with no logical SHA",
            "static preexisting hostile symlink leaf",
        ],
        "no_product_claims": [
            "untrusted index is not externally signed",
            "no general RAW verification",
            "no arbitrary tree/hardlink/symlink publication",
            "no adversarial concurrent destination/source mutation",
            "no crash-recovery or full-tree atomicity",
            "no whole-process RSS or portable host benchmark",
            "no release or official performance parity",
        ],
    }
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": receipt["decision"],
        "case_bytes": list(cases),
        "positive_count": len(cases),
        "negative_count": 3 * len(cases),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
