from __future__ import annotations

"""Superseding R27 custody wrapper for the frozen R26 Incremental Backups diagnosis.

R27 changes only the impossible R26 full-release-fingerprint equality. The actual three arm workers,
corpus target, locality observation and per-arm measurements are reused directly from the frozen R26
instrument so the scientific question and measurement grammar do not drift.
"""

import argparse
import json
import os
from pathlib import Path
import shutil

from benchmarks import v030_r26_incremental_backups_floor_diagnostic as R26
from benchmarks import v030_release_ablation_canonical as A
from experiments import entropygraph_v030_release_lock_strict as RELEASE_LOCK

AUTHORITY_PRODUCT_SUBSTRATE_HEAD = "b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a"
SCHEMA = "cmpct-v030-r27-incremental-backups-floor-diagnostic-v1"


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    # The full release fingerprint is evidence, not the product-substrate identity. Registering
    # this v030 benchmark/workflow intentionally changes that fingerprint. Product immutability is
    # enforced fail-closed by the workflow's exact Git diff against AUTHORITY_PRODUCT_SUBSTRATE_HEAD.
    manifest = RELEASE_LOCK.load_manifest_strict()
    release_fingerprint, fingerprint_paths = RELEASE_LOCK.CORE.fingerprint(manifest)

    target_source: Path | None = None
    expected_historical_tree: str | None = None
    for suite, source, expected in A._build_corpora(work_root / "corpus"):
        if suite == R26.TARGET_SUITE and source.name == R26.TARGET_NAME:
            target_source = source
            expected_historical_tree = expected
            break
    if target_source is None:
        raise RuntimeError("R27 frozen Incremental Backups corpus was not generated")

    member, member_bytes = R26._largest_regular_member(target_source)
    rows = {
        arm: R26._run_worker(arm, target_source, work_root / "archives" / f"{arm}.cmpct", member)
        for arm in R26.ARMS
    }
    trees = {row["tree_sha256"] for row in rows.values()}
    if len(trees) != 1:
        raise RuntimeError(f"R27 arm product identities diverged: {trees!r}")

    genuine = rows["genuine-r24"]
    release = rows["release-r24"]
    product = rows["current-product"]
    deltas = {
        "release_r24_minus_genuine_r24_bytes": int(release["archive_bytes"]) - int(genuine["archive_bytes"]),
        "current_product_minus_genuine_r24_bytes": int(product["archive_bytes"]) - int(genuine["archive_bytes"]),
        "current_product_minus_release_r24_bytes": int(product["archive_bytes"]) - int(release["archive_bytes"]),
    }

    if int(product["archive_bytes"]) <= int(genuine["archive_bytes"]):
        decision = "D1_REPRODUCTION_OR_SUBSTRATE_MISMATCH"
    elif not bool(genuine["locality_within_8x"]):
        decision = "D3_D4_GENUINE_R24_BYTE_FLOOR_EXPORTS_LOCALITY_DEBT"
    else:
        decision = "D2_LAWFUL_GENUINE_R24_FLOOR_EXISTS_REQUIRE_CARRYING_COST_BUILDER"

    return {
        "schema": SCHEMA,
        "status": "diagnostic-only-no-release-credit",
        "source_head": os.environ.get("GITHUB_SHA"),
        "authority_product_substrate_head": AUTHORITY_PRODUCT_SUBSTRATE_HEAD,
        "release_fingerprint_at_execution": release_fingerprint,
        "release_fingerprint_path_count": len(fingerprint_paths),
        "supersedes": "R26-invalid-self-inclusive-release-fingerprint-binding",
        "target": {"suite": R26.TARGET_SUITE, "name": R26.TARGET_NAME},
        "historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": next(iter(trees)),
        "largest_regular_member": member,
        "largest_regular_member_bytes": member_bytes,
        "locality_ceiling": R26.MAX_LOCALITY,
        "arms": rows,
        "deltas": deltas,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/r27-backups-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/r27-backups.json"))
    args = parser.parse_args()

    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "authority_product_substrate_head": result["authority_product_substrate_head"],
        "release_fingerprint_at_execution": result["release_fingerprint_at_execution"],
        "deltas": result["deltas"],
        "locality": {
            arm: row["decoded_context_amplification"] for arm, row in result["arms"].items()
        },
        "decision": result["decision"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
