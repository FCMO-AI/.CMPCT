#!/usr/bin/env python3
"""Independent stdlib-only referee for J24G22. Does not import cmpct or court code."""
import argparse
import hashlib
import json
from pathlib import Path

MODES = {"eager", "spool", "premature"}
CASES = {"pristine-direct": "direct.bin", "pristine-large": "larger.bin", "corrupt-late": "direct.bin"}

def validate(directory: Path) -> int:
    record = json.loads((directory / "receipt.json").read_text())
    old = (directory / "original.cmpct").read_bytes()
    bad = (directory / "late-corrupt.cmpct").read_bytes()
    assert len(old) == len(bad) == record["original_bytes"] == record["corrupt_bytes"]
    assert hashlib.sha256(old).hexdigest() == record["original_sha256"]
    assert hashlib.sha256(bad).hexdigest() == record["corrupt_sha256"]
    difference = [i for i, (a, b) in enumerate(zip(old, bad)) if a != b]
    assert difference == [record["mutated_physical_offset"]]
    assert (old[difference[0]] ^ bad[difference[0]]) == 1
    assert record["cases"]["direct.bin"]["kind"] == 0
    assert record["cases"]["direct.bin"]["physical_codec"] == 0
    assert record["decision"] == "VERIFIED_STDOUT_REQUIRES_BUFFER_OR_SPOOL_OR_TWO_PASSES; PREMATURE_RANGE_EMITS_CORRUPTION"
    rows = record["observations"]
    assert len(rows) == 27
    seen = set()
    checked = 0
    for row in rows:
        assert row["case"] in CASES
        assert row["mode"] in MODES
        assert row["member"] == CASES[row["case"]]
        assert row["repetition"] in (0, 1, 2)
        key = (row["case"], row["mode"], row["repetition"])
        assert key not in seen
        seen.add(key)
        assert row["archive_sha256"] == record["corrupt_sha256" if row["case"] == "corrupt-late" else "original_sha256"]
        assert row["size"] == record["cases"][row["member"]]["bytes"]
        assert row["cpu_ns"] > 0 and row["wall_ns"] > 0
        assert row["rss_peak_kib"] >= row["rss_increment_over_open_kib"] >= 0
        assert row["temp_bytes_written"] == (row["size"] if row["mode"] == "spool" else 0)
        if row["case"] != "corrupt-late":
            assert row["error"] is None
            assert row["emitted_bytes"] == row["size"]
            assert row["emitted_sha256"] == record["cases"][row["member"]]["sha256"]
        elif row["mode"] in {"eager", "spool"}:
            assert row["error"] is not None
            assert row["emitted_bytes"] == 0
            assert row["emitted_sha256"] == hashlib.sha256(b"").hexdigest()
        else:
            assert row["error"] is None and row["emitted_bytes"] == row["size"]
            assert row["emitted_sha256"] != record["cases"][row["member"]]["sha256"]
        checked += 15
    assert len(seen) == 27
    return checked + 10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--tamper-test", action="store_true")
    args = parser.parse_args()
    count = validate(args.directory)
    if args.tamper_test:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            for name in ("original.cmpct", "late-corrupt.cmpct", "receipt.json"):
                (target / name).write_bytes((args.directory / name).read_bytes())
            info = json.loads((target / "receipt.json").read_text())
            info["observations"][0]["emitted_bytes"] += 1
            (target / "receipt.json").write_text(json.dumps(info))
            try:
                validate(target)
            except AssertionError:
                pass
            else:
                raise AssertionError("referee accepted tampered receipt")
            count += 1
    print(json.dumps({"status": "PASS", "referee_checks": count, "tampered_receipts_rejected": int(args.tamper_test)}))

if __name__ == "__main__":
    main()
