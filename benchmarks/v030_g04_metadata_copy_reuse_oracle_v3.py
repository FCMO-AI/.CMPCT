from __future__ import annotations

"""Canonical-profile binding for the G0-G4 duplicate-metadata A/B.

The v1 experiment builds the promoted product and then opens the resulting G0-G4 archive after the product builder
has restored research globals. That makes canonical ``CMP25G4`` bytes look like a non-G0-G4 archive to the research
reader and aborts before measurement. v2 correctly separates clean negative evidence from promotion, but inherits
that binding bug. v3 holds the exact shipping revision-25 profile context around the complete v2 experiment.

No archive byte, cache budget, locality rule, recovery path or speed threshold changes.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_g04_metadata_copy_reuse_oracle_v2 as V2
from experiments import entropygraph_v030_release_product as PRODUCT


def run(work_root: Path) -> dict:
    with PRODUCT.C._revision25_profile_context():
        result = dict(V2.run(work_root))
    result["schema"] = "cmpct-v030-g04-metadata-copy-reuse-v3"
    result["canonical_profile_binding"] = {
        "format_revision": 25,
        "magic": PRODUCT.G04_MAGIC.hex(),
        "tail_magic": PRODUCT.G04_TAIL.hex(),
        "operation_scoped": True,
        "research_globals_restored_after_run": True,
    }
    result["claim_boundary"] = (
        "Research-only duplicate-control decode A/B on the exact promoted canonical ML G0-G4 archive. v3 fixes "
        "only profile binding; v1/v2 identity, corruption, cache-budget and material-speed requirements are unchanged."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-meta-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "canonical_profile_binding": result["canonical_profile_binding"],
                "verify_improvement_fraction": result["verify_improvement_fraction"],
                "extract_improvement_fraction": result["extract_improvement_fraction"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("G0-G4 metadata-copy reuse experiment invalid")


if __name__ == "__main__":
    main()
