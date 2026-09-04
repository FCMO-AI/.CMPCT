from __future__ import annotations

"""Frozen R29 same-run superseding Builder for Incremental Backups r24 carrying cost.

R29 changes only R28's invalid cross-run exact-gap equality. Target, arms, workers,
measurements and locality law are reused from R28.
"""

import argparse
import json
import os
from pathlib import Path
import shutil

from benchmarks import v030_r28_incremental_backups_r24_carrying_cost_builder as R28
from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

AUTHORITY_PRODUCT_SUBSTRATE = "b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a"
SCHEMA = "cmpct-v030-r29-incremental-backups-r24-carrying-cost-same-run-v1"


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    manifest = RELEASE_LOCK.load_manifest_strict()
    fingerprint, _paths = RELEASE_LOCK.CORE.fingerprint(manifest)

    target_source: Path | None = None
    expected_historical_tree: str | None = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == R28.TARGET_SUITE and source.name == R28.TARGET_NAME:
            target_source = source
            expected_historical_tree = expected
            break
    if target_source is None:
        raise RuntimeError("R29 frozen Incremental Backups corpus was not generated")

    member, member_bytes = R28._largest_regular_member(target_source)
    rows = {
        arm: R28._run_worker(arm, target_source, work_root / "archives" / f"{arm}.cmpct", member)
        for arm in R28.ARMS
    }
    trees = {row["tree_sha256"] for row in rows.values()}
    strong_ok = all(bool(row["strong_verify_ok"]) for row in rows.values())
    same_tree = len(trees) == 1

    genuine_bytes = int(rows["genuine-r24"]["archive_bytes"])
    release_bytes = int(rows["release-r24"]["archive_bytes"])
    same_run_gap = release_bytes - genuine_bytes

    for arm in R28.EXPERIMENTAL_ARMS:
        arm_bytes = int(rows[arm]["archive_bytes"])
        removed = release_bytes - arm_bytes
        rows[arm]["bytes_vs_release"] = arm_bytes - release_bytes
        rows[arm]["bytes_vs_genuine"] = arm_bytes - genuine_bytes
        rows[arm]["positive_gap_removed_bytes"] = max(0, removed)
        rows[arm]["positive_gap_removed_fraction"] = max(0, removed) / same_run_gap if same_run_gap > 0 else None

    if not strong_ok or not same_tree or same_run_gap <= 0:
        decision = "SUBSTRATE_OR_CORRECTNESS_FAILURE"
    else:
        restoring = [
            arm for arm in R28.EXPERIMENTAL_ARMS
            if int(rows[arm]["archive_bytes"]) <= genuine_bytes
        ]
        locality_debt = [arm for arm in restoring if not bool(rows[arm]["locality_within_8x"])]
        lawful_restoring = [arm for arm in restoring if bool(rows[arm]["locality_within_8x"])]
        partial = [
            arm for arm in R28.EXPERIMENTAL_ARMS
            if int(rows[arm]["archive_bytes"]) < release_bytes
            and bool(rows[arm]["locality_within_8x"])
        ]
        if locality_debt:
            decision = "LOCALITY_DEBT"
        elif len(lawful_restoring) == 1:
            decision = "SINGLE_OWNER"
        elif len(lawful_restoring) > 1:
            decision = "MULTIPLE_SINGLE_OWNERS"
        elif partial:
            decision = "PARTIAL_OWNER"
        else:
            decision = "NO_ONE_FACTOR_EXPLANATION"

    ranked_partial = sorted(
        (
            {
                "arm": arm,
                "positive_gap_removed_bytes": int(rows[arm]["positive_gap_removed_bytes"]),
                "positive_gap_removed_fraction": rows[arm]["positive_gap_removed_fraction"],
            }
            for arm in R28.EXPERIMENTAL_ARMS
            if int(rows[arm]["positive_gap_removed_bytes"]) > 0
            and bool(rows[arm]["locality_within_8x"])
        ),
        key=lambda row: (-row["positive_gap_removed_bytes"], row["arm"]),
    )

    return {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "source_head": os.environ.get("GITHUB_SHA"),
        "authority_product_substrate_head": AUTHORITY_PRODUCT_SUBSTRATE,
        "release_fingerprint_at_execution": fingerprint,
        "supersedes": "R28-invalid-cross-run-exact-gap-equality",
        "target": {"suite": R28.TARGET_SUITE, "name": R28.TARGET_NAME},
        "generator_expected_tree_sha256": expected_historical_tree,
        "product_tree_sha256": next(iter(trees)) if same_tree else None,
        "largest_regular_member": member,
        "largest_regular_member_bytes": member_bytes,
        "locality_ceiling": R28.MAX_LOCALITY,
        "same_run_release_minus_genuine_bytes": same_run_gap,
        "arms": rows,
        "ranked_partial_owners": ranked_partial,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r29-backups-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r29-backups.json"))
    args = parser.parse_args()

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "release_fingerprint_at_execution": result["release_fingerprint_at_execution"],
        "same_run_release_minus_genuine_bytes": result["same_run_release_minus_genuine_bytes"],
        "arms": {
            arm: {
                "archive_bytes": row["archive_bytes"],
                "amplification": row["decoded_context_amplification"],
                "bytes_vs_release": row.get("bytes_vs_release"),
                "bytes_vs_genuine": row.get("bytes_vs_genuine"),
            }
            for arm, row in result["arms"].items()
        },
        "ranked_partial_owners": result["ranked_partial_owners"],
        "decision": result["decision"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
