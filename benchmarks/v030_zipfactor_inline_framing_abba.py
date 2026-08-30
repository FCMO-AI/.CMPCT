from __future__ import annotations

"""Exact-byte A/B for fusing ZIP-factor framing admission into EOCD parsing.

The shipping scanner parses each source ZIP and then walks its materialized local/central dictionaries a second time
to compare the static framing signature with the first accepted member. Exact profiling put that scan on the dominant
ZIP-factor creation path. This research candidate compiles the first member's exact BASE._signature projection once
and checks subsequent members while the EOCD-indexed parser already owns their scalar central/local fields.

The experiment deliberately reuses the shipping scanner and changes only its research-process parser/comparator seams.
Every arm must return an identical scan fingerprint and retain the exact 14,033-byte final archive/SHA. A positive
signal requires >=200 us and >=5% full-scan improvement; smaller wins are preserved as negative evidence because they
cannot plausibly close the remaining complete ZIP creation deficit.

Research only: no selector, archive grammar, release threshold, recovery, native or Android behavior changes here.
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
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as BUILD
from experiments import entropygraph_v030_zipfactor_eocd_parser as ZIP
from experiments import entropygraph_v030_zipfactor_fused as FUSED

ROUNDS = 41
EXPECTED_BYTES = 14033
EXPECTED_SHA256 = "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31"
MIN_ABSOLUTE_SAVING_S = 0.0002
MIN_RELATIVE_SAVING = 0.05


class _InlineParser:
    def __init__(self) -> None:
        self.reference: ZIP.FramingReference | None = None
        self.last_match = True

    def __call__(self, raw: bytes) -> dict | None:
        if self.reference is None:
            parsed = ZIP.parse_zip(raw)
            if parsed is not None:
                self.reference = ZIP.framing_reference(parsed)
                self.last_match = True
            return parsed
        parsed, match = ZIP.parse_zip_with_framing(raw, self.reference)
        self.last_match = match
        return parsed

    def compare(self, _reference: dict, _candidate: dict) -> bool:
        # FUSED._scan calls the comparator immediately after the parser. The candidate parser has already proven the
        # exact static law while those fields were scalar locals, so this O(1) handoff deletes only the second walk.
        return self.last_match


def _fingerprint(result) -> str:
    manifest, items, stats = result
    h = hashlib.sha256(manifest)
    for rel, parsed in items:
        h.update(rel.encode("utf-8"))
        h.update(repr(parsed).encode("utf-8"))
    h.update(json.dumps(stats, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def _candidate_scan(stage: Path) -> tuple[bytes, list[tuple[str, dict]], dict]:
    parser = _InlineParser()
    original = FUSED._same_framing_signature
    try:
        # Research-process-only seam: the scanner itself is reused verbatim so filesystem traversal, hashing,
        # manifest construction and admission diagnostics remain on the shipping path.
        FUSED._same_framing_signature = parser.compare
        return FUSED._scan(stage, parse_zip=parser)
    finally:
        FUSED._same_framing_signature = original


def _timed(stage: Path, candidate: bool) -> tuple[float, str]:
    t0 = time.perf_counter_ns()
    result = _candidate_scan(stage) if candidate else FUSED._scan(stage)
    elapsed = (time.perf_counter_ns() - t0) / 1e9
    return elapsed, _fingerprint(result)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-inline-framing-", dir=work_root) as td_raw:
        stage = EXT._normalized_stage(source, Path(td_raw))
        baseline_fp = _fingerprint(FUSED._scan(stage))
        baseline_times: list[float] = []
        candidate_times: list[float] = []
        fingerprints = {baseline_fp}
        for round_index in range(ROUNDS):
            order = (False, True) if round_index % 2 == 0 else (True, False)
            for candidate in order:
                elapsed, fp = _timed(stage, candidate)
                fingerprints.add(fp)
                (candidate_times if candidate else baseline_times).append(elapsed)
        archive, _stats = BUILD.build_bytes(stage, level=3, group_size=7)

    archive_sha = hashlib.sha256(archive).hexdigest()
    baseline_median = float(statistics.median(baseline_times))
    candidate_median = float(statistics.median(candidate_times))
    saving_s = baseline_median - candidate_median
    saving_ratio = saving_s / baseline_median if baseline_median else 0.0
    scan_identity = len(fingerprints) == 1
    archive_identity = len(archive) == EXPECTED_BYTES and archive_sha == EXPECTED_SHA256
    experiment_valid = (
        scan_identity
        and archive_identity
        and len(baseline_times) == len(candidate_times) == ROUNDS
        and baseline_median > 0
        and candidate_median > 0
    )
    promotion_signal = bool(
        experiment_valid
        and saving_s >= MIN_ABSOLUTE_SAVING_S
        and saving_ratio >= MIN_RELATIVE_SAVING
    )
    return {
        "schema": "cmpct-v030-zipfactor-inline-framing-abba-v1",
        "contract": {
            "rounds": ROUNDS,
            "same_runner_alternating": True,
            "exact_scan_result_identity_required": True,
            "exact_final_archive_identity_required": True,
            "minimum_absolute_saving_s": MIN_ABSOLUTE_SAVING_S,
            "minimum_relative_saving": MIN_RELATIVE_SAVING,
            "baseline": "parse-then-second-static-framing-walk",
            "candidate": "eocd-parse-plus-inline-static-framing-proof",
            "selector_change": False,
            "archive_semantics_changed": False,
            "release_credit": False,
        },
        "candidate": {"archive_bytes": len(archive), "archive_sha256": archive_sha},
        "medians_s": {"baseline_scan": baseline_median, "inline_framing_scan": candidate_median},
        "delta": {"saving_s": saving_s, "saving_ratio": saving_ratio},
        "samples_s": {"baseline": baseline_times, "candidate": candidate_times},
        "identity": {"scan_result_identity": scan_identity, "final_archive_identity": archive_identity},
        "experiment_valid": experiment_valid,
        "promotion_signal": promotion_signal,
        "release_credit": False,
        "claim_boundary": "Exact-byte full-scan A/B only. Promotion requires separate product/native/recovery/Android and complete external authority.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-inline-framing-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-inline-framing.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("medians_s", "delta", "identity", "experiment_valid", "promotion_signal")}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor inline-framing A/B evidence invalid")


if __name__ == "__main__":
    main()
