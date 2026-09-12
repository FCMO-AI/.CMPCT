from __future__ import annotations

"""Arithmetic referee for the remaining authenticated-trust locality budget.

Authority: adjudicated compact-monotone v2 receipt (run 34709794379): charged cold selective read
32,746 B under the fixed 32,768 B / 8x contract, leaving 22 B. The diagnostic footer contains a SHA-256
root but that root is not itself an external trust anchor.

Hypothesis: a fully cold/stateless reader could additionally fetch even the minimum 32-byte SHA-256
external trust anchor without violating 8x. Disproof is arithmetic: 32,746 + 32 > 32,768.

This does not claim canonical archive-open state must be re-read for every request. It freezes the semantic
fork: either reclaim >=10 B of cold locality, or bind the locator root into authenticated archive-open state
whose acquisition/verification cost is explicitly accounted elsewhere. Treating the root as free is forbidden.
"""

import json
import os
from pathlib import Path

SCHEMA = "cmpct-v030-r4-office-locator-trust-anchor-budget-v1"
LIMIT = 32_768
ADJUDICATED_COLD_READ = 32_746
SHA256_ROOT = 32


def run() -> dict:
    stateless = ADJUDICATED_COLD_READ + SHA256_ROOT
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "authority": {
            "run_id": 34709794379,
            "charged_cold_read_bytes": ADJUDICATED_COLD_READ,
            "fixed_limit_bytes": LIMIT,
            "existing_slack_bytes": LIMIT - ADJUDICATED_COLD_READ,
        },
        "trust_anchor": {
            "sha256_bytes": SHA256_ROOT,
            "stateless_cold_read_with_external_root_bytes": stateless,
            "over_limit_bytes": max(0, stateless - LIMIT),
        },
        "hypothesis": {
            "stateless_cold_sha256_trust_anchor_fits_existing_8x_slack": stateless <= LIMIT,
        },
        "decision": {
            "minimum_locality_bytes_to_reclaim_for_stateless_root": max(0, stateless - LIMIT),
            "alternative": "bind locator root to authenticated archive-open state and account that state explicitly",
            "free_trust_anchor_forbidden": True,
        },
        "contract": {"diagnostic_only": True, "release_credit": False, "thresholds_unchanged": True},
    }


def main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-locator-trust-anchor-budget.json'))
    a=p.parse_args()
    d=run(); a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps(d,sort_keys=True))


if __name__ == '__main__':
    main()
