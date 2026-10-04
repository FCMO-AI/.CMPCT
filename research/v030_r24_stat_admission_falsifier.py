from __future__ import annotations
"""Retrospective research-only falsifier for simple exact-r24-stat terminal r25 admission.

No product/release credit. The instrument asks whether cheap facts already available
from exact r24 can safely reject full shared-r25 search without workload identity,
timing, tree hashes, or post-r25 facts.
"""
import argparse
import itertools
import json
from pathlib import Path

FEATURES = (
    "files",
    "logical_bytes",
    "average_regular_bytes",
    "r24_product_bytes",
    "r24_archive_to_logical",
)

def _preserved_source_facts(root: Path) -> dict[tuple[str, str], dict]:
    historical = json.loads(
        (root / "benchmarks/history/2026-08-16-entropygraph-v028.json").read_text()
    )
    repair = json.loads(
        (root / "benchmarks/history/2026-08-19-neutral-hostile-determinism-repair-v6.json").read_text()
    )
    rows = {
        (row["suite"], row["name"]): {
            "files": int(row["files"]),
            "logical_bytes": int(row["logical_bytes"]),
        }
        for row in historical["rows"]
    }
    for row in repair["rows"]:
        rows[("neutral_hostile_v1", row["name"])] = {
            "files": int(row["files"]),
            "logical_bytes": int(row["logical_bytes"]),
        }
    return rows

def _rows(root: Path, external: dict) -> list[dict]:
    facts = _preserved_source_facts(root)
    out = []
    for row in external["rows"]:
        cp = row["formats"]["cmpct_v030"].get("candidate_profile") or {}
        if cp.get("g04_shared_candidate_build_s") is None:
            continue
        suite, name = row["label"].split("/", 1)
        source = facts[(suite, name)]
        logical = source["logical_bytes"]
        files = source["files"]
        selected = row["formats"]["cmpct_v030"]["selected"]
        out.append(
            {
                "suite": suite,
                "name": name,
                "files": files,
                "logical_bytes": logical,
                "average_regular_bytes": logical / files,
                "r24_product_bytes": int(cp["r24_product_bytes"]),
                "r24_archive_to_logical": int(cp["r24_product_bytes"]) / logical,
                "r25_winner": selected != "r24-fallback",
            }
        )
    return out

def _stumps(rows: list[dict]):
    out = []
    for feature in FEATURES:
        values = sorted({float(row[feature]) for row in rows})
        cuts = [
            values[0] - 1e-12,
            *[(a + b) / 2 for a, b in zip(values, values[1:])],
            values[-1] + 1e-12,
        ]
        for threshold in cuts:
            out.extend(((feature, "<=", threshold), (feature, ">=", threshold)))
    return out

def _predict(row: dict, rule) -> bool:
    return all(
        float(row[feature]) <= threshold
        if op == "<="
        else float(row[feature]) >= threshold
        for feature, op, threshold in rule
    )

def _best(rows: list[dict], max_terms: int):
    stumps = _stumps(rows)
    best = None
    for terms in range(1, max_terms + 1):
        for rule in itertools.combinations(stumps, terms):
            if any(row["r25_winner"] and not _predict(row, rule) for row in rows):
                continue
            false_admits = sum(
                (not row["r25_winner"]) and _predict(row, rule) for row in rows
            )
            key = (
                false_admits,
                len(rule),
                tuple((f, op, round(t, 12)) for f, op, t in rule),
            )
            if best is None or key < best[0]:
                best = (key, rule)
    if best is None:
        raise RuntimeError("no zero-training-false-reject rule")
    return best[1]

def _court(rows: list[dict], max_terms: int) -> dict:
    full = _best(rows, max_terms)
    leave_one_out = []
    for index, held in enumerate(rows):
        rule = _best(rows[:index] + rows[index + 1 :], max_terms)
        admit = _predict(held, rule)
        leave_one_out.append(
            {
                "held_out": f'{held["suite"]}/{held["name"]}',
                "winner": held["r25_winner"],
                "admit": admit,
                "correct": admit == held["r25_winner"],
                "rule": [list(x) for x in rule],
            }
        )
    winners = [row for row in leave_one_out if row["winner"]]
    return {
        "max_terms": max_terms,
        "full_fit_rule": [list(x) for x in full],
        "full_fit_false_admits": sum(
            (not row["r25_winner"]) and _predict(row, full) for row in rows
        ),
        "loocv_accuracy": sum(row["correct"] for row in leave_one_out)
        / len(leave_one_out),
        "loocv_winner_recall": sum(row["admit"] for row in winners)
        / max(1, len(winners)),
        "loocv_winner_false_rejects": [
            row["held_out"] for row in winners if not row["admit"]
        ],
        "leave_one_out": leave_one_out,
    }

def run(repo_root: Path, external_json: Path) -> dict:
    external = json.loads(external_json.read_text())
    rows = _rows(repo_root, external)
    sweep = [_court(rows, max_terms) for max_terms in (1, 2, 3)]
    unsafe = any(court["loocv_winner_false_rejects"] for court in sweep)
    return {
        "schema": "cmpct-v030-r24-stat-terminal-admission-falsifier-v1",
        "prediction_status": "RETROSPECTIVE__NO_PREREGISTRATION_CREDIT",
        "candidate_fingerprint": external.get("candidate_fingerprint"),
        "feature_policy": {
            "features": list(FEATURES),
            "excludes": [
                "workload identity",
                "tree hash",
                "timing",
                "post-r25 facts",
            ],
        },
        "rows": rows,
        "complexity_sweep": sweep,
        "decision": (
            "RETIRE_LOW_COMPLEXITY_R24_STAT_TERMINAL_REJECTION"
            if unsafe
            else "HEADROOM__REQUIRES_INDEPENDENT_HELD_OUT_CONFIRMATION"
        ),
        "product_credit": False,
        "release_credit": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--external-json", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.repo_root, args.external_json)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload)
    print(payload, end="")

if __name__ == "__main__":
    main()
