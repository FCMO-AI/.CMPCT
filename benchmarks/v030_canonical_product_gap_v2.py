from __future__ import annotations

"""Superseding Office/Analytics product-gap diagnostic on exact accepted repair-v6 source identities."""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import neutral_hostile_determinism_repair_v6 as REPAIR
from benchmarks import v030_canonical_product_gap_diagnostic as V1
from benchmarks import v030_release_generalization as GENERAL

PREREG = "docs/v030-rnd/V030_CANONICAL_PRODUCT_GAP_V2_PREREG.md"
TARGETS = (
    ("02_office_workspace", V1.N.corpus_office),
    ("04_analytics_and_database", V1.N.corpus_analytics),
)


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    accepted = GENERAL._accepted_v029_rows()

    # Install the exact accepted producer repair before either target is generated. normalize_workload below remains
    # the accepted idempotent post-generation guard, matching release-generalization custody.
    REPAIR.install_generation_hooks(V1.N)

    rows: list[dict] = []
    for name, builder in TARGETS:
        corpus_root = work_root / f"corpus-{name}"
        corpus_root.mkdir(parents=True, exist_ok=True)
        builder(corpus_root)
        source = corpus_root / name
        if not source.is_dir():
            raise RuntimeError(f"workload builder did not create expected source tree: {source}")
        REPAIR.normalize_workload(source)

        expected = accepted[("neutral_hostile_v1", name)]
        historical_tree = GENERAL._historical_treehash(source)
        if historical_tree != str(expected["tree_sha256"]):
            raise RuntimeError(
                f"repair-v6 source identity mismatch for {name}: {historical_tree} != {expected['tree_sha256']}"
            )
        expected_v029_bytes = int(expected["accepted_v029_bytes"])

        with tempfile.TemporaryDirectory(prefix=f"gap-v2-{name}-", dir=work_root) as td:
            measured = V1._candidate_stats(source, Path(td))
        if int(measured["accepted_v029_bytes"]) != expected_v029_bytes:
            raise RuntimeError(
                f"rebuilt accepted-v0.29 byte floor drift for {name}: "
                f"{measured['accepted_v029_bytes']} != {expected_v029_bytes}"
            )

        row = {
            "workload": name,
            "suite": "neutral_hostile_v1",
            "accepted_repair_v6_tree_sha256": str(expected["tree_sha256"]),
            "measured_historical_tree_sha256": historical_tree,
            "source_identity_match": True,
            "accepted_v029_floor_bytes": expected_v029_bytes,
            **measured,
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    return {
        "schema": "cmpct-v030-canonical-product-gap-v2",
        "preregistration": PREREG,
        "supersedes": "cmpct-v030-canonical-product-gap-v1 for exact Office/Analytics product-gap claims",
        "v1_office_status": "INVALID_AS_EXACT_ACCEPTED_V029_GAP_DUE_TO_MISSING_REPAIR_V6_SOURCE_CUSTODY",
        "claim_boundary": (
            "diagnostic-only exact byte decomposition on accepted repair-v6 source identities; control-free bytes "
            "gift required filesystem semantics and never earn product/release credit"
        ),
        "rows": rows,
        "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/canonical-product-gap-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/canonical-product-gap-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
