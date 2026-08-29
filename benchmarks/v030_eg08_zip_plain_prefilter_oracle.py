from __future__ import annotations

"""Research-only A/B oracle for the dominant C25EG08 ZIP-member inspection cost.

The exact EG08 graph hot-path profiler shows that the v0.25 semantic builder spends a material share of Office
wall time eagerly inflating and SHA-256 hashing every supported ZIP member even though member plaintext is used
only to prove exact equality with a loose top-level object. This experiment tests a cheap (file_size, CRC32)
prefilter while keeping SHA-256 as the authoritative equality proof for survivors.

This is deliberately a falsification oracle. A candidate that changes bytes is rejected, but that rejection is
written as durable negative evidence instead of crashing before a receipt exists. A valid negative result grants
zero selector/release credit and must not be mistaken for a passing candidate.
"""

import argparse
import binascii
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
_NEW_INIT = """t0=time.perf_counter();files=sorted(p for p in ROOT.rglob('*') if p.is_file());rels={p:p.relative_to(ROOT).as_posix() for p in files};raws={p:p.read_bytes() for p in files}\n raw_hash={p:H(raws[p]) for p in files};top_by_hash={}\n for tp in files:top_by_hash.setdefault(raw_hash[tp],[]).append(tp)\n loose_crc_size={(len(raws[p]),binascii.crc32(raws[p])&0xffffffff) for p in files}"""
_OLD_OPEN = "with zipfile.ZipFile(p) as ar: infos=sorted([i for i in ar.infolist() if not i.is_dir()],key=lambda x:x.header_offset);plain_by_offset={i.header_offset:ar.read(i) for i in infos if i.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED)}"
_NEW_OPEN = "with zipfile.ZipFile(p) as ar: infos=sorted([i for i in ar.infolist() if not i.is_dir()],key=lambda x:x.header_offset)"
_OLD_MEMBER = """if zi.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED):\n     pb=plain_by_offset[zi.header_offset];ph=H(pb);member_plain.setdefault(ph,[]).append((p,hh,zi.compress_type,len(pb),len(b)));members.append((ph,hh,zi.compress_type,len(pb),len(b)))"""
_NEW_MEMBER = """if zi.compress_type in (zipfile.ZIP_DEFLATED,zipfile.ZIP_STORED) and (zi.file_size,zi.CRC&0xffffffff) in loose_crc_size:\n     pb=ar.read(zi);ph=H(pb)\n     # CRC32+length are only a necessary prefilter. SHA-256 remains the exact equality proof.\n     if ph in top_by_hash:\n      member_plain.setdefault(ph,[]).append((p,hh,zi.compress_type,len(pb),len(b)));members.append((ph,hh,zi.compress_type,len(pb),len(b)))"""
_OLD_TOP = """top_by_hash={}\n for tp in files:top_by_hash.setdefault(H(raws[tp]),[]).append(tp)"""


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label} patch boundary drifted: expected 1 occurrence, got {count}")
    return source.replace(old, new, 1)


def _candidate_module() -> types.ModuleType:
    source = Path(V25.__file__).read_text(encoding="utf-8")
    source = _replace_once(source, _OLD_INIT, _NEW_INIT, "build-init")
    source = _replace_once(source, _OLD_OPEN, _NEW_OPEN, "zip-open")
    source = _replace_once(source, _OLD_MEMBER, _NEW_MEMBER, "member-plaintext")
    source = _replace_once(source, _OLD_TOP, "", "top-hash-duplicate")
    source = source.replace("member_plain.get(H(raws[p]),[])", "member_plain.get(raw_hash[p],[])")
    source = source.replace("decode_derived={};raw_hash_paths={}\n for tp in files:raw_hash_paths.setdefault(H(raws[tp]),[]).append(tp)", "decode_derived={};raw_hash_paths=top_by_hash")
    source = source.replace("if H(cand)==H(raws[tp]):plain=cand;break", "if H(cand)==raw_hash[tp]:plain=cand;break")
    module = types.ModuleType("cmpct_v025_zip_plain_prefilter_candidate")
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
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-prefilter-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        normalized_tree = V25.treehash(stage)
        baseline_times: list[float] = []
        candidate_times: list[float] = []
        baseline_digests: set[str] = set()
        candidate_digests: set[str] = set()
        baseline_sizes: set[int] = set()
        candidate_sizes: set[int] = set()
        byte_identity: list[bool] = []
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
                row[kind] = {"create_s": float(elapsed), "stats_create_s": float(stats["create_s"]), "bytes": len(blob), "sha256": digest}
                blobs[kind] = blob
            identical = blobs["baseline"] == blobs["candidate"]
            byte_identity.append(identical)
            baseline_times.append(row["baseline"]["create_s"])
            candidate_times.append(row["candidate"]["create_s"])
            baseline_digests.add(row["baseline"]["sha256"]); candidate_digests.add(row["candidate"]["sha256"])
            baseline_sizes.add(row["baseline"]["bytes"]); candidate_sizes.add(row["candidate"]["bytes"])
            raw.append(row)
            if not identical:
                first_mismatch = {
                    "repetition": rep,
                    "baseline_bytes": row["baseline"]["bytes"], "candidate_bytes": row["candidate"]["bytes"],
                    "baseline_sha256": row["baseline"]["sha256"], "candidate_sha256": row["candidate"]["sha256"],
                }
                break

    completed_pairs = len(raw)
    baseline_median = statistics.median(baseline_times)
    candidate_median = statistics.median(candidate_times)
    saving = baseline_median - candidate_median
    ratio = candidate_median / baseline_median if baseline_median else 1.0
    byte_neutral = completed_pairs == ROUNDS and all(byte_identity)
    baseline_deterministic = len(baseline_digests) == 1 and len(baseline_sizes) == 1
    candidate_deterministic = len(candidate_digests) == 1 and len(candidate_sizes) == 1
    experiment_valid = completed_pairs >= 1 and baseline_deterministic and candidate_deterministic
    materially_faster = byte_neutral and saving >= MIN_MEDIAN_SAVING_S and candidate_median < baseline_median
    promotion_eligible = experiment_valid and byte_neutral and materially_faster
    return {
        "schema": "cmpct-v030-eg08-zip-plain-prefilter-oracle-v2",
        "contract": {
            "release_credit": False, "production_change": False, "benchmark_identity_not_policy_input": True,
            "prefilter": "ZIP member uncompressed size + CRC32; exact equality still SHA-256",
            "required_byte_identity": True, "minimum_median_saving_s": MIN_MEDIAN_SAVING_S,
            "negative_evidence_is_successful_measurement_not_candidate_promotion": True,
        },
        "office": {
            "accepted_v029_bytes": int(accepted_v029), "normalized_tree_sha256": normalized_tree,
            "planned_rounds": ROUNDS, "completed_pairs": completed_pairs,
            "baseline_archive_bytes": next(iter(baseline_sizes)), "candidate_archive_bytes": next(iter(candidate_sizes)),
            "baseline_archive_sha256": next(iter(baseline_digests)), "candidate_archive_sha256": next(iter(candidate_digests)),
            "baseline_median_create_s": float(baseline_median), "candidate_median_create_s": float(candidate_median),
            "median_saving_s": float(saving), "candidate_over_baseline_ratio": float(ratio),
            "byte_identical_all_completed_pairs": all(byte_identity), "first_mismatch": first_mismatch, "raw": raw,
        },
        "gate": {
            "experiment_valid": experiment_valid, "byte_neutral": byte_neutral,
            "materially_faster": materially_faster, "promotion_eligible": promotion_eligible,
            "passed": experiment_valid,
        },
        "claim_boundary": (
            "A valid negative result is durable evidence, not a candidate pass. Byte drift or insufficient speed keeps "
            "promotion_eligible false and grants zero selector/release credit."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-zip-prefilter-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-zip-prefilter.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"office": result["office"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("EG08 ZIP plaintext prefilter experiment could not be measured safely")


if __name__ == "__main__":
    main()
