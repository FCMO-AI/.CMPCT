"""Strict semantic wrapper for the ONE-G0.2 native witness-deferral A/B.

This wrapper deliberately strengthens, rather than changes, the frozen performance
question.  The underlying A/B owns timing/traffic.  Here every case labelled as a
positive by the frozen matrix must actually reach the same accepted Law in both
arms; positive rows cannot disappear merely because the baseline failed to
nominate them.  When both arms run the safe proof, its accepted-proof count and
safe-dispatch path must also agree.
"""
from __future__ import annotations

import json

from benchmarks.one.one_g02_native_witness_deferral_safe_proof_ab import NEGATIVES, run


def main() -> int:
    result = run()
    rows = result["rows"]

    required_positive_failures = []
    safe_proof_parity_failures = []
    for row in rows:
        case = str(row["case"])
        key = (int(row["relation_bytes"]), int(row["seed"]), case)
        if case not in NEGATIVES:
            if not (bool(row["baseline_final_law"]) and bool(row["candidate_final_law"])):
                required_positive_failures.append(key)
        if bool(row["baseline_nominated"]) and bool(row["candidate_nominated"]):
            if (
                int(row["baseline_dispatch_path"]) != int(row["candidate_dispatch_path"])
                or int(row["baseline_exact_proofs"]) != int(row["candidate_exact_proofs"])
            ):
                safe_proof_parity_failures.append(key)

    result["strict_required_positive_failures"] = required_positive_failures
    result["strict_safe_proof_parity_failures"] = safe_proof_parity_failures
    result["strict_semantic_gate"] = not required_positive_failures and not safe_proof_parity_failures

    if result["decision"] == "advance_native_witness_deferral_safe_proof" and not result["strict_semantic_gate"]:
        result["decision"] = "reject_native_witness_deferral_safe_proof"
    elif result["decision"] == "hold_native_witness_deferral_safe_proof" and not result["strict_semantic_gate"]:
        result["decision"] = "reject_native_witness_deferral_safe_proof"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] != "reject_native_witness_deferral_safe_proof" else 1


if __name__ == "__main__":
    raise SystemExit(main())
