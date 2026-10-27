"""J24C02b: source-exact original vs composed Reader cold-open cost on identical valid r24 archives.

Research budget only. Input bytes generated once; no encoding or process startup in timed sections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time


PARENT_SHA = "d3b12852511095d6e98803f55cfd700b8e9ac6b3"
COUNTS = (1, 4096, 65536, 262144)
CYCLES = 3
REPEATS = 5


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def worker(path: str, logical_bytes: int, runs: int) -> None:
    import inspect
    import cmpct.reader as reader_module
    from cmpct.reader import CMPCT

    reader_path = Path(inspect.getfile(reader_module)).resolve()
    digest = sha256_bytes(normalized(reader_path.read_bytes()))
    wall_ns, cpu_ns = [], []
    # One pre-measurement warmup to take imports/allocator startup outside timed opens.
    with CMPCT(Path(path)) as reader:
        assert len(reader.files) == 1
        assert reader.files[0][4] == logical_bytes
    for _ in range(runs):
        t0, c0 = time.perf_counter_ns(), time.process_time_ns()
        with CMPCT(Path(path)) as reader:
            assert len(reader.files) == 1
            assert reader.files[0][4] == logical_bytes
        wall_ns.append(time.perf_counter_ns() - t0)
        cpu_ns.append(time.process_time_ns() - c0)
    result = {
        "reader_file": str(reader_path),
        "reader_sha256": digest,
        "wall_ns": wall_ns,
        "cpu_ns": cpu_ns,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    print(json.dumps(result, sort_keys=True))


def run_controller(parent_site: Path, output: Path) -> None:
    from test_o215_fixed_chunk_admission import _make_archive

    workspace = Path(os.environ["GITHUB_WORKSPACE"])
    def git_source(ref: str) -> bytes:
        return subprocess.check_output(
            ["git", "show", ref + ":src/cmpct/reader.py"], cwd=workspace
        )
    expected_sha = {
        "parent": sha256_bytes(normalized(git_source(PARENT_SHA))),
        "candidate": sha256_bytes(normalized(git_source("HEAD"))),
    }
    assert expected_sha["parent"] != expected_sha["candidate"]
    assert parent_site.is_dir(), ("missing independently installed parent", parent_site)
    all_rows = []
    with tempfile.TemporaryDirectory(prefix="j24c02b-r24-") as temp:
        root = Path(temp)
        for count in COUNTS:
            physical = _make_archive([0] * count, b"ABCD" * count)
            path = root / ("refs-" + str(count) + ".cmpct")
            path.write_bytes(physical)
            fixture = {
                "refs": count,
                "logical_bytes": count * 4,
                "archive_bytes": len(physical),
                "archive_sha256": sha256_bytes(physical),
            }
            observations = []
            for cycle in range(CYCLES):
                for arm in ("parent", "candidate", "candidate", "parent"):
                    env = os.environ.copy()
                    if arm == "parent":
                        env["PYTHONPATH"] = str(parent_site)
                    else:
                        env.pop("PYTHONPATH", None)
                    command = [
                        sys.executable, str(Path(__file__).resolve()), "--worker",
                        str(path), str(count * 4), str(REPEATS),
                    ]
                    cp = subprocess.run(command, cwd=root, env=env, capture_output=True,
                                        text=True, check=True, timeout=120)
                    payload = json.loads(cp.stdout.strip())
                    if payload["reader_sha256"] != expected_sha[arm]:
                        raise AssertionError(("incorrect installed Reader", arm, payload))
                    if arm == "parent" and "j24c02-parent-site" not in payload["reader_file"]:
                        raise AssertionError(("not isolated parent site", payload["reader_file"]))
                    if arm == "candidate" and "j24c02-parent-site" in payload["reader_file"]:
                        raise AssertionError(("candidate accidentally uses parent", payload["reader_file"]))
                    payload.update({"arm": arm, "cycle": cycle})
                    observations.append(payload)
            aggregated = {}
            for arm in ("parent", "candidate"):
                arm_obs = [x for x in observations if x["arm"] == arm]
                aggregated[arm] = {
                    "median_worker_wall_ns": statistics.median(
                        statistics.median(x["wall_ns"]) for x in arm_obs),
                    "median_worker_cpu_ns": statistics.median(
                        statistics.median(x["cpu_ns"]) for x in arm_obs),
                    "median_process_peak_rss_kib": statistics.median(
                        x["process_peak_rss_kib"] for x in arm_obs),
                }
            base = aggregated["parent"]["median_worker_wall_ns"]
            cand = aggregated["candidate"]["median_worker_wall_ns"]
            ratio = cand / base
            delta_ms = (cand - base) / 1e6
            debt = ratio >= 2 and (
                (count == 65536 and delta_ms > 5)
                or (count == 262144 and delta_ms > 20)
            )
            all_rows.append({
                "fixture": fixture,
                "raw_observations": observations,
                "summary": aggregated,
                "candidate_base_wall_ratio": ratio,
                "candidate_minus_base_wall_ms": delta_ms,
                "prospective_material_debt": debt,
            })
            print(
                f"J24C02B_REFS={count} WALL_RATIO={ratio:.4f} "
                f"DELTA_MS={delta_ms:.4f} MATERIAL_DEBT={debt}", flush=True
            )
    result = {
        "classification": "RESEARCH_SAME_SOURCE_R24_COLD_OPEN_ONLY",
        "candidate_commit": os.environ.get("SOURCE_SHA", "UNBOUND"),
        "parent_commit": PARENT_SHA,
        "reader_sha256": expected_sha,
        "system": {
            "python": sys.version,
            "platform": sys.platform,
            "process_startup_in_timed_section": False,
            "included_operation": "CMPCT constructor and close, after import warmup",
            "peak_rss_units": "Linux ru_maxrss KiB, absolute process peak",
        },
        "fixtures": all_rows,
        "any_material_debt": any(x["prospective_material_debt"] for x in all_rows),
        "decision": (
            "MATERIAL_COLD_OPEN_DEBT" if any(x["prospective_material_debt"] for x in all_rows)
            else "NO_PROSPECTIVE_MATERIAL_OPEN_DEBT_IN_TEST"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24C02B_DECISION=" + result["decision"], flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", action="store_true")
    ap.add_argument("arguments", nargs="*")
    ap.add_argument("--parent-site", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.worker:
        if len(args.arguments) != 3:
            ap.error("worker requires path logical_bytes repeats")
        worker(args.arguments[0], int(args.arguments[1]), int(args.arguments[2]))
    else:
        if args.arguments or args.parent_site is None or args.output is None:
            ap.error("controller needs --parent-site and --output")
        run_controller(args.parent_site, args.output)


if __name__ == "__main__":
    main()
