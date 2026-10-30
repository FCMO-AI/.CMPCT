#!/usr/bin/env python3
"""J24G73 detached receipt arithmetic/identity referee; imports NO CMPCT modules."""
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

EXPECTED = {"delete": {"del": 63, "put": 0, "ren": 0, "members": 2048},
            "mixed": {"del": 21, "put": 21, "ren": 21, "members": 118}}


def verify(result, directory, head):
    assert result["schema"] == "cmpct-j24g73-research-v1"
    assert result["source"]["head"] == head
    assert result["source"]["parent"] == "41cd7f88d9fede55a495f36e78126b26eff85880"
    assert result["source"]["prereg"] == "47098cb201bf2424a436d197d7bd09162d872b78"
    assert result["status"] == "PASS" and result["product_credit"] == 0
    assert set(result["cases"]) == set(EXPECTED)
    for family, expected in EXPECTED.items():
        entry = result["cases"][family]
        physical = entry["physical"]
        archive = directory / (family + "-physical.cmpct")
        assert archive.exists() and archive.stat().st_size == physical["archive_bytes"]
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == physical["archive_sha256"]
        assert physical["footers"] == 64
        assert physical["ops"] == {key: expected[key] for key in ("del", "put", "ren")}
        assert physical["members"] == physical["preflight"] == expected["members"]
        assert len(physical["index_sha256"]) == 64
        for mode, item in entry["recovery"].items():
            assert mode in {"bad-footer-sha", "truncated-footer"}
            assert item["recovered_depth"] == 62 and len(item["index_sha256"]) == 64
        assert set(entry["recovery"]) == {"bad-footer-sha", "truncated-footer"}
        observations = entry["benchmark"]["samples"]
        assert len(observations) == 64
        observed = {"reference": [], "factored": []}
        for block in range(8):
            for order in ("ABBA", "BAAB"):
                rows = [x for x in observations if x["block"] == block and x["order"] == order]
                assert "".join("A" if x["variant"] == "reference" else "B" for x in rows) == order
        for item in observations:
            assert item["variant"] in observed
            assert isinstance(item["wall_ns"], int) and 0 < item["wall_ns"] < 10**11
            assert isinstance(item["cpu_ns"], int) and 0 <= item["cpu_ns"] < 10**11
            observed[item["variant"]].append(item)
        assert all(len(v) == 32 for v in observed.values())
        for metric in ("wall_ns", "cpu_ns"):
            for variant, rows in observed.items():
                measured = statistics.median(x[metric] for x in rows)
                claimed = entry["benchmark"]["medians"][metric][variant]
                assert math.isclose(measured, claimed, abs_tol=0, rel_tol=1e-12)
        medians = entry["benchmark"]["medians"]["wall_ns"]
        ratio = medians["reference"] / medians["factored"]
        assert math.isclose(ratio, entry["benchmark"]["wall_speedup"], rel_tol=1e-12)
        trace = entry["benchmark"]["tracemalloc_peak_bytes"]
        assert all(isinstance(trace[v], int) and trace[v] > 0 for v in observed)
        for variant, samples in entry["rss_probes"].items():
            assert variant in observed and len(samples) == 3
            assert all(isinstance(s["rss_bytes"], int) and s["rss_bytes"] > 0 for s in samples)
            assert all(isinstance(s["peak_rss_bytes"], int) and s["peak_rss_bytes"] > 0 for s in samples)
    assessment = result["local_mechanism_result"]
    b = result["cases"]["delete"]["benchmark"]
    delta = b["tracemalloc_peak_bytes"]["factored"] - b["tracemalloc_peak_bytes"]["reference"]
    assert math.isclose(assessment["delete_reader_speedup"], b["wall_speedup"], rel_tol=1e-12)
    assert assessment["traced_peak_delta_bytes"] == delta
    assert assessment["meets_local_threshold"] is (b["wall_speedup"] >= 2.0 and delta <= 2*1024*1024)
    return {"host": result["host"], "head": head, "decision": "AUDIT_PASS",
            "delete_wall_speedup": assessment["delete_reader_speedup"],
            "delete_peak_delta": delta}


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: referee RESULT_JSON EVIDENCE_DIR EXPECTED_HEAD")
    path, directory, head = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    result = json.loads(path.read_text())
    accepted = verify(result, directory, head)
    # Sensitivity controls: reject arithmetic laundering, source drift, missing
    # physical bytes, manufactured pass and false recovery.
    variants = []
    a = copy.deepcopy(result)
    a["cases"]["delete"]["benchmark"]["medians"]["wall_ns"]["factored"] *= 0.5
    variants.append(a)
    a = copy.deepcopy(result)
    a["cases"]["mixed"]["physical"]["archive_sha256"] = "0"*64
    variants.append(a)
    a = copy.deepcopy(result)
    a["cases"]["delete"]["benchmark"]["samples"][0]["variant"] = "factored"
    variants.append(a)
    a = copy.deepcopy(result)
    a["status"] = "FAIL"
    variants.append(a)
    a = copy.deepcopy(result)
    a["cases"]["mixed"]["recovery"]["bad-footer-sha"]["recovered_depth"] = 63
    variants.append(a)
    a = copy.deepcopy(result)
    a["product_credit"] = 1
    variants.append(a)
    for i, tampered in enumerate(variants):
        try:
            verify(tampered, directory, head)
        except (AssertionError, KeyError, TypeError, ZeroDivisionError):
            continue
        raise AssertionError("detached referee accepted tamper " + str(i))
    output = directory / "j24g73-referee.json"
    output.write_text(json.dumps({**accepted, "mutations_rejected": len(variants)},
                                 indent=2, sort_keys=True) + "\n")
    print("J24G73_DETACHED_AUDIT", json.dumps(accepted, sort_keys=True),
          "TAMPERS_REJECTED", len(variants))


if __name__ == "__main__":
    main()
