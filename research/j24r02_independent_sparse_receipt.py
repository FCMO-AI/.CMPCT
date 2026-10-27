"""Independent J24R02 referee for PR #584's unchanged source-exact ABBA receipt.

Recomputes groups, provenance, ABBA order, and both positive/negative claims.
Not the instrument under test. A malformed or partial result is a hard evidence failure.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

BASE_REF = "c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
CANDIDATE_REF = "70336307312b5b277f0885c0057d2cddab0aefc1"
COUNTS = (1, 4, 4096, 65536)
METRICS = ("open_wall_ms", "open_cpu_ms", "range_batch_wall_ms", "range_batch_cpu_ms")


def checked(condition, message):
    if not condition:
        raise AssertionError(message)


def source_digest(repo: Path, commit: str) -> str:
    source = subprocess.check_output(
        ("git", "show", f"{commit}:src/cmpct/reader.py"), cwd=repo
    )
    return hashlib.sha256(source.replace(b"\r\n", b"\n")).hexdigest()


def independently_audit(raw_path: Path, repo: Path, base_site: Path, candidate_site: Path):
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    checked(payload["schema"] == "j24r01-v1", "wrong protocol")
    raw = payload["observations"]
    checked(len(raw) == 48, f"expected 48 physical subprocess observations, got {len(raw)}")
    expected_sha = {
        "baseline": source_digest(repo, BASE_REF),
        "candidate": source_digest(repo, CANDIDATE_REF),
    }
    sites = {"baseline": base_site.resolve(), "candidate": candidate_site.resolve()}
    for count in COUNTS:
        manifest = payload["fixture_manifest"][str(count)]
        checked(manifest["wire_bytes"] > 0 and manifest["logical_bytes"] > 0,
                f"invalid archived/logical bytes count={count}")
        for field in ("wire_sha256", "logical_sha256"):
            value = manifest[field]
            checked(isinstance(value, str) and len(value) == 64
                    and all(ch in "0123456789abcdef" for ch in value),
                    f"bad {field} for {count}")

    grouped = {str(count): {} for count in COUNTS}
    for index, record in enumerate(raw):
        mode = record["version"]
        count = record["extent_count"]
        iteration = record["iteration"]
        checked(mode in sites and count in COUNTS and iteration in (0, 1, 2),
                f"invalid mode/count/round at record {index}")
        checked(record["reader_source_sha256"] == expected_sha[mode],
                f"actual installed {mode} module does not match Git source")
        module_path = Path(record["reader_module"]).resolve()
        checked(module_path.is_relative_to(sites[mode]),
                f"workspace/global import leakage: {module_path} != {sites[mode]}")
        fixture = payload["fixture_manifest"][str(count)]
        checked(record["archive_bytes"] == fixture["wire_bytes"]
                and record["logical_bytes"] == fixture["logical_bytes"],
                "unequal physical input or logical truth")
        checked(record["range_checks"] == (531 if count == 1 else 533),
                "dropped or shortened correctness queries")
        for metric in METRICS:
            value = record[metric]
            checked(type(value) in (float, int) and math.isfinite(value) and value >= 0,
                    f"invalid {metric}: {value!r}")
        checked(record["open_wall_ms"] > 0 and record["range_batch_wall_ms"] > 0,
                "missing timing")
    for count in COUNTS:
        for iteration in (0, 1, 2):
            seq = [
                o["version"] for o in raw
                if o["extent_count"] == count and o["iteration"] == iteration
            ]
            expected = ["baseline", "candidate", "candidate", "baseline"] \
                if iteration % 2 == 0 else ["candidate", "baseline", "baseline", "candidate"]
            checked(seq == expected, f"ABBA sequence/attrition mismatch: {count}/{iteration} {seq}")
        for mode in ("baseline", "candidate"):
            samples = [o for o in raw if o["extent_count"] == count and o["version"] == mode]
            checked(len(samples) == 6, f"missing paired trials count={count} mode={mode}")
            medians = {metric: statistics.median(o[metric] for o in samples)
                       for metric in METRICS}
            for metric in METRICS:
                claimed = payload["medians"][str(count)][mode][metric]
                checked(type(claimed) in (float, int) and math.isclose(
                    medians[metric], claimed, rel_tol=1e-10, abs_tol=1e-10),
                    f"median mismatch: {count}/{mode}/{metric}")
            grouped[str(count)][mode] = medians

    speedup = (
        grouped["65536"]["baseline"]["range_batch_wall_ms"]
        / grouped["65536"]["candidate"]["range_batch_wall_ms"]
    )
    checked(math.isclose(speedup, payload["late_65536_speedup"],
                         rel_tol=1e-10, abs_tol=1e-10),
            "high-E headline does not match original subprocess observations")
    expected_decision = (
        "SELECTIVE_HEADROOM_CONFIRMED" if speedup >= 10
        else "SELECTIVE_HEADROOM_NOT_CONFIRMED"
    )
    checked(payload["decision"] == expected_decision, "instrument decision mismatch")

    losses = []
    for count in (1, 4):
        for metric in ("range_batch_wall_ms", "range_batch_cpu_ms"):
            base = grouped[str(count)]["baseline"][metric]
            new = grouped[str(count)]["candidate"][metric]
            delta = new - base
            if new > base * 1.10 and delta > 0.1:
                losses.append({"count": count, "metric": metric,
                               "extra_ms": delta, "ratio": new / base})
    classification = (
        "SELECTIVE_HEADROOM_CONFIRMED_SCOPED"
        if speedup >= 10 else "SELECTIVE_HEADROOM_NOT_CONFIRMED"
    )
    return {
        "schema": "j24r02-independent-audit-v1",
        "decision": classification,
        "source_verified": expected_sha,
        "complete_abba": True,
        "raw_observations": len(raw),
        "source_module_outside_checkout": True,
        "high_extent_range_wall_speedup": speedup,
        "small_extent_promotion_debt": losses,
        "medians": grouped,
        "limitations": [
            "Only the original inherited selected-range workload was measured",
            "Linux-only timing and RSS; portability courts are separate",
            "No full release parity, no overwrite/inode security or random host workloads",
        ],
    }


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: audit.py results.json repo base-site candidate-site audit.json")
    raw, repo, base, candidate, out = (Path(v) for v in sys.argv[1:])
    report = independently_audit(raw, repo, base, candidate)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("J24R02_INDEPENDENT_AUDIT=PASS", flush=True)
    print("J24R02_DECISION=" + report["decision"], flush=True)
    print("J24R02_HIGH_EXTENT_SPEEDUP=" +
          format(report["high_extent_range_wall_speedup"], ".3f"), flush=True)
    print("J24R02_SMALL_E_DEBT_CASES=" +
          str(len(report["small_extent_promotion_debt"])), flush=True)


if __name__ == "__main__":
    main()
