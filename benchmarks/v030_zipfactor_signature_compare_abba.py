from __future__ import annotations

"""Exact-byte A/B for ZIP-factor framing-signature allocation removal.

The shipping fused scanner used to materialize BASE._signature(parsed) for every source ZIP. The product now compares
those exact static fields directly against the first parsed member. This oracle temporarily restores the old
comparator inside the same process, then alternates old/new full source scans over the exact frozen deflate-family
source. It proves scan-result identity and the final archive byte/SHA ratchet before reporting any timing signal.

This is performance evidence only. It cannot relax external ZIP/Zstd, recovery, native/Android or release gates.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD

ROUNDS = 41
EXPECTED_BYTES = 14033
EXPECTED_SHA256 = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"
MIN_ABSOLUTE_SAVING_S = 0.00005
MIN_RELATIVE_SAVING = 0.01


def _legacy_same_signature(reference: dict, candidate: dict) -> bool:
    return FUSED.BASE._signature(reference) == FUSED.BASE._signature(candidate)


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8"))
        h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def _scan_with(stage: Path, comparator) -> tuple[float, str]:
    original = FUSED._same_framing_signature
    try:
        FUSED._same_framing_signature = comparator
        t0 = time.perf_counter_ns()
        result = FUSED._scan(stage)
        elapsed = (time.perf_counter_ns() - t0) / 1e9
        return elapsed, _fingerprint(result)
    finally:
        FUSED._same_framing_signature = original


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-signature-abba-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        candidate_fp = _fingerprint(FUSED._scan(stage))
        legacy_times: list[float] = []
        candidate_times: list[float] = []
        observed_fps: set[str] = {candidate_fp}
        for round_index in range(ROUNDS):
            order = (("legacy", _legacy_same_signature), ("candidate", FUSED._same_framing_signature))
            if round_index % 2:
                order = tuple(reversed(order))
            for label, comparator in order:
                elapsed, fp = _scan_with(stage, comparator)
                observed_fps.add(fp)
                (legacy_times if label == "legacy" else candidate_times).append(elapsed)

        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)

    archive_sha = hashlib.sha256(archive).hexdigest()
    legacy_median = float(statistics.median(legacy_times))
    candidate_median = float(statistics.median(candidate_times))
    saving_s = legacy_median - candidate_median
    saving_ratio = saving_s / legacy_median if legacy_median else 0.0
    exact_identity = len(observed_fps) == 1
    archive_identity = len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA256
    experiment_valid = (
        exact_identity
        and archive_identity
        and len(legacy_times) == len(candidate_times) == ROUNDS
        and legacy_median > 0
        and candidate_median > 0
    )
    promotion_signal = bool(
        experiment_valid
        and saving_s >= MIN_ABSOLUTE_SAVING_S
        and saving_ratio >= MIN_RELATIVE_SAVING
    )
    return {
        "schema": "cmpct-v030-zipfactor-signature-compare-abba-v1",
        "contract": {
            "rounds": ROUNDS,
            "same_runner_alternating": True,
            "exact_scan_result_identity_required": True,
            "exact_final_archive_identity_required": True,
            "minimum_absolute_saving_s": MIN_ABSOLUTE_SAVING_S,
            "minimum_relative_saving": MIN_RELATIVE_SAVING,
            "release_credit": False,
            "selector_change": False,
            "archive_semantics_changed": False,
        },
        "candidate": {"archive_bytes": len(archive), "archive_sha256": archive_sha},
        "medians_s": {"legacy_tuple_signature_scan": legacy_median, "direct_signature_scan": candidate_median},
        "delta": {"saving_s": saving_s, "saving_ratio": saving_ratio},
        "samples_s": {"legacy": legacy_times, "candidate": candidate_times},
        "identity": {"scan_result_identity": exact_identity, "final_archive_identity": archive_identity},
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "release_credit": False,
        "claim_boundary": "Exact-byte scan A/B only. A positive signal justifies retaining the allocation removal; it does not certify the complete four-way external contract.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-signature-abba-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-signature-abba.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("medians_s", "delta", "identity", "experiment_valid", "promotion_signal")}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor signature A/B evidence invalid")


if __name__ == "__main__":
    main()
