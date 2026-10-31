#!/usr/bin/env python3
"""J24I72: actual fresh-process economics of the source-locked 63-DELETE Reader.

Research-only child of J24I70 #871. No product, format, release or gate mutation.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "_reference_j24g91"
LABELS = ("public", "factored", "owned", "delete_only")
PARENT_HEAD = "df2edd9d61a782616d7de1f3c054841e9ebb9eb2"
READER_BLOB = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
REF_HEAD = "129edec976efe8bb604584517de39553487fec34"
PREREG = "b130e333cb94b1c43f1dc38789397fa1ebf5af7f"


def selected_class(label: str):
    if label == "public":
        from cmpct.reader import CMPCT
        return CMPCT
    if label == "factored":
        from j24g73_reader_open import FactoredCMPCT
        return FactoredCMPCT
    if label == "owned":
        from j24g74_owned_decoder_court import OwnedCMPCT
        return OwnedCMPCT
    if label == "delete_only":
        from j24g91_delete_reader_checkpoint import OwnedDeleteCMPCT
        return OwnedDeleteCMPCT
    raise ValueError("unknown Reader")


def high_water_kib():
    if sys.platform.startswith("linux"):
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss is KB on Linux, bytes on Darwin; record only after normalizing.
        return int(value / 1024) if sys.platform == "darwin" else int(value)
    except (ImportError, OSError):
        return None


def child(args):
    import hashlib
    import msgpack
    sys.path.insert(0, str(REFERENCE / "research"))
    sys.path.insert(0, str(ROOT / "research"))
    label, mode = args[0], args[1]
    assert label in LABELS and mode in ("open", "import")
    t0, c0 = time.perf_counter_ns(), time.process_time_ns()
    klass = selected_class(label)
    t1, c1 = time.perf_counter_ns(), time.process_time_ns()
    result = {
        "label": label, "mode": mode, "import_wall_ns": t1 - t0,
        "import_cpu_ns": c1 - c0, "import_hwm_kib": high_water_kib(),
        "python": sys.version.split()[0], "platform": sys.platform,
    }
    if mode == "open":
        if len(args) != 8:
            raise ValueError("expected label,mode,path,member count,index sha,member name,member sha,depth")
        path, count, index_sha, member_name, member_sha, depth = (
            Path(args[2]), int(args[3]), args[4], args[5], args[6], int(args[7]))
        t2, c2 = time.perf_counter_ns(), time.process_time_ns()
        with klass(path) as reader:
            t3, c3 = time.perf_counter_ns(), time.process_time_ns()
            assert len(reader.by) == count, "different logical membership"
            assert reader.delta_depth == depth, "wrong signed generation depth"
            assert hashlib.sha256(msgpack.packb(reader.index, use_bin_type=True)).hexdigest() == index_sha
            content = reader.read(member_name)
            assert hashlib.sha256(content).hexdigest() == member_sha
            route = getattr(reader, "_research_route", None)
            if label != "public":
                expected = {
                    "factored": "factored" if depth else "checkpoint",
                    "owned": "owned-fresh-decoder" if depth else "checkpoint",
                    "delete_only": "onepass-owned-delete" if depth else "checkpoint",
                }[label]
                assert route == expected, (label, depth, route)
        t4, c4 = time.perf_counter_ns(), time.process_time_ns()
        result.update({
            "count": count, "index_sha256": index_sha,
            "member": member_name, "member_sha256": member_sha,
            "depth": depth, "route": route,
            "constructor_wall_ns": t3 - t2,
            "constructor_cpu_ns": c3 - c2,
            "open_plus_proof_wall_ns": t4 - t2,
            "open_plus_proof_cpu_ns": c4 - c2,
            "operation_hwm_kib": high_water_kib(),
        })
    print(json.dumps(result, sort_keys=True), flush=True)


def parent():
    import hashlib
    import os
    import platform
    import shutil
    import statistics
    import subprocess
    import tempfile
    from j24i70_cross_owner_reader import (
        check_all_readers, make_court, digest, source_identity)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    output = Path(os.environ.get("J24I72_EVIDENCE", "evidence/j24i72"))
    output.mkdir(parents=True, exist_ok=True)
    git = lambda *a: subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    assert git("merge-base", PARENT_HEAD, "HEAD") == PARENT_HEAD
    assert git("merge-base", PREREG, "HEAD") == PREREG
    assert git("rev-parse", "HEAD:src/cmpct/reader.py") == READER_BLOB
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REFERENCE, text=True).strip() == REF_HEAD
    source = source_identity()
    source["j24i72_parent_head"] = PARENT_HEAD
    source["j24i72_prereg_commit"] = PREREG
    source["j24i72_instrument_blob"] = git("rev-parse", "HEAD:research/j24i72_cold_owned_reader.py")
    report = {
        "schema": "cmpct-j24i72-cold-owner-v1", "status": "RUNNING",
        "head": git("rev-parse", "HEAD"), "host": platform.platform(),
        "product_credit": 0, "source": source,
        "protocol": {
            "cases": [4096, 8192], "repeats": 8,
            "labels": list(LABELS), "archive_modes": ["A", "B"],
            "full_process_boundary": "parent perf_counter: Python spawn through child exit including proof",
            "import_boundary": "child immediately before import through completed selected Reader import",
            "constructor_boundary": "child immediately before Reader() through its return",
            "hwm": "kernel process high-water where available; never Python heap proxy",
        },
        "cases": {},
    }
    try:
        with tempfile.TemporaryDirectory(prefix="j24i72-source-physical-") as scratch:
            for n in (4096, 8192):
                case = make_court(Path(scratch), n)
                semantic = check_all_readers(case, n)
                assert set(semantic) == {"A", "B", "C"}
                physical = {}
                for key in ("A", "B"):
                    target = output / f"{n}-{key}.cmpct"
                    shutil.copyfile(case["paths"][key], target)
                    assert digest(target) == case["physical"][key]["sha256"]
                    physical[key] = {
                        "file": target.name, "sha256": digest(target),
                        "size": target.stat().st_size,
                    }
                member = f"f{63:05d}.dat"
                assert member in case["expected"]
                common = [
                    str(n - 63), case["index_sha256"],
                    member, case["expected"][member],
                ]
                raw = {"A": {label: [] for label in LABELS},
                       "B": {label: [] for label in LABELS}}
                # eight independent balanced rotations; reverse second block
                for iteration in range(8):
                    ordering = list(LABELS[iteration % 4:] + LABELS[:iteration % 4])
                    if iteration >= 4:
                        ordering.reverse()
                    files = ("A", "B") if iteration % 2 == 0 else ("B", "A")
                    for file_label in files:
                        for label in ordering:
                            command = [
                                sys.executable, str(Path(__file__).resolve()),
                                "--child", label, "open",
                                str(case["paths"][file_label]), *common,
                                str(63 if file_label == "A" else 0),
                            ]
                            start = time.perf_counter_ns()
                            done = subprocess.run(command, capture_output=True, text=True)
                            elapsed = time.perf_counter_ns() - start
                            if done.returncode:
                                raise RuntimeError(
                                    f"child={label} archive={file_label} N={n}:\n{done.stderr}\n{done.stdout}")
                            row = json.loads(done.stdout.strip())
                            assert row["mode"] == "open" and row["label"] == label
                            assert row["index_sha256"] == case["index_sha256"]
                            assert row["depth"] == (63 if file_label == "A" else 0)
                            row.update({"whole_process_wall_ns": elapsed,
                                        "iteration": iteration,
                                        "archive": file_label, "order": ordering})
                            raw[file_label][label].append(row)
                # Import-only controls deliberately separate; their median is not subtracted as a causal estimate.
                imports = {}
                for label in LABELS:
                    imports[label] = []
                    for iteration in range(4):
                        command = [sys.executable, str(Path(__file__).resolve()),
                                   "--child", label, "import"]
                        start = time.perf_counter_ns()
                        done = subprocess.run(command, capture_output=True, text=True)
                        elapsed = time.perf_counter_ns() - start
                        if done.returncode:
                            raise RuntimeError(f"import {label}: {done.stderr}\n{done.stdout}")
                        row = json.loads(done.stdout.strip())
                        assert row["mode"] == "import" and row["label"] == label
                        row.update({"whole_process_wall_ns": elapsed, "iteration": iteration})
                        imports[label].append(row)
                medians = {
                    file_label: {
                        label: {metric: statistics.median(row[metric] for row in raw[file_label][label])
                                for metric in ("whole_process_wall_ns", "import_wall_ns",
                                               "constructor_wall_ns", "open_plus_proof_wall_ns",
                                               "import_cpu_ns", "constructor_cpu_ns")}
                        for label in LABELS}
                    for file_label in ("A", "B")
                }
                gross = lambda key, name: medians[key][name]["whole_process_wall_ns"]
                ratio_owned_public = gross("A", "owned") / gross("A", "public")
                ratio_owned_B = gross("A", "owned") / gross("B", "public")
                tests = {
                    "H1_owned_cold_material_benefit": (
                        ratio_owned_public <= .95 and gross("A", "public") -
                        gross("A", "owned") >= 3_000_000),
                    "H2_owned_A_at_most_1p2_public_B": ratio_owned_B <= 1.2,
                }
                report["cases"][str(n)] = {
                    "physical": physical, "semantics": semantic,
                    "index_sha256": case["index_sha256"],
                    "expected_members": n - 63, "member": member,
                    "member_sha256": case["expected"][member],
                    "checkpoint_extra_bytes": case["checkpoint_extra_bytes"],
                    "generation_seconds": case["generation_seconds"],
                    "raw": raw, "import_only_raw": imports,
                    "medians": medians,
                    "ratios": {
                        "owned_A_over_public_A_gross": ratio_owned_public,
                        "owned_A_over_public_B_gross": ratio_owned_B,
                        "delete_A_over_public_A_gross": gross("A", "delete_only") / gross("A", "public"),
                    },
                    "predictions": tests,
                }
                assert all(len(raw[a][label]) == 8 for a in ("A", "B") for label in LABELS)
                assert all(len(imports[label]) == 4 for label in LABELS)
                assert digest(case["paths"]["A"]) == physical["A"]["sha256"]
                assert digest(case["paths"]["B"]) == physical["B"]["sha256"]
                print("J24I72_N", n, tests, report["cases"][str(n)]["ratios"], flush=True)
        report["status"] = "PASS"  # experiment completed, NOT H1 or release PASS
        report["prospective_two_size_evidence"] = {
            "H1_8192": report["cases"]["8192"]["predictions"]["H1_owned_cold_material_benefit"],
            "H2_8192": report["cases"]["8192"]["predictions"]["H2_owned_A_at_most_1p2_public_B"],
        }
    except BaseException as exc:
        report["status"] = "FAIL"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(sys.argv[2:])
    elif len(sys.argv) == 1:
        parent()
    else:
        raise SystemExit("J24I72 accepts only internal --child arguments")
