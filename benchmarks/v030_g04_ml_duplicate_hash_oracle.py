from __future__ import annotations

"""Research-only paired A/B for duplicate SHA-256 work in the canonical ML reader.

The streaming G0-G4 semantic owner authenticates each physical payload and then authenticates
its reconstructed logical record. For an untransformed CODEC_RAW record those are the exact
same immutable bytes object, so hashing the object twice is redundant if the first digest is
reused only for that same object identity. This oracle measures that narrow optimization
without changing archive bytes, cache limits, physical-read counts, locality, or reader
control flow.

The experiment monkey-patches only the reader's pure H(bytes)->digest function with a
one-entry object-identity memo during a single verify/extract call. It alternates baseline and
candidate order, strongly checks the canonical archive/tree first, requires identical reader
results and physical-record reads on every pair, and grants no production or release credit.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
ROUNDS = 9
MIN_VERIFY_IMPROVEMENT = 0.03
MIN_EXTRACT_IMPROVEMENT = 0.03


class _IdentityHashReuse:
    def __init__(self, original):
        self.original = original
        self.last_obj = None
        self.last_digest = None
        self.calls = 0
        self.reuses = 0

    def __call__(self, payload: bytes) -> bytes:
        self.calls += 1
        if payload is self.last_obj:
            self.reuses += 1
            assert self.last_digest is not None
            return self.last_digest
        digest = self.original(payload)
        self.last_obj = payload
        self.last_digest = digest
        return digest


@contextmanager
def _hash_reuse():
    original = RR.H
    memo = _IdentityHashReuse(original)
    RR.H = memo
    try:
        yield memo
    finally:
        RR.H = original


def _call(archive: Path, destination: Path | None, *, reuse: bool) -> tuple[dict, float, dict]:
    if destination is not None:
        shutil.rmtree(destination, ignore_errors=True)
    started = time.perf_counter()
    if reuse:
        with _hash_reuse() as memo:
            result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        hash_stats = {"calls": memo.calls, "reuses": memo.reuses}
    else:
        result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        hash_stats = {"calls": None, "reuses": 0}
    return result, time.perf_counter() - started, hash_stats


def _equivalent(a: dict, b: dict) -> None:
    keys = (
        "ok", "engine", "files", "logical_bytes", "tree_sha256",
        "max_member_read_amplification", "max_physical_record_bytes",
        "max_logical_node_bytes", "record_cache_peak_bound_bytes",
        "node_cache_peak_bound_bytes", "physical_record_reads",
        "tail_metadata_authenticated",
    )
    for key in keys:
        if a.get(key) != b.get(key):
            raise RuntimeError(f"reader result drift for {key}: {a.get(key)!r} != {b.get(key)!r}")


def _median_improvement(baseline: list[float], candidate: list[float]) -> tuple[float, float, float]:
    b = statistics.median(baseline)
    c = statistics.median(candidate)
    return b, c, (b - c) / b if b else 0.0


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML duplicate-hash target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
            raise RuntimeError("canonical ML archive failed pre-A/B verification")

        archive_bytes = archive.read_bytes()
        archive_sha = hashlib.sha256(archive_bytes).hexdigest()
        archive_size = len(archive_bytes)
        samples = []
        verify_base: list[float] = []
        verify_reuse: list[float] = []
        extract_base: list[float] = []
        extract_reuse: list[float] = []
        verify_reuses = set()
        extract_reuses = set()

        for rep in range(ROUNDS):
            order = (False, True) if rep % 2 == 0 else (True, False)
            pair = {}
            for reuse in order:
                label = "reuse" if reuse else "baseline"
                v, vt, vh = _call(archive, None, reuse=reuse)
                dest = work_root / f"extract-{rep}-{label}"
                e, et, eh = _call(archive, dest, reuse=reuse)
                if PRODUCT.treehash(dest) != source_tree:
                    raise RuntimeError("duplicate-hash extraction changed user tree")
                pair[label] = {"verify": v, "verify_s": vt, "verify_hash": vh, "extract": e, "extract_s": et, "extract_hash": eh}
            _equivalent(pair["baseline"]["verify"], pair["reuse"]["verify"])
            _equivalent(pair["baseline"]["extract"], pair["reuse"]["extract"])
            verify_base.append(float(pair["baseline"]["verify_s"]))
            verify_reuse.append(float(pair["reuse"]["verify_s"]))
            extract_base.append(float(pair["baseline"]["extract_s"]))
            extract_reuse.append(float(pair["reuse"]["extract_s"]))
            verify_reuses.add(int(pair["reuse"]["verify_hash"]["reuses"]))
            extract_reuses.add(int(pair["reuse"]["extract_hash"]["reuses"]))
            samples.append({
                "rep": rep,
                "order": ["reuse" if x else "baseline" for x in order],
                "baseline_verify_s": pair["baseline"]["verify_s"],
                "reuse_verify_s": pair["reuse"]["verify_s"],
                "baseline_extract_s": pair["baseline"]["extract_s"],
                "reuse_extract_s": pair["reuse"]["extract_s"],
                "verify_hash_reuses": pair["reuse"]["verify_hash"]["reuses"],
                "extract_hash_reuses": pair["reuse"]["extract_hash"]["reuses"],
                "physical_record_reads": pair["reuse"]["verify"]["physical_record_reads"],
            })

    if archive.stat().st_size != archive_size or hashlib.sha256(archive.read_bytes()).hexdigest() != archive_sha:
        raise RuntimeError("duplicate-hash A/B changed canonical archive bytes")
    vb, vr, vi = _median_improvement(verify_base, verify_reuse)
    eb, er, ei = _median_improvement(extract_base, extract_reuse)
    deterministic_reuse = len(verify_reuses) == 1 and len(extract_reuses) == 1
    reusable = next(iter(verify_reuses)) if deterministic_reuse else 0
    promotion = bool(deterministic_reuse and reusable > 0 and vi >= MIN_VERIFY_IMPROVEMENT and ei >= MIN_EXTRACT_IMPROVEMENT)

    return {
        "schema": "cmpct-v030-g04-ml-duplicate-hash-oracle-v1",
        "target": "/".join(TARGET),
        "contract": {
            "release_credit": False,
            "production_change": False,
            "archive_byte_change": False,
            "cache_budget_change": False,
            "physical_read_policy_change": False,
            "hash_reuse_key": "same immutable bytes object identity within one reader call",
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
        },
        "archive": {"bytes": archive_size, "sha256": archive_sha, "tree_sha256": source_tree, "selected": built.get("selected")},
        "results": {
            "rounds": ROUNDS,
            "median_baseline_verify_s": vb,
            "median_reuse_verify_s": vr,
            "verify_improvement_fraction": vi,
            "median_baseline_extract_s": eb,
            "median_reuse_extract_s": er,
            "extract_improvement_fraction": ei,
            "verify_hash_reuses": sorted(verify_reuses),
            "extract_hash_reuses": sorted(extract_reuses),
            "samples": samples,
        },
        "gate": {
            "experiment_valid": bool(deterministic_reuse and reusable > 0),
            "reader_results_identical": True,
            "archive_identity_preserved": True,
            "logical_identity_preserved": True,
            "promotion_signal": promotion,
            "passed": bool(deterministic_reuse and reusable > 0),
        },
        "claim_boundary": "Research-only causal A/B. A positive signal authorizes only direct semantic-owner productization plus hostile-input/runtime/native/Android authority; a valid weak result is durable negative evidence.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-duplicate-hash-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-duplicate-hash.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"results": {k: v for k, v in result["results"].items() if k != "samples"}, "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("duplicate-hash A/B produced no deterministic reusable hash work")


if __name__ == "__main__":
    main()
