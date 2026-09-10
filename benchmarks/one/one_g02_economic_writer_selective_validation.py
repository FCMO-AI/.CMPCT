from __future__ import annotations

"""Selective-read companion falsifier for ONE-G0.2 economic writer admission.

Uses only transfer inputs from the writer-admission preregistration. It does not inspect or
execute Genesis workloads or frozen comparators.
"""

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from typing import Any

from benchmarks.one.one_g02_economic_writer_admission import _write_pair
from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import build_general_law_archive

OUT = Path("one-g02-economic-writer-selective-validation.json")
CASES = (
    ("add8", 8),      # economically rejected -> Surprise
    ("add8", 11),     # break-even -> retained Law
    ("xor", 32),      # profitable retained Law
    ("xor", 4096),    # multi-page-ish retained Law boundary
)


def _probe(root: Path, *, economic: bool, relation: str, length: int) -> dict[str, Any]:
    wire, _stats = build_general_law_archive(root, economic_admission=economic)
    opened = open_authenticated_archive(wire)
    target_path = "01-target.bin"
    target = (root / target_path).read_bytes()
    if length <= 8:
        start, take = 2, 4
    elif length <= 32:
        start, take = length // 3, min(7, length - length // 3)
    else:
        # Cross the 4 KiB auth-leaf boundary when possible; 4096 itself cannot cross, so
        # exercise a tail range near the boundary instead.
        start, take = max(0, length - 17), min(17, length)
    value, stats = opened.read_range(target_path, start, take)
    entry = opened.base.entries[target_path]
    root_obj = opened.program.roots[entry["root"]]
    op = opened.program.nodes[root_obj.ref.node].op
    return {
        "economic_admission": economic,
        "relation": relation,
        "length": length,
        "start": start,
        "requested": take,
        "target_op": op,
        "exact": value == target[start : start + take],
        "stats": asdict(stats),
        "fallback": stats.fallback,
        "movement_bytes": stats.modeled_data_movement_bytes,
        "peak_temporary_bytes": stats.peak_temporary_bytes,
    }


def run() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="one-g02-economic-selective-") as td:
        parent = Path(td)
        for relation, length in CASES:
            root = parent / f"{relation}-{length}"
            _write_pair(root, relation, length)
            current = _probe(root, economic=False, relation=relation, length=length)
            economic = _probe(root, economic=True, relation=relation, length=length)
            rows.append({
                "case": f"{relation}-{length}",
                "current": current,
                "economic": economic,
                "exact_both": current["exact"] and economic["exact"],
                "native_both": not current["fallback"] and not economic["fallback"],
                "economic_requested_matches": economic["stats"]["requested_bytes"] == economic["requested"],
            })

    expected_ops = {
        "add8-8": "surprise",
        "add8-11": "add8",
        "xor-32": "xor",
        "xor-4096": "xor",
    }
    structure_ok = all(row["economic"]["target_op"] == expected_ops[row["case"]] for row in rows)
    exact = all(row["exact_both"] for row in rows)
    native = all(row["native_both"] for row in rows)
    stats_ok = all(row["economic_requested_matches"] for row in rows)
    decision = "ADVANCE_ECONOMIC_WRITER_SELECTIVE_ACCESS" if exact and native and stats_ok and structure_ok else "HOLD_ECONOMIC_WRITER_SELECTIVE_ACCESS"
    payload = {
        "schema": "cmpct-one-g02-economic-writer-selective-validation-v1",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "transfer selective-access evidence only; no Genesis inputs/comparators/scoring",
        "rows": rows,
        "structure_ok": structure_ok,
        "selective_exact": exact,
        "native_no_fallback": native,
        "stats_consistent": stats_ok,
        "decision": decision,
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
