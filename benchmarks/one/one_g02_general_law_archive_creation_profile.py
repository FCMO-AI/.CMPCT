from __future__ import annotations

"""Fresh-process creation/RSS falsifier for the automatic general Law archive seed.

Frozen by ONE_G02_GENERAL_LAW_ARCHIVE_CREATION_PROFILE_PREREG_2026-09-10.md.
Uses transfer fixtures only and never imports the Genesis workload generators.
"""

from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

ROUNDS = 9
PRODUCTIVE = ("exact-copy-1m", "add8-1m", "mixed-8x512k")


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write_case(root: Path, name: str, files: list[tuple[str, bytes]]) -> Path:
    case = root / name
    case.mkdir(parents=True)
    for rel, payload in files:
        path = case / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return case


def _make_cases(root: Path) -> dict[str, Path]:
    one_mib = 1024 * 1024
    half = 512 * 1024
    a = _hash_stream(one_mib, b"profile-a")
    b = _hash_stream(one_mib, b"profile-b")
    mixed_base = _hash_stream(half, b"mixed-base")
    mixed_add = bytes(((x + 37) & 0xFF) for x in mixed_base)
    mixed_xor = bytes((x ^ 0xA5) for x in mixed_add)
    return {
        "unrelated-1m": _write_case(root, "unrelated-1m", [("a.bin", a), ("b.bin", b)]),
        "exact-copy-1m": _write_case(root, "exact-copy-1m", [("a.bin", a), ("b.bin", a)]),
        "add8-1m": _write_case(
            root,
            "add8-1m",
            [("a.bin", a), ("b.bin", bytes(((x + 37) & 0xFF) for x in a))],
        ),
        "mixed-8x512k": _write_case(
            root,
            "mixed-8x512k",
            [
                ("00-base.bin", mixed_base),
                ("01-copy.bin", mixed_base),
                ("02-add.bin", mixed_add),
                ("03-xor.bin", mixed_xor),
                ("04-fill.bin", b"Q" * half),
                ("05-random.bin", _hash_stream(half, b"mixed-random")),
                ("06-random.bin", _hash_stream(half, b"mixed-random-2")),
                ("07-random.bin", _hash_stream(half, b"mixed-random-3")),
            ],
        ),
    }


def _rss_bytes() -> int:
    # Linux reports KiB. The dedicated hosted lane is Linux-only by preregistration.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _verify(case: Path, wire: bytes) -> None:
    from experiments.one.authenticated_archive_envelope import open_authenticated_archive

    opened = open_authenticated_archive(wire)
    for path in sorted(p for p in case.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(case).as_posix()
        if opened.read_file(rel) != path.read_bytes():
            raise AssertionError(f"round-trip mismatch for {rel}")


def _worker(arm: str, case: Path) -> dict:
    if arm == "candidate":
        from experiments.one.general_law_archive import build_general_law_archive
        build = build_general_law_archive
    elif arm == "baseline":
        from experiments.one.authenticated_archive_envelope import build_authenticated_archive
        build = build_authenticated_archive
    else:
        raise ValueError(arm)

    c0 = time.process_time_ns()
    w0 = time.perf_counter_ns()
    wire, stats = build(case)
    wall_ns = time.perf_counter_ns() - w0
    cpu_ns = time.process_time_ns() - c0
    peak_rss_bytes = _rss_bytes()
    _verify(case, wire)
    payload = {
        "arm": arm,
        "case": case.name,
        "build_cpu_ns": cpu_ns,
        "build_wall_ns": wall_ns,
        "peak_rss_bytes": peak_rss_bytes,
        "wire_bytes": len(wire),
        "wire_sha256": sha256(wire).hexdigest(),
        "stats": asdict(stats),
        "roundtrip_exact": True,
    }
    return payload


def _launch(arm: str, case: Path) -> tuple[dict, int]:
    t0 = time.perf_counter_ns()
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_g02_general_law_archive_creation_profile", "--worker", arm, "--case", str(case)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    launch_ns = time.perf_counter_ns() - t0
    payload = json.loads(proc.stdout)
    return payload, launch_ns


def _median(samples: list[dict], field: str) -> float:
    return float(statistics.median(float(row[field]) for row in samples))


def _summarize(name: str, candidate: list[dict], baseline: list[dict], launch_c: list[int], launch_b: list[int]) -> dict:
    c_cpu = _median(candidate, "build_cpu_ns")
    b_cpu = _median(baseline, "build_cpu_ns")
    c_wall = _median(candidate, "build_wall_ns")
    b_wall = _median(baseline, "build_wall_ns")
    c_rss = _median(candidate, "peak_rss_bytes")
    b_rss = _median(baseline, "peak_rss_bytes")
    stored_ratio = candidate[0]["wire_bytes"] / baseline[0]["wire_bytes"]
    paired_cpu = [c["build_cpu_ns"] / b["build_cpu_ns"] for c, b in zip(candidate, baseline, strict=True)]
    return {
        "case": name,
        "candidate": candidate,
        "baseline": baseline,
        "candidate_median_build_cpu_ns": c_cpu,
        "baseline_median_build_cpu_ns": b_cpu,
        "build_cpu_ratio": c_cpu / b_cpu,
        "candidate_median_build_wall_ns": c_wall,
        "baseline_median_build_wall_ns": b_wall,
        "build_wall_ratio": c_wall / b_wall,
        "candidate_median_peak_rss_bytes": c_rss,
        "baseline_median_peak_rss_bytes": b_rss,
        "peak_rss_ratio": c_rss / b_rss,
        "stored_ratio": stored_ratio,
        "candidate_wire_bytes": candidate[0]["wire_bytes"],
        "baseline_wire_bytes": baseline[0]["wire_bytes"],
        "worst_paired_cpu_ratio": max(paired_cpu),
        "candidate_median_process_launch_elapsed_ns": float(statistics.median(launch_c)),
        "baseline_median_process_launch_elapsed_ns": float(statistics.median(launch_b)),
        "candidate_wire_deterministic": len({row["wire_sha256"] for row in candidate}) == 1,
        "baseline_wire_deterministic": len({row["wire_sha256"] for row in baseline}) == 1,
        "wire_byte_identical": candidate[0]["wire_sha256"] == baseline[0]["wire_sha256"],
    }


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-general-profile-") as td:
        cases = _make_cases(Path(td))
        rows = []
        # Untimed sanity/import launches are deliberately discarded from measured samples.
        for case in cases.values():
            _launch("baseline", case)
            _launch("candidate", case)

        for name, case in cases.items():
            candidate: list[dict] = []
            baseline: list[dict] = []
            launch_c: list[int] = []
            launch_b: list[int] = []
            for round_index in range(ROUNDS):
                order = ("baseline", "candidate") if round_index % 2 == 0 else ("candidate", "baseline")
                values = {}
                launches = {}
                for arm in order:
                    values[arm], launches[arm] = _launch(arm, case)
                baseline.append(values["baseline"])
                candidate.append(values["candidate"])
                launch_b.append(launches["baseline"])
                launch_c.append(launches["candidate"])
            rows.append(_summarize(name, candidate, baseline, launch_c, launch_b))

    by_name = {row["case"]: row for row in rows}
    unrelated = by_name["unrelated-1m"]
    productive = [by_name[name] for name in PRODUCTIVE]
    productive_cpu_ratios = [row["build_cpu_ratio"] for row in productive]
    productive_stored_ratios = [row["stored_ratio"] for row in productive]
    productive_rss_ratios = [row["peak_rss_ratio"] for row in productive]

    semantic_ok = all(
        all(sample["roundtrip_exact"] for sample in row["candidate"] + row["baseline"])
        and row["candidate_wire_deterministic"]
        and row["baseline_wire_deterministic"]
        for row in rows
    )
    unrelated_stats = unrelated["candidate"][0]["stats"]
    gates = {
        "semantic_exact": semantic_ok,
        "unrelated_cpu_ratio": unrelated["build_cpu_ratio"],
        "unrelated_wall_ratio": unrelated["build_wall_ratio"],
        "unrelated_worst_paired_cpu_ratio": unrelated["worst_paired_cpu_ratio"],
        "unrelated_rss_ratio": unrelated["peak_rss_ratio"],
        "unrelated_wire_byte_identical": unrelated["wire_byte_identical"],
        "unrelated_exact_proof_bytes": unrelated_stats["discovery_exact_proof_bytes"],
        "productive_median_stored_ratio": float(statistics.median(productive_stored_ratios)),
        "productive_median_cpu_ratio": float(statistics.median(productive_cpu_ratios)),
        "productive_worst_cpu_ratio": max(productive_cpu_ratios),
        "productive_median_rss_ratio": float(statistics.median(productive_rss_ratios)),
        "every_productive_stored_smaller": all(row["stored_ratio"] < 1.0 for row in productive),
        "candidate_auth_source_reread_zero": all(row["candidate"][0]["stats"]["authentication_source_reread_bytes"] == 0 for row in rows),
    }
    passes = (
        gates["semantic_exact"]
        and gates["unrelated_cpu_ratio"] <= 1.15
        and gates["unrelated_wall_ratio"] <= 1.15
        and gates["unrelated_worst_paired_cpu_ratio"] <= 1.30
        and gates["unrelated_rss_ratio"] <= 1.10
        and gates["unrelated_wire_byte_identical"]
        and gates["unrelated_exact_proof_bytes"] == 0
        and gates["every_productive_stored_smaller"]
        and gates["productive_median_stored_ratio"] <= 0.70
        and gates["productive_median_cpu_ratio"] <= 2.00
        and gates["productive_worst_cpu_ratio"] <= 2.50
        and gates["productive_median_rss_ratio"] <= 1.20
        and gates["candidate_auth_source_reread_zero"]
    )
    return {
        "schema": "cmpct-one-g02-general-law-archive-creation-profile-v1",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "fresh-process transfer creation/RSS profile; no Genesis corpus; no product/native claim",
        "rounds": ROUNDS,
        "rows": rows,
        "gates": gates,
        "decision": "ADVANCE_CREATION_PROFILE" if passes else "HOLD_CREATION_COMPUTE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=("candidate", "baseline"))
    parser.add_argument("--case", type=Path)
    args = parser.parse_args()
    if args.worker:
        if args.case is None:
            parser.error("--worker requires --case")
        print(json.dumps(_worker(args.worker, args.case), sort_keys=True))
        return
    result = run()
    Path("one-g02-general-law-archive-creation-profile.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
