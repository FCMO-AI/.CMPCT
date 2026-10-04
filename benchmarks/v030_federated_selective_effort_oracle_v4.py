from __future__ import annotations

"""Schema-correct selective-effort frontier for the repaired accepted-v0.29 baseline.

v3 correctly expanded the final-pack effort search through Zstd levels 20-22, but its inherited v1 runner still
looked for ``archive_bytes`` in ``v030_release_generalization._accepted_v029_rows()``.  The authoritative repaired
baseline intentionally names that field ``accepted_v029_bytes``.  This front door adapts only that evidence schema
boundary, preserving the exact frozen byte values and every v3 timing/locality/comparator rule.

No benchmark threshold, compressor setting, candidate default, selector rule, locality budget, or release policy
is changed.  The adapter exists solely so the expensive experiment reaches measurement instead of crashing before
profiling.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_federated_selective_effort_oracle as V1
from benchmarks import v030_federated_selective_effort_oracle_v3 as V3

# Capture the authoritative loader exactly once, before the compatibility shim is installed.  The prior v4
# implementation called ``V1.GENERAL._accepted_v029_rows`` from inside the replacement itself; because GENERAL is
# the same module object, that name already pointed back at the replacement and recursed until Python aborted.
# Keeping this immutable function reference also makes the evidence provenance explicit: the shim can only add the
# legacy field alias to rows returned by the original authoritative loader.
_AUTHORITATIVE_ACCEPTED_ROWS = V1.GENERAL._accepted_v029_rows


def _accepted_rows_with_legacy_alias() -> dict:
    rows = _AUTHORITATIVE_ACCEPTED_ROWS()
    adapted = {}
    accepted_total = 0
    for key, source in rows.items():
        row = dict(source)
        if "accepted_v029_bytes" not in row:
            raise RuntimeError(f"authoritative accepted-v0.29 row lacks accepted_v029_bytes: {key!r}")
        accepted = int(row["accepted_v029_bytes"])
        if "archive_bytes" in row and int(row["archive_bytes"]) != accepted:
            raise RuntimeError(f"conflicting accepted-v0.29 byte aliases for {key!r}")
        row["archive_bytes"] = accepted
        adapted[key] = row
        accepted_total += accepted
    if len(adapted) != 15:
        raise RuntimeError(f"accepted-v0.29 workload count drifted: {len(adapted)} != 15")
    if accepted_total != 137_499_525:
        raise RuntimeError(
            f"accepted-v0.29 aggregate drifted: {accepted_total} != 137499525"
        )
    return adapted


def run(work_root: Path) -> dict:
    before = V1.GENERAL._accepted_v029_rows
    V1.GENERAL._accepted_v029_rows = _accepted_rows_with_legacy_alias
    try:
        result = dict(V3.run(work_root))
    finally:
        V1.GENERAL._accepted_v029_rows = before
    result["schema"] = "cmpct-v030-federated-selective-effort-v4"
    result["accepted_v029_schema_adapter"] = {
        "source_field": "accepted_v029_bytes",
        "compatibility_alias": "archive_bytes",
        "values_unchanged": True,
        "workloads": 15,
        "accepted_v029_aggregate_bytes": 137_499_525,
        "authoritative_loader_restored": V1.GENERAL._accepted_v029_rows is before,
    }
    result["claim_boundary"] = (
        "research-only C25EG01 final-pack effort frontier using the authoritative accepted_v029_bytes values. "
        "The archive_bytes alias exists only inside this experiment for compatibility with the inherited v1 "
        "runner. No baseline byte, threshold, compressor setting, selector, locality rule, native/Android rule, "
        "or release authority is changed."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg01-selective.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("federated selective-effort v4 measurement invalid")


if __name__ == "__main__":
    main()
