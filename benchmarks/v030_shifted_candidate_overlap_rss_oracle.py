from __future__ import annotations

"""Exact fresh-process attribution of Shifted candidate-family overlap RSS.

The canonical r25 candidate builder intentionally overlaps PrefixGraph with G0-G4 to reduce wall time. Existing
phase evidence shows that the full Shifted product peak is materially above isolated r24 construction, but a
process high-water mark alone cannot prove that cross-family overlap owns the excess. This oracle measures the
three decisive arms in fresh processes on the exact frozen Shifted source: G0-G4 alone, PrefixGraph alone, and the
unchanged canonical overlapped candidate builder.

It is diagnostic only. It changes no production scheduling, candidate set, tournament, archive grammar, selector,
locality ceiling, decode-unit ceiling, integrity rule or release threshold. Correctness is checked after the RSS and
wall snapshots so reader allocations cannot contaminate construction attribution. The overlapped result must equal
one of the exact individually constructed candidate byte streams; otherwise the experiment fails closed.
"""

import argparse
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

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF

ROOT = Path(__file__).resolve().parents[1]
SUITE = "resemblance_hostile_v1"
TARGET = "01_shifted_versions"
MODES = ("g04", "prefixgraph", "overlap")
ROUNDS = 2


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _worker(mode: str, source: Path, work_root: Path) -> dict:
    # Import the complete canonical surface before the baseline sample so module/import ownership is equal.
    from experiments import entropygraph_v030_canonical_final as canonical

    source = Path(source)
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    archive = work_root / f"{mode}.cmpct"
    source_tree = canonical.treehash(source)
    baseline_rss = _rss_kib()
    started = time.perf_counter()

    if mode == "g04":
        stats = dict(canonical.RC.G04.build(source, archive))
    elif mode == "prefixgraph":
        stats = dict(canonical.RC.PG.build(source, archive))
    elif mode == "overlap":
        stats = dict(canonical.RC.build(source, archive))
    else:  # pragma: no cover - argparse constrains this.
        raise ValueError(mode)

    wall_s = time.perf_counter() - started
    operation_peak_rss = _rss_kib()
    archive_bytes = archive.stat().st_size
    archive_sha256 = _sha256_file(archive)

    # Semantic checks intentionally occur after timing/RSS snapshots.
    if mode == "g04":
        verified = dict(canonical.RC.G04.strong_verify(archive))
    elif mode == "prefixgraph":
        verified = dict(canonical.RC.PG.strong_verify(archive))
    else:
        verified = dict(canonical.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError(f"{mode} candidate failed semantic verification: {verified!r}")

    return {
        "mode": mode,
        "source_tree_sha256": source_tree,
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_sha256,
        "wall_s": wall_s,
        "baseline_rss_kib": baseline_rss,
        "operation_peak_rss_kib": operation_peak_rss,
        "incremental_peak_rss_kib": max(0, operation_peak_rss - baseline_rss),
        "build_stats": stats,
        "verified_tree_sha256": verified.get("tree_sha256"),
    }


def _run_worker(mode: str, source: Path, work_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-mode",
            mode,
            "--source",
            str(source),
            "--work-root",
            str(work_root),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # CI must expose the child traceback. The first version used check=True, which hid the only actionable
        # diagnostic behind CalledProcessError and turned a harness defect into an opaque red lane.
        raise RuntimeError(
            f"candidate-overlap worker failed for {mode} rc={proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"candidate-overlap worker emitted no JSON for {mode}: {proc.stderr!r}")
    return json.loads(lines[-1])


def _ratio(num: float, den: float) -> float | None:
    return None if den <= 0 else float(num) / float(den)


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]
    expected_tree = str(accepted[(SUITE, TARGET)]["tree_sha256"])
    if GENERAL._historical_treehash(source) != expected_tree:
        raise RuntimeError("Shifted candidate-overlap source drifted from accepted v0.29 authority")

    repetitions: list[dict] = []
    for rep, order in enumerate((MODES, tuple(reversed(MODES)))):
        measured: dict[str, dict] = {}
        for mode in order:
            measured[mode] = _run_worker(mode, source, work_root / "arms" / f"r{rep}-{mode}")
            if measured[mode]["source_tree_sha256"] != expected_tree:
                raise RuntimeError(f"{mode} source tree drift in repetition {rep}")
        repetitions.append(measured)

    # Every arm must be deterministic across fresh processes.
    for mode in MODES:
        shas = {rep[mode]["archive_sha256"] for rep in repetitions}
        sizes = {int(rep[mode]["archive_bytes"]) for rep in repetitions}
        trees = {rep[mode]["verified_tree_sha256"] for rep in repetitions}
        if len(shas) != 1 or len(sizes) != 1 or trees != {expected_tree}:
            raise RuntimeError(f"{mode} candidate drift across fresh-process repetitions")

    component_shas = {
        repetitions[0]["g04"]["archive_sha256"],
        repetitions[0]["prefixgraph"]["archive_sha256"],
    }
    overlap_sha = repetitions[0]["overlap"]["archive_sha256"]
    if overlap_sha not in component_shas:
        raise RuntimeError("overlapped canonical tournament emitted bytes unequal to either exact component")

    med = {}
    for mode in MODES:
        med[mode] = {
            "wall_s": statistics.median(rep[mode]["wall_s"] for rep in repetitions),
            "baseline_rss_kib": statistics.median(rep[mode]["baseline_rss_kib"] for rep in repetitions),
            "operation_peak_rss_kib": statistics.median(rep[mode]["operation_peak_rss_kib"] for rep in repetitions),
            "incremental_peak_rss_kib": statistics.median(rep[mode]["incremental_peak_rss_kib"] for rep in repetitions),
            "archive_bytes": int(repetitions[0][mode]["archive_bytes"]),
            "archive_sha256": repetitions[0][mode]["archive_sha256"],
        }

    isolated_max = max(med["g04"]["incremental_peak_rss_kib"], med["prefixgraph"]["incremental_peak_rss_kib"])
    isolated_sum = med["g04"]["incremental_peak_rss_kib"] + med["prefixgraph"]["incremental_peak_rss_kib"]
    serial_wall_lower_bound = med["g04"]["wall_s"] + med["prefixgraph"]["wall_s"]
    return {
        "schema": "cmpct-v030-shifted-candidate-overlap-rss-v1",
        "target": f"{SUITE}/{TARGET}",
        "rounds": ROUNDS,
        "expected_historical_tree_sha256": expected_tree,
        "repetitions": repetitions,
        "median": med,
        "derived": {
            "overlap_to_max_isolated_rss_ratio": _ratio(med["overlap"]["incremental_peak_rss_kib"], isolated_max),
            "overlap_to_sum_isolated_rss_ratio": _ratio(med["overlap"]["incremental_peak_rss_kib"], isolated_sum),
            "overlap_wall_vs_serial_components_ratio": _ratio(med["overlap"]["wall_s"], serial_wall_lower_bound),
            "isolated_component_rss_sum_kib": isolated_sum,
            "isolated_component_rss_max_kib": isolated_max,
            "serial_component_wall_sum_s": serial_wall_lower_bound,
        },
        "contract": {
            "fresh_process_per_arm": True,
            "operation_rss_snapshot_precedes_correctness_checks": True,
            "overlap_uses_unchanged_canonical_scheduler": True,
            "individual_arms_use_unchanged_canonical_component_builders": True,
            "overlap_output_must_equal_exact_component_bytes": True,
            "archive_bytes_changed": False,
            "selector_changed": False,
            "scheduling_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "rss_release_threshold_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
        },
        "experiment_valid": True,
        "promotion_signal": False,
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-candidate-overlap-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-candidate-overlap-rss.json"))
    parser.add_argument("--worker-mode", choices=MODES)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()

    if args.worker_mode:
        if args.source is None:
            raise SystemExit("--source is required with --worker-mode")
        print(json.dumps(_worker(args.worker_mode, args.source, args.work_root), separators=(",", ":"), default=str))
        return

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"median": result["median"], "derived": result["derived"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
