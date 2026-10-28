#!/usr/bin/env python3
"""Independent stdlib J24B03-M receipt referee: no CMPCT or instrument import."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics

SCALES = (1, 4096, 65536)
ORDER = ("baseline", "candidate", "candidate", "baseline")
METRICS = ("open_wall_ns", "open_cpu_ns", "read_wall_ns", "read_cpu_ns",
           "session_wall_ns", "session_cpu_ns", "preflight_wall_ns", "preflight_cpu_ns",
           "peak_vmhwm_session_kib", "peak_vmhwm_total_kib")
PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(d):
    assert d["experiment"] == "J24B03-M"
    assert d["rung"] == "authentic r24 source-exact direct session ABBA"
    assert d["design"] == {"scales": [1, 4096, 65536], "order": list(ORDER), "rounds": 3}
    source = d["source_sha256"]
    assert set(source) == {"baseline", "candidate"} and source["baseline"] != source["candidate"]
    for arm, root in (("baseline", Path("frozen-baseline/src")), ("candidate", Path("src"))):
        assert set(source[arm]) == {"reader", "validation"}
        assert digest(root / "cmpct/reader.py") == source[arm]["reader"]
        assert digest(root / "cmpct/validation.py") == source[arm]["validation"]
    archives = d["archives"]
    assert [x["n"] for x in archives] == list(SCALES)
    by_n = {x["n"]: x for x in archives}
    for a in archives:
        raw = Path(a["path"]).read_bytes()
        assert raw.startswith(b"CMPCT24\x00")
        assert hashlib.sha256(raw).hexdigest() == a["archive_sha256"]
        assert a["bytes"] == len(raw) and a["name"] == str(a["n"])
        assert a["expected_checksum"] == sum(PAYLOAD[(i * 7) % 121] for i in range(a["n"]))
    rows = d["rows"]
    assert len(rows) == 36
    unique = set()
    for row in rows:
        arm, n, rnd, slot = row["arm"], row["profile"], row["round"], row["order_slot"]
        assert n in SCALES and arm in source and 0 <= rnd < 3 and 0 <= slot < 4
        assert arm == ORDER[slot]
        key = (n, rnd, slot)
        assert key not in unique
        unique.add(key)
        a = by_n[n]
        assert row["archive_sha256"] == a["archive_sha256"]
        assert row["physical_archive_bytes"] == a["bytes"]
        assert row["checksum"] == a["expected_checksum"]
        assert row["files"] == n and row["physical_blobs"] == 1
        root = Path("frozen-baseline/src" if arm == "baseline" else "src").resolve()
        assert Path(row["reader_path"]).resolve() == root / "cmpct/reader.py"
        assert Path(row["validation_path"]).resolve() == root / "cmpct/validation.py"
        assert row["reader_sha256"] == source[arm]["reader"]
        assert row["validation_sha256"] == source[arm]["validation"]
        for metric in METRICS:
            assert type(row[metric]) in (int, float) and row[metric] > 0
        assert row["peak_vmhwm_total_kib"] >= row["peak_vmhwm_session_kib"]
        assert row["session_wall_ns"] >= row["open_wall_ns"]
        assert row["session_cpu_ns"] >= row["open_cpu_ns"]
    assert len(unique) == 36

    computed = {}
    for n in SCALES:
        pair = {}
        for arm in source:
            subset = [x for x in rows if x["profile"] == n and x["arm"] == arm]
            assert len(subset) == 6
            pair[arm] = {m: statistics.median(x[m] for x in subset) for m in METRICS}
        ratio = {m: pair["candidate"][m] / pair["baseline"][m] for m in METRICS}
        delta = {m: pair["candidate"][m] - pair["baseline"][m] for m in METRICS}
        recorded = d["summary"][str(n)]
        for name, values in (("ratio", ratio), ("delta", delta)):
            for m, val in values.items():
                assert abs(recorded[name][m] - val) <= max(1e-8, abs(val) * 1e-10)
        for arm in source:
            for m, val in pair[arm].items():
                assert abs(recorded["arms"][arm][m] - val) <= max(1e-8, abs(val) * 1e-10)
        computed[n] = (ratio, delta)
    session = preflight = False
    for n in (4096, 65536):
        ratio, delta = computed[n]
        if ((ratio["session_wall_ns"] >= 1.10 and ratio["session_cpu_ns"] >= 1.10
             and delta["session_wall_ns"] >= 25_000_000
             and delta["session_cpu_ns"] >= 25_000_000)
            or delta["peak_vmhwm_session_kib"] >= 8192):
            session = True
        if (ratio["preflight_wall_ns"] >= 1.15 and ratio["preflight_cpu_ns"] >= 1.15
            and delta["preflight_wall_ns"] >= 50_000_000
            and delta["preflight_cpu_ns"] >= 50_000_000):
            preflight = True
    verdict = ("MATERIAL_DIRECT_SESSION_AND_PREFLIGHT_DEBT" if session and preflight else
               "MATERIAL_DIRECT_SESSION_DEBT" if session else
               "MATERIAL_DIRECT_PREFLIGHT_DEBT" if preflight else
               "NO_PREREGISTERED_MACRO_DEBT_SIGNAL")
    assert d["decision"] == verdict
    return {"audit": "PASS", "source_exact": True, "n_processes": len(rows),
            "decision": verdict, "ratios_at_65536": computed[65536][0],
            "deltas_at_65536": computed[65536][1], "product_release_credit": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    result = audit(data)
    attacks = [
        ("checksum", lambda d: d["rows"][0].__setitem__("checksum", 0)),
        ("identity", lambda d: d["rows"][1].__setitem__("reader_sha256", "0" * 64)),
        ("order", lambda d: d["rows"][2].__setitem__("order_slot", 0)),
    ]
    for label, alter in attacks:
        forged = copy.deepcopy(data)
        alter(forged)
        try:
            audit(forged)
        except (AssertionError, KeyError, ValueError):
            pass
        else:
            raise AssertionError(f"forged {label} receipt accepted")
    result["forged_receipts_rejected"] = len(attacks)
    print(json.dumps(result, sort_keys=True))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
