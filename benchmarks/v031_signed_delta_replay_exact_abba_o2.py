#!/usr/bin/env python3
"""O2 research: authentic historical vs indexed preflight on byte-identical signed r24 inputs.

Evidence-only: same-host, source-bound paired ABBA/BAAB; not the release gate.
The entire historical validation module comes from a pinned Git blob, rather
than reconstructing its historical _apply_delta in a benchmark surrogate.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.validation as candidate

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v031_signed_delta_replay_o0 import PAYLOAD, make_case  # frozen O0 fixture generator


BASE_COMMIT = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
BASE_BLOB = "51c2849061f99a4afeddb7666956b24566ce7de0"
CANDIDATE_COMMIT = "fb887d8610dced551acf5a84778ba539d08dac59"
SOURCE = "src/cmpct/validation.py"
DEPENDENCIES = ("src/cmpct/codec.py", "src/cmpct/path_policy.py")


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], check=True, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def actual_modules(tmp: Path):
    head = git("rev-parse", "HEAD").decode().strip()
    git("merge-base", "--is-ancestor", CANDIDATE_COMMIT, head)
    base_name = git("rev-parse", f"{BASE_COMMIT}:{SOURCE}").decode().strip()
    assert base_name == BASE_BLOB, (base_name, BASE_BLOB)
    baseline = git("cat-file", "blob", BASE_BLOB)
    assert git("hash-object", "--stdin", data=baseline).decode().strip() == BASE_BLOB

    candidate_bytes = Path(candidate.__file__).read_bytes()
    pinned = git("show", f"{CANDIDATE_COMMIT}:{SOURCE}")
    assert candidate_bytes == pinned, "candidate validation module changed from O1 head"
    candidate_blob = git("hash-object", "--stdin", data=candidate_bytes).decode().strip()

    # Relative dependencies must be identical to the source baseline, otherwise
    # a historic validation module in the present package is not an exact control.
    for path in DEPENDENCIES:
        assert git("show", f"{BASE_COMMIT}:{path}") == git("show", f"{CANDIDATE_COMMIT}:{path}"), path
        assert git("show", f"{CANDIDATE_COMMIT}:{path}") == Path(path).read_bytes(), path

    baseline_path = tmp / "baseline_exact_validation.py"
    baseline_path.write_bytes(baseline)
    name = "cmpct._source_exact_o2_legacy_validation"
    spec = importlib.util.spec_from_file_location(name, baseline_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    assert Path(mod.__file__).read_bytes() == baseline
    return mod, {
        "base_commit": BASE_COMMIT, "base_validation_blob": BASE_BLOB,
        "candidate_source_commit": CANDIDATE_COMMIT,
        "candidate_validation_blob": candidate_blob,
        "exact_workflow_head": head,
        "sha256_baseline_module": digest(baseline),
        "sha256_candidate_module": digest(candidate_bytes),
        "shared_deps": list(DEPENDENCIES),
        "historical_full_validator_loaded": True,
    }


def attach_attribution(module):
    old = module._apply_delta
    ticks = []

    def attributed(*args, **kwargs):
        start = time.perf_counter_ns()
        try:
            return old(*args, **kwargs)
        finally:
            ticks.append(time.perf_counter_ns() - start)

    module._apply_delta = attributed
    return ticks


def one_call(module, archive: Path, ticks: list[int]):
    ticks.clear()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    result = module.preflight_archive(archive)
    cpu = time.process_time_ns() - cpu_start
    wall = time.perf_counter_ns() - wall_start
    return {"wall_ns": wall, "cpu_ns": cpu, "replay_ns": sum(ticks),
            "replay_calls": len(ticks)}, result


def memory_probe(module, archive: Path):
    """Isolate Python allocation measurement from all time trials."""
    gc.collect()
    tracemalloc.start()
    tracemalloc.reset_peak()
    result = module.preflight_archive(archive)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"peak_traced_bytes": peak, "postcall_traced_bytes": current,
            "files": result["files"]}


def median_ms(samples, field):
    return statistics.median(x[field] for x in samples) / 1e6


def trial(baseline, meta: dict, delta: Path, checkpoint: Path, repeats: int, ticks):
    modules = {"historical": baseline, "indexed": candidate}
    paths = {"delta": delta, "checkpoint": checkpoint}
    expect = {"delta": baseline.preflight_archive(delta),
              "checkpoint": baseline.preflight_archive(checkpoint)}
    assert expect["delta"] == candidate.preflight_archive(delta)
    assert expect["checkpoint"] == candidate.preflight_archive(checkpoint)
    assert expect["delta"]["files"] == expect["checkpoint"]["files"] == meta["file_count"]
    assert expect["delta"]["delta_depth"] == 1 and expect["checkpoint"]["delta_depth"] == 0

    samples = {label: {which: [] for which in paths} for label in modules}
    for name, mod in modules.items():
        for kind, path in paths.items():
            one_call(mod, path, ticks[name])  # bounded warmup outside measurements

    for round_no in range(repeats):
        # True source A/B B/A, reversing the whole order on alternate rounds.
        order = ("historical", "indexed", "indexed", "historical")
        if round_no % 2:
            order = tuple(reversed(order))
        for which in order:
            kinds = ("delta", "checkpoint") if round_no % 2 == 0 else ("checkpoint", "delta")
            for kind in kinds:
                measured, answer = one_call(modules[which], paths[kind], ticks[which])
                assert answer == expect[kind], f"source {which} disagrees on {kind}"
                assert measured["replay_calls"] == (1 if kind == "delta" else 0)
                samples[which][kind].append(measured)

    # tracemalloc changes interpreter costs substantially: separate, untimed court.
    memory = {
        which: {kind: memory_probe(modules[which], path) for kind, path in paths.items()}
        for which, mod in modules.items()
    }
    medians = {
        which: {kind: {
            "wall_ms": median_ms(samples[which][kind], "wall_ns"),
            "cpu_ms": median_ms(samples[which][kind], "cpu_ns"),
            "replay_ms": median_ms(samples[which][kind], "replay_ns"),
        } for kind in paths}
        for which in modules
    }
    base = medians["historical"]["delta"]["wall_ms"]
    chosen = medians["indexed"]["delta"]["wall_ms"]
    assert chosen > 0
    return {
        "identity": meta,
        "preflight_answers": expect,
        "raw_samples_ns": samples,
        "summary_median": medians,
        "tracemalloc_separate_pass": memory,
        "observed_delta_wall_ratio_historical_over_candidate": base / chosen,
        "comparison_scope": "same-host/full-historical-validation-module/same-archive-bytes",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--sizes", type=int, nargs="+", default=[128, 512, 2048, 4096])
    args = parser.parse_args()
    if args.repeats < 3 or any(n < 1 or n > 8192 for n in args.sizes):
        parser.error("bad court size/repetitions")
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-o2-source-exact-") as folder:
        tmp = Path(folder)
        baseline, source = actual_modules(tmp)
        tree = tmp / "input"
        tree.mkdir()
        (tree / "single.bin").write_bytes(PAYLOAD)
        source_archive = tmp / "builder.cmpct"
        Builder(tree, workers=1, reproducible=True).build(source_archive)
        with CMPCT(source_archive) as reader:
            assert reader.read("single.bin") == PAYLOAD
        receipt = {
            "experiment": "source-exact-signed-delta-replay-o2",
            "status": "FOCUSED_RESEARCH_NOT_RELEASE",
            "source": source,
            "host": platform.platform(),
            "python": sys.version,
            "semantics": "identical signed r24 delta/checkpoint bytes for both sources; full historic module",
            "repeats": args.repeats,
            "cases": {},
        }
        ticks = {"historical": attach_attribution(baseline),
                 "indexed": attach_attribution(candidate)}
        for n in args.sizes:
            delta, checkpoint, meta = make_case(tmp, source_archive, n)
            # Same files reused on both validators; keep their complete SHA in receipt.
            assert digest(delta.read_bytes()) == meta["delta_sha256"]
            assert digest(checkpoint.read_bytes()) == meta["checkpoint_sha256"]
            item = trial(baseline, meta, delta, checkpoint, args.repeats, ticks)
            receipt["cases"][str(n)] = item
            print("O2_RESULT " + json.dumps({
                "n": n,
                "historical_delta_wall_ms": item["summary_median"]["historical"]["delta"]["wall_ms"],
                "indexed_delta_wall_ms": item["summary_median"]["indexed"]["delta"]["wall_ms"],
                "historical_checkpoint_wall_ms": item["summary_median"]["historical"]["checkpoint"]["wall_ms"],
                "indexed_checkpoint_wall_ms": item["summary_median"]["indexed"]["checkpoint"]["wall_ms"],
                "ratio": item["observed_delta_wall_ratio_historical_over_candidate"],
                "complete_delta_bytes": meta["delta_archive_bytes"],
            }), flush=True)
    output = args.out / "source-exact-abba-o2.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("O2_RECEIPT " + str(output) + " SHA256=" + digest(output.read_bytes()), flush=True)


if __name__ == "__main__":
    main()
