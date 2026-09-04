from __future__ import annotations

"""A/B exact primary->tail G0-G4 metadata decode reuse on the shipping ML archive.

G0-G4 writes the same authenticated compressed metadata at the head and tail. The release reader currently reads,
decompresses, unpacks and validates both copies on every successful open. That is necessary when the copies differ,
but when the compressed bytes and authenticated declarations are byte-identical the second decode is provably the
same computation.

This oracle changes no archive bytes, integrity rule, cache budget or locality rule. The candidate memo is scoped to
one `_stream_g04` call, so the primary metadata is always decoded normally; only an exactly identical second copy
may reuse that already-validated object. A differing/corrupt tail remains on the full existing decoder path.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 7
MIN_VERIFY_IMPROVEMENT = 0.08
MIN_EXTRACT_IMPROVEMENT = 0.08


def _stream_once(archive: Path, destination: Path | None, *, reuse_identical_copy: bool) -> tuple[float, dict, int]:
    original = RR._decode_g04_meta
    hits = [0]
    memo: dict[tuple[bytes, int, bytes], dict] = {}

    def decode(comp: bytes, raw_size: int, expected_sha: bytes, expected_count: int | None):
        key = (bytes(comp), int(raw_size), bytes(expected_sha))
        if reuse_identical_copy and key in memo:
            meta = memo[key]
            if expected_count is not None and len(meta["record_leaf_sha256"]) != int(expected_count):
                raise RuntimeError("memoized G0-G4 header/metadata record-count mismatch")
            hits[0] += 1
            return meta
        meta = original(comp, raw_size, expected_sha, expected_count)
        if reuse_identical_copy:
            memo[key] = meta
        return meta

    RR._decode_g04_meta = decode
    try:
        started = time.perf_counter()
        result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
        return time.perf_counter() - started, result, hits[0]
    finally:
        RR._decode_g04_meta = original


def _campaign(archive: Path, source_tree: str, root: Path, *, reuse: bool) -> dict:
    verify = []
    extract = []
    verify_hits = []
    extract_hits = []
    physical_reads = []
    for rep in range(ROUNDS):
        verify_s, verified, vh = _stream_once(archive, None, reuse_identical_copy=reuse)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("G0-G4 metadata-copy verification identity drift")
        verify.append(verify_s)
        verify_hits.append(vh)

        destination = root / f"extract-{rep}"
        shutil.rmtree(destination, ignore_errors=True)
        extract_s, extracted, eh = _stream_once(archive, destination, reuse_identical_copy=reuse)
        if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
            raise RuntimeError("G0-G4 metadata-copy extraction identity drift")
        if PRODUCT.treehash(destination) != source_tree:
            raise RuntimeError("G0-G4 metadata-copy extracted filesystem identity drift")
        extract.append(extract_s)
        extract_hits.append(eh)
        physical_reads.append(int(extracted["physical_record_reads"]))
        shutil.rmtree(destination, ignore_errors=True)
    return {
        "reuse_identical_copy": reuse,
        "median_verify_s": statistics.median(verify),
        "verify_samples_s": verify,
        "median_extract_s": statistics.median(extract),
        "extract_samples_s": extract,
        "verify_reuse_hits": verify_hits,
        "extract_reuse_hits": extract_hits,
        "median_physical_record_reads": statistics.median(physical_reads),
    }


def _tail_corruption_semantics(archive: Path, work_root: Path, source_tree: str) -> dict:
    payload = bytearray(archive.read_bytes())
    # Flip one byte immediately before the fixed footer. This lands in the duplicated tail metadata for the
    # canonical writer and deliberately makes it differ from primary. Existing semantics allow a good primary
    # copy to carry the read; the memoized path must therefore miss and behave identically.
    offset = len(payload) - RR.G04.FTR.size - 1
    if offset <= RR.G04.HDR.size:
        raise RuntimeError("ML G0-G4 archive unexpectedly lacks tail metadata")
    payload[offset] ^= 0x01
    damaged = work_root / "tail-damaged.cmpct"
    damaged.write_bytes(payload)
    baseline_s, baseline, baseline_hits = _stream_once(damaged, None, reuse_identical_copy=False)
    candidate_s, candidate, candidate_hits = _stream_once(damaged, None, reuse_identical_copy=True)
    if baseline.get("tree_sha256") != source_tree or candidate.get("tree_sha256") != source_tree:
        raise RuntimeError("tail-damaged primary recovery identity drift")
    return {
        "baseline_ok": bool(baseline.get("ok")),
        "candidate_ok": bool(candidate.get("ok")),
        "same_tree": baseline.get("tree_sha256") == candidate.get("tree_sha256") == source_tree,
        "baseline_reuse_hits": baseline_hits,
        "candidate_reuse_hits": candidate_hits,
        "candidate_did_not_reuse_different_tail": candidate_hits == 0,
        "baseline_s": baseline_s,
        "candidate_s": candidate_s,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"
    built = PRODUCT.build(source, archive)
    if archive.read_bytes()[:8] != RR.G04.MAG:
        raise RuntimeError("ML runtime target did not select canonical G0-G4")
    verified = PRODUCT.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
        raise RuntimeError("ML metadata-copy oracle source archive failed strong verification")

    baseline = _campaign(archive, source_tree, work_root / "baseline", reuse=False)
    candidate = _campaign(archive, source_tree, work_root / "candidate", reuse=True)
    verify_improvement = 1.0 - candidate["median_verify_s"] / max(baseline["median_verify_s"], 1e-9)
    extract_improvement = 1.0 - candidate["median_extract_s"] / max(baseline["median_extract_s"], 1e-9)
    corruption = _tail_corruption_semantics(archive, work_root, source_tree)

    gate = {
        "candidate_reused_identical_tail_every_verify": all(hit == 1 for hit in candidate["verify_reuse_hits"]),
        "candidate_reused_identical_tail_every_extract": all(hit == 1 for hit in candidate["extract_reuse_hits"]),
        "physical_record_reads_unchanged": candidate["median_physical_record_reads"] == baseline["median_physical_record_reads"],
        "tail_difference_forces_full_decode_path": corruption["candidate_did_not_reuse_different_tail"],
        "tail_corruption_primary_recovery_same_tree": corruption["same_tree"] and corruption["baseline_ok"] and corruption["candidate_ok"],
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-metadata-copy-reuse-v1",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "rounds": ROUNDS,
        "baseline": baseline,
        "candidate": candidate,
        "verify_improvement_fraction": verify_improvement,
        "extract_improvement_fraction": extract_improvement,
        "tail_corruption": corruption,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "reuse_key": "exact compressed metadata bytes + raw size + authenticated raw SHA",
            "memo_scope": "one archive open only; primary is always decoded normally",
            "archive_bytes_change": 0,
            "memory_budget_change_bytes": 0,
            "locality_change": "none",
        },
        "gate": gate,
        "claim_boundary": "research-only exact duplicate-control decode A/B; production reader/runtime/fuzz/native gates remain mandatory",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("G0-G4 metadata-copy reuse did not earn promotion")


if __name__ == "__main__":
    main()
