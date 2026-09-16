from __future__ import annotations

"""Exact-byte Shifted A/B: 4-worker shipping vs 3-worker provable-loser terminals.

The four-worker PrefixGraph RSS peak is now causally attributed to simultaneously live
Zstd level-19 CCtx workspaces.  Merely lowering worker count saves memory but previously
missed the wall-time envelope.  This oracle asks whether an *exact* terminal can recover
that time without guessing about similarity or benchmark identity.

For each anchor, a probe follows the historical candidate's original member order and
uses the same raw-prefix compressor and exact MIN_PREFIX_PAYLOAD_SAVING choice.  After
each decided payload, it computes a deliberately weak lower bound on the final complete
artifact: immutable header+footer bytes plus payload bytes already forced by that exact
candidate prefix (including the anchor's mandatory direct payload).  Unseen payloads and
both metadata copies are optimistically priced at zero.  Therefore if this lower bound
is strictly greater than the current complete incumbent size, that anchor cannot win
under any possible continuation and may be abandoned. Equal-size cases are never pruned.

Surviving anchors are rebuilt by the unchanged historical serializer, so only impossible
losers can avoid construction.  The A/B requires exact archive SHA/tree identity and
fresh-process RSS/time evidence.  It is research-only even if 3 workers crosses both the
<=0.75 RSS and <=1.05 wall ratios against shipping.
"""

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import threading
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_prefixgraph as BASE
from experiments import entropygraph_v030_prefixgraph_parallel as SHIPPING

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
ROUNDS = 2
CANDIDATE_WORKERS = 3
MAX_RSS_RATIO = 0.75
MAX_WALL_RATIO = 1.05


def _rss_kib() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_build(source: Path, archive: Path) -> dict:
    files = sorted(p for p in source.rglob("*") if p.is_file())
    rels = [p.relative_to(source).as_posix() for p in files]
    raws = [p.read_bytes() for p in files]
    expected_tree = BASE._treehash_parts(rels, raws)
    direct = [BASE._compress(raw) for raw in raws]
    direct_blob, direct_stats = BASE._serialize_candidate(rels, raws, direct, expected_tree, None)
    best = [direct_blob, direct_stats]
    lock = threading.Lock()
    terminal_anchors: list[int] = []
    completed_anchors: list[int] = []
    probe_compressions = 0

    def incumbent_bytes() -> int:
        with lock:
            return len(best[0])

    def probe(anchor: int):
        nonlocal probe_compressions
        compressor, dictionary = BASE._prefix_codec(raws[anchor])
        # The anchor itself is always direct, even before its position is reached.
        forced_payload_bytes = len(direct[anchor])
        minimum_complete_bytes = BASE.HEADER.size + BASE.FOOTER.size
        local_compressions = 0
        for index, (raw, direct_payload) in enumerate(zip(raws, direct, strict=True)):
            if index == anchor:
                continue
            chosen_len = len(direct_payload)
            if raw and raws[anchor]:
                trial = compressor.compress(raw)
                local_compressions += 1
                if len(direct_payload) - len(trial) >= BASE.MIN_PREFIX_PAYLOAD_SAVING:
                    chosen_len = len(trial)
            forced_payload_bytes += chosen_len
            # Strict > only: ties remain in the exact historical tournament.
            if minimum_complete_bytes + forced_payload_bytes > incumbent_bytes():
                with lock:
                    probe_compressions += local_compressions
                    terminal_anchors.append(anchor)
                return None
        del compressor, dictionary
        candidate = BASE._serialize_candidate(rels, raws, direct, expected_tree, anchor)
        with lock:
            probe_compressions += local_compressions
            completed_anchors.append(anchor)
        return candidate

    anchors = BASE._anchor_indices(len(raws))
    with ThreadPoolExecutor(max_workers=CANDIDATE_WORKERS, thread_name_prefix="cmpct-pg-exact-lb") as pool:
        pending = {}
        anchor_iter = iter(anchors)

        def submit_one() -> bool:
            try:
                anchor = next(anchor_iter)
            except StopIteration:
                return False
            pending[pool.submit(probe, anchor)] = anchor
            return True

        for _ in range(CANDIDATE_WORKERS):
            if not submit_one():
                break
        while pending:
            done, _ = wait(tuple(pending), return_when=FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                candidate = future.result()
                if candidate is not None:
                    with lock:
                        if SHIPPING._candidate_key(candidate) < SHIPPING._candidate_key((best[0], best[1])):
                            best[0], best[1] = candidate
                submit_one()

    blob, stats = best
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(blob)
    verified = BASE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError("exact-lower-bound candidate failed strong verification")
    return {
        "archive_bytes": len(blob),
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "tree_sha256": expected_tree,
        "anchor_auditions": len(anchors),
        "terminal_anchors": sorted(terminal_anchors),
        "terminal_anchor_count": len(terminal_anchors),
        "fully_rebuilt_anchor_count": len(completed_anchors),
        "probe_compressions": probe_compressions,
        "selected_anchor": stats.get("anchor"),
    }


def _worker(mode: str, source: Path, archive: Path) -> dict:
    baseline = _rss_kib()
    started = time.perf_counter()
    if mode == "shipping":
        SHIPPING.MAX_ANCHOR_WORKERS = 4
        stats = SHIPPING.build(source, archive)
        detail = {"selected_anchor": stats.get("anchor"), "terminal_anchor_count": 0}
    elif mode == "exact-lb-w3":
        detail = _candidate_build(source, archive)
    else:
        raise ValueError(mode)
    wall = time.perf_counter() - started
    peak = _rss_kib()
    expected_tree = BASE.treehash(source)
    verified = BASE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"{mode} verification drift")
    return {
        "mode": mode,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha(archive),
        "tree_sha256": expected_tree,
        "wall_s": wall,
        "baseline_rss_kib": baseline,
        "peak_rss_kib": peak,
        "incremental_peak_rss_kib": peak - baseline,
        **detail,
    }


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, __file__, "--worker-mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, check=True, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(proc.stderr)
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    rounds = []
    for rep in range(ROUNDS):
        order = ("shipping", "exact-lb-w3") if rep == 0 else ("exact-lb-w3", "shipping")
        measured = {}
        for mode in order:
            measured[mode] = _run_worker(mode, source, work_root / f"r{rep}-{mode}.cmpct")
        identities = {(v["archive_bytes"], v["archive_sha256"], v["tree_sha256"]) for v in measured.values()}
        if len(identities) != 1:
            raise RuntimeError(f"exact lower-bound terminal changed winning archive identity: {identities!r}")
        rounds.append({"round": rep, "order": list(order), "measurements": measured})

    def med(mode: str, field: str) -> float:
        return float(statistics.median(float(r["measurements"][mode][field]) for r in rounds))

    shipping_wall = med("shipping", "wall_s")
    candidate_wall = med("exact-lb-w3", "wall_s")
    shipping_rss = med("shipping", "incremental_peak_rss_kib")
    candidate_rss = med("exact-lb-w3", "incremental_peak_rss_kib")
    wall_ratio = candidate_wall / max(shipping_wall, 1e-12)
    rss_ratio = candidate_rss / max(shipping_rss, 1.0)
    terminal_counts = [int(r["measurements"]["exact-lb-w3"]["terminal_anchor_count"]) for r in rounds]
    exact = all(
        r["measurements"]["shipping"]["archive_sha256"] == r["measurements"]["exact-lb-w3"]["archive_sha256"]
        for r in rounds
    )
    promotion = exact and rss_ratio <= MAX_RSS_RATIO and wall_ratio <= MAX_WALL_RATIO and min(terminal_counts) > 0
    return {
        "schema": "cmpct-v030-prefixgraph-exact-lb-w3-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "target": list(TARGET),
        "rounds": rounds,
        "summary": {
            "shipping_median_wall_s": shipping_wall,
            "candidate_median_wall_s": candidate_wall,
            "wall_ratio": wall_ratio,
            "shipping_median_incremental_peak_rss_kib": shipping_rss,
            "candidate_median_incremental_peak_rss_kib": candidate_rss,
            "rss_ratio": rss_ratio,
            "terminal_anchor_counts": terminal_counts,
        },
        "contract": {
            "candidate_workers": CANDIDATE_WORKERS,
            "terminal_law": "strict complete-artifact lower bound > current complete incumbent bytes",
            "unseen_payload_lower_bound_bytes": 0,
            "metadata_lower_bound_bytes": 0,
            "equal_size_terminal_allowed": False,
            "anchor_nomination_changed": False,
            "winning_candidate_serializer_changed": False,
            "tie_law_changed": False,
            "reader_changed": False,
            "grammar_changed": False,
            "release_credit": False,
            "maximum_rss_ratio": MAX_RSS_RATIO,
            "maximum_wall_ratio": MAX_WALL_RATIO,
        },
        "exact_archive_identity": exact,
        "promotion_signal": promotion,
        "release_credit": False,
        "claim_boundary": "Research-only exact terminal plus worker-cap A/B; any positive signal still requires productization and complete release authority.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-exact-lb-w3-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-exact-lb-w3.json"))
    p.add_argument("--worker-mode", choices=("shipping", "exact-lb-w3"))
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    args = p.parse_args()
    if args.worker_mode:
        if args.source is None or args.archive is None:
            raise SystemExit("worker mode requires --source and --archive")
        print(json.dumps(_worker(args.worker_mode, args.source, args.archive), separators=(",", ":")), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "exact_archive_identity": result["exact_archive_identity"], "promotion_signal": result["promotion_signal"]}, indent=2), flush=True)
    if not result["exact_archive_identity"]:
        raise SystemExit("exact lower-bound terminal identity mismatch")


if __name__ == "__main__":
    main()
