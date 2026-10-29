#!/usr/bin/env python3
"""J24I39b: prospective hostile FLAC framing mutations, never modify original archive."""
import argparse
import hashlib
import json
from pathlib import Path

TAIL = b"\xffJ24I39_TRAILING_TEST"
assert len(TAIL) == 21

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    args = p.parse_args()
    base = args.case_dir
    m = json.loads((base / "stream-manifest.json").read_text())
    assert m["schema"] == "j24i39-independent-split-v1"
    record = m["records"]["8"]
    original = (base / record["flac_path"]).read_bytes()
    assert sha(original) == record["flac_sha256"]
    cases = {
        "valid": original,
        "trailer": original + TAIL,
        "truncated": original[:-64],
        "concatenated": original + original,
    }
    rows = {}
    for name, data in cases.items():
        path = base / f"tail-{name}.flac"
        path.write_bytes(data)
        rows[name] = {
            "file": path.name,
            "bytes": len(data),
            "sha256": sha(data),
            "prefix_exact": data[:min(len(data), len(original))] == original[:min(len(data), len(original))],
        }
    assert rows["valid"]["sha256"] == record["flac_sha256"]
    assert rows["trailer"]["bytes"] == len(original) + 21
    assert rows["truncated"]["bytes"] == len(original) - 64
    assert rows["concatenated"]["bytes"] == 2 * len(original)
    data = {"schema": "j24i39b-encoded-tail-v1", "source_archive_sha256": record["archive_sha256"],
            "reference_flac_sha256": record["flac_sha256"], "tail_hex": TAIL.hex(),
            "variants": rows}
    (base / "tail-manifest.json").write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print(json.dumps(data, sort_keys=True))

if __name__ == "__main__":
    main()
