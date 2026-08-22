from __future__ import annotations

"""Frozen 15-workload v0.29-ratchet shadow for the prospective logs terminal selector.

The shipping generalization authority remains unchanged and red until *all* historical regressions are removed.
This promotion lane asks whether the candidate eliminates the known logs regression without creating a new one,
using the same source identities, independently rebuilt accepted-v0.29 floors, complete canonical product bytes,
strong verification and <=8x selected-member locality accounting as the canonical authority.
"""

import argparse
import json
from pathlib import Path
import tempfile

from benchmarks import v030_release_generalization as HIST
from benchmarks import v030_release_generalization_canonical as CANON_BENCH
from experiments import entropygraph_v030_release_product_logs_candidate as CAND

PREDECESSOR_CANDIDATE_BYTES = 150_668_374
PREDECESSOR_REGRESSED_ROWS = 7
MIN_TOTAL_IMPROVEMENT_BYTES = 1_000_000


class _CandidateAdapter:
    treehash = staticmethod(CAND.treehash)
    strong_verify = staticmethod(CAND.strong_verify)

    @staticmethod
    def build(root: Path, out: Path) -> dict:
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".cmpct-v030-logs-generalization-floor-", dir=out.parent) as td:
            historical_path = Path(td) / "accepted-v029.cmpct"
            historical_stats = dict(CANON_BENCH.HIST_G04.BASE.build(root, historical_path))
            historical_bytes = historical_path.stat().st_size
            product = dict(CAND.build(root, out))
        old_canon = CANON_BENCH.CANON
        CANON_BENCH.CANON = CAND
        try:
            return CANON_BENCH._normalize_product_stats(product, historical_bytes, historical_stats, out)
        finally:
            CANON_BENCH.CANON = old_canon


ADAPTER = _CandidateAdapter()


def run(work_root: Path) -> dict:
    old_rc = HIST.RC
    HIST.RC = ADAPTER
    try:
        result = dict(HIST.run(work_root))
    finally:
        HIST.RC = old_rc

    logs_row = next(
        row for row in result["rows"]
        if row["suite"] == "neutral_hostile_v1" and row["name"] == "05_logs_and_telemetry"
    )
    logs_archive = work_root / "archives" / logs_row["suite"] / f"{logs_row['name']}.cmpct"
    verified = CAND.strong_verify(logs_archive)
    revision, profile = CAND._revision_for_archive(logs_archive)
    selected = logs_row["selected"]

    totals = result["totals"]
    promotion_gate = {
        "exact_workload_count": int(totals["workloads"]) == 15,
        "no_source_or_product_tree_drift": (
            int(totals["baseline_tree_drift_rows"]) == 0 and int(totals["product_tree_drift_rows"]) == 0
        ),
        "accepted_v029_identity_unchanged": int(totals["accepted_v029_bytes"]) == 137_499_525,
        "logs_selected_canonical_profile": selected == "logs-inverse" and revision == 25 and profile == CAND.LOGS_PROFILE,
        "logs_strong_verify": bool(verified.get("ok")) and verified.get("tree_sha256") == logs_row["tree_sha256"],
        "logs_strictly_beats_v029": int(logs_row["candidate_bytes"]) < int(logs_row["accepted_v029_bytes"]),
        "one_historical_regression_removed": int(totals["workloads_regressed"]) <= PREDECESSOR_REGRESSED_ROWS - 1,
        "aggregate_materially_advances": int(totals["candidate_bytes"]) <= PREDECESSOR_CANDIDATE_BYTES - MIN_TOTAL_IMPROVEMENT_BYTES,
        "locality_preserved": float(totals["max_selected_member_read_amplification"]) <= 8.0,
        "shipping_gate_not_reinterpreted": result["gate"].get("passed") is False or int(totals["workloads_regressed"]) == 0,
    }
    promotion_gate["passed"] = all(promotion_gate.values())
    result["candidate_engine"] = "experiments/entropygraph_v030_release_product_logs_candidate.py"
    result["candidate_release_facade"] = "cmpct-v030-release-product-logs-candidate-v1"
    result["logs_candidate"] = {
        "accepted_v029_bytes": int(logs_row["accepted_v029_bytes"]),
        "candidate_bytes": int(logs_row["candidate_bytes"]),
        "saving_vs_v029_bytes": int(logs_row["saving_vs_v029_bytes"]),
        "selected": selected,
        "format_revision": revision,
        "format_profile": profile,
    }
    result["candidate_promotion_gate"] = promotion_gate
    result["claim_boundary"] = (
        "promotion shadow only; frozen v0.29 no-regression and >=687,783-byte release saving remain unchanged and "
        "the canonical generalization authority must still reach zero regressed rows before release"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-selector-generalization-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-selector-generalization.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "totals": result["totals"],
        "logs_candidate": result["logs_candidate"],
        "candidate_promotion_gate": result["candidate_promotion_gate"],
        "shipping_gate": result["gate"],
    }, indent=2), flush=True)
    if not result["candidate_promotion_gate"]["passed"]:
        raise SystemExit("logs selector generalization promotion shadow failed")


if __name__ == "__main__":
    main()
