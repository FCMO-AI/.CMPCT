from __future__ import annotations

"""Full Office integration referee for the direct canonical-uvarint rule.

Mission Lock
============
The deterministic v6 representation, 644 B authenticated groups, LOC1 bytes, primary/tail/footer,
1 MiB raw ceiling, zlib compressBound input ceiling, source-sealed v0.29 control and fixed 8x locality
law remain unchanged. The only candidate change is the v4 streaming parser's proof of canonical unsigned
LEB128: replace slice+re-encode comparison with the decision-equivalent local terminal-payload rule already
falsified against boundary/overlong controls in the fresh-process resource referee.

Hypothesis
----------
The direct rule preserves every v6 density/locality/integrity/recovery/resource verdict and exact record
recovery on the Office corpus, while retaining canonical/non-canonical hostile decisions. Since persisted
bytes are unchanged, any size or locality drift falsifies the integration immediately.

Disproof
--------
False on any inherited hostile-control regression, reconstruction/record mismatch, changed stored bytes,
changed worst-read charge, canonical-control mismatch or v6 dual-bound failure. PASS remains diagnostic:
canonical archive-root binding, end-to-end isolated reader throughput/RSS, held-out transfer, native parity
and portability are still promotion debt.
"""

import argparse
import json
import os
from pathlib import Path

from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_office_compact_monotone_directory_v6 as V6
from benchmarks import v030_r4_compact_locator_parser_resource_v2 as FAST

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v7"


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    controls = FAST._semantic_controls()
    original = V4._read_canonical_uvarint
    V4._read_canonical_uvarint = FAST._read_canonical_uvarint_fast
    try:
        d = V6.run(work, v029_checkout, worker)
    finally:
        V4._read_canonical_uvarint = original

    inherited = bool(
        d["hypothesis"]["compact_monotone_locator_preserves_density_8x_integrity_parser_and_dual_bounds"]
    )
    controls_ok = all(controls.values())
    d["schema"] = SCHEMA
    d["source_commit"] = os.environ.get("EVIDENCE_HEAD")
    d["uvarint_proof"] = {
        "method": "terminal-payload canonical unsigned LEB128 rule",
        "canonical_boundaries_match": controls["canonical_boundaries_match"],
        "overlong_controls_match": controls["overlong_controls_match"],
        "representation_bytes_changed": False,
    }
    d["contract"]["direct_uvarint_rule_only_candidate_change"] = True
    d["contract"]["v6_representation_and_thresholds_frozen"] = True
    d["hypothesis"] = {
        "direct_uvarint_proof_preserves_full_office_locator_contract": inherited and controls_ok,
    }
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v7-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-v7.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "compact_locator": d["compact_locator"],
        "selective_read": d["selective_read"],
        "hostile_controls": d["hostile_controls"],
        "resource_bounds": d["resource_bounds"],
        "uvarint_proof": d["uvarint_proof"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
