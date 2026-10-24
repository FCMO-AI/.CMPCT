#!/usr/bin/env python3
"""O11: installed-package source-exact O3 versus O9 Reader startup/RSS economics.

Research instrument only: uses real Builder + signed r24 checkpoint/journal,
and loads actual historical and O7 Reader source in independent processes.
No timing claim from an oracle, simulation or different corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BASE_HEAD = "bf09afa516024e2503143189017a6931fc4947d0"
BASE_BLOB = "79171b2f53dbc7c1e0cfb3f3266a35663fcf9cd8"
CANDIDATE_BLOB = "bd1df6091c952e74c8690cf2ba0764747e6db815"
EXPECTED_PAYLOAD_SHA = hashlib.sha256(b"DELTA-REPLAY-EXACT-CONTENT\x00").hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rss_kib(field: str) -> int | None:
    # Linux only, and reported separately from ru_maxrss (lifetime HWM).
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith(field + ":"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def maxrss_kib() -> int | None:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except (ImportError, OSError):
        return None


def worker(version: str, archive: Path, historical: Path, count: int) -> None:
    if version not in ("historical", "candidate"):
        raise ValueError("unsupported Reader version")
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    if version == "candidate":
        from cmpct.reader import CMPCT
    else:
        import importlib.util
        import cmpct  # noqa: F401 -- establishes package namespace for relative imports
        name = "cmpct._reader_o11_source_exact_o3"
        spec = importlib.util.spec_from_file_location(name, historical)
        if spec is None or spec.loader is None:
            raise RuntimeError("historical Reader loader unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        CMPCT = module.CMPCT
    t1, c1 = time.perf_counter_ns(), time.process_time_ns()
    before = {
        "VmRSS_kib": rss_kib("VmRSS"),
        "VmHWM_kib": rss_kib("VmHWM"),
        "ru_maxrss_kib": maxrss_kib(),
    }
    with CMPCT(archive) as reader:
        t2, c2 = time.perf_counter_ns(), time.process_time_ns()
        after = {
            "VmRSS_kib": rss_kib("VmRSS"),
            "VmHWM_kib": rss_kib("VmHWM"),
            "ru_maxrss_kib": maxrss_kib(),
        }
        assert len(reader.files) == count
        sample = reader.read("g000000.bin")
        assert sha(sample) == EXPECTED_PAYLOAD_SHA, "physical reconstruction differs"
        # Independent index receipt, never timing by this JSON/string work.
        index_sha = sha(repr(reader.index).encode("utf-8"))
        recorded_depth = reader.delta_depth
    output = {
        "version": version, "archive": archive.name, "count": count,
        "import_wall_ns": t1 - t0, "import_cpu_ns": c1 - c0,
        "constructor_wall_ns": t2 - t1, "constructor_cpu_ns": c2 - c1,
        "import_plus_constructor_wall_ns": t2 - t0,
        "import_plus_constructor_cpu_ns": c2 - c0,
        "rss_before_constructor": before, "rss_after_constructor": after,
        "payload_sha256": sha(sample),
        "final_index_repr_sha256": index_sha, "journal_depth": recorded_depth,
        "platform": platform.platform(), "python": sys.version,
    }
    print(json.dumps(output, sort_keys=True), flush=True)


def median_ms(rows: list[dict], metric: str) -> float:
    return statistics.median(row[metric] for row in rows) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sizes", type=int, nargs="+", default=[512, 4096])
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()
    if args.repeats < 5 or any(n not in (512, 4096) for n in args.sizes):
        raise SystemExit("O11 fixed prospective sizes 512/4096 and >=5 repeats only")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert head == os.environ.get("EVIDENCE_HEAD", head), "not exact checkout HEAD"
    blob = subprocess.check_output(
        ["git", "hash-object", "src/cmpct/reader.py"], text=True,
    ).strip()
    assert blob == CANDIDATE_BLOB, "Reader changed: O9 installed source custody mismatch"
    # Ensure that the measured candidate actually comes from an installed wheel,
    # not an editable checkout masquerading as installed-product evidence.
    import cmpct.reader as installed_reader
    installed_path = Path(installed_reader.__file__).resolve()
    source_path = (Path.cwd() / "src").resolve()
    assert not installed_path.is_relative_to(source_path), (
        "candidate Reader is sourced from editable repository", installed_path
    )
    installed_blob = subprocess.check_output(
        ["git", "hash-object", str(installed_path)], text=True,
    ).strip()
    assert installed_blob == CANDIDATE_BLOB, (
        "installed package drift", installed_blob, CANDIDATE_BLOB
    )
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "experiment": "cmpct-r24-installed-reader-cold-economics-o11",
        "head": head, "baseline_source_commit": BASE_HEAD,
        "installed_candidate_reader_path": str(installed_path),
        "installed_candidate_reader_git_blob": installed_blob,
        "comparison_scope": "O3 Reader-only substitution with O9 installed dependency closure",
        "limitation": "historical Reader uses dynamic package-namespaced loader; not a full O3 wheel",
        "baseline_reader_blob": BASE_BLOB, "candidate_reader_blob": blob,
        "credit": "installed O9 Reader vs exact O3 Reader source-only substitution; not whole package A/B nor release parity",
        "os": platform.platform(), "python": sys.version,
        "start_boundary": "worker t0 just before loading Reader module",
        "total_process_wall_boundary": "parent subprocess.run includes Python startup and exit",
        "rss_boundary": "Linux kernel /proc VmRSS/VmHWM; ru_maxrss sampled before/after constructor",
        "cases": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-installed-cold-o11-") as folder:
        root = Path(folder)
        raw = subprocess.check_output(["git", "show", f"{BASE_HEAD}:src/cmpct/reader.py"])
        old_blob = subprocess.check_output(
            ["git", "hash-object", "--stdin"], input=raw,
        ).decode().strip()
        assert old_blob == BASE_BLOB, (old_blob, BASE_BLOB)
        historical = root / "reader_o11_o3_source.py"
        historical.write_bytes(raw)

        # Parent's imports/build are never inside child timing boundaries.
        from cmpct.builder import Builder
        from cmpct.reader import CMPCT
        from cmpct.validation import preflight_archive
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from v031_signed_delta_replay_o0 import PAYLOAD, make_case

        source_dir = root / "source"
        source_dir.mkdir()
        (source_dir / "single.bin").write_bytes(PAYLOAD)
        source = root / "authentic.cmpct"
        Builder(source_dir, workers=1, reproducible=True).build(source)
        with CMPCT(source) as r:
            assert r.read("single.bin") == PAYLOAD

        for count in args.sizes:
            delta, checkpoint, identity = make_case(root, source, count)
            assert identity["result_index_equal"] is True
            assert preflight_archive(delta)["files"] == count
            assert preflight_archive(checkpoint)["files"] == count
            archives = {"journal": delta, "checkpoint": checkpoint}
            raw_samples = {
                version: {kind: [] for kind in archives}
                for version in ("historical", "candidate")
            }
            for iteration in range(args.repeats):
                # Each cell has its own fresh interpreter; ABBA vs BAAB reversal
                # changes source and archive order without changing test inputs.
                versions = (
                    ("historical", "candidate", "candidate", "historical")
                    if iteration % 2 == 0
                    else ("candidate", "historical", "historical", "candidate")
                )
                kinds = ("journal", "checkpoint") if iteration % 2 == 0 else (
                    "checkpoint", "journal"
                )
                for kind in kinds:
                    for version in versions:
                        command = [
                            sys.executable, str(Path(__file__).resolve()), "--worker",
                            version, str(archives[kind]), str(historical), str(count),
                        ]
                        start = time.perf_counter_ns()
                        done = subprocess.run(command, capture_output=True, text=True)
                        process_ns = time.perf_counter_ns() - start
                        if done.returncode:
                            raise RuntimeError(
                                f"Worker {version}/{kind}/{count}: {done.stderr}\n{done.stdout}"
                            )
                        row = json.loads(done.stdout.strip().splitlines()[-1])
                        row["whole_process_wall_ns"] = process_ns
                        row["iteration"] = iteration
                        raw_samples[version][kind].append(row)
            for kind in archives:
                hashes = {
                    row["final_index_repr_sha256"]
                    for version in raw_samples
                    for row in raw_samples[version][kind]
                }
                assert len(hashes) == 1, ("Reader index mismatch", kind, hashes)
                depths = {row["journal_depth"] for version in raw_samples
                          for row in raw_samples[version][kind]}
                assert depths == ({1} if kind == "journal" else {0}), depths
            for version in raw_samples:
                assert len(raw_samples[version]["journal"]) == 2 * args.repeats
                assert len(raw_samples[version]["checkpoint"]) == 2 * args.repeats

            def summary(version: str, kind: str) -> dict:
                rows = raw_samples[version][kind]
                metrics = (
                    "import_wall_ns", "constructor_wall_ns",
                    "import_plus_constructor_wall_ns",
                    "import_cpu_ns", "constructor_cpu_ns",
                    "whole_process_wall_ns",
                )
                return {
                    "median_ms": {key: median_ms(rows, key) for key in metrics},
                    "median_HWM_after_kib": statistics.median(
                        row["rss_after_constructor"]["VmHWM_kib"] for row in rows
                        if row["rss_after_constructor"]["VmHWM_kib"] is not None
                    ),
                    "median_HWM_before_kib": statistics.median(
                        row["rss_before_constructor"]["VmHWM_kib"] for row in rows
                        if row["rss_before_constructor"]["VmHWM_kib"] is not None
                    ),
                    "raw": rows,
                }

            summaries = {
                version: {kind: summary(version, kind) for kind in archives}
                for version in raw_samples
            }
            h = summaries["historical"]["journal"]["median_ms"]["import_plus_constructor_wall_ns"]
            c = summaries["candidate"]["journal"]["median_ms"]["import_plus_constructor_wall_ns"]
            hc = summaries["historical"]["checkpoint"]["median_ms"]["import_plus_constructor_wall_ns"]
            cc = summaries["candidate"]["checkpoint"]["median_ms"]["import_plus_constructor_wall_ns"]
            hwm_h = summaries["historical"]["journal"]["median_HWM_after_kib"]
            hwm_c = summaries["candidate"]["journal"]["median_HWM_after_kib"]
            hwm_red = hwm_c - hwm_h
            memory_debt = hwm_red > 10240 and hwm_red / max(hwm_h, 1) > 0.10
            checkpoint_debt = cc > hc * 1.05 and cc - hc > 3.0
            decision = (
                "COLD_WIN_WITH_MEMORY_DEBT" if h / c >= 1.5 and memory_debt
                else "COLD_WIN_NO_MATERIAL_OBSERVED_HWM_DEBT"
                if h / c >= 1.5 and not checkpoint_debt
                else "NO_COLD_WIN_OR_CHECKPOINT_REGRESSION"
            )
            if checkpoint_debt:
                decision = "NO_COLD_WIN_OR_CHECKPOINT_REGRESSION"
            report["cases"][str(count)] = {
                "identity": identity, "full_archive_bytes": {
                    key: archive.stat().st_size for key, archive in archives.items()
                }, "full_archive_sha256": {
                    key: sha(archive.read_bytes()) for key, archive in archives.items()
                }, "historical_over_candidate_cold_ratio": h / c,
                "checkpoint_cold_candidate_minus_historical_ms": cc - hc,
                "journal_candidate_minus_historical_HWM_kib": hwm_red,
                "memory_debt_threshold_fired": memory_debt,
                "checkpoint_debt_threshold_fired": checkpoint_debt,
                "decision": decision,
                "summary": summaries,
            }
            print("O11_INSTALLED_READER " + json.dumps({
                "count": count, "historical_cold_ms": h, "candidate_cold_ms": c,
                "cold_ratio": h / c, "historical_checkpoint_ms": hc,
                "candidate_checkpoint_ms": cc,
                "historical_HWM_kib": hwm_h, "candidate_HWM_kib": hwm_c,
                "decision": decision,
            }), flush=True)
    out = args.out / "installed-reader-cold-economics-o11.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("O11_RECEIPT_SHA256=" + sha(out.read_bytes()), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        if len(sys.argv) != 6:
            raise SystemExit("worker <historical|candidate> <archive> <old_src> <n>")
        worker(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), int(sys.argv[5]))
    else:
        main()
