#!/usr/bin/env python3
"""O8: held-out exact-file public-C grouped-vs-serial court; NEVER a shipping extractor."""
from __future__ import annotations

import hashlib
import json
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_batch_abi import source_bytes

REPS = 4
COHORTS = (
    "related_64", "related_256", "independent_256",
    "mixed_256", "duplicates_256", "singleton",
)


def noise(n: int, seed: str) -> bytes:
    """Stable high-entropy bytes with a cohort/member-independent seed namespace."""
    return b"".join(
        hashlib.sha256(f"cmpct-o8-{seed}-{j}".encode("ascii")).digest()
        for j in range((n + 31) // 32)
    )[:n]


def population(cohort: str) -> dict[str, bytes]:
    if cohort == "related_64":
        return {f"related-{i:04d}.dat": source_bytes(i) for i in range(64)}
    if cohort == "related_256":
        return {f"related-{i:04d}.dat": source_bytes(i) for i in range(256)}
    if cohort == "independent_256":
        return {f"independent-{i:04d}.dat": noise(768, f"independent-{i}")
                for i in range(256)}
    if cohort == "mixed_256":
        data = {f"rel-{i:04d}.dat": source_bytes(i + 128) for i in range(128)}
        data.update({f"ind-{i:04d}.dat": noise(768, f"mixed-{i}") for i in range(128)})
        data["unpacked-noise.bin"] = noise(70_000, "mixed-large")
        return data
    if cohort == "duplicates_256":
        return {f"duplicate-{i:04d}.dat": source_bytes(0) for i in range(256)}
    if cohort == "singleton":
        return {"singleton-noise.bin": noise(70_000, "singleton")}
    raise AssertionError(f"unregistered cohort {cohort}")


def child_cpu() -> float:
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_trial(binary: Path, archive: Path, dest: Path, mode: str,
              cohort: str, round_no: int, trial_no: int,
              expected: dict[str, str], bytes_expected: int) -> dict:
    dest.mkdir()
    cpu0 = child_cpu()
    start = time.perf_counter_ns()
    run = subprocess.run(
        [str(binary), str(archive), str(dest), mode],
        text=True, capture_output=True, check=False,
    )
    wall_ms = (time.perf_counter_ns() - start) / 1e6
    cpu_ms = (child_cpu() - cpu0) * 1e3
    if run.returncode != 0:
        raise AssertionError(
            f"{cohort} {mode} exit={run.returncode}\nstdout={run.stdout}\nstderr={run.stderr}"
        )
    reply = json.loads(run.stdout.strip())
    if reply["mode"] != mode or reply["members"] != len(expected):
        raise AssertionError((cohort, mode, "member census", reply))
    if reply["decoded_bytes"] != bytes_expected:
        raise AssertionError((cohort, mode, "decoded byte census", reply))
    if mode == "serial":
        assert reply["batch_count"] == reply["batched_members"] == 0
        assert reply["fallback"] == len(expected)
    else:
        assert reply["fallback"] + reply["batched_members"] == len(expected)
        assert (reply["batch_count"] == 0) == (reply["batched_members"] == 0)
        assert reply["batch_count"] <= reply["batched_members"] // 2
        if cohort == "singleton":
            assert reply["batch_count"] == reply["batched_members"] == 0
    produced = {p.name: hash_file(p) for p in dest.iterdir() if p.is_file()}
    actual_tree = [p.name for p in dest.iterdir()]
    if len(actual_tree) != len(expected) or produced != expected:
        raise AssertionError(
            (cohort, mode, "independent exact-set/hash mismatch",
             sorted(set(expected) - set(produced))[:5],
             sorted(set(produced) - set(expected))[:5])
        )
    return dict(
        cohort=cohort, round=round_no, trial=trial_no, mode=mode,
        wall_ms=wall_ms, child_cpu_ms=cpu_ms, **reply,
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tests/native_pack_heldout_o8.py C_CONSUMER RECEIPT_JSON")
    binary = Path(sys.argv[1]).resolve()
    receipt = Path(sys.argv[2]).resolve()
    if not binary.is_file():
        raise AssertionError(f"missing exact public-C consumer {binary}")
    result = {
        "schema": "cmpct-native-public-c-heldout-o8-v1",
        "cohorts": {},
        "reps_per_cohort": REPS,
        "source_base": "PR327@030bd50aff682592f67eba1dc5376b83bfe83fae",
        "scope": "root-level test-only C consumer; no production filesystem-handler claims",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-native-o8-") as tmp:
        home = Path(tmp)
        for cohort in COHORTS:
            files = population(cohort)
            assert all("/" not in n and "\\" not in n and not n.startswith(".") for n in files)
            source = home / cohort / "src"
            source.mkdir(parents=True)
            expected = {}
            for name, data in sorted(files.items()):
                (source / name).write_bytes(data)
                expected[name] = hashlib.sha256(data).hexdigest()
            bytes_expected = sum(map(len, files.values()))
            archive = source.parent / "archive.cmpct"
            Builder(source, workers=1, reproducible=True).build(archive)
            archived_hash = hash_file(archive)
            rows = []
            for round_no in range(REPS):
                order = ("serial", "group", "group", "serial") if round_no % 2 == 0 else (
                    "group", "serial", "serial", "group"
                )
                for trial_no, mode in enumerate(order):
                    dest = source.parent / f"extract-{round_no}-{trial_no}-{mode}"
                    rows.append(run_trial(
                        binary, archive, dest, mode, cohort, round_no, trial_no,
                        expected, bytes_expected,
                    ))
                    if hash_file(archive) != archived_hash:
                        raise AssertionError((cohort, "immutable archive modified"))
            def med(mode: str, key: str) -> float:
                return statistics.median(row[key] for row in rows if row["mode"] == mode)
            baseline = med("serial", "wall_ms")
            candidate = med("group", "wall_ms")
            baseline_cpu = med("serial", "child_cpu_ms")
            candidate_cpu = med("group", "child_cpu_ms")
            grp = [row for row in rows if row["mode"] == "group"]
            unique_schedules = {(row["batched_members"], row["fallback"], row["batch_count"])
                                for row in grp}
            assert len(unique_schedules) == 1, (cohort, "non-deterministic batching", unique_schedules)
            bad = candidate > baseline * 1.10 and candidate - baseline > 5.0
            outcome = {
                "source_archive_sha256": archived_hash,
                "source_archive_bytes": archive.stat().st_size,
                "logical_bytes": bytes_expected,
                "members": len(expected),
                "logical_manifest_sha256": hashlib.sha256(
                    json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "group_schedule": {
                    "batched_members": grp[0]["batched_members"],
                    "fallback_members": grp[0]["fallback"],
                    "batch_count": grp[0]["batch_count"],
                },
                "serial_wall_median_ms": baseline,
                "group_wall_median_ms": candidate,
                "wall_ratio_serial_over_group": baseline / candidate if candidate else None,
                "serial_child_cpu_median_ms": baseline_cpu,
                "group_child_cpu_median_ms": candidate_cpu,
                "serial_rss_median_kib": med("serial", "rss_kib"),
                "group_rss_median_kib": med("group", "rss_kib"),
                "material_group_regression": bad,
                "interpretation": "NARROW_ADMISSION_DEBT" if bad else "EXACT_NO_MATERIAL_REGRESSION_OBSERVED",
                "raw_abba": rows,
            }
            result["cohorts"][cohort] = outcome
            print(json.dumps({
                "cohort": cohort, "source_archive_bytes": outcome["source_archive_bytes"],
                "group_schedule": outcome["group_schedule"],
                "wall_ratio_serial_over_group": outcome["wall_ratio_serial_over_group"],
                "material_group_regression": bad,
                "status": "BYTE_EXACT", "observations": len(rows),
            }, sort_keys=True), flush=True)
    result["summary"] = {
        "status": "O8_COMPLETE_WITH_NEGATIVES_PRESERVED",
        "cohorts": len(COHORTS),
        "total_extractions": len(COHORTS) * REPS * 4,
        "cohorts_with_material_group_regression": [
            name for name, rec in result["cohorts"].items()
            if rec["material_group_regression"]
        ],
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
