from __future__ import annotations

"""Research-only exact-byte A/B for caching repeated top-level SHA-256 work in EG08.

The EG08 graph hot-path profile shows SHA-256 as one of the dominant CPU owners.  The
v0.25 semantic builder currently hashes the same already-materialized top-level bytes
again while building multiple exact lookup tables and while probing inverse transforms.
This oracle changes only that computation: one authoritative SHA-256 is cached per
source file and reused wherever the baseline recomputes the identical digest.

No ZIP member is skipped, no equality condition is weakened, and no format/selector
semantics change.  Promotion requires byte-for-byte identical artifacts across every
paired run plus a material median wall-time saving.  This lane grants no release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tempfile
import time
import types

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from experiments import entropygraph_v025 as V25

ROUNDS = 11
MIN_MEDIAN_SAVING_S = 0.010

_OLD_INIT = "t0=time.perf_counter();files=sorted(p for p in ROOT.rglob('*') if p.is_file());rels={p:p.relative_to(ROOT).as_posix() for p in files};raws={p:p.read_bytes() for p in files}"
_NEW_INIT = """t0=time.perf_counter();files=sorted(p for p in ROOT.rglob('*') if p.is_file());rels={p:p.relative_to(ROOT).as_posix() for p in files};raws={p:p.read_bytes() for p in files]\n raw_hash={p:H(raws[p]) for p in files};top_by_hash={}\n for tp in files:top_by_hash.setdefault(raw_hash[tp],[]).append(tp)"""
_OLD_TOP = """top_by_hash={}\n for tp in files:top_by_hash.setdefault(H(raws[tp]),[]).append(tp)"""
_OLD_RAW_HASH_PATHS = """decode_derived={};raw_hash_paths={}\n for tp in files:raw_hash_paths.setdefault(H(raws[tp]),[]).append(tp)"""


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label} patch boundary drifted: expected 1 occurrence, got {count}")
    return source.replace(old, new, 1)


def _candidate_module() -> types.ModuleType:
    source = Path(V25.__file__).read_text(encoding="utf-8")
    source = _replace_once(source, _OLD_INIT, _NEW_INIT, "build-init")
    source = _replace_once(source, _OLD_TOP, "", "top-hash-duplicate")
    source = _replace_once(source, _OLD_RAW_HASH_PATHS, "decode_derived={};raw_hash_paths=top_by_hash", "raw-hash-paths-duplicate")
    source = source.replace("member_plain.get(H(raws[p]),[])", "member_plain.get(raw_hash[p],[])")
    source = source.replace("if H(cand)==H(raws[tp]):plain=cand;break", "if H(cand)==raw_hash[tp]:plain=cand;break")
    # The only remaining top-level raw hash expression should be the one cache fill above.
    if source.count("H(raws[") != 1:
        raise RuntimeError("unexpected uncached top-level raw SHA-256 boundary")
    module = types.ModuleType("cmpct_v025_raw_hash_cache_candidate")
    module.__file__ = str(V25.__file__)
    module.__package__ = "experiments"
    exec(compile(source, str(V25.__file__), "exec"), module.__dict__)
    return module


def _build(engine, source: Path, archive: Path) -> tuple[bytes, dict, float]:
    old = (engine.ROOT, engine.OUT)
    engine.ROOT = source
    engine.OUT = archive
    try:
        started = time.perf_counter()
        stats = dict(engine.build())
        elapsed = time.perf_counter() - started
        blob = archive.read_bytes()
    finally:
        engine.ROOT, engine.OUT = old
    if not blob:
        raise RuntimeError("engine emitted no archive bytes")
    return blob, stats, elapsed


def run(work_root: Path) -> dict:
    work_root.mkdir(parents=True, exist_ok=True)
    candidate = _candidate_module()
    source, accepted_v029 = V1._frozen_office(work_root / "frozen")
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-raw-hash-cache-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        normalized_tree = V25.treehash(stage)
        baseline_times: list[float] = []
        candidate_times: list[float] = []
        baseline_digests: set[str] = set()
        candidate_digests: set[str] = set()
        baseline_sizes: set[int] = set()
        candidate_sizes: set[int] = set()
        raw = []
        first_mismatch = None
        for rep in range(ROUNDS):
            order = ("baseline", "candidate") if rep % 2 == 0 else ("candidate", "baseline")
            row = {}
            blobs = {}
            for kind in order:
                engine = V25 if kind == "baseline" else candidate
                blob, stats, elapsed = _build(engine, stage, root / f"{kind}-{rep}.cmpnx5")
                digest = hashlib.sha256(blob).hexdigest()
                row[kind] = {
                    "create_s": float(elapsed),
                    "stats_create_s": float(stats["create_s"]),
                    "bytes": len(blob),
                    "sha256": digest,
                }
                blobs[kind] = blob
            baseline_times.append(row["baseline"]["create_s"])
            candidate_times.append(row["candidate"]["create_s"])
            baseline_digests.add(row["baseline"]["sha256"])
            candidate_digests.add(row["candidate"]["sha256"])
            baseline_sizes.add(row["baseline"]["bytes"])
            candidate_sizes.add(row["candidate"]["bytes"])
            raw.append(row)
            if blobs["baseline"] != blobs["candidate"]:
                first_mismatch = {
                    "repetition": rep,
                    "baseline_bytes": row["baseline"]["bytes"],
                    "candidate_bytes": row["candidate"]["bytes"],
                    "baseline_sha256": row["baseline"]["sha256"],
                    "candidate_sha256": row["candidate"]["sha256"],
                }
                break

    completed_pairs = len(raw)
    baseline_median = statistics.median(baseline_times)
    candidate_median = statistics.median(candidate_times)
    saving = baseline_median - candidate_median
    byte_neutral = (
        completed_pairs == ROUNDS
        and first_mismatch is None
        and baseline_sizes == candidate_sizes
        and baseline_digests == candidate_digests
        and len(baseline_sizes) == len(baseline_digests) == 1
    )
    experiment_valid = completed_pairs >= 1 and len(baseline_sizes) == 1 and len(candidate_sizes) == 1
    materially_faster = byte_neutral and saving >= MIN_MEDIAN_SAVING_S and candidate_median < baseline_median
    promotion_eligible = experiment_valid and byte_neutral and materially_faster
    return {
        "schema": "cmpct-v030-eg08-raw-hash-cache-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "benchmark_identity_not_policy_input": True,
            "change": "cache one SHA-256 per already-materialized top-level file and reuse identical digest lookups",
            "required_byte_identity": True,
            "minimum_median_saving_s": MIN_MEDIAN_SAVING_S,
        },
        "office": {
            "accepted_v029_bytes": int(accepted_v029),
            "normalized_tree_sha256": normalized_tree,
            "planned_rounds": ROUNDS,
            "completed_pairs": completed_pairs,
            "baseline_archive_bytes": next(iter(baseline_sizes)),
            "candidate_archive_bytes": next(iter(candidate_sizes)),
            "baseline_archive_sha256": next(iter(baseline_digests)),
            "candidate_archive_sha256": next(iter(candidate_digests)),
            "baseline_median_create_s": float(baseline_median),
            "candidate_median_create_s": float(candidate_median),
            "median_saving_s": float(saving),
            "byte_identical_all_rounds": bool(byte_neutral),
            "first_mismatch": first_mismatch,
            "raw": raw,
        },
        "gate": {
            "experiment_valid": bool(experiment_valid),
            "byte_neutral": bool(byte_neutral),
            "materially_faster": bool(materially_faster),
            "promotion_eligible": bool(promotion_eligible),
            "passed": bool(experiment_valid),
        },
        "claim_boundary": "Only exact-byte identity plus >=10 ms median saving can justify productization; this oracle itself grants zero release credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-raw-hash-cache-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-raw-hash-cache.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office": result["office"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("EG08 raw-hash-cache experiment could not be measured safely")


if __name__ == "__main__":
    main()
