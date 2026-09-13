from __future__ import annotations

"""Genesis15 transfer referee for locality-derived r24 micro-packing.

Research-only. Does not rerun/rescore frozen ONE/v0.29/v0.30 contenders.
When full regeneration drifts, exact-matching frozen rows may still be measured as a
sealed diagnostic subset, but the full Genesis15 experiment remains invalid.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import neutral_hostile_corpus_v1 as NEUTRAL
from benchmarks import resemblance_hostile_corpus_v1 as RESEMBLANCE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME

EXPECTED = {
    ("neutral_hostile_v1", "01_developer_repository"): (1266, 2624373, "d1706c497de75764b6bd0f49c5d8bdde251694eea40fc683dcbbfed5027c2f49"),
    ("neutral_hostile_v1", "02_office_workspace"): (20, 16063798, "aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57"),
    ("neutral_hostile_v1", "03_media_library"): (28, 28841872, "d821e6c6760279820b9c3a5c14ffccc4f6fc7ac4f6e7a59ff3e81c90a26290ca"),
    ("neutral_hostile_v1", "04_analytics_and_database"): (5, 31265767, "6d0854fe058a95258588b89dca653ac8f00c61f815c6127b179e86cc58b1789d"),
    ("neutral_hostile_v1", "05_logs_and_telemetry"): (11, 16994250, "7356b866d7b99bfce2dd1fc6ef86d61d09c9d8a38a2ff3fec7d9a92e46020931"),
    ("neutral_hostile_v1", "06_incremental_backups"): (769, 14006619, "a823728d98e5882542645e3ab0f777894479cfb3de4dedcec14341fedbb11a05"),
    ("neutral_hostile_v1", "07_incompressible_and_encrypted_like"): (1425, 10182899, "da4f37ac1d7a6751c4adcaabb50cc2cd6f2ffbed7bd2100d34b9ef597f7d1d80"),
    ("neutral_hostile_v1", "08_many_tiny_files"): (5000, 736546, "a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f"),
    ("neutral_hostile_v1", "09_ml_artifacts"): (4, 18172774, "efc09910fea8ef67d24cd8957d3d576df3a7cc7f10f14585e3a3ae269017901d"),
    ("neutral_hostile_v1", "10_large_mixed_binary"): (1, 33554432, "9373f96626c7f463b4112bf138ac5db766e7e71def9b209c7ba28fe44f0878d3"),
    ("resemblance_hostile_v1", "01_shifted_versions"): (18, 33525242, "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd"),
    ("resemblance_hostile_v1", "02_false_neighbors"): (600, 39524435, "3427fd306a10a7c293d4303323d64948ee74d4065353bf99310cfed34dc73d0e"),
    ("resemblance_hostile_v1", "03_boundary_churn"): (12, 9744144, "3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d"),
    ("resemblance_hostile_v1", "04_deflate_family"): (14, 126270, "527a9e356e923e5bcc26566a8f677a7f7277af1577493e09c2bdca1b6d17154a"),
    ("resemblance_hostile_v1", "05_incompressible"): (80, 10606293, "1efe49fb1adb16ef911f64f44d41629db599dbeef264d72fd8f26e40515130e4"),
}
EXPECTED_LOGICAL = 265_969_714


def _seal_rows(root: Path) -> tuple[dict[tuple[str, str], Path], list[dict]]:
    neutral_root = root / "neutral"
    resemblance_root = root / "resemblance"
    neutral = NEUTRAL.build(neutral_root)
    resemblance = RESEMBLANCE.build(resemblance_root)
    rows = []
    paths: dict[tuple[str, str], Path] = {}
    for suite, manifest, parent, key in (
        ("neutral_hostile_v1", neutral, neutral_root, "corpora"),
        ("resemblance_hostile_v1", resemblance, resemblance_root, "workloads"),
    ):
        for row in manifest[key]:
            name = row["name"]
            identity = (suite, name)
            expected = EXPECTED.get(identity)
            actual = (int(row["files"]), int(row["logical_bytes"]), str(row["tree_sha256"]))
            rows.append({
                "suite": suite,
                "name": name,
                "files": actual[0],
                "logical_bytes": actual[1],
                "tree_sha256": actual[2],
                "expected": None if expected is None else {
                    "files": expected[0], "logical_bytes": expected[1], "tree_sha256": expected[2]
                },
                "match": expected == actual,
            })
            paths[identity] = parent / name
    return paths, rows


def _summarize(rows: dict[str, dict]) -> dict:
    if not rows:
        return {
            "same_grammar_independent_bytes": 0,
            "same_grammar_derived_bytes": 0,
            "delta_bytes": 0,
            "delta_pct": 0.0,
            "grouped_wins": 0,
            "zero_group_ties": 0,
            "economic_failures": 0,
            "invariant_failures": 0,
            "max_member_amplification": 0.0,
            "max_decode_unit_bytes": 0,
            "independent_build_cpu_s_sum": 0.0,
            "derived_build_cpu_s_sum": 0.0,
            "independent_build_wall_s_sum": 0.0,
            "derived_build_wall_s_sum": 0.0,
        }
    independent_total = sum(int(r["same_grammar_independent_bytes"]) for r in rows.values())
    derived_total = sum(int(r["same_grammar_derived_bytes"]) for r in rows.values())
    delta = derived_total - independent_total
    return {
        "same_grammar_independent_bytes": independent_total,
        "same_grammar_derived_bytes": derived_total,
        "delta_bytes": delta,
        "delta_pct": (delta / independent_total * 100.0) if independent_total else 0.0,
        "grouped_wins": sum(1 for r in rows.values() if r["derived_group_count"] > 0 and r["same_grammar_delta_bytes"] < 0),
        "zero_group_ties": sum(1 for r in rows.values() if r["derived_group_count"] == 0 and r["same_grammar_delta_bytes"] == 0),
        "economic_failures": sum(1 for r in rows.values() if not r["economic_pass"]),
        "invariant_failures": sum(1 for r in rows.values() if not r["invariants_pass"]),
        "max_member_amplification": max(float(r["max_member_amplification"]) for r in rows.values()),
        "max_decode_unit_bytes": max(int(r["max_decode_unit_bytes"]) for r in rows.values()),
        "independent_build_cpu_s_sum": sum(float(r["independent_build_cpu_s"]) for r in rows.values()),
        "derived_build_cpu_s_sum": sum(float(r["derived_build_cpu_s"]) for r in rows.values()),
        "independent_build_wall_s_sum": sum(float(r["independent_build_wall_s"]) for r in rows.values()),
        "derived_build_wall_s_sum": sum(float(r["derived_build_wall_s"]) for r in rows.values()),
    }


def _measure(paths: dict[tuple[str, str], Path], identities: list[tuple[str, str]], work_root: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for suite, name in identities:
        key = f"{suite}/{name}"
        rows[key] = SAME._one(paths[(suite, name)], work_root / suite / name)
    return rows


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    paths, seal = _seal_rows(work_root / "corpus")
    seal_keys = {(r["suite"], r["name"]) for r in seal}
    matching = [(r["suite"], r["name"]) for r in seal if r["match"] and (r["suite"], r["name"]) in EXPECTED]
    mismatching = [(r["suite"], r["name"]) for r in seal if not r["match"] or (r["suite"], r["name"]) not in EXPECTED]
    exact_seal = (
        seal_keys == set(EXPECTED)
        and len(seal) == 15
        and len(matching) == 15
        and sum(r["logical_bytes"] for r in seal) == EXPECTED_LOGICAL
    )

    if not exact_seal:
        sealed_rows = _measure(paths, matching, work_root / "sealed-subset-work")
        return {
            "schema": "cmpct-v030-r24-micropack-genesis15-transfer-v1",
            "experiment_valid": False,
            "release_credit": False,
            "canonical_builder_changed": False,
            "corpus_seal_pass": False,
            "seal": seal,
            "matching_identities": [f"{s}/{n}" for s, n in matching],
            "mismatching_identities": [f"{s}/{n}" for s, n in mismatching],
            "sealed_subset_rows": sealed_rows,
            "sealed_subset_aggregate": _summarize(sealed_rows),
            "verdict": "INVALID_GENESIS15_INPUT_SEAL",
        }

    rows = _measure(paths, list(EXPECTED), work_root / "work")
    invariant_failures = [k for k, r in rows.items() if not r["invariants_pass"]]
    economic_failures = [k for k, r in rows.items() if not r["economic_pass"]]
    grouped_wins = [k for k, r in rows.items() if r["derived_group_count"] > 0 and r["same_grammar_delta_bytes"] < 0]
    zero_group_ties = [k for k, r in rows.items() if r["derived_group_count"] == 0 and r["same_grammar_delta_bytes"] == 0]
    aggregate = _summarize(rows)

    if invariant_failures:
        verdict = "RETIRE_GENESIS15_MICROPACK_TRANSFER"
    elif economic_failures or aggregate["delta_bytes"] >= 0:
        verdict = "GENESIS15_MICROPACK_NEEDS_ECONOMIC_ADMISSION"
    else:
        verdict = "GENESIS15_MICROPACK_GENERALIZES"

    return {
        "schema": "cmpct-v030-r24-micropack-genesis15-transfer-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "corpus_seal_pass": True,
        "expected_logical_bytes": EXPECTED_LOGICAL,
        "rows": rows,
        "aggregate": aggregate,
        "invariant_failures": invariant_failures,
        "economic_failures": economic_failures,
        "grouped_wins": grouped_wins,
        "zero_group_ties": zero_group_ties,
        "seal": seal,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-genesis15-micropack-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-genesis15-micropack.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "experiment_valid": result["experiment_valid"],
        "verdict": result["verdict"],
        "aggregate": result.get("aggregate"),
        "sealed_subset_aggregate": result.get("sealed_subset_aggregate"),
        "mismatching_identities": result.get("mismatching_identities", []),
        "economic_failures": result.get("economic_failures", []),
    }, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
