from __future__ import annotations

"""Three-family slack-derived Office metadata-group locality referee.

Mission Lock / Referee
======================
The 4 KiB whole-group receipt at 22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2
measured a worst 4 KiB read with 30,690 B of compressed payload under the frozen 32,768 B
(8x) contract. That leaves 2,078 B for metadata.

A first slack-derived experiment allocated that allowance as if one metadata group were touched,
using a 2,030 B body cap after one 48 B auth/directory tax. Hostile review before adjudication
identified the missing structural fact: the unchanged reader can touch three independently grouped
record families -- ANC1 anchors, BST1 block state and selected SED1 seeds. A per-family bound must
pay all three group taxes before dividing the remaining body allowance.

Hypothesis
----------
Freeze the same measured payload ceiling, page size, 8x law, record grammar, admission candidate,
seed selector and source-sealed v0.29 comparator. Derive exactly one body bound:

    floor((32,768 - 30,690 - 3*48) / 3) = 644 B.

Pack each metadata family independently with this 644 B body ceiling and charge every whole group
touched by all 1,800 fixed probes and 908 adjacent-page-pair certificates. The representation is
supported only if exactness is preserved, every charged read is <=32,768 B and the *actual* grouped
stored bytes remain strictly below same-input frozen v0.29.

Disproof
--------
Any record larger than 644 B, byte mismatch, locality violation, or loss of same-input density
falsifies this geometry. The 644 B value is not swept or tuned. Reads may touch multiple groups of
the same family; that consequence is charged and may falsify the hypothesis.

A pass remains research evidence only. It still owes real serialization, authenticated directory/root
semantics, recovery, actual pread/seeks, corruption/resource attacks, isolated CPU/RSS, held-out
transfer and native/platform parity.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_r4_office_slack_derived_group_locality_referee as ONEGROUP

SCHEMA = "cmpct-v030-r4-office-three-family-group-locality-v1"
LOCALITY_LIMIT_BYTES = 32_768
PRIOR_WORST_PAYLOAD_BYTES = 30_690
FAMILY_COUNT = 3
FRAME_TAX_BYTES = ONEGROUP.FRAME_TAX_BYTES
BODY_BUDGET_BYTES = LOCALITY_LIMIT_BYTES - PRIOR_WORST_PAYLOAD_BYTES - FAMILY_COUNT * FRAME_TAX_BYTES
DERIVED_GROUP_BODY_LIMIT = BODY_BUDGET_BYTES // FAMILY_COUNT

if DERIVED_GROUP_BODY_LIMIT != 644:
    raise RuntimeError("three-family derived grouping invariant drift")


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    old_limit = ONEGROUP.DERIVED_GROUP_BODY_LIMIT
    ONEGROUP.DERIVED_GROUP_BODY_LIMIT = DERIVED_GROUP_BODY_LIMIT
    try:
        d = ONEGROUP.run(work, v029_checkout, worker)
    finally:
        ONEGROUP.DERIVED_GROUP_BODY_LIMIT = old_limit

    old_hyp = bool(d["hypothesis"].get("slack_derived_2030b_groups_preserve_density_and_8x_locality"))
    d["schema"] = SCHEMA
    d["derived_geometry"] = {
        "prior_receipt_sha": "22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2",
        "prior_worst_payload_bytes": PRIOR_WORST_PAYLOAD_BYTES,
        "fixed_locality_limit_bytes": LOCALITY_LIMIT_BYTES,
        "metadata_allowance_bytes": LOCALITY_LIMIT_BYTES - PRIOR_WORST_PAYLOAD_BYTES,
        "metadata_families": ["anchor", "block", "seed"],
        "family_count": FAMILY_COUNT,
        "unchanged_frame_tax_bytes": FRAME_TAX_BYTES,
        "three_family_tax_bytes": FAMILY_COUNT * FRAME_TAX_BYTES,
        "body_budget_after_family_tax_bytes": BODY_BUDGET_BYTES,
        "derived_group_body_limit_bytes": DERIVED_GROUP_BODY_LIMIT,
        "parameter_sweep": False,
        "derivation": "floor((32768-30690-3*48)/3)",
    }
    d["hypothesis"] = {
        "three_family_644b_groups_preserve_density_and_8x_locality": old_hyp,
    }
    d["contract"]["group_body_limit_bytes"] = DERIVED_GROUP_BODY_LIMIT
    d["contract"]["derived_from_three_physical_metadata_families"] = True
    d["contract"]["parameter_sweep"] = False
    d["next_if_supported"] = (
        "serialize this exact 644 B three-family geometry with authenticated directory/root + recovery and actual pread; "
        "then rerun the same locality surface and held-out transfer before selector admission"
    )
    d["next_if_falsified"] = (
        "preserve whether failure is density, record indivisibility or multi-group fanout; use the overfetch attribution "
        "to redesign co-access layout rather than sweep caps or relax 8x"
    )
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-three-family-group-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-three-family-group-locality.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "derived_geometry": d["derived_geometry"],
        "grouped_storage": d["grouped_storage"],
        "whole_group_locality": {k: v for k, v in d["whole_group_locality"].items() if k != "rows"},
        "profile": d["profile"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
