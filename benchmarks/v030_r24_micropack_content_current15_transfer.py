from __future__ import annotations

"""Current-fingerprint 15-workload transfer for path-blind content-economic micro-packs.

Mission lock
============
The content-economic builder earned path-blind origin/hostile density evidence and
survived the causal selective-read referee.  This transfer asks the next falsifiable
question without changing its rule: does the *exact frozen builder* remain non-losing
against the same-grammar independent control across the full current 15-workload
portfolio, while preserving strong reconstruction, recovery and <=8x locality?

This is not a Genesis rescore and grants no release credit.  Execution faults are
kept separate from product losses.
"""

import argparse
import json
from pathlib import Path
import shutil
import traceback

from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks import v030_r24_micropack_content_economic_admission as CONTENT


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    paths, identities = CUR._build(work_root / "corpus")
    if len(identities) != 15:
        raise RuntimeError(f"expected 15 current workloads, got {len(identities)}")

    rows: dict[str, dict] = {}
    execution_errors: dict[str, dict[str, str]] = {}
    for ident in identities:
        key = f"{ident['suite']}/{ident['name']}"
        try:
            rows[key] = CONTENT._one(
                paths[key], work_root / "work" / ident["suite"] / ident["name"]
            )
        except Exception as exc:
            execution_errors[key] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=8)),
            }

    invariant_failures = [k for k, r in rows.items() if not r["invariants_pass"]]
    losses_vs_independent = [k for k, r in rows.items() if r["economic_delta_vs_independent_bytes"] > 0]
    losses_vs_extension = [k for k, r in rows.items() if r["economic_delta_vs_extension_bytes"] > 0]
    strict_wins_vs_independent = [k for k, r in rows.items() if r["economic_delta_vs_independent_bytes"] < 0]
    ties_vs_independent = [k for k, r in rows.items() if r["economic_delta_vs_independent_bytes"] == 0]

    independent_total = sum(int(r["independent"]["archive_bytes"]) for r in rows.values())
    extension_total = sum(int(r["extension"]["archive_bytes"]) for r in rows.values())
    content_total = sum(int(r["content_economic"]["archive_bytes"]) for r in rows.values())
    delta_ind = content_total - independent_total
    delta_ext = content_total - extension_total
    max_amp = max((float(r["content_economic"]["max_member_amplification"]) for r in rows.values()), default=0.0)
    max_decode = max((int(r["content_economic"]["max_decode_unit_bytes"]) for r in rows.values()), default=0)
    audit_cpu = sum(float(r["content_economic"]["audit"].get("audition_cpu_s", 0.0)) for r in rows.values())
    audit_wall = sum(float(r["content_economic"]["audit"].get("audition_wall_s", 0.0)) for r in rows.values())
    accepted_groups = sum(int(r["content_economic"]["audit"].get("accepted_groups", 0)) for r in rows.values())
    rejected_groups = sum(int(r["content_economic"]["audit"].get("rejected_groups", 0)) for r in rows.values())

    if execution_errors:
        verdict = "CONTENT_CURRENT15_EXECUTION_BLOCKED"
    elif invariant_failures:
        verdict = "RETIRE_CONTENT_CURRENT15_TRANSFER"
    elif losses_vs_independent or delta_ind > 0:
        verdict = "CONTENT_CURRENT15_NEEDS_REHABILITATION"
    elif losses_vs_extension:
        verdict = "CONTENT_CURRENT15_SAFE_WITH_EXTENSION_DEBT"
    else:
        verdict = "CONTENT_CURRENT15_GENERALIZES"

    return {
        "schema": "cmpct-v030-r24-micropack-content-current15-v1",
        "experiment_valid": not execution_errors,
        "release_credit": False,
        "canonical_builder_changed": False,
        "genesis_rescore": False,
        "path_signal_used": False,
        "corpus_fingerprint": CUR._fingerprint(identities),
        "identities": identities,
        "rows": rows,
        "execution_errors": execution_errors,
        "completed_workloads": len(rows),
        "invariant_failures": invariant_failures,
        "losses_vs_independent": losses_vs_independent,
        "losses_vs_extension": losses_vs_extension,
        "strict_wins_vs_independent": strict_wins_vs_independent,
        "ties_vs_independent": ties_vs_independent,
        "aggregate": {
            "logical_bytes": sum(int(r["logical_bytes"]) for r in identities),
            "independent_bytes": independent_total,
            "extension_bytes": extension_total,
            "content_economic_bytes": content_total,
            "delta_vs_independent_bytes": delta_ind,
            "delta_vs_extension_bytes": delta_ext,
            "strict_wins_vs_independent": len(strict_wins_vs_independent),
            "ties_vs_independent": len(ties_vs_independent),
            "losses_vs_independent": len(losses_vs_independent),
            "losses_vs_extension": len(losses_vs_extension),
            "max_member_amplification": max_amp,
            "max_decode_unit_bytes": max_decode,
            "audition_cpu_s": audit_cpu,
            "audition_wall_s": audit_wall,
            "accepted_groups": accepted_groups,
            "rejected_groups": rejected_groups,
            "invariant_failures": len(invariant_failures),
            "execution_failures": len(execution_errors),
        },
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-content-current15-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-content-current15.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "experiment_valid": result["experiment_valid"],
        "corpus_fingerprint": result["corpus_fingerprint"],
        "completed_workloads": result["completed_workloads"],
        "aggregate": result["aggregate"],
        "losses_vs_independent": result["losses_vs_independent"],
        "losses_vs_extension": result["losses_vs_extension"],
        "execution_errors": result["execution_errors"],
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
