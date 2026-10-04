from __future__ import annotations

"""Current-fingerprint 15-workload hostile transfer for locality-derived micro-packing.

This is deliberately not a frozen Genesis score. It regenerates the current corpus,
fingerprints it, then compares the two physical strategies under the same grammar.
Execution failures are persisted per workload instead of aborting the whole receipt:
a harness/runtime failure is not product-loss evidence.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import traceback

from benchmarks import v030_current15_stable_corpus as NEUTRAL
from benchmarks import resemblance_hostile_corpus_v1 as RESEMBLANCE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME


def _build(root: Path) -> tuple[dict[str, Path], list[dict]]:
    neutral_root = root / "neutral"
    resemblance_root = root / "resemblance"
    neutral = NEUTRAL.build(neutral_root)
    resemblance = RESEMBLANCE.build(resemblance_root)
    paths: dict[str, Path] = {}
    identities: list[dict] = []
    for suite, manifest, parent, key in (
        ("neutral_hostile_v1", neutral, neutral_root, "corpora"),
        ("resemblance_hostile_v1", resemblance, resemblance_root, "workloads"),
    ):
        for row in manifest[key]:
            name = str(row["name"])
            ident = {
                "suite": suite,
                "name": name,
                "files": int(row["files"]),
                "logical_bytes": int(row["logical_bytes"]),
                "tree_sha256": str(row["tree_sha256"]),
            }
            key_name = f"{suite}/{name}"
            identities.append(ident)
            paths[key_name] = parent / name
    identities.sort(key=lambda r: (r["suite"], r["name"]))
    return paths, identities


def _fingerprint(rows: list[dict]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    paths, identities = _build(work_root / "corpus")
    if len(identities) != 15:
        raise RuntimeError(f"expected 15 current workloads, got {len(identities)}")

    rows: dict[str, dict] = {}
    execution_errors: dict[str, dict[str, str]] = {}
    for ident in identities:
        key = f"{ident['suite']}/{ident['name']}"
        try:
            rows[key] = SAME._one(
                paths[key], work_root / "work" / ident["suite"] / ident["name"]
            )
        except Exception as exc:  # Receipt must preserve the failing workload and mechanism.
            execution_errors[key] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__, limit=8)
                ),
            }

    invariant_failures = [k for k, r in rows.items() if not r["invariants_pass"]]
    economic_failures = [k for k, r in rows.items() if not r["economic_pass"]]
    grouped_wins = [
        k for k, r in rows.items()
        if r["derived_group_count"] > 0 and r["same_grammar_delta_bytes"] < 0
    ]
    zero_group_ties = [
        k for k, r in rows.items()
        if r["derived_group_count"] == 0 and r["same_grammar_delta_bytes"] == 0
    ]

    independent_total = sum(int(r["same_grammar_independent_bytes"]) for r in rows.values())
    derived_total = sum(int(r["same_grammar_derived_bytes"]) for r in rows.values())
    delta = derived_total - independent_total

    if execution_errors:
        verdict = "CURRENT15_MICROPACK_EXECUTION_BLOCKED"
    elif invariant_failures:
        verdict = "RETIRE_CURRENT15_MICROPACK_TRANSFER"
    elif economic_failures or delta >= 0:
        verdict = "CURRENT15_MICROPACK_NEEDS_ECONOMIC_ADMISSION"
    else:
        verdict = "CURRENT15_MICROPACK_GENERALIZES"

    max_amp = max((float(r["max_member_amplification"]) for r in rows.values()), default=0.0)
    max_decode = max((int(r["max_decode_unit_bytes"]) for r in rows.values()), default=0)

    return {
        "schema": "cmpct-v030-r24-micropack-current15-transfer-v2",
        "experiment_valid": not execution_errors,
        "release_credit": False,
        "canonical_builder_changed": False,
        "corpus_fingerprint": _fingerprint(identities),
        "identities": identities,
        "rows": rows,
        "execution_errors": execution_errors,
        "completed_workloads": len(rows),
        "aggregate": {
            "logical_bytes": sum(int(r["logical_bytes"]) for r in identities),
            "same_grammar_independent_bytes": independent_total,
            "same_grammar_derived_bytes": derived_total,
            "delta_bytes": delta,
            "delta_pct": (delta / independent_total * 100.0) if independent_total else 0.0,
            "grouped_wins": len(grouped_wins),
            "zero_group_ties": len(zero_group_ties),
            "economic_failures": len(economic_failures),
            "invariant_failures": len(invariant_failures),
            "execution_failures": len(execution_errors),
            "max_member_amplification": max_amp,
            "max_decode_unit_bytes": max_decode,
            "independent_build_cpu_s_sum": sum(float(r["independent_build_cpu_s"]) for r in rows.values()),
            "derived_build_cpu_s_sum": sum(float(r["derived_build_cpu_s"]) for r in rows.values()),
            "independent_build_wall_s_sum": sum(float(r["independent_build_wall_s"]) for r in rows.values()),
            "derived_build_wall_s_sum": sum(float(r["derived_build_wall_s"]) for r in rows.values()),
        },
        "invariant_failures": invariant_failures,
        "economic_failures": economic_failures,
        "grouped_wins": grouped_wins,
        "zero_group_ties": zero_group_ties,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-current15-micropack-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-current15-micropack.json"))
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
        "economic_failures": result["economic_failures"],
        "execution_errors": result["execution_errors"],
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
