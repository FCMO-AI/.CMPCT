#!/usr/bin/env python3
"""J24G20: cold, stage-separated physical Reader RSS court. Research only."""
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

import msgpack
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from j24g18_native_reader_court import BODY, append_delta, exact_released_reader
from j24g19_signed_reader_court import ProjectedReader
from j24g19_certified_projection import certify

READER_BLOB = "f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PUBLISHED_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
PARENT = "e15553bf409f4bb3b339af2ec1af83062af2926a"
ARMS = ("published", "parent", "projected")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mem():
    fields = {}
    with open("/proc/self/status", encoding="ascii") as f:
        for line in f:
            key = line.split(":", 1)[0]
            if key in ("VmRSS", "VmHWM", "VmPeak"):
                fields[key + "_kib"] = int(line.split()[1])
    fields["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return fields


def worker(file_name: str, arm: str):
    # All source imports and the historical Git compilation precede stage B0.
    reader = (exact_released_reader() if arm == "published" else
              CMPCT if arm == "parent" else ProjectedReader)
    b0 = mem()
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    outcome = {}
    try:
        with reader(Path(file_name)) as obj:
            b1 = mem()
            found = "renamed.bin" if "renamed.bin" in obj.by else "owner.bin"
            raw = obj.read(found)
            ranged = obj.read_range(found, 1, 17)
            b2 = mem()
            assert raw == BODY and ranged == BODY[1:18]
            verification = obj.verify()
            b3 = mem()
            outcome = {
                "status": "opened", "footer": obj.latest_footer_pos,
                "depth": obj.delta_depth, "member": found,
                "member_sha256": digest(raw), "verified": verification
            }
    except Exception as ex:
        outcome = {"status": "error", "error": type(ex).__name__}
        b1 = b2 = b3 = mem()
    outcome.update(arm=arm, file=Path(file_name).name, before=b0,
                   after_open=b1, after_read=b2, after_verify=b3,
                   cpu_ns=time.process_time_ns()-c0,
                   wall_ns=time.perf_counter_ns()-t0)
    print(json.dumps(outcome, sort_keys=True))


def court(out: Path, repeats: int):
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", PARENT, "HEAD"], check=True)
    for ref, want in (("HEAD", READER_BLOB),
                      ("80c358f8824ec1b20d349c92ed94c898090969b0", PUBLISHED_BLOB)):
        actual = subprocess.check_output(
            ["git", "rev-parse", ref + ":src/cmpct/reader.py"], text=True).strip()
        assert actual == want, (ref, actual)
    assert Path(__file__).read_bytes() == subprocess.check_output(
        ["git", "show", "HEAD:research/j24g20_cold_rss_court.py"])
    cases = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g20-") as d:
        temp = Path(d)
        tree = temp / "tree"
        tree.mkdir()
        (tree / "owner.bin").write_bytes(BODY)
        base = temp / "checkpoint.cmpct"
        Builder(tree).build(base)
        with CMPCT(base) as original:
            checkpoint = original.latest_footer_pos
            assert original.read("owner.bin") == BODY and checkpoint > 0
        archive_root = out / "physical"
        archive_root.mkdir(parents=True, exist_ok=True)
        stored = archive_root / "checkpoint.cmpct"
        stored.write_bytes(base.read_bytes())
        cases["checkpoint"] = {
            "path": str(stored.relative_to(out)), "count": 0,
            "bytes": stored.stat().st_size, "sha256": digest(stored.read_bytes()),
            "footer": checkpoint, "payload_bytes": 0
        }
        # Generate physical inputs outside every measured worker, and reuse
        # the exact same physical archive across all three Reader arms.
        rename = [["ren", "owner.bin", "renamed.bin"]]
        for count in (200000, 400000, 800000):
            value = {"blobs": [], "ops": rename, "extension": [{"x": 0}] * count}
            payload = msgpack.packb(value, use_bin_type=True)
            assert len(payload) < 16 * 1024 * 1024 and certify(payload)[0]
            name = "linked-" + str(count)
            target = archive_root / (name + ".cmpct")
            signed = append_delta(base, target, payload, checkpoint)
            cases[name] = {
                "path": str(target.relative_to(out)), "count": count,
                "bytes": target.stat().st_size, "sha256": digest(target.read_bytes()),
                "footer": signed["footer"], "payload_bytes": len(payload),
                "payload_sha256": digest(payload),
                "footer_sha256": signed["footer_sha256"]
            }
            del value, payload
    observations = {}
    for case, info in cases.items():
        observations[case] = {}
        for arm in ARMS:
            rows = []
            for repetition in range(repeats):
                run = subprocess.run(
                    [sys.executable, __file__, "--worker", str(out / info["path"]), arm],
                    text=True, capture_output=True)
                assert run.returncode == 0, (case, arm, run.stderr[-2000:])
                row = json.loads(run.stdout)
                row["repetition"] = repetition
                assert row["status"] == "opened", (case, arm, row)
                assert row["depth"] == (0 if case == "checkpoint" else 1)
                assert row["footer"] == info["footer"]
                assert row["member"] == ("owner.bin" if case == "checkpoint" else "renamed.bin")
                assert row["member_sha256"] == digest(BODY)
                assert row["verified"] == 1
                for stage in ("before", "after_open", "after_read", "after_verify"):
                    assert row[stage]["VmHWM_kib"] >= row["before"]["VmHWM_kib"]
                rows.append(row)
            observations[case][arm] = rows
    medians = {}
    for case in cases:
        medians[case] = {}
        for arm in ARMS:
            rows = observations[case][arm]
            medians[case][arm] = {
                key: statistics.median(r[stage][metric] for r in rows)
                for key, stage, metric in (
                    ("baseline_hwm_kib", "before", "VmHWM_kib"),
                    ("open_hwm_kib", "after_open", "VmHWM_kib"),
                    ("final_hwm_kib", "after_verify", "VmHWM_kib"),
                    ("open_rss_kib", "after_open", "VmRSS_kib"))
            }
            medians[case][arm]["cpu_ms"] = statistics.median(r["cpu_ns"] for r in rows)/1e6
    large = medians["linked-800000"]
    rss_delta_pub = large["published"]["final_hwm_kib"] - large["projected"]["final_hwm_kib"]
    rss_delta_parent = large["parent"]["final_hwm_kib"] - large["projected"]["final_hwm_kib"]
    result = {
        "schema": "cmpct-j24g20-cold-rss-court-v1",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "parent": PARENT, "readers": {"published": PUBLISHED_BLOB, "parent": READER_BLOB},
        "archive_inputs": cases, "observations": observations, "medians": medians,
        "h1_preopen_peaks_recorded": True,
        "h2_large_rss_16mib_pass": rss_delta_pub >= 16384 and rss_delta_parent >= 16384,
        "large_delta_pub_kib": rss_delta_pub,
        "large_delta_parent_kib": rss_delta_parent,
        "semantics": "all checked same-file read/range/verify/latest-footer PASS",
        "full_product_release_credit": False,
        "platforms": "Linux /proc, Ubuntu 24.04 only"
    }
    (out / "j24g20_result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: result[key] for key in
                      ("h2_large_rss_16mib_pass", "large_delta_pub_kib",
                       "large_delta_parent_kib", "medians")}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--worker", nargs=2, metavar=("PATH", "ARM"))
    p.add_argument("--out", type=Path, default=Path("j24g20-artifacts"))
    p.add_argument("--repeats", type=int, default=3)
    args = p.parse_args()
    if args.worker:
        worker(*args.worker)
    else:
        court(args.out, args.repeats)
