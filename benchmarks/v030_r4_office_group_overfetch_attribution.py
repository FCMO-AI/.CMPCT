from __future__ import annotations

"""Attribute the Office whole-group locality failures to metadata over-fetch.

Mission Lock / Referee
======================
The exact 4 KiB whole-group referee at 22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2
kept the same-input candidate below frozen v0.29 but produced 5/1,800 fixed-probe and
6/908 page-pair violations, worst 34,826 B. The preceding gated-seed reconstruction
had zero locality failures when metadata was charged as independently addressed records.

Hypothesis
----------
Without changing any bytes, grouping, reader, seed selector, request surface, codec,
page size or 8x limit, every request that fails under whole-group charging would satisfy
the same 32,768 B limit if charged only for the exact ANC1/BST1/SED1 records it actually
uses. Therefore the remaining failure is metadata *group over-fetch*, not compressed
payload/reconstruction work.

Disproof
--------
If any request that exceeds 32,768 B under whole-group accounting also exceeds 32,768 B
when the unchanged reader's exact individually framed metadata records are charged, the
hypothesis is false. This diagnostic does not authorize returning to one-frame-per-record
storage: that representation is already known to lose same-input density. It exists to
locate the debt so the next physical layout can amortize proof traffic without fetching
unrelated records.
"""

import argparse
import json
import os
from pathlib import Path

from benchmarks import v030_r4_office_group_charge_locality_referee as BASE

SCHEMA = "cmpct-v030-r4-office-group-overfetch-attribution-v1"
LIMIT = BASE.LIMIT


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    events: list[dict] = []
    original_charge = BASE._charge_groups

    def charged(reader, amap, bmap, smap, costs):
        group_bytes = int(original_charge(reader, amap, bmap, smap, costs))
        individual_bytes = int(reader.metadata_bytes())
        payload_bytes = int(reader.payload_bytes())
        group_ids: set[str] = set()
        for p in reader.anchor_frames:
            group_ids.add(amap[p])
        for bid in reader.block_frames:
            group_ids.add(bmap[bid])
        if isinstance(reader, BASE.SEED.SeedReader):
            for p in reader.seed_frames:
                group_ids.add(smap[p])
        kinds = {"anchor": 0, "block": 0, "seed": 0}
        for gid in group_ids:
            if ":a:" in gid:
                kinds["anchor"] += 1
            elif ":b:" in gid:
                kinds["block"] += 1
            elif ":s:" in gid:
                kinds["seed"] += 1
            else:
                raise RuntimeError(f"unknown metadata group kind: {gid}")
        events.append({
            "payload_bytes": payload_bytes,
            "individual_metadata_bytes": individual_bytes,
            "whole_group_metadata_bytes": group_bytes,
            "group_overfetch_bytes": group_bytes - individual_bytes,
            "individual_combined_bytes": payload_bytes + individual_bytes,
            "whole_group_combined_bytes": payload_bytes + group_bytes,
            "whole_group_fails_8x": payload_bytes + group_bytes > LIMIT,
            "individual_fails_8x": payload_bytes + individual_bytes > LIMIT,
            "anchor_records_touched": len(reader.anchor_frames),
            "block_records_touched": len(reader.block_frames),
            "seed_records_touched": len(reader.seed_frames) if isinstance(reader, BASE.SEED.SeedReader) else 0,
            "groups_touched": len(group_ids),
            "group_kinds_touched": kinds,
        })
        return group_bytes

    BASE._charge_groups = charged
    try:
        base = BASE.run(work, v029_checkout, worker)
    finally:
        BASE._charge_groups = original_charge

    failures = [e for e in events if e["whole_group_fails_8x"]]
    counterexamples = [e for e in failures if e["individual_fails_8x"]]
    if not failures:
        raise RuntimeError("prerequisite whole-group locality failure disappeared")

    worst_overfetch = max(events, key=lambda e: e["group_overfetch_bytes"])
    worst_group_failure = max(failures, key=lambda e: e["whole_group_combined_bytes"])
    max_individual_among_group_failures = max(e["individual_combined_bytes"] for e in failures)
    supported = len(counterexamples) == 0

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "prerequisite": {
            "source_sha": "22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2",
            "same_input_margin_bytes": base["grouped_storage"]["margin_to_same_input_v029_bytes"],
            "fixed_requests": base["whole_group_locality"]["fixed_requests"],
            "pair_requests": base["whole_group_locality"]["pair_requests"],
            "fixed_locality_failures": base["whole_group_locality"]["locality_failures"],
            "pair_locality_failures": base["whole_group_locality"]["pair_failures"],
            "worst_whole_group_bytes": base["whole_group_locality"]["worst_fixed_probe"]["combined_bytes"],
        },
        "attribution": {
            "charge_events": len(events),
            "whole_group_failure_events": len(failures),
            "individual_record_counterexamples": len(counterexamples),
            "max_individual_combined_bytes_among_group_failures": max_individual_among_group_failures,
            "slack_to_8x_at_that_max_bytes": LIMIT - max_individual_among_group_failures,
            "worst_group_failure": worst_group_failure,
            "worst_overfetch_event": worst_overfetch,
        },
        "hypothesis": {
            "all_whole_group_failures_are_metadata_overfetch_only": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_reader_and_payload": True,
            "same_4k_groups": True,
            "same_seed_selector": True,
            "fixed_limit_bytes": LIMIT,
            "no_parameter_sweep": True,
            "individual_frame_storage_is_not_a_candidate": True,
        },
        "next_if_supported": (
            "redesign only metadata physical grouping around actual co-access while preserving grouped storage economics; "
            "do not change payload reader, seed selector, codec, 4KiB page or 8x law"
        ),
        "next_if_falsified": (
            "preserve the counterexample and return to payload/reconstruction work before changing metadata grouping"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-group-overfetch-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-group-overfetch-attribution.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"attribution": d["attribution"], "hypothesis": d["hypothesis"]}, sort_keys=True))


if __name__ == "__main__":
    main()
