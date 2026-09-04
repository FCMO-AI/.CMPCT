from __future__ import annotations

"""Fail-closed causal ratchet for the frozen-Shifted PrefixGraph RSS owner.

The underlying oracle measures python-zstandard's own reported ZSTD_CCtx memory after
real level-19 raw-prefix auditions and independently re-measures fresh-process 1- and
4-worker shipping PrefixGraph RSS.  This wrapper deliberately adds no new compressor
or product behavior.  It strengthens the interpretation boundary: live CCtx memory is
allowed to nominate a native/context-lifetime redesign only when (a) one context owns a
material share of the single-worker increment, (b) shipping RSS scales strongly with
worker count, and (c) four independently reported context footprints explain a material
share of the four-worker increment.

A failed causal ratchet is useful negative evidence and must redirect investigation;
a pass is research direction only and grants zero release credit.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_prefixgraph_cctx_memory_oracle as BASE

MIN_FOUR_CCTX_SHARE_OF_W4 = 0.60


def run(work_root: Path) -> dict:
    evidence = BASE.run(work_root)
    summary = evidence["summary"]
    base_gate = evidence["gate"]
    four_share = float(summary["four_max_cctx_to_w4_incremental_rss"])
    causal = bool(base_gate["causal_signal"] and four_share >= MIN_FOUR_CCTX_SHARE_OF_W4)
    return {
        "schema": "cmpct-v030-prefixgraph-cctx-causal-ratchet-v1",
        "source_commit": evidence["source_commit"],
        "target": evidence["target"],
        "base_evidence": evidence,
        "contract": {
            "production_change": False,
            "candidate_set_changed": False,
            "compressor_parameters_changed": False,
            "archive_identity_required": True,
            "minimum_four_cctx_share_of_w4_incremental_rss": MIN_FOUR_CCTX_SHARE_OF_W4,
            "release_credit": False,
        },
        "gate": {
            "exact_shipping_identity": bool(base_gate["exact_shipping_identity"]),
            "base_causal_signal": bool(base_gate["causal_signal"]),
            "four_cctx_share_of_w4_incremental_rss": four_share,
            "strong_causal_signal": causal,
            "passed": bool(base_gate["passed"]),
        },
        "next_architecture_target": (
            "native-or-explicit-ZSTD_CCtx-lifetime redesign"
            if causal
            else "continue memory ownership attribution before changing product architecture"
        ),
        "release_credit": False,
        "claim_boundary": (
            "Research-only causal attribution. Even a strong signal cannot alter shipping workers, bytes, "
            "release thresholds, or release authority; it only selects the next exact experiment."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-cctx-causal-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-cctx-causal.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["base_evidence"]["summary"], "gate": result["gate"], "next": result["next_architecture_target"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("PrefixGraph CCtx causal ratchet lost exact shipping identity")


if __name__ == "__main__":
    main()
