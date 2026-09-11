"""Fail-closed checker for the frozen ONE-G0.2 native shared-auth family transfer.

The C profiler deliberately emits primitive measured rows. This checker is the authoritative
result layer: it corrects the descriptor-tree persisted-byte accounting to charge ALL ten
non-root hashes of the fixed V=8 q4 tree (8 leaves + 2 level-1 parents), then enforces every
frozen gate. No timing/corpus/threshold is changed here.
"""
from __future__ import annotations

import json
import pathlib
import sys

Q4_NONROOT_HASH_BYTES = 10 * 32
C_PROFILER_CHARGED_Q4_BYTES = 2 * 32
CORRECTION_BYTES = Q4_NONROOT_HASH_BYTES - C_PROFILER_CHARGED_Q4_BYTES
MAX_BUILD_RATIO = 0.20
MAX_READ_RATIO = 1.20


def main(path: str) -> int:
    raw = json.loads(pathlib.Path(path).read_text())
    rows = []
    for r in raw["rows"]:
        r = dict(r)
        r["raw_shared_persisted_bytes"] = r["shared_persisted_bytes"]
        r["shared_persisted_bytes"] += CORRECTION_BYTES
        r["persisted_ratio"] = r["shared_persisted_bytes"] / r["independent_persisted_bytes"]
        rows.append(r)
    exact_ok = raw.get("exact_failures") == 0
    corruption_ok = raw.get("corruption_failures") == 0
    persisted_ok = all(r["shared_persisted_bytes"] < r["independent_persisted_bytes"] for r in rows)
    build_ok = all(r["build_ratio"] <= MAX_BUILD_RATIO for r in rows)
    read_ok = all(r["read_ratio"] <= MAX_READ_RATIO for r in rows)
    passed = exact_ok and corruption_ok and persisted_ok and build_ok and read_ok
    out = {
        "schema": "cmpct-one-g02-native-shared-auth-family-checked-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": raw.get("source_sha", "workflow-bound-by-checkout"),
        "descriptor_q4_nonroot_hash_bytes": Q4_NONROOT_HASH_BYTES,
        "prototype_accounting_correction_bytes": CORRECTION_BYTES,
        "frozen_gate": {
            "max_build_ratio": MAX_BUILD_RATIO,
            "max_read_ratio": MAX_READ_RATIO,
            "persisted_strictly_lower_each_family": True,
            "exact_and_corruption_rejection": True,
        },
        "exact_failures": raw.get("exact_failures"),
        "corruption_failures": raw.get("corruption_failures"),
        "max_persisted_ratio": max(r["persisted_ratio"] for r in rows),
        "max_build_ratio": max(r["build_ratio"] for r in rows),
        "max_read_ratio": max(r["read_ratio"] for r in rows),
        "decision": "advance_native_shared_auth_family" if passed else "native_shared_auth_family_debt",
        "claim_boundary": raw.get("claim_boundary"),
        "rows": rows,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
