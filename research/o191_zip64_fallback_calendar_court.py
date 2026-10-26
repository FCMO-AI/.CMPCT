#!/usr/bin/env python3
"""O191: source-exact ZIP64 *fallback-path* DOS metadata court.

This is deliberately a branch-forcing test, NOT proof that CMPCT can stream or
export a genuine 4GiB+ member. The file payload stays small and authentic.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import o190_zip_dos_repair_court as o190


def run(directory: Path) -> dict:
    from cmpct.reader import CMPCT
    ident = o190.identity()
    source = json.loads((directory / "producer.json").read_text(encoding="utf-8"))
    assert source["schema"] == "cmpct-o190-producer-v1"
    assert source["provenance"]["head"] == ident["head"]
    assert source["provenance"]["reader_sha256"] == ident["reader_sha256"]

    default_zi = zipfile.ZipInfo("raw.bin")
    assert tuple(default_zi.date_time) == o190.ZIP_MIN, "stdlib control drift"
    results = {}
    for label, data in o190.DATA.items():
        archive_path = directory / (label + ".cmpct")
        expected_source = source["archives"][label]
        before = o190.sha(archive_path)
        assert before == expected_source["sha256"]
        assert archive_path.stat().st_size == expected_source["bytes"]
        with CMPCT(archive_path) as reader:
            assert reader.verify() == 1
            assert len(reader.files) == 1 and reader.files[0][0] == "raw.bin"
            assert reader.read("raw.bin") == data["content"]
            assert reader.files[0][3] == data["mtime_ns"]
            # Deliberately change ONLY the ephemeral in-memory size used by
            # the writer's dispatch. Reader.by and genuine r24 bytes stay intact.
            original_row = reader.files[0]
            synthetic_row = list(original_row)
            synthetic_row[4] = 0xffffffff
            reader.files[0] = tuple(synthetic_row)
            assert reader.files[0][4] >= 0xffffffff
            target = directory / (label + "-forced-zip64-path.zip")
            reader.export_zip(target)
            reader.files[0] = original_row

            ztime, zdate = reader._zip_dos_time(data["mtime_ns"])
            expected = (
                1980 + (zdate >> 9), (zdate >> 5) & 15, zdate & 31,
                ztime >> 11, (ztime >> 5) & 63, (ztime & 31) * 2,
            )
            with zipfile.ZipFile(target) as z:
                assert z.namelist() == ["raw.bin"]
                assert z.testzip() is None
                assert z.read("raw.bin") == data["content"]
                info = z.getinfo("raw.bin")
                got = tuple(info.date_time)
                assert got == expected, (label, got, expected)
                assert info.file_size == len(data["content"])
                assert info.CRC == __import__("binascii").crc32(data["content"]) & 0xffffffff

            assert o190.sha(archive_path) == before
            results[label] = {
                "original_cmpct_sha256": before,
                "synthetic_declared_size_only_in_memory": 0xffffffff,
                "actual_payload_bytes": len(data["content"]),
                "zip_bytes": target.stat().st_size,
                "zip_sha256": o190.sha(target),
                "zip_datetime": got,
                "expected_datetime": expected,
                "baseline_ZipInfo_default_datetime": tuple(default_zi.date_time),
                "member_crc_ok": True,
            }

    assert results["ordinary"]["zip_datetime"] != tuple(default_zi.date_time), (
        "the ordinary 2000 case must discriminate the legacy silent 1980 loss"
    )
    assert results["future"]["zip_datetime"] == o190.ZIP_MAX
    assert results["pre1970"]["zip_datetime"] == o190.ZIP_MIN
    return {
        "schema": "cmpct-o191-forced-fallback-v1",
        "provenance": ident,
        "mode": "synthetic-in-memory-size-dispatch; genuine small r24 payload; not genuine ZIP64 size",
        "results": results,
        "verdict": "ZIP64_FALLBACK_CALENDAR_FIDELITY_FORCED_BRANCH_PASS",
        "product_large_member_credit": False,
        "format_change": False,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = run(args.directory)
        rc = 0
    except Exception as exc:
        result = {
            "schema": "cmpct-o191-forced-fallback-v1", "verdict": "FAILED_OR_BLOCKED",
            "error": str(exc), "exception": type(exc).__name__,
            "traceback": traceback.format_exc()[-5000:],
        }
        rc = 1
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
