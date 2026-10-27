#!/usr/bin/env python3
"""Independent stdlib referee for J24V02; no CMPCT imports or product code."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import statistics
import sys

ORDER = ("baseline", "candidate", "candidate", "baseline")
KEYS = ("cpu_ns", "wall_ns", "peak_kib", "incremental_peak_kib")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()


def audit(data, check_files=True):
    assert data["schema"] == "j24v02-source-exact-sparse-verify-abba-v1"
    assert data["release_commit"] == "80c358f8824ec1b20d349c92ed94c898090969b0"
    assert data["candidate_owner_commit"] == "3b2bf3c2e033fa27d77b2355821dc0087aa46873"
    assert data["process_count"] == 24 == len(data["observations"])
    assert len(data["fixtures"]) == 2
    assert {f["size_mib"] for f in data["fixtures"]} == {64, 256}
    assert data["reader_sha256"]["candidate"] != data["reader_sha256"]["baseline"]
    by_size = {f["size_mib"]: f for f in data["fixtures"]}
    for f in data["fixtures"]:
        assert f["archive_bytes"] > 0 and f["archive_bytes"] < f["logical_size"]
        assert f["logical_size"] > 0 and f["extent_count"] >= 2
        assert isinstance(f["logical_sha256"], str) and len(f["logical_sha256"]) == 64
        assert isinstance(f["archive_sha256"], str) and len(f["archive_sha256"]) == 64
        if check_files:
            assert digest(f["archive"]) == f["archive_sha256"], "changed wire bytes"
    positions = set()
    source_files = {}
    for row in data["observations"]:
        n, rd, pos, mode = (row["size_mib"], row["round"], row["position"], row["mode"])
        assert n in (64, 256) and 0 <= rd < 3 and 0 <= pos < 4
        assert mode == ORDER[pos], "ABBA order falsified"
        key = (n, rd, pos)
        assert key not in positions, "duplicate fresh-process cell"
        positions.add(key)
        f = by_size[n]
        assert row["archive_sha256"] == f["archive_sha256"], "different archive bytes"
        assert row["logical_size"] == f["logical_size"], "changed member geometry"
        assert row["verified"] == 1
        assert row["reader_sha256"] == data["reader_sha256"][mode], "mixed source identity"
        assert row["source_path"].endswith("/src/cmpct/reader.py")
        assert mode not in source_files or source_files[mode] == row["source_path"]
        source_files[mode] = row["source_path"]
        for k in KEYS:
            assert isinstance(row[k], int) and not isinstance(row[k], bool) and row[k] >= 0
        assert row["cpu_ns"] > 0 and row["wall_ns"] > 0 and row["peak_kib"] >= row["before_peak_kib"]
        assert row["incremental_peak_kib"] == row["peak_kib"] - row["before_peak_kib"]
    assert len(positions) == 24
    if check_files:
        for mode, path in source_files.items():
            assert digest(path) == data["reader_sha256"][mode], "Reader source drift"
    summary = {}
    for n in (64, 256):
        groups = {
            mode: [r for r in data["observations"] if r["size_mib"] == n and r["mode"] == mode]
            for mode in ("baseline", "candidate")
        }
        assert all(len(g) == 6 for g in groups.values())
        summary[str(n)] = {
            mode: {k: statistics.median(row[k] for row in group) for k in KEYS}
            for mode, group in groups.items()
        }
        assert summary[str(n)] == data["summary"][str(n)], "fabricated summary median"
    old = summary["256"]["baseline"]
    new = summary["256"]["candidate"]
    saved = old["peak_kib"] - new["peak_kib"]
    memory = saved >= 128 * 1024 and new["peak_kib"] < 128 * 1024
    veto = {}
    for k in ("cpu_ns", "wall_ns"):
        ratio = new[k] / old[k]
        absolute = (new[k] - old[k]) / 1e9
        veto[k] = {"ratio": ratio, "absolute_seconds": absolute,
                   "fired": ratio >= 1.15 and absolute >= 0.20}
    decision = ("RSS_PASS_NO_MATERIAL_CPU_WALL_VETO" if memory and not any(v["fired"] for v in veto.values())
                else "RSS_PASS_WITH_RUNTIME_DEBT" if memory
                else "RSS_PREDICTION_FALSIFIED")
    return {"schema": "j24v02-stdlib-referee-v1", "checks": 24,
            "source_files": source_files, "recomputed_summary": summary,
            "saved_peak_kib": saved, "memory_prediction_pass": memory,
            "veto": veto, "decision": decision}


def self_test(original):
    # Deliberately corrupted copies must fail: identity, source, repeated processes, summary and ABBA.
    import copy
    cases = []
    a = copy.deepcopy(original)
    a["observations"][0]["mode"] = "candidate"
    cases.append(a)
    a = copy.deepcopy(original)
    a["observations"][1]["reader_sha256"] = "0" * 64
    cases.append(a)
    a = copy.deepcopy(original)
    a["observations"][0]["round"] = 1
    cases.append(a)
    a = copy.deepcopy(original)
    a["summary"]["256"]["candidate"]["wall_ns"] += 123456
    cases.append(a)
    a = copy.deepcopy(original)
    a["observations"][0]["archive_sha256"] = "0" * 64
    cases.append(a)
    rejected = 0
    for item in cases:
        try:
            audit(item, check_files=False)
        except (AssertionError, KeyError, ValueError, TypeError):
            rejected += 1
    assert rejected == len(cases), (rejected, len(cases))
    return rejected


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text())
    result = audit(raw)
    result["adversarial_receipts_rejected"] = self_test(raw)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("j24v02-audit.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "saved_peak_kib": result["saved_peak_kib"],
                      "tamper_rejected": result["adversarial_receipts_rejected"]}, sort_keys=True))
