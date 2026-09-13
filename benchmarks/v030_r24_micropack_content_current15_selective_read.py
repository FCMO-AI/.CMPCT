from __future__ import annotations

"""Current-15 selective-read transfer for path-blind content-economic micro-packs.

The focused Developer/Tiny referee survived, but the full current-15 density
transfer exposed a larger legal decode unit (938,064 B).  This referee owns that
new risk directly: build the exact unchanged content-economic candidate and
same-grammar independent control for every current workload, select the most
expensive content-packed members by decoded context, and time identical fixed
range reads.

No locality threshold, range size, builder policy, comparator or timing envelope
is changed. Execution faults remain separate from product debt. Research-only.
"""

import argparse
import json
from pathlib import Path
import shutil
import traceback

from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks import v030_r24_micropack_content_selective_read_referee as SEL
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder


def _one(source: Path, root: Path) -> dict:
    independent = SEL._build_variant(SAME.NoMicroPackBuilder, source, root / "independent")
    content = SEL._build_variant(ContentEconomicBuilder, source, root / "content")
    clean = {
        "independent": {k: v for k, v in independent.items() if k not in {"archive", "index"}},
        "content_economic": {k: v for k, v in content.items() if k not in {"archive", "index"}},
    }
    probes = SEL._probes(source, content)
    if not probes:
        if content["final_membership_bytes"] != independent["final_membership_bytes"]:
            raise RuntimeError("zero content-pack workload changed artifact economics")
        return {
            "grouped": False,
            "variants": clean,
            "probe_count": 0,
            "timing_debt": False,
            "invariants_pass": bool(independent["strong_tree_exact"] and content["strong_tree_exact"] and content["locality_pass"]),
        }

    timings = {
        "independent": SEL._time_variant(independent, probes),
        "content_economic": SEL._time_variant(content, probes),
    }
    debt = SEL._confirmed_regression(timings["content_economic"], timings["independent"])
    invariants = {
        "independent_tree": bool(independent["strong_tree_exact"]),
        "content_tree": bool(content["strong_tree_exact"]),
        "content_locality": bool(content["locality_pass"]),
        "content_payload": bool(content["physical_payload_exact"]),
        "content_recovery": bool(content["tail_recovery"]),
        "read_exact": not timings["independent"]["correctness_failures"] and not timings["content_economic"]["correctness_failures"],
        "amp_at_most_8x": float(content["max_member_amplification"]) <= SEL.BASE.LOCALITY_BUDGET + 1e-9,
    }
    max_probe = max(
        (x for x in timings["content_economic"]["charges"]),
        key=lambda x: int(x["decoded_context_bytes"]),
    )
    return {
        "grouped": True,
        "variants": clean,
        "probe_count": len(probes),
        "timings": timings,
        "content_vs_independent": debt,
        "timing_debt": bool(debt["confirmed_regression"]),
        "max_probe": max_probe,
        "invariants": invariants,
        "invariants_pass": all(invariants.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    paths, identities = CUR._build(work_root / "corpus")
    if len(identities) != 15:
        raise RuntimeError(f"expected 15 workloads, got {len(identities)}")
    rows = {}
    execution_errors = {}
    for ident in identities:
        key = f"{ident['suite']}/{ident['name']}"
        try:
            rows[key] = _one(paths[key], work_root / "work" / ident["suite"] / ident["name"])
        except Exception as exc:
            execution_errors[key] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, limit=8)),
            }

    grouped = [k for k, r in rows.items() if r["grouped"]]
    timing_debt = [k for k, r in rows.items() if r.get("timing_debt")]
    invariant_failures = [k for k, r in rows.items() if not r["invariants_pass"]]
    max_decode_key = max(
        grouped,
        key=lambda k: int(rows[k]["variants"]["content_economic"]["max_decode_unit_bytes"]),
        default=None,
    )
    if execution_errors:
        verdict = "CONTENT_CURRENT15_SELECTIVE_EXECUTION_BLOCKED"
    elif invariant_failures:
        verdict = "RETIRE_CONTENT_CURRENT15_SELECTIVE"
    elif timing_debt:
        verdict = "CONTENT_CURRENT15_SELECTIVE_REHABILITATION_REQUIRED"
    else:
        verdict = "CONTENT_CURRENT15_SELECTIVE_SURVIVES"

    return {
        "schema": "cmpct-v030-r24-content-current15-selective-v1",
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
        "grouped_workloads": grouped,
        "timing_debt": timing_debt,
        "invariant_failures": invariant_failures,
        "max_decode_workload": max_decode_key,
        "max_decode_unit_bytes": int(rows[max_decode_key]["variants"]["content_economic"]["max_decode_unit_bytes"]) if max_decode_key else 0,
        "timing_regression_confidence": {
            "relative": SEL.RELATIVE_REGRESSION,
            "absolute_s": SEL.ABSOLUTE_REGRESSION_S,
            "rule": "confirmed only when candidate slowdown exceeds both thresholds",
        },
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-content-current15-selective-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-content-current15-selective.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "completed_workloads": result["completed_workloads"],
        "grouped_workloads": result["grouped_workloads"],
        "timing_debt": result["timing_debt"],
        "invariant_failures": result["invariant_failures"],
        "execution_errors": result["execution_errors"],
        "max_decode_workload": result["max_decode_workload"],
        "max_decode_unit_bytes": result["max_decode_unit_bytes"],
        "grouped_timings_ms_per_probe": {
            name: {
                "independent": row["timings"]["independent"]["median_read_wall_ms_per_probe"],
                "content": row["timings"]["content_economic"]["median_read_wall_ms_per_probe"],
                "max_decode": row["variants"]["content_economic"]["max_decode_unit_bytes"],
            }
            for name, row in result["rows"].items() if row["grouped"]
        },
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
