from __future__ import annotations

"""Research-only attribution of promoted G04 physical-record decode cost.

Earlier exact-substrate oracles localized the ML verification regression to the one-pass G04 stream and then to
record() calls. This instrument times record cache hits and misses by record id while executing the unchanged
promoted policy verifier. After the measured interval it reads immutable record headers/transforms from the same
archive to classify miss cost by physical codec and geometry transform. No product decision, archive byte,
threshold, cache size, or integrity check is changed. Zero release credit.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
import traceback

from benchmarks import v030_release_performance as PERF

ENGINE = "v030-g04-record-decode-attribution-v1"
SUITE = "neutral_hostile_v1"
TARGET = "09_ml_artifacts"
REPETITIONS = 3


def _json_child(cmd: list[str]) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    proc = subprocess.run(cmd, text=True, capture_output=True, env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"child failed returncode={proc.returncode} cmd={cmd!r}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"child emitted no JSON: {cmd!r}")
    return json.loads(lines[-1])


def _codec_name(R, codec: int) -> str:
    O = R.G04.O
    if codec == O.CODEC_RAW:
        return "raw"
    if codec == O.CODEC_ZSTD:
        return "zstd"
    if codec == O.CODEC_PREFLATE:
        return "preflate"
    return f"unknown-{codec}"


def _transform_name(transform) -> str:
    if transform is None:
        return "none"
    return str(transform[0])


def _classify_records(R, archive: Path) -> list[dict]:
    session = R._G04Session(archive)
    try:
        rows = []
        for record_id, rel in enumerate(session.offsets):
            session.stream.seek(session.record_start + rel)
            header = session.stream.read(R.PH.size)
            if len(header) != R.PH.size:
                raise RuntimeError("short G04 record header during classification")
            codec, usize, csize, _crc, _sha = R.PH.unpack(header)
            rows.append(
                {
                    "record_id": record_id,
                    "codec": _codec_name(R, int(codec)),
                    "transform": _transform_name(session.transforms[record_id]),
                    "usize": int(usize),
                    "csize": int(csize),
                }
            )
        return rows
    finally:
        session.close()


def _worker(archive: Path) -> int:
    from experiments import entropygraph_v030_release_product as CANON

    R = CANON.POLICY.R
    Session = R._G04Session
    original_record = Session.record
    per_record: dict[int, dict] = {}
    totals = {
        "record_hit_calls": 0,
        "record_miss_calls": 0,
        "record_hit_wall_s": 0.0,
        "record_miss_wall_s": 0.0,
    }

    def timed_record(self, record_id):
        rid = int(record_id)
        hit = rid in self.record_cache
        started = time.perf_counter()
        try:
            return original_record(self, record_id)
        finally:
            dt = time.perf_counter() - started
            row = per_record.setdefault(
                rid,
                {"record_id": rid, "hit_calls": 0, "miss_calls": 0, "hit_wall_s": 0.0, "miss_wall_s": 0.0},
            )
            if hit:
                totals["record_hit_calls"] += 1
                totals["record_hit_wall_s"] += dt
                row["hit_calls"] += 1
                row["hit_wall_s"] += dt
            else:
                totals["record_miss_calls"] += 1
                totals["record_miss_wall_s"] += dt
                row["miss_calls"] += 1
                row["miss_wall_s"] += dt

    Session.record = timed_record
    try:
        started = time.perf_counter()
        with CANON.C._revision25_profile_context():
            result = dict(CANON.POLICY.strong_verify(archive))
        total_wall = time.perf_counter() - started
    finally:
        Session.record = original_record

    if not result.get("ok"):
        raise RuntimeError(f"policy verification failed: {result!r}")

    classes = {row["record_id"]: row for row in _classify_records(R, archive)}
    detailed = []
    by_codec = defaultdict(lambda: {"records": 0, "usize": 0, "csize": 0, "miss_wall_s": 0.0})
    by_transform = defaultdict(lambda: {"records": 0, "usize": 0, "csize": 0, "miss_wall_s": 0.0})
    by_codec_transform = defaultdict(lambda: {"records": 0, "usize": 0, "csize": 0, "miss_wall_s": 0.0})
    for rid in sorted(classes):
        cls = classes[rid]
        timing = per_record.get(rid, {"record_id": rid, "hit_calls": 0, "miss_calls": 0, "hit_wall_s": 0.0, "miss_wall_s": 0.0})
        row = dict(cls)
        row.update(timing)
        detailed.append(row)
        for key, bucket in (
            (cls["codec"], by_codec),
            (cls["transform"], by_transform),
            (f"{cls['codec']}+{cls['transform']}", by_codec_transform),
        ):
            agg = bucket[key]
            agg["records"] += 1
            agg["usize"] += cls["usize"]
            agg["csize"] += cls["csize"]
            agg["miss_wall_s"] += float(timing["miss_wall_s"])

    payload = {
        "wall_s": total_wall,
        **totals,
        "physical_record_reads": int(result.get("physical_record_reads", 0)),
        "logical_bytes": int(result.get("logical_bytes", 0)),
        "content_graph_tree_sha256": result.get("tree_sha256"),
        "records": detailed,
        "by_codec": dict(by_codec),
        "by_transform": dict(by_transform),
        "by_codec_transform": dict(by_codec_transform),
    }
    print(json.dumps(payload, separators=(",", ":")), flush=True)
    return 0


def _sum_groups(samples: list[dict], group_key: str) -> dict:
    keys = sorted({key for sample in samples for key in sample[group_key]})
    result = {}
    for key in keys:
        rows = [sample[group_key][key] for sample in samples]
        result[key] = {
            "records": int(rows[0]["records"]),
            "usize": int(rows[0]["usize"]),
            "csize": int(rows[0]["csize"]),
            "median_miss_wall_s": statistics.median(float(row["miss_wall_s"]) for row in rows),
        }
    return result


def run(work_root: Path) -> dict:
    from experiments import entropygraph_v030_release_product as CANON

    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = PERF.GENERAL._accepted_v029_rows()
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[(SUITE, TARGET)]
    archive = work_root / "archive" / "v030.cmpct"
    archive.parent.mkdir(parents=True, exist_ok=True)
    pack = _json_child([
        sys.executable, str(PERF.WORKER), "--engine", "v030", "--op", "pack",
        "--source", str(source), "--archive", str(archive),
    ])
    if pack.get("build_stats", {}).get("selected") != "g04-overlay":
        raise RuntimeError(f"target no longer selects G04: {pack.get('build_stats', {}).get('selected')!r}")

    expected = accepted[(SUITE, TARGET)]
    historical_tree = PERF.GENERAL._historical_treehash(source)
    if historical_tree != expected["tree_sha256"]:
        raise RuntimeError(f"historical source drift: {historical_tree} != {expected['tree_sha256']}")
    semantic_user_tree = CANON.treehash(source)

    samples = []
    for rep in range(REPETITIONS):
        row = _json_child([sys.executable, str(Path(__file__).resolve()), "--worker", "--archive", str(archive)])
        row["rep"] = rep
        samples.append(row)

    graph_tree = samples[0]["content_graph_tree_sha256"]
    physical_reads = int(samples[0]["physical_record_reads"])
    record_count = len(samples[0]["records"])
    for sample in samples:
        if sample["content_graph_tree_sha256"] != graph_tree:
            raise RuntimeError("content graph identity drift")
        if int(sample["physical_record_reads"]) != physical_reads:
            raise RuntimeError("physical record read drift")
        if int(sample["record_miss_calls"]) != physical_reads:
            raise RuntimeError("record miss count disagrees with promoted physical read count")
        if len(sample["records"]) != record_count:
            raise RuntimeError("record classification count drift")
        if sum(int(row["miss_calls"]) for row in sample["records"]) != physical_reads:
            raise RuntimeError("per-record misses do not reconcile")

    med_wall = statistics.median(float(s["wall_s"]) for s in samples)
    med_hit = statistics.median(float(s["record_hit_wall_s"]) for s in samples)
    med_miss = statistics.median(float(s["record_miss_wall_s"]) for s in samples)
    med_record = med_hit + med_miss
    comparison = {
        "median_policy_verify_wall_s": med_wall,
        "median_record_hit_wall_s": med_hit,
        "median_record_miss_wall_s": med_miss,
        "median_record_total_wall_s": med_record,
        "record_hit_fraction_of_policy": med_hit / max(med_wall, 1e-9),
        "record_miss_fraction_of_policy": med_miss / max(med_wall, 1e-9),
        "record_miss_fraction_of_record_time": med_miss / max(med_record, 1e-9),
        "median_record_hit_calls": statistics.median(int(s["record_hit_calls"]) for s in samples),
        "median_record_miss_calls": statistics.median(int(s["record_miss_calls"]) for s in samples),
        "physical_record_reads": physical_reads,
        "record_count": record_count,
        "by_codec": _sum_groups(samples, "by_codec"),
        "by_transform": _sum_groups(samples, "by_transform"),
        "by_codec_transform": _sum_groups(samples, "by_codec_transform"),
    }
    return {
        "engine": ENGINE,
        "status": "PASS",
        "evidence_class": "research-oracle-instrumented",
        "product_release_credit": False,
        "claim": "attribute G04 record() cost between cache hits and physical decode misses, then classify miss cost by physical codec and geometry transform",
        "contract": {
            "suite": SUITE,
            "workload": TARGET,
            "historical_substrate_tree_sha256": historical_tree,
            "semantic_user_tree_sha256": semantic_user_tree,
            "content_graph_tree_sha256": graph_tree,
            "accepted_v029_bytes": int(expected["accepted_v029_bytes"]),
            "v030_archive_bytes": int(pack["archive_bytes"]),
            "v030_selected": pack["build_stats"]["selected"],
            "repetitions": REPETITIONS,
            "fresh_process_per_sample": True,
            "same_archive_all_samples": True,
            "classification_after_measured_interval": True,
            "instrumentation_only": True,
            "product_code_changed": False,
            "release_thresholds_changed": False,
        },
        "comparison": comparison,
        "samples": samples,
    }


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/g04-record-decode-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-record-decode.json"))
    args = parser.parse_args()
    if args.worker:
        if args.archive is None:
            parser.error("--worker requires --archive")
        raise SystemExit(_worker(args.archive))
    try:
        result = run(args.work_root)
    except BaseException as exc:
        _write(args.output, {
            "engine": ENGINE, "status": "HARNESS_FAILURE", "evidence_class": "research-oracle-instrumented",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        })
        raise
    _write(args.output, result)
    print(json.dumps(result["comparison"], indent=2), flush=True)


if __name__ == "__main__":
    main()
