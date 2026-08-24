from __future__ import annotations

"""Frozen-suite search for a content-agnostic r24 dictionary-training skip envelope.

The dictionary-training cost A/B has shown that some workloads can omit dictionary training while producing
byte-identical canonical r24 archives. This oracle asks the next question: is there a cheap pre-training rule that
admits only such rows, without using workload names, paths, hashes, or benchmark identity?

This remains research-only. A zero-counterexample rule on the frozen suite must still survive independent
adversarial/generalization evidence before production admission can change.
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import stat

from benchmarks import v030_r24_dictionary_training_cost_oracle as COST
from experiments import entropygraph_v030_release_product as P


@dataclass(frozen=True)
class Rule:
    feature: str
    op: str
    threshold: float

    def matches(self, features: dict[str, float]) -> bool:
        value = float(features[self.feature])
        return value >= self.threshold if self.op == ">=" else value <= self.threshold

    def json(self) -> dict:
        return {"feature": self.feature, "op": self.op, "threshold": self.threshold}


def _source_shape(root: Path) -> tuple[int, int, int]:
    regular = logical = largest = 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [n for n in dirnames if not os.path.islink(Path(dirpath) / n)]
        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                regular += 1
                logical += int(st.st_size)
                largest = max(largest, int(st.st_size))
    return regular, logical, largest


def _pretraining_features(root: Path) -> dict[str, float]:
    """Derive only facts available immediately before Builder._train_dictionary()."""
    builder = P.C.Builder(root, deflate_reuse_min=P.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = P.R24_RELEASE_MICRO_MAX_FILE_BYTES
    regular, logical, largest = _source_shape(root)
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
    finally:
        P._R24_CDC_POLICY.wide_single_file = old_wide
        P._R24_CDC_POLICY.medium_binary_pack = old_medium

    # Mirror Builder._train_dictionary's exact pre-training sample predicate without invoking the trainer.
    samples = [
        c.raw
        for c in builder.cands.values()
        if len(c.raw) >= 64 and ".cmpct-pack" not in c.hints and any(x in P.C.TEXT_EXT for x in c.hints)
    ]
    sample_bytes = sum(map(len, samples))
    return {
        "regular_files": float(regular),
        "logical_bytes": float(logical),
        "largest_file_bytes": float(largest),
        "dictionary_sample_count": float(len(samples)),
        "dictionary_sample_bytes": float(sample_bytes),
        "sample_mean_bytes": float(sample_bytes / max(1, len(samples))),
        "sample_bytes_per_regular": float(sample_bytes / max(1, regular)),
        "sample_fraction_of_logical": float(sample_bytes / max(1, logical)),
    }


def _candidate_rules(rows: list[dict]) -> list[Rule]:
    features = tuple(rows[0]["pretraining_features"].keys()) if rows else ()
    rules: list[Rule] = []
    for feature in features:
        values = sorted({float(r["pretraining_features"][feature]) for r in rows})
        for threshold in values:
            rules.append(Rule(feature, ">=", threshold))
            rules.append(Rule(feature, "<=", threshold))
    return rules


def _search(rows: list[dict]) -> list[dict]:
    rules = _candidate_rules(rows)
    solutions = []
    # Keep the family intentionally small: one rule or conjunction of two simple pre-training thresholds.
    candidates: list[tuple[Rule, ...]] = [(r,) for r in rules]
    for i, a in enumerate(rules):
        for b in rules[i + 1 :]:
            if a.feature == b.feature and a.op == b.op:
                continue
            candidates.append((a, b))
    for combo in candidates:
        admitted = [r for r in rows if all(rule.matches(r["pretraining_features"]) for rule in combo)]
        if not admitted:
            continue
        exact = all(r["measurement"]["exact_archive_bytes_and_sha"] and r["measurement"]["canonical_product_tree_equal"] for r in admitted)
        positive = all(float(r["measurement"]["saved_s"]) >= 0.005 for r in admitted)
        material = [r for r in admitted if r["measurement"]["material_exact_opportunity"]]
        if not (exact and positive and material):
            continue
        solutions.append(
            {
                "rules": [rule.json() for rule in combo],
                "admitted_rows": len(admitted),
                "material_rows": len(material),
                "minimum_saved_s": min(float(r["measurement"]["saved_s"]) for r in admitted),
                "minimum_saved_ratio": min(float(r["measurement"]["saved_ratio"]) for r in admitted),
                "admitted_feature_vectors": [r["pretraining_features"] for r in admitted],
            }
        )
    solutions.sort(key=lambda s: (-s["material_rows"], -s["admitted_rows"], len(s["rules"]), -s["minimum_saved_s"]))
    return solutions[:25]


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    rows = []
    for label, root, accepted_source_tree in COST._sources(work_root / "corpus"):
        work = work_root / "rows" / label.replace("/", "__")
        work.mkdir(parents=True, exist_ok=True)
        features = _pretraining_features(root)
        measurement = COST._measure(root, work, accepted_source_tree)
        rows.append({"label": label, "pretraining_features": features, "measurement": measurement})
        print(json.dumps({"label": label, "features": features, "material_exact": measurement["material_exact_opportunity"]}), flush=True)
    solutions = _search(rows)
    return {
        "schema": "cmpct-v030-r24-dictionary-skip-admission-v1",
        "contract": {
            "workloads": 15,
            "production_change": False,
            "release_credit": False,
            "policy_inputs": [
                "regular_files",
                "logical_bytes",
                "largest_file_bytes",
                "dictionary_sample_count",
                "dictionary_sample_bytes",
                "sample_mean_bytes",
                "sample_bytes_per_regular",
                "sample_fraction_of_logical",
            ],
            "forbidden_policy_inputs": ["workload_name", "benchmark_name", "path", "filename", "content_hash", "archive_hash"],
            "zero_nonexact_admissions_required": True,
            "positive_saved_time_required_for_every_admission": True,
            "material_exact_row_required": True,
            "future_promotion_requires_adversarial_generalization": True,
        },
        "rows": rows,
        "solutions": solutions,
        "summary": {
            "exact_workload_count": len(rows) == 15,
            "zero_counterexample_envelopes": len(solutions),
            "best_envelope": solutions[0] if solutions else None,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
