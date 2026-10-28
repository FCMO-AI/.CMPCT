#!/usr/bin/env python3
"""Independent stdlib-only referee for J24B03-P paired source-exact timing receipts.

Does not import CMPCT, the Reader, or the performance runner. It recomputes
pairing, identity and preregistered thresholds from raw subprocess observations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import sys


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path):
    d = json.loads(path.read_text())
    assert d["experiment"] == "J24B03-P"
    assert d["rung"] == "source-exact micro-ABBA only"
    plan = d["design"]
    assert plan == {"calls_per_worker": 30000, "order": [
        "baseline", "candidate", "candidate", "baseline"],
        "rounds": 3, "offsets": [0, 7, 31, 63, 111], "length": 16}

    owners = d["source_sha256"]
    for arm, root in (("baseline", "frozen-baseline/src"), ("candidate", "src")):
        actual = sha(Path(root) / "cmpct/reader.py")
        assert actual == owners[arm], (arm, actual, owners[arm])
    assert owners["baseline"] != owners["candidate"]

    archives = {x["name"]: x for x in d["archives"]}
    assert set(archives) == {"raw", "zstd", "deflate"}
    for name, entry in archives.items():
        assert entry["name"] == name
        assert sha(Path(entry["path"])) == entry["sha256"]
        assert len(entry["expected_hex"]) == 5
        assert all(len(bytes.fromhex(v)) == 16 for v in entry["expected_hex"])
    assert len({x["sha256"] for x in archives.values()}) == 3

    records = d["rows"]
    assert len(records) == 36
    seen = set()
    for x in records:
        arm, name, rnd, slot = x["arm"], x["profile"], x["round"], x["order_slot"]
        assert name in archives and arm in owners
        assert 0 <= rnd < 3 and 0 <= slot < 4
        assert arm == ("baseline", "candidate", "candidate", "baseline")[slot]
        key = (name, rnd, slot)
        assert key not in seen
        seen.add(key)
        assert x["reader_sha256"] == owners[arm]
        assert Path(x["reader_path"]).resolve() == (
            Path("frozen-baseline/src" if arm == "baseline" else "src") /
            "cmpct/reader.py").resolve()
        assert x["archive_sha256"] == archives[name]["sha256"]
        assert x["calls"] == 30000 and x["logical_return_bytes"] == 480000
        assert x["range_wall_ns"] > 0 and x["range_cpu_ns"] > 0
        assert x["open_wall_ns"] > 0 and x["open_cpu_ns"] > 0
        assert x["peak_vmhwm_kib"] is not None and x["peak_vmhwm_kib"] > 0
        expected = sum(int.from_bytes(bytes.fromhex(h)[:1], "big")
                       for h in archives[name]["expected_hex"]) * 6000
        assert x["answer_checksum"] == expected
    assert len(seen) == 36

    output = {}
    for name in archives:
        median = {}
        for arm in owners:
            rows = [r for r in records if r["arm"] == arm and r["profile"] == name]
            assert len(rows) == 6
            median[arm] = {
                "wall": statistics.median(r["range_wall_ns"] / 30000 for r in rows),
                "cpu": statistics.median(r["range_cpu_ns"] / 30000 for r in rows),
            }
        ratio_w = median["candidate"]["wall"] / median["baseline"]["wall"]
        ratio_c = median["candidate"]["cpu"] / median["baseline"]["cpu"]
        add_w = median["candidate"]["wall"] - median["baseline"]["wall"]
        s = d["summary"][name]
        for key, result in (("wall_ratio", ratio_w), ("cpu_ratio", ratio_c),
                            ("wall_ns_additional_per_call", add_w)):
            assert abs(s[key] - result) < 1e-8, (name, key, s[key], result)
        output[name] = {"wall_ratio": ratio_w, "cpu_ratio": ratio_c,
                        "wall_ns_additional_per_call": add_w}
    raw = output["raw"]
    expected = ("RAW_GUARD_PERF_DEBT_SIGNAL" if
                raw["wall_ratio"] >= 1.20 and raw["cpu_ratio"] >= 1.20 and
                raw["wall_ns_additional_per_call"] >= 500 else
                "NO_PREREGISTERED_RAW_DEBT_SIGNAL")
    assert expected == d["decision"], (expected, d["decision"])
    result = {"audit": "PASS", "source_exact": True, "observations": len(records),
              "identical_signed_inputs": True, "decision": expected,
              "computed": output, "product_promotion": False}
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
