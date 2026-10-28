#!/usr/bin/env python3
"""O218e independent source, wheel and raw-worker receipt referee.

Computes results without importing the code being measured. Corruptions must fail.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import statistics

SOURCE = {"reader": "b37b786966ac1506a0439567d4a58eea472d85f8",
          "validator": "fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8",
          "native_c": "a54f15181d9dbe667b9e8c9d52e927b09c80152f"}
PARENT = "fdd5b040dbbaeaac79f029c2ab5c58162ec894cd"
PREREG = "c65874a3c548016d7135727959214884eeb306c2"
PROFILES = ((65536, 1), (262144, 1), (65536, 256))
MODES = ("original", "fast", "direct", "abi3", "unguarded")
N_WORKERS = 2 * 2

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def close(actual: float, expected: float):
    if abs(actual-expected) > max(1e-8, abs(expected) * 1e-9):
        raise AssertionError(f"computed receipt differs: {actual} vs {expected}")

def audit(receipt: dict, folder: Path, check_disk: bool = True):
    if receipt["tier"] != "whole_installed_reader_research_not_product":
        raise AssertionError("unearned product tier")
    if receipt["parent"] != PARENT or receipt["prereg"] != PREREG or receipt["source"] != SOURCE:
        raise AssertionError("source or prereg identity drift")
    host = receipt["host"]
    if tuple(host["python_minor"]) not in ((3, 11), (3, 13)):
        raise AssertionError("unsupported interpreter")
    if receipt["wheel"]["wheel_name"].find("cp311-abi3-") < 0:
        raise AssertionError("not the stable ABI wheel")
    if receipt["semantics"]["inherited_cases"] < 19 or receipt["semantics"]["fuzz_cases"] != 2500 or len(receipt["semantics"]["named_cases"]) != 24:
        raise AssertionError("semantic control missing")
    if [tuple((x["count"], x["owners"])) for x in receipt["fixtures"]] != list(PROFILES):
        raise AssertionError("fixture selection drift")
    if sha(json.dumps(receipt["raw_workers"], sort_keys=True, separators=(",", ":")).encode()) != receipt.get("raw_workers_sha256"):
        raise AssertionError("raw-worker content digest mismatch")
    if len(receipt["raw_workers"]) != len(PROFILES)*len(MODES)*N_WORKERS:
        raise AssertionError("missing workers")
    if check_disk:
        actual_binary = folder / receipt["direct_native"]["artifact"]
        if sha(actual_binary.read_bytes()) != receipt["direct_native"]["binary_sha256"]:
            raise AssertionError("native C artifact bytes changed")
        wheel = next((folder.parent.parent / "research" / "o218d_abi3_package" / "dist").glob("*.whl"), None)
        if wheel and sha(wheel.read_bytes()) != receipt["wheel"]["wheel_sha256"]:
            raise AssertionError("wheel bytes changed")
    seen = Counter()
    for w in receipt["raw_workers"]:
        key = (w["count"], w["owners"], w["mode"], w["cycle"])
        seen[key] += 1
        if tuple(w["python_minor"]) != tuple(host["python_minor"]) or w["source"] != SOURCE:
            raise AssertionError("worker source/python mismatch")
        if w["abi3_binary_sha256"] != receipt["wheel"]["installed_binary_sha256"]:
            raise AssertionError("abi3 binary identity changed")
        if w["direct_binary_sha256"] != receipt["direct_native"]["binary_sha256"]:
            raise AssertionError("direct C identity changed")
        fixture = next((r for r in receipt["fixtures"] if (r["count"],r["owners"]) == key[:2]), None)
        if not fixture or w["archive_sha256"] != fixture["archive_sha256"]:
            raise AssertionError("source archive identity changed")
        if w["fresh_process_wall_ns"] <= 0 or len(w["samples"]) != 5:
            raise AssertionError("worker process/samples absent")
        if any(type(sample["wall_ns"]) is not int or sample["wall_ns"] <= 0 or
               type(sample["cpu_ns"]) is not int or sample["cpu_ns"] < 0
               for sample in w["samples"]):
            raise AssertionError("invalid raw timing")
    for n, owners in PROFILES:
        for mode in MODES:
            for cycle in range(2):
                if seen[(n,owners,mode,cycle)] != 2:
                    raise AssertionError("not two workers per cycle/arm")
    if len(receipt["summary"]) != len(PROFILES):
        raise AssertionError("wrong profile summaries")
    for summary in receipt["summary"]:
        count, owners = summary["count"], summary["owners"]
        if (count, owners) not in PROFILES:
            raise AssertionError("unregistered profile")
        for mode in MODES:
            workers = [x for x in receipt["raw_workers"]
                       if (x["count"],x["owners"],x["mode"]) == (count,owners,mode)]
            row = summary["by_mode"][mode]
            med_wall = statistics.median(statistics.median(s["wall_ns"] for s in w["samples"]) for w in workers) / 1e6
            med_cpu = statistics.median(statistics.median(s["cpu_ns"] for s in w["samples"]) for w in workers) / 1e6
            med_start = statistics.median(w["fresh_process_wall_ns"] for w in workers) / 1e6
            close(row["median_constructor_wall_ms"], med_wall)
            close(row["median_constructor_cpu_ms"], med_cpu)
            close(row["median_fresh_process_wall_ms"], med_start)
            if row["zero_cpu_samples"] != sum(s["cpu_ns"] == 0 for w in workers for s in w["samples"]):
                raise AssertionError("CPU quantization falsified")
            rss = [w["vmhwm_bytes"] for w in workers]
            med_rss = statistics.median(rss) if all(x is not None for x in rss) else None
            if row["median_vmhw_bytes_linux_only"] != med_rss:
                raise AssertionError("peak memory receipt altered")
        med = {m:summary["by_mode"][m]["median_constructor_wall_ms"] for m in MODES}
        close(summary["safe_python_over_abi3"], med["fast"]/med["abi3"])
        close(summary["abi3_over_direct"], med["abi3"]/med["direct"])
        close(summary["abi3_over_unsafe"], med["abi3"]/med["unguarded"])
    focus = [x for x in receipt["summary"] if x["owners"] == 1 and x["count"] in (65536,262144)]
    strong = all(x["safe_python_over_abi3"] >= 2 and x["abi3_over_direct"] <= 2 for x in focus)
    negative = any(x["safe_python_over_abi3"] <= 1 for x in focus)
    decision = ("ABI3_FULL_READER_STRONG_HOST_PASS" if strong else
                "ABI3_FULL_READER_ECONOMIC_NEGATIVE" if negative else
                "ABI3_FULL_READER_INSUFFICIENT_OR_AMBIGUOUS")
    if receipt["decision"] != decision:
        raise AssertionError("decision not derivable from raw evidence")
    if check_disk:
        archive_root = folder.parent / "archives"
        for item in receipt["fixtures"]:
            f = archive_root / item["archive"]
            if f.stat().st_size != item["archive_bytes"] or sha(f.read_bytes()) != item["archive_sha256"]:
                raise AssertionError("physical archive mutated")
        lines = [json.loads(x) for x in (folder / "raw-workers.jsonl").read_text().splitlines() if x.strip()]
        if lines != receipt["raw_workers"]:
            raise AssertionError("JSONL receipts disagree with aggregate")
    return {"decision": decision, "host": host, "raw_workers": len(receipt["raw_workers"]),
            "raw_samples": sum(len(w["samples"]) for w in receipt["raw_workers"]),
            "median_reconstructed": True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    folder = args.directory.resolve()
    source = json.loads((folder / "result.json").read_text())
    result = audit(source, folder)
    forgeries = [
        lambda x: x["raw_workers"][0]["samples"][0].__setitem__("wall_ns", x["raw_workers"][0]["samples"][0]["wall_ns"] + 99999),
        lambda x: x["source"].__setitem__("reader", "0"*40),
        lambda x: x["wheel"].__setitem__("installed_binary_sha256", "0"*64),
        lambda x: x["summary"][0].__setitem__("safe_python_over_abi3", x["summary"][0]["safe_python_over_abi3"]+1),
        lambda x: x["raw_workers"].pop(),
    ]
    for patch in forgeries:
        bad = copy.deepcopy(source)
        patch(bad)
        try:
            audit(bad, folder, check_disk=False)
        except (AssertionError, ValueError, KeyError, TypeError):
            pass
        else:
            raise AssertionError("forged scientific receipt accepted")
    result["forgeries_rejected"] = len(forgeries)
    (folder / "referee.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("O218E_INDEPENDENT_REFEREE_PASS " + json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
