#!/usr/bin/env python3
"""O4: fresh-process resident-memory court for authenticated v0.31 preflight.

Test-only, no product modifications. The historical arm executes the exact
Git-blob replay function within the same current validator, deliberately
isolating the change in signed-journal replay from unrelated validator code.
Linux ru_maxrss is maximum *process* RSS, not per-function allocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time

HISTORIC_VALIDATION_BLOB = "51c2849061f99a4afeddb7666956b24566ce7de0"
COMBINED_HEAD = "0062961be78cd4d28231a9acaf37a4d9cf43920c"
SIZES = (512, 2048, 4096)
REPEATS = 5


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def archive_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def live_vm_rss_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def load_historic_replay() -> str:
    import cmpct.validation as validation

    source = subprocess.check_output(
        ["git", "cat-file", "blob", HISTORIC_VALIDATION_BLOB], text=True
    )
    start = source.index("def _apply_delta(")
    end = source.index("\ndef _index_from_footer(", start)
    original = source[start:end]
    # Require an exact function from historical Git object; never synthesize
    # a smaller/faster comparator or mix historical parser limits.
    assert "def _apply_delta_indexed" not in original
    assert "for i, current in enumerate(files):" in original
    exec(compile(original, f"git-blob:{HISTORIC_VALIDATION_BLOB}", "exec"), validation.__dict__)
    return hashlib.sha256(original.encode()).hexdigest()


def run_child(engine: str, archive: Path, expected_digest: str, expected_n: int,
              kind: str) -> None:
    import cmpct.validation as validation

    if engine == "historical":
        exact_function = load_historic_replay()
    elif engine == "combined":
        assert git("rev-parse", "HEAD") == os.environ["EVIDENCE_HEAD"]
        exact_function = "combined-source-unmodified"
    else:
        raise ValueError("unknown engine")
    assert archive_hash(archive) == expected_digest
    before_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    before_live = live_vm_rss_kib()
    t0 = time.perf_counter_ns()
    c0 = time.process_time_ns()
    answer = validation.preflight_archive(archive)
    c1 = time.process_time_ns()
    t1 = time.perf_counter_ns()
    after_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    after_live = live_vm_rss_kib()
    assert answer["files"] == expected_n
    assert answer["delta_depth"] == (1 if kind == "delta" else 0)
    print(json.dumps({
        "engine": engine,
        "kind": kind,
        "archive_sha256": expected_digest,
        "expected_files": expected_n,
        "preflight_files": answer["files"],
        "delta_depth": answer["delta_depth"],
        "wall_ns": t1 - t0,
        "cpu_ns": c1 - c0,
        "ru_maxrss_before_kib": before_peak,
        "ru_maxrss_after_kib": after_peak,
        "ru_maxrss_increment_kib": max(0, after_peak - before_peak),
        "vmrss_before_kib": before_live,
        "vmrss_after_kib": after_live,
        "historic_replay_function_sha256": exact_function,
    }, sort_keys=True), flush=True)


def median(v: list[float]) -> float:
    return float(statistics.median(v))


def summarize(samples: list[dict]) -> dict:
    cols = (
        "wall_ns", "cpu_ns", "ru_maxrss_after_kib",
        "ru_maxrss_increment_kib", "vmrss_before_kib", "vmrss_after_kib",
    )
    out = {}
    for name in cols:
        v = [row[name] for row in samples if row[name] is not None]
        out[name] = {"median": median(v), "raw": v} if v else None
    return out


def run_parent(destination: Path, repeats: int, sizes: tuple[int, ...]) -> None:
    from v031_signed_delta_replay_o0 import PAYLOAD, make_case
    from cmpct.builder import Builder

    head = git("rev-parse", "HEAD")
    assert head == os.environ["EVIDENCE_HEAD"], "exact HEAD checkout mismatch"
    assert git("cat-file", "-t", HISTORIC_VALIDATION_BLOB) == "blob"
    destination.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": "v031-fresh-process-rss-o4",
        "status": "RESEARCH_ONLY_NOT_PROMOTION",
        "base_combined_head": COMBINED_HEAD,
        "source_head": head,
        "historic_validation_blob": HISTORIC_VALIDATION_BLOB,
        "python": sys.version,
        "platform": platform.platform(),
        "kernel": platform.release(),
        "rss_units": "Linux ru_maxrss KiB; /proc/self/status VmRSS KiB",
        "timing": "preflight_archive in child, excludes subprocess/interpreter startup",
        "semantics": "exact same authenticated bytes per engine and run; historical _apply_delta transplanted source-exact only",
        "sizes": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-preflight-rss-o4-") as td:
        root = Path(td)
        inputs = root / "input"
        inputs.mkdir()
        (inputs / "single.bin").write_bytes(PAYLOAD)
        source = root / "builder.cmpct"
        Builder(inputs, workers=1, reproducible=True).build(source)
        for n in sizes:
            delta, checkpoint, case = make_case(root, source, n)
            assert archive_hash(delta) == case["delta_sha256"]
            assert archive_hash(checkpoint) == case["checkpoint_sha256"]
            receipt_case = {"corpus": case, "samples": {}, "summary": {}}
            # Deterministic rotated paired order keeps both engines close in
            # time while each subprocess owns an independent RSS high-water mark.
            for kind, path in (("delta", delta), ("checkpoint", checkpoint)):
                samples = {"historical": [], "combined": []}
                for repetition in range(repeats):
                    order = ("historical", "combined") if repetition % 2 == 0 else ("combined", "historical")
                    for engine in order:
                        child = subprocess.run([
                            sys.executable, str(Path(__file__).resolve()),
                            "--child", "--engine", engine, "--archive", str(path),
                            "--expected-sha256", archive_hash(path),
                            "--expected-files", str(n), "--kind", kind,
                        ], cwd=Path.cwd(), capture_output=True, text=True, check=False,
                           timeout=90, env=os.environ.copy())
                        if child.returncode:
                            raise RuntimeError(f"{engine} {n} {kind} child failed {child.returncode}: {child.stderr[-6000:]}")
                        row = json.loads(child.stdout.strip())
                        assert row["preflight_files"] == n
                        samples[engine].append(row)
                receipt_case["samples"][kind] = samples
                receipt_case["summary"][kind] = {name: summarize(rows) for name, rows in samples.items()}
                h = receipt_case["summary"][kind]["historical"]
                c = receipt_case["summary"][kind]["combined"]
                print(
                    f"N={n} {kind}: historic {h['wall_ns']['median']/1e6:.3f}ms "
                    f"combined {c['wall_ns']['median']/1e6:.3f}ms; "
                    f"peak-RSS {h['ru_maxrss_after_kib']['median']:.0f}/{c['ru_maxrss_after_kib']['median']:.0f}KiB "
                    f"(historical/combined)", flush=True,
                )
            receipt["sizes"][str(n)] = receipt_case
    target = destination / "fresh-process-rss-o4.json"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("O4_RECEIPT_SHA256", archive_hash(target), "PATH", target, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(SIZES))
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--engine", choices=("historical", "combined"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-files", type=int)
    parser.add_argument("--kind", choices=("delta", "checkpoint"))
    args = parser.parse_args()
    if args.child:
        assert args.engine and args.archive and args.expected_sha256 and args.expected_files and args.kind
        run_child(args.engine, args.archive, args.expected_sha256, args.expected_files, args.kind)
        return
    if not args.out or args.repeats < 5 or any(n < 1 or n > 8192 for n in args.sizes):
        parser.error("require --out, >=5 repetitions, and file count in [1, 8192]")
    run_parent(args.out, args.repeats, tuple(args.sizes))


if __name__ == "__main__":
    main()
