from __future__ import annotations

"""Canonical-profile binding for the G0-G4 ML cache-policy A/B.

The original oracle correctly builds the promoted product, but then inspects and streams that archive through the
release-reader module outside the canonical r25 operation context.  The promoted ML winner uses ``CMP25G4`` while
the research module globals are restored to ``CMPNXG4`` after ``PRODUCT.build`` returns, so the oracle rejected the
real shipping G0-G4 archive before measuring either cache policy.

This wrapper changes no cache policy, archive byte, reader limit or promotion hurdle.  It holds the exact same
operation-scoped canonical profile binding used by the shipping r25 facade around the complete A/B.  The underlying
v1 oracle still requires the same 32 MiB node cache, 64 MiB record cache, exact tree identity, no increase in
physical reads, >=10% verification improvement and >=15% extraction improvement before the experiment may pass.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_g04_ml_cache_policy_oracle as V1
from experiments import entropygraph_v030_release_product as PRODUCT


def run(work_root: Path) -> dict:
    with PRODUCT.C._revision25_profile_context():
        result = dict(V1.run(work_root))
    result["schema"] = "cmpct-v030-g04-ml-cache-policy-v2"
    result["canonical_profile_binding"] = {
        "format_revision": 25,
        "magic": PRODUCT.G04_MAGIC.hex(),
        "tail_magic": PRODUCT.G04_TAIL.hex(),
        "operation_scoped": True,
        "research_globals_restored_after_run": True,
    }
    result["claim_boundary"] = (
        "Research-only same-memory cache-policy A/B on the exact promoted canonical ML G0-G4 archive. v2 fixes "
        "only the oracle's profile binding; v1's cache budgets, exact-tree checks, physical-read requirement and "
        "material speed thresholds remain unchanged. A green result does not authorize a production reader change; "
        "ordinary reader/fuzz/native/runtime authority must pass after any implementation."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cache-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-cache-v2.json"))
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
                "extract_physical_read_improvement_fraction": result["extract_physical_read_improvement_fraction"],
                "gate": result["gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["gate"]["passed"]:
        raise SystemExit("canonical G0-G4 ML reuse-aware cache policy did not earn promotion")


if __name__ == "__main__":
    main()
