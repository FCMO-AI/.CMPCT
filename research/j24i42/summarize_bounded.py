#!/usr/bin/env python3
"""J24I42 full raw-measurement parser; never award product performance credit."""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path

RX = re.compile(
    r"^([AB]) J24I42 size=(8|32) mode=(native|bounded) iter=(\d+) "
    r"wall_ns=(\d+) rchar=(\d+) vmhwm_kib=(\d+) bounded_read=(\d+)$"
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source = args.raw.read_bytes()
    manifest = json.loads(args.manifest.read_text())
    assert manifest["schema"] == "j24i42-audited-original-container-ranges-v1"
    records = {str(n): {"native": [], "bounded": []} for n in (8, 32)}
    for line in source.decode().splitlines():
        m = RX.fullmatch(line.strip())
        assert m is not None, f"missing/ambiguous observation: {line!r}"
        lane, size, mode, iteration, wall, rchar, rss, bytes_read = m.groups()
        assert (lane, mode) in (("A", "native"), ("B", "bounded"))
        assert int(iteration) in range(4)
        row = manifest["records"][size]
        if mode == "native":
            assert int(bytes_read) == 0
        else:
            assert 0 < int(bytes_read) <= row["encoded_bytes"]
            assert int(rchar) >= int(bytes_read)
        records[size][mode].append({
            "iter": int(iteration), "wall_ns": int(wall), "rchar": int(rchar),
            "vmhwm_kib": int(rss), "bounded_read": int(bytes_read)
        })
    summary = {}
    for size, modes in records.items():
        assert len(modes["native"]) == len(modes["bounded"]) == 16, (size, modes)
        med = lambda mode, key: statistics.median(r[key] for r in modes[mode])
        native_wall, bounded_wall = med("native", "wall_ns"), med("bounded", "wall_ns")
        native_read, bounded_read = med("native", "rchar"), med("bounded", "rchar")
        summary[size] = {
            "archive_sha256": manifest["records"][size]["archive_sha256"],
            "encoded_bytes": manifest["records"][size]["encoded_bytes"],
            "native_wall_median_ns": native_wall,
            "bounded_wall_median_ns": bounded_wall,
            "wall_native_over_bounded": round(native_wall / bounded_wall, 6),
            "native_rchar_median": native_read,
            "bounded_rchar_median": bounded_read,
            "rchar_native_over_bounded": round(native_read / bounded_read, 6),
            "native_vmhwm_median_kib": med("native", "vmhwm_kib"),
            "bounded_vmhwm_median_kib": med("bounded", "vmhwm_kib"),
            "bounded_payload_read_median": med("bounded", "bounded_read"),
            "product_credit": False,
        }
    out = {
        "schema": "j24i42-inarchive-range-oracle-result-v1",
        "status": "RESEARCH_MEASURED_NOT_PRODUCT",
        "raw_sha256": hashlib.sha256(source).hexdigest(),
        "measurements": 64,
        "per_size_per_mode": 16,
        "summary": summary,
        "observations": records,
        "scope": "detached-audited physical slice, no complete native product equivalence",
    }
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"], "summary": summary}, sort_keys=True))

if __name__ == "__main__":
    main()
