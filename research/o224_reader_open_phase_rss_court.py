#!/usr/bin/env python3
"""O224: research-only, source-exact staged Reader-open memory attribution.

Never monkeypatch product source on disk. The skip arm intentionally weakens
validation ONLY on independently authenticated valid synthetic fixtures; it
is an unsafe counterfactual and must never be shipped.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

NS = (4096, 65536, 262144)
KINDS = ("fixed", "cdc")
LAYOUTS = ("repeat", "eight")
ARMS = ("plain", "skip", "instrumented")
REPEATS = 3
PREREG = "c630c7e15637c51895d70ad7ef3f8fd96f1a3214"
READER_BLOB = "dbd4ac576a05a47eae97e1e40de89cf1de440516"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def proc_memory():
    values = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:", "VmSize:", "VmPeak:")):
            name, val = line.split(":", 1)
            values[name + "_kib"] = int(val.strip().split()[0])
    try:
        lines = Path("/proc/self/smaps_rollup").read_text().splitlines()
        for line in lines:
            if line.startswith(("Rss:", "Pss:", "Private_Clean:", "Private_Dirty:")):
                name, val = line.split(":", 1)
                values["smaps_" + name.lower() + "_kib"] = int(val.strip().split()[0])
    except OSError:
        values["smaps_unavailable"] = True
    values["ru_maxrss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return values


def child(args):
    import cmpct.reader as reader_module
    import cmpct.validation as validation_module
    import tracemalloc

    if args.trace:
        tracemalloc.start()
    events = []

    def snapshot(stage):
        stats = proc_memory()
        if args.trace:
            current, peak = tracemalloc.get_traced_memory()
            stats["python_traced_current_bytes"] = current
            stats["python_traced_peak_bytes"] = peak
        events.append({"stage": stage, "rss": stats, "time_ns": time.perf_counter_ns()})

    snapshot("before_open")
    if args.arm in ("instrumented", "instrumented_trace"):
        original_zd = reader_module.zd
        original_unpack = reader_module.msgpack.unpackb
        original_validate = validation_module._validate_storage
        done_validation = [False]

        def hooked_zd(*a, **kw):
            result = original_zd(*a, **kw)
            snapshot("after_decompress")
            return result

        def hooked_unpack(*a, **kw):
            result = original_unpack(*a, **kw)
            snapshot("after_unpack")
            return result

        def hooked_validation(*a, **kw):
            first = not done_validation[0]
            if first:
                snapshot("before_validation")
                done_validation[0] = True
            result = original_validate(*a, **kw)
            if first:
                snapshot("after_validation")
            return result

        reader_module.zd = hooked_zd
        reader_module.msgpack.unpackb = hooked_unpack
        validation_module._validate_storage = hooked_validation
    elif args.arm == "skip":
        # UNSAFE counterfactual: valid, SHA-bound researcher-made fixtures only.
        validation_module._validate_storage = lambda *a, **kw: None
    elif args.arm != "plain":
        raise AssertionError("unknown arm")

    started = time.perf_counter_ns()
    with reader_module.CMPCT(Path(args.archive)) as r:
        snapshot("after_open")
        name = "fixed.bin" if args.kind == "fixed" else "cdc.bin"
        row = r.by[name]
        if row[4] != args.n or bytes(row[5]).hex() != args.expected_sha:
            raise AssertionError("Reader index does not bind expected bytes")
        if len(row[6][1]) != args.n:
            raise AssertionError("fixture reference count mismatch")
        # After measuring open, independently check the exact last logical byte.
        got = r.read_range(name, args.n - 1, 1)
        if got.hex() != args.last_byte_hex:
            raise AssertionError("Reader selective output differs")
    finished = time.perf_counter_ns()
    snapshot("after_close")
    print(json.dumps({
        "kind": args.kind, "n": args.n, "layout": args.layout,
        "arm": args.arm, "archive_sha256": args.archive_sha,
        "expected_sha256": args.expected_sha,
        "result_last_byte": got.hex(), "events": events,
        "open_wall_ms": (events[-2]["time_ns"] - started) / 1e6,
        "session_wall_ms": (finished - started) / 1e6,
        "pid": os.getpid(), "python": sys.version.split()[0],
        "trace": bool(args.trace),
    }, sort_keys=True))


def imported_test(path):
    spec = importlib.util.spec_from_file_location("o224_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_fixture(root, kind, n, layout):
    if layout == "repeat":
        payloads = (b"Q",)
        refs = [0] * n
    elif layout == "eight":
        payloads = tuple(bytes((65 + i,)) for i in range(8))
        refs = [(i * 5 + i // 31) % 8 for i in range(n)]
    else:
        raise ValueError(layout)
    expected = bytes(payloads[i][0] for i in refs)
    if kind == "fixed":
        mod = imported_test(root / "tests/test_o215_fixed_chunk_admission.py")
        wire = mod._make_archive(refs, expected, blobs=payloads)
    else:
        mod = imported_test(root / "tests/test_o214_cdc_admission.py")
        wire = mod._r24([[1, i] for i in refs], expected, blobs=payloads)
    return wire, expected


def one_child(script, archive, kind, n, layout, arm, digest, lastbyte, trace=False):
    cmd = [
        sys.executable, str(script), "--child", "--archive", str(archive),
        "--kind", kind, "--n", str(n), "--layout", layout,
        "--arm", arm, "--archive-sha", sha(archive.read_bytes()),
        "--expected-sha", digest, "--last-byte-hex", lastbyte.hex(),
    ]
    if trace:
        cmd.append("--trace")
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if p.returncode:
        raise RuntimeError(f"child failed ({kind},{n},{layout},{arm}): {p.stderr[-4000:]}")
    record = json.loads(p.stdout.strip().splitlines()[-1])
    assert record["archive_sha256"] == sha(archive.read_bytes())
    assert record["expected_sha256"] == digest
    assert record["result_last_byte"] == lastbyte.hex()
    assert record["events"][0]["stage"] == "before_open"
    assert "after_open" in [e["stage"] for e in record["events"]]
    return record


def med(rows, stage, name="VmHWM_kib"):
    numbers = []
    for row in rows:
        event = next(e for e in row["events"] if e["stage"] == stage)
        numbers.append(event["rss"][name])
    return statistics.median(numbers)


def run(args):
    root = Path(args.workspace).resolve()
    script = Path(__file__).resolve()
    raw = []
    fixtures = []
    with tempfile.TemporaryDirectory(prefix="o224-genuine-r24-") as td:
        for n in NS:
            for kind in KINDS:
                for layout in LAYOUTS:
                    wire, expected = build_fixture(root, kind, n, layout)
                    archive = Path(td) / f"{kind}-{n}-{layout}.cmpct"
                    archive.write_bytes(wire)
                    fixture = {"kind": kind, "n": n, "layout": layout,
                               "archive_sha256": sha(wire), "archive_bytes": len(wire),
                               "expected_sha256": sha(expected), "last_byte_hex": expected[-1:].hex()}
                    fixtures.append(fixture)
                    for rep in range(args.repeats):
                        for arm in ARMS:
                            row = one_child(script, archive, kind, n, layout, arm,
                                            sha(expected), expected[-1:])
                            row["repeat"] = rep
                            raw.append(row)
                    # tracemalloc is corroboration only, not qualifying HWM evidence
                    if n == 262144:
                        row = one_child(script, archive, kind, n, layout,
                                        "instrumented_trace", sha(expected), expected[-1:], True)
                        row["repeat"] = "traced_control"
                        raw.append(row)
    findings = []
    for kind in KINDS:
        for layout in LAYOUTS:
            group = [r for r in raw if r["n"] == 262144 and
                     r["kind"] == kind and r["layout"] == layout]
            plain = [r for r in group if r["arm"] == "plain"]
            skip = [r for r in group if r["arm"] == "skip"]
            staged = [r for r in group if r["arm"] == "instrumented"]
            nonmonotonic = [r for r in staged if any(a > b for a, b in zip(
                [e["rss"]["VmHWM_kib"] for e in r["events"]],
                [e["rss"]["VmHWM_kib"] for e in r["events"]][1:]))]
            plain_hwm = med(plain, "after_open")
            skip_hwm = med(skip, "after_open")
            staged_hwm = med(staged, "after_open")
            perturbation = (staged_hwm - plain_hwm) / plain_hwm if plain_hwm else float("inf")
            order = ["before_open", "after_decompress", "after_unpack",
                     "before_validation", "after_validation", "after_open"]
            missing = [x for x in order if any(x not in
                       [e["stage"] for e in s["events"]] for s in staged)]
            stages = {}
            if not missing:
                for left, right in zip(order, order[1:]):
                    stages[right] = med(staged, right) - med(staged, left)
            baseline_growth = med(staged, "after_open") - med(staged, "before_open")
            phase = max(stages, key=stages.get) if stages else None
            findings.append({
                "kind": kind, "layout": layout, "n": 262144,
                "baseline_hwm_kib": plain_hwm, "skip_hwm_kib": skip_hwm,
                "instrumented_hwm_kib": staged_hwm,
                "instrumentation_inflation_fraction": perturbation,
                "no_validation_hwm_saving_kib": plain_hwm - skip_hwm,
                "growth_instrumented_kib": baseline_growth,
                "stage_hwm_increment_kib": stages, "missing_stages": missing,
                "largest_stage": phase,
                "largest_stage_fraction": (
                    stages[phase] / baseline_growth if phase and baseline_growth > 0 else None),
                "nonmonotonic_staged_samples": len(nonmonotonic),
                "valid_stage_claim": bool(not missing and not nonmonotonic and perturbation <= 0.15 and
                                          baseline_growth > 0 and phase),
            })
    observed_perturbation = any(x["instrumentation_inflation_fraction"] > 0.15 for x in findings)
    invalid_stage_hwm = any(x["nonmonotonic_staged_samples"] > 0 for x in findings)
    dominant = (not invalid_stage_hwm and not observed_perturbation and all(
        x["valid_stage_claim"] and x["largest_stage_fraction"] >= .60 and
        x["stage_hwm_increment_kib"][x["largest_stage"]] >= 65536 for x in findings)
        and len({x["largest_stage"] for x in findings}) == 1)
    omit = all(x["no_validation_hwm_saving_kib"] >= 65536 for x in findings)
    decision = {
        "stage": ("INVALID_STAGE_HWM_SEQUENCE" if invalid_stage_hwm else
                  "DOMINANT_PHASE_SCOPED" if dominant else
                  "MEASUREMENT_PERTURBED" if observed_perturbation else "MIXED_OR_UNRESOLVED"),
        "largest_stage": findings[0]["largest_stage"] if dominant else None,
        "validation_counterfactual": (
            "VALIDATOR_COUNTERFACTUAL_HEADROOM" if omit else "VALIDATOR_HWM_NOT_PROVEN"),
    }
    results = {
        "schema": "o224-reader-open-phase-rss-v1", "prereg_commit": PREREG,
        "reader_blob": READER_BLOB, "code_scope": "unmodified source installed J24C02 Reader",
        "counts": {"primary": 72, "instrumented": 36, "trace_controls": 4},
        "fixtures": fixtures, "samples": raw, "findings": findings, "decision": decision,
        "limits": ["Linux process RSS HWM is lifetime-highwater not retained/live heap",
                   "tracemalloc samples may perturb allocations",
                   "unsafe validation omission is research counterfactual on valid fixtures only",
                   "no product, release, compressed-codec, native, Windows or macOS claim"],
    }
    Path(args.output).write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": decision, "findings": findings, "samples": len(raw)}, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workspace")
    p.add_argument("--output")
    p.add_argument("--child", action="store_true")
    p.add_argument("--archive")
    p.add_argument("--kind")
    p.add_argument("--n", type=int)
    p.add_argument("--layout")
    p.add_argument("--arm")
    p.add_argument("--archive-sha")
    p.add_argument("--expected-sha")
    p.add_argument("--last-byte-hex")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--repeats", type=int, default=3)
    a = p.parse_args()
    if a.child:
        child(a)
    else:
        if not a.workspace or not a.output or a.repeats != REPEATS:
            p.error("prospective hosted court requires --workspace/--output --repeats 3")
        run(a)


if __name__ == "__main__":
    main()
