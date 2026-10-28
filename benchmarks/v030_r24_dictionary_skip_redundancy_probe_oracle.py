from __future__ import annotations

"""Research-only structural probe for safe r24 dictionary-training skip admission.

The broad file/sample-count rule was disproved by large text families sharing a 24--32 KiB prefix. This oracle asks
whether a cheap, order-independent statistic over the *same bytes already visible to Builder._train_dictionary()* can
separate independent high-entropy samples from those correlated counterexamples before dictionary training starts.

The statistic is positional modal agreement: for each byte offset in the first 32 KiB of every eligible training
sample, measure the fraction of samples holding the most common byte, then average across offsets. It uses no names,
paths, hashes or benchmark identity and is invariant to sample ordering. Probe time is charged against creation-time
savings. Production policy is unchanged regardless of outcome.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
from time import perf_counter

from benchmarks import v030_r24_dictionary_skip_admission_oracle as ADMIT
from benchmarks import v030_r24_dictionary_skip_adversarial_v2 as V2
from benchmarks import v030_r24_dictionary_skip_adversarial_oracle as V1
from benchmarks import v030_r24_dictionary_skip_correlated_adversarial_v3 as V3
from benchmarks import v030_r24_dictionary_training_cost_oracle as COST
from experiments import entropygraph_v030_release_product as P

SCHEMA = "cmpct-v030-r24-dictionary-skip-redundancy-probe-v1"
PROBE_BYTES = 32 * 1024
# Fixed before measurement: comfortably above random finite-sample modal agreement, far below the deliberately
# correlated 24--32 KiB shared-prefix surface. This is an architectural-discrimination threshold, not promotion law.
MAX_AGREEMENT_FOR_SKIP = 0.25
MIN_SAMPLES = 32
MIN_ADJUSTED_SAVED_S = 0.005
TARGET_LABELS = {
    "large_entropy_text_40",
    "large_entropy_text_64",
    "large_shared_prefix_40",
    "large_shared_prefix_64",
}


def _training_samples(root: Path) -> list[bytes]:
    builder = P.C.Builder(root, deflate_reuse_min=P.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular, _logical, largest = ADMIT._source_shape(root)
    if largest:
        builder.micro_pack_target = min(P.R24_RELEASE_PACK_CAP_BYTES, 8 * largest)
    old_wide = getattr(P._R24_CDC_POLICY, "wide_single_file", False)
    old_medium = getattr(P._R24_CDC_POLICY, "medium_binary_pack", False)
    P._R24_CDC_POLICY.wide_single_file = regular == 1 and largest >= P.R24_RELEASE_WIDE_CHUNK_BYTES
    P._R24_CDC_POLICY.medium_binary_pack = True
    try:
        builder.scan()
        builder._build_micro_packs()
        builder._prepare_deflate_reuse()
        text_ext = P.R24_BUILDER_MODULE.TEXT_EXT
        return [
            c.raw
            for c in builder.cands.values()
            if len(c.raw) >= 64 and ".cmpct-pack" not in c.hints and any(x in text_ext for x in c.hints)
        ]
    finally:
        P._R24_CDC_POLICY.wide_single_file = old_wide
        P._R24_CDC_POLICY.medium_binary_pack = old_medium


def _positional_modal_agreement(samples: list[bytes], *, limit: int = PROBE_BYTES) -> float:
    if not samples:
        return 1.0
    width = min(limit, min(map(len, samples)))
    if width <= 0:
        return 1.0
    n = len(samples)
    total = 0.0
    # Order independent by construction: Counter only observes the multiset at each position.
    for offset in range(width):
        counts = Counter(sample[offset] for sample in samples)
        total += max(counts.values()) / n
    return total / width


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus = work_root / "corpus"
    cases = V3._build_v3_adversarial(corpus)
    selected = [(name, root, provenance) for name, root, provenance in cases if name in TARGET_LABELS]
    if {name for name, _root, _prov in selected} != TARGET_LABELS:
        raise RuntimeError("target redundancy-probe surface incomplete")

    rows = []
    for name, root, provenance in selected:
        samples = _training_samples(root)
        t0 = perf_counter()
        agreement = _positional_modal_agreement(samples)
        probe_s = perf_counter() - t0
        measurement = COST._measure(root, work_root / "measure" / name, provenance)
        exact = bool(measurement["exact_archive_bytes_and_sha"] and measurement["canonical_product_tree_equal"])
        adjusted_saved_s = float(measurement["saved_s"]) - probe_s
        admitted = len(samples) >= MIN_SAMPLES and agreement <= MAX_AGREEMENT_FOR_SKIP
        safe_useful = (not admitted) or (exact and adjusted_saved_s >= MIN_ADJUSTED_SAVED_S)
        row = {
            "label": f"adversarial/{name}",
            "sample_count": len(samples),
            "probe_bytes_per_sample": min(PROBE_BYTES, min(map(len, samples))) if samples else 0,
            "positional_modal_agreement": agreement,
            "probe_s": probe_s,
            "admitted": admitted,
            "exact_archive_and_tree": exact,
            "raw_saved_s": float(measurement["saved_s"]),
            "adjusted_saved_s": adjusted_saved_s,
            "safe_useful": safe_useful,
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    independent = [r for r in rows if "large_entropy_text" in r["label"]]
    correlated = [r for r in rows if "large_shared_prefix" in r["label"]]
    separation = (
        len(independent) == 2
        and len(correlated) == 2
        and all(r["admitted"] and r["exact_archive_and_tree"] and r["adjusted_saved_s"] >= MIN_ADJUSTED_SAVED_S for r in independent)
        and all((not r["admitted"]) and (not r["exact_archive_and_tree"]) for r in correlated)
    )
    return {
        "schema": SCHEMA,
        "contract": {
            "production_change": False,
            "release_credit": False,
            "probe_uses_existing_pretraining_samples": True,
            "sample_order_affects_feature": False,
            "probe_time_charged_inside_saved_time": True,
            "probe_bytes_per_sample_cap": PROBE_BYTES,
            "minimum_training_samples": MIN_SAMPLES,
            "maximum_agreement_for_skip": MAX_AGREEMENT_FOR_SKIP,
            "minimum_adjusted_saved_s": MIN_ADJUSTED_SAVED_S,
            "policy_inputs": ["dictionary_sample_count", "positional_modal_agreement"],
            "forbidden_policy_inputs": ["workload_name", "benchmark_name", "path", "filename", "content_hash", "archive_hash"],
            "full_frozen_adversarial_generalization_required_before_productization": True,
        },
        "rows": rows,
        "summary": {
            "target_surface_complete": len(rows) == 4,
            "all_admissions_safe_useful": all(r["safe_useful"] for r in rows),
            "independent_entropy_admitted": sum(bool(r["admitted"]) for r in independent),
            "correlated_counterexamples_rejected": sum(not bool(r["admitted"]) for r in correlated),
            "separation_signal": separation,
        },
        "promotion_signal": False,
        "next_boundary_signal": separation,
        "release_credit": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True), flush=True)
    if not result["summary"]["target_surface_complete"]:
        raise SystemExit("redundancy-probe target surface incomplete")
    if not result["summary"]["all_admissions_safe_useful"]:
        raise SystemExit("redundancy probe admitted a nonexact or non-useful row")


if __name__ == "__main__":
    main()
