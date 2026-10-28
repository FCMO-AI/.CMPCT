from __future__ import annotations

"""All-15 repaired-corpus binding for the historical r24 compact-control composition proof.

The v1 composition oracle accidentally reused ``v030_release_performance._build_corpora``. That helper is
intentionally a three-row runtime gate, so the composition campaign stopped after shifted versions, logs and ML
instead of exercising the frozen 15-workload release corpus. This wrapper changes only corpus construction: it
reuses the authoritative generalization gate's accepted-v0.29 identities, repair-v6 generation hooks and both
frozen workload suites, then delegates every archive/competitor/control calculation back to the v1 oracle.

Canonical C25CC01 has since acquired its own profile/productization/native/Android/selector/external authorities.
This older projection therefore cannot earn release or selector credit. A strict four-way result remains useful
historical evidence, while a fully exact near miss is valid negative evidence rather than a permanently failing CI
lane. Exactness, all-15 coverage, semantic preservation and zero projected regressions remain mandatory.

No product byte, threshold, timing boundary or admission rule changes here.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_r24_compact_control_composition_oracle as BASE
from benchmarks import v030_release_generalization as GENERAL


def _build_all(root: Path) -> dict[str, Path]:
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_compact_control_composition_neutral_v2",
    )
    hostile = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_compact_control_composition_hostile_v2",
    )
    repair = GENERAL.V029._load(
        GENERAL.V029.REPAIR_PATH,
        "cmpct_v030_compact_control_composition_repair_v2",
    )
    repair.install_generation_hooks(neutral)

    roots: dict[str, Path] = {}
    seen_keys: set[tuple[str, str]] = set()
    for label, builder, suite_root in (
        ("neutral_hostile_v1", neutral, root / "neutral"),
        ("resemblance_hostile_v1", hostile, root / "resemblance"),
    ):
        builder.build(suite_root)
        if label == "neutral_hostile_v1":
            repair.normalize_root(suite_root)
        for workload in sorted(path for path in suite_root.iterdir() if path.is_dir()):
            key = (label, workload.name)
            expected = accepted.get(key)
            if expected is None:
                raise RuntimeError(f"unexpected frozen workload in compact-control corpus: {key!r}")
            got_tree = GENERAL._historical_treehash(workload)
            expected_tree = str(expected["tree_sha256"])
            if got_tree != expected_tree:
                raise RuntimeError(
                    f"compact-control frozen source drift for {label}/{workload.name}: "
                    f"{got_tree} != {expected_tree}"
                )
            if workload.name in roots:
                raise RuntimeError(f"compact-control workload basename collision: {workload.name!r}")
            roots[workload.name] = workload
            seen_keys.add(key)

    missing = sorted(set(accepted) - seen_keys)
    if missing or len(roots) != 15:
        raise RuntimeError(
            f"compact-control composition requires the exact 15 accepted workloads: "
            f"built={len(roots)} missing={missing!r}"
        )
    return roots


BASE._build_all = _build_all


def run(work_root: Path) -> dict:
    result = BASE.run(work_root)
    all15 = result["all15"]
    target = result["encrypted_like"]
    four_way = bool(
        target["smaller_than_zip"]
        and target["smaller_than_zstd19"]
        and target["faster_than_zip"]
        and target["faster_than_zstd19"]
    )
    experiment_valid = bool(
        all15["workloads"] == 15
        and all15["zero_projected_byte_regressions"]
        and all15["all_semantics_preserved"]
        and all15["improved_workloads"] == 15
        and target["rounds"] == BASE.ROUNDS
        and target["shipping_size_deterministic"]
        and target["projected_size_deterministic"]
        and target["competitor_sizes_deterministic"]
        and target["dead_dictionary_elision_observed"]
        and target["compact_control_saving_bytes"] > 0
        and target["smaller_than_zip"]
        and target["faster_than_zstd19"]
        and target["strict_four_way_potential"] is four_way
    )
    result["schema"] = "cmpct-v030-r24-compact-control-composition-v2"
    result["historical_four_way_potential"] = four_way
    result["experiment_valid"] = experiment_valid
    result["promotion_signal"] = False
    result["selector_change"] = False
    result["release_credit"] = False
    result["claim_boundary"] = (
        "Historical research-only composition proof. Valid exact near misses are durable negative evidence. "
        "This lane cannot authorize selector or release changes; canonical C25CC01 authorities own promotion."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-compact-control-composition-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r24-compact-control-composition.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all15": {k: v for k, v in result["all15"].items() if k != "rows"},
                "encrypted_like": result["encrypted_like"],
                "historical_four_way_potential": result["historical_four_way_potential"],
                "experiment_valid": result["experiment_valid"],
                "promotion_signal": result["promotion_signal"],
                "release_credit": result["release_credit"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["experiment_valid"]:
        raise SystemExit("r24 compact-control composition experiment is invalid")


if __name__ == "__main__":
    main()
