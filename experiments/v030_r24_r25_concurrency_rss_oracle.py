from __future__ import annotations

"""Research-only attribution of canonical product create RSS to r24/r25 concurrency.

The shipping canonical builder intentionally constructs complete r24 and r25 candidates concurrently before
choosing the smaller valid product. The frozen runtime gate's worst measured pack-RSS regression is
`resemblance_hostile_v1/01_shifted_versions`, so this oracle targets that exact release workload. It changes
*only scheduling* in a separate diagnostic process: the control runs the real concurrent builder; the treatment
monkeypatches the builder's ThreadPoolExecutor with an API-compatible synchronous executor. All product builders,
grammars, selectors, thresholds, and verification remain unchanged.

Promotion criteria are deliberately absent: this experiment receives zero release credit. Its sole question is
causal attribution. If serial scheduling materially lowers peak RSS while emitting byte-identical archives,
concurrency owns measurable memory debt; if not, the memory search must move deeper into candidate construction.

The top-level harness deliberately persists structured failure evidence before returning nonzero. A broken
oracle must remain red, but it must not become an opaque red check that erases the causal information needed by
the next zero-history agent.
"""

import argparse
from concurrent.futures import Future
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_release_generalization as GATE

ENGINE = "v030-r24-r25-concurrency-rss-oracle-v1"
SUITE = "resemblance_hostile_v1"
TARGET = "01_shifted_versions"


class SerialExecutor:
    def __init__(self, max_workers: int | None = None, **_kwargs):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, /, *args, **kwargs):
        future = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # preserve Future.result() behavior
            future.set_exception(exc)
        return future


def _worker(root: Path, out: Path, mode: str) -> int:
    # Import after process startup so both modes pay the same module-loading footprint.
    from experiments import entropygraph_v030_canonical_final_impl as IMPL
    from experiments import entropygraph_v030_release_product as CANON

    if mode == "serial":
        IMPL.ThreadPoolExecutor = SerialExecutor
    elif mode != "concurrent":
        raise ValueError(mode)

    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.perf_counter()
    stats = dict(CANON.build(root, out))
    wall = time.perf_counter() - started
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    verified = CANON.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"strong verification failed: {verified!r}")
    payload = {
        "mode": mode,
        "wall_s": wall,
        "ru_maxrss_kib": int(after),
        "ru_maxrss_before_kib": int(before),
        "archive_bytes": out.stat().st_size,
        "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "tree_sha256": verified.get("tree_sha256"),
        "format_revision": verified.get("format_revision"),
        "format_profile": verified.get("format_profile"),
        "selected": stats.get("selected"),
        "r24_product_bytes": stats.get("r24_product_bytes"),
        "r25_product_bytes": stats.get("r25_product_bytes"),
        "v029_research_floor_bytes": stats.get("v029_research_floor_bytes"),
    }
    print(json.dumps(payload), flush=True)
    return 0


def _run_child(root: Path, out: Path, mode: str) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", "--root", str(root), "--archive", str(out), "--mode", mode]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{mode} worker failed\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"{mode} worker emitted no JSON")
    return json.loads(lines[-1])


def run(work_root: Path, repetitions: int) -> dict:
    if repetitions < 2:
        raise ValueError("repetitions must be >=2")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    hostile = V029._load(
        V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_concurrency_rss_hostile",
    )
    corpus_root = work_root / "resemblance"
    hostile.build(corpus_root)
    target = corpus_root / TARGET
    if not target.is_dir():
        candidates = sorted(p.name for p in corpus_root.iterdir() if p.is_dir())
        raise RuntimeError(f"target {TARGET!r} not found; got {candidates}")

    accepted = GATE._accepted_v029_rows()[(SUITE, TARGET)]
    historical_tree = GATE._historical_treehash(target)
    if historical_tree != accepted["tree_sha256"]:
        raise RuntimeError(f"historical source drift: {historical_tree} != {accepted['tree_sha256']}")

    samples = {"concurrent": [], "serial": []}
    # Interleave modes by repetition so shared-host drift cannot systematically favor one side.
    for i in range(repetitions):
        order = ("concurrent", "serial") if i % 2 == 0 else ("serial", "concurrent")
        for mode in order:
            out = work_root / "archives" / f"{mode}-{i}.cmpct"
            out.parent.mkdir(parents=True, exist_ok=True)
            sample = _run_child(target, out, mode)
            sample["repetition"] = i
            samples[mode].append(sample)
            print(json.dumps(sample), flush=True)

    identities = {
        (sample["archive_bytes"], sample["archive_sha256"], sample["tree_sha256"], sample["format_revision"], sample["format_profile"])
        for mode in samples.values() for sample in mode
    }
    byte_identical = len(identities) == 1
    summaries = {}
    for mode, values in samples.items():
        summaries[mode] = {
            "median_wall_s": statistics.median(float(v["wall_s"]) for v in values),
            "median_ru_maxrss_kib": statistics.median(int(v["ru_maxrss_kib"]) for v in values),
            "max_ru_maxrss_kib": max(int(v["ru_maxrss_kib"]) for v in values),
            "archive_bytes": values[0]["archive_bytes"],
            "archive_sha256": values[0]["archive_sha256"],
            "format_revision": values[0]["format_revision"],
            "format_profile": values[0]["format_profile"],
            "selected": values[0]["selected"],
        }
    c = summaries["concurrent"]
    s = summaries["serial"]
    comparison = {
        "byte_identical_outputs": byte_identical,
        "serial_vs_concurrent_wall_ratio": s["median_wall_s"] / c["median_wall_s"],
        "serial_vs_concurrent_median_rss_ratio": s["median_ru_maxrss_kib"] / c["median_ru_maxrss_kib"],
        "serial_rss_reduction_kib": c["median_ru_maxrss_kib"] - s["median_ru_maxrss_kib"],
        "serial_rss_reduction_fraction": 1.0 - (s["median_ru_maxrss_kib"] / c["median_ru_maxrss_kib"]),
    }
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "causal attribution of canonical create RSS to concurrent versus serial r24/r25 construction",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_tree_sha256": historical_tree,
            "accepted_v029_bytes": int(accepted["accepted_v029_bytes"]),
            "repetitions_per_mode": repetitions,
            "only_scheduling_changed": True,
            "product_grammar_changed": False,
            "selector_changed": False,
            "release_thresholds_changed": False,
        },
        "summaries": summaries,
        "comparison": comparison,
        "samples": samples,
    }


def _write_result(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _failure_payload(args: argparse.Namespace, exc: BaseException) -> dict:
    return {
        "engine": ENGINE,
        "status": "HARNESS_FAILURE",
        "evidence_class": "research-oracle",
        "product_release_credit": False,
        "claim": "causal attribution of canonical create RSS to concurrent versus serial r24/r25 construction",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "repetitions_per_mode": int(args.repetitions),
            "only_scheduling_changed": True,
            "product_grammar_changed": False,
            "selector_changed": False,
            "release_thresholds_changed": False,
        },
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(limit=24),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--mode", choices=("concurrent", "serial"))
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/concurrency-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/concurrency-rss.json"))
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    if args.worker:
        if args.root is None or args.archive is None or args.mode is None:
            parser.error("--worker requires --root, --archive, and --mode")
        raise SystemExit(_worker(args.root, args.archive, args.mode))

    try:
        result = run(args.work_root, args.repetitions)
    except BaseException as exc:
        # Preserve failure as structured evidence while retaining a red process exit.
        _write_result(args.output, _failure_payload(args, exc))
        raise

    _write_result(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
