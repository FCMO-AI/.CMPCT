from __future__ import annotations

"""Second-generation content-agnostic C25EG08 office effort-policy distillation.

The v1 experiment deliberately searched a single monotone threshold rule over two generic final-pack features:
raw byte length and the already-required level-1 compression ratio. Exact CI falsified that family: no single
rule retained enough compression to cross the immutable office v0.29 size floor.

This v2 experiment preserves that negative evidence and expands only the *shape* of the policy, not its inputs.
A policy contains at most two bounded regions in the same two-dimensional feature space. Each region has a raw
size interval, a maximum level-1 ratio and one reviewed compression level. If both regions match a pack, the
higher effort wins. Pack SHA-256, path, workload/benchmark identity and source filename are never inputs.

The search is exact on archive bytes: compression outputs for each final physical pack and reviewed level are
precomputed once, then the complete C25EG08 framing size is evaluated arithmetically for every rule/pair. Only the
lowest modeled-effort policy that clears all frozen size floors is rebuilt three times through the complete
verified creation boundary. Strict ZIP/Zstd creation-speed wins, locality and deterministic bytes remain mandatory.

A green result is still promotion-incomplete: all-15/adversarial generalization, production selector ownership,
native/Android parity and strict release authority remain mandatory.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as V5
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EXPECTED_OFFICE_V029 = V1.EXPECTED_OFFICE_V029
ROUNDS = V1.ROUNDS
LEVELS = V1.LEVELS
# Reviewable generic feature boundaries.  Zero and None permit whole-range regions; neither encodes corpus identity.
SIZE_EDGES = (0, 64 << 10, 128 << 10, 256 << 10, 384 << 10, 512 << 10, 1 << 20, 2 << 20)
RATIO_THRESHOLDS = V1.RATIO_THRESHOLDS


def _rule_space() -> list[dict]:
    rules: list[dict] = []
    upper_edges: tuple[int | None, ...] = tuple(SIZE_EDGES[1:]) + (None,)
    for lower_i, lower in enumerate(SIZE_EDGES):
        for upper in upper_edges[lower_i:]:
            if upper is not None and upper <= lower:
                continue
            for ratio in RATIO_THRESHOLDS:
                for level in LEVELS[1:]:
                    rules.append(
                        {
                            "min_raw_bytes": int(lower),
                            "max_raw_bytes_exclusive": None if upper is None else int(upper),
                            "max_level1_ratio": float(ratio),
                            "level": int(level),
                        }
                    )
    return rules


def _matches(row: dict, rule: dict) -> bool:
    raw_bytes = int(row["raw_bytes"])
    ratio = float(row["level1_ratio"])
    upper = rule["max_raw_bytes_exclusive"]
    return (
        raw_bytes >= int(rule["min_raw_bytes"])
        and (upper is None or raw_bytes < int(upper))
        and ratio <= float(rule["max_level1_ratio"])
    )


def _policy_selection(features: list[dict], rules: list[dict]) -> dict[int, int]:
    """Choose effort using only raw_bytes and level1_ratio."""
    result: dict[int, int] = {}
    for row in features:
        level = 1
        for rule in rules:
            if _matches(row, rule):
                level = max(level, int(rule["level"]))
        result[int(row["index"])] = level
    return result


def _payload_table(raws: list[bytes]) -> list[dict[int, int]]:
    table: list[dict[int, int]] = []
    for raw in raws:
        row: dict[int, int] = {}
        for level in LEVELS:
            compressed = V25.zc(raw, int(level))
            row[int(level)] = len(compressed) if len(compressed) + 8 < len(raw) else len(raw)
        table.append(row)
    return table


def _exact_archive_bytes(meta_comp: bytes, payload_table: list[dict[int, int]], by_index: dict[int, int]) -> int:
    return (
        EG08.HDR.size
        + len(meta_comp)
        + sum(EG08.PH.size + payload_table[index][int(by_index[index])] for index in range(len(payload_table)))
        + len(meta_comp)
        + EG08.FTR.size
    )


def _effort_key(by_index: dict[int, int], archive_bytes: int, rules: list[dict]) -> tuple:
    selected = [level for level in by_index.values() if int(level) != 1]
    # This is a policy-search ordering only, not benchmark credit. Prefer less speculative work first.
    return (
        len(selected),
        sum(int(level) - 1 for level in selected),
        max(selected, default=1),
        len(rules),
        int(archive_bytes),
    )


def _candidate_once(stage: Path, root: Path, rules: list[dict]) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = V5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    _meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
    features = V1._pack_features(raws)
    by_index = _policy_selection(features, rules)
    output = root / "policy-v2.c25eg08"
    emitted = V1._emit(raw_eg07, output, by_index)
    verified = EG08.strong_verify(output, expected_tree=EG07._treehash(stage))
    locality = EG08.locality_report(output)
    elapsed = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("distilled EG08 v2 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("distilled EG08 v2 policy exceeded frozen locality/decode bounds")
    return {
        "archive_bytes": int(emitted["archive_bytes"]),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "verified_create_s": elapsed,
        "graph_s": float(graph_s),
        "emit_s": float(emitted["emit_s"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": [int(by_index[index]) for index in sorted(by_index)],
        "locality": locality,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-policy-v2-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")

        raw_eg07, _ = V5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
        features = V1._pack_features(raws)
        payload_table = _payload_table(raws)
        rules = _rule_space()

        size_ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )

        # Cache every single rule's selection. Pair search then evaluates exact complete framing bytes without
        # repeatedly invoking Zstd or writing throwaway archives.
        rule_selections = [_policy_selection(features, [rule]) for rule in rules]
        candidates: list[tuple[tuple, int, list[dict], dict[int, int]]] = []

        def consider(rule_indices: tuple[int, ...]) -> None:
            chosen_rules = [rules[i] for i in rule_indices]
            if len(rule_indices) == 1:
                by_index = dict(rule_selections[rule_indices[0]])
            else:
                a = rule_selections[rule_indices[0]]
                b = rule_selections[rule_indices[1]]
                by_index = {index: max(int(a[index]), int(b[index])) for index in a}
            archive_bytes = _exact_archive_bytes(meta_comp, payload_table, by_index)
            if archive_bytes < size_ceiling:
                candidates.append((_effort_key(by_index, archive_bytes, chosen_rules), archive_bytes, chosen_rules, by_index))

        for i in range(len(rules)):
            consider((i,))
        for i, j in itertools.combinations(range(len(rules)), 2):
            consider((i, j))

        if not candidates:
            result = {
                "schema": "cmpct-v030-eg08-policy-distillation-v2",
                "candidate": "C25EG08",
                "accepted_v029_bytes": int(accepted_v029),
                "policy_inputs": ["raw_bytes", "level1_ratio"],
                "forbidden_policy_inputs": ["sha256", "path", "workload_label", "benchmark_name"],
                "predecessor_single_rule_family_falsified": True,
                "search_family": {
                    "max_rules": 2,
                    "levels": list(LEVELS),
                    "size_edges": list(SIZE_EDGES),
                    "ratio_thresholds": list(RATIO_THRESHOLDS),
                    "single_rules": len(rules),
                    "two_rule_pairs": len(rules) * (len(rules) - 1) // 2,
                    "candidate_policies_clearing_size_floors": 0,
                },
                "comparators": comparators,
                "strict": {"passed": False},
                "claim_boundary": "Negative evidence: even the bounded two-region generic policy family cannot clear office size floors.",
            }
            return result

        candidates.sort(key=lambda item: item[0])
        _effort, projected_bytes, selected_rules, projected_selection = candidates[0]

        samples: list[float] = []
        sizes: set[int] = set()
        shas: set[str] = set()
        selected_level_vectors: set[tuple[int, ...]] = set()
        last = None
        for round_index in range(ROUNDS):
            measured = _candidate_once(stage, root / f"measure-{round_index}", selected_rules)
            samples.append(float(measured["verified_create_s"]))
            sizes.add(int(measured["archive_bytes"]))
            shas.add(str(measured["archive_sha256"]))
            selected_level_vectors.add(tuple(measured["selected_levels"]))
            last = measured
        if len(sizes) != 1 or len(shas) != 1 or len(selected_level_vectors) != 1:
            raise RuntimeError("distilled EG08 v2 policy is nondeterministic")
        assert last is not None
        candidate_bytes = next(iter(sizes))
        if candidate_bytes != int(projected_bytes):
            raise RuntimeError(f"exact size projection drift: projected={projected_bytes}, measured={candidate_bytes}")
        if tuple(projected_selection[i] for i in sorted(projected_selection)) != next(iter(selected_level_vectors)):
            raise RuntimeError("policy selection drift between search and repeated measurement")

        candidate_median = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": candidate_bytes < accepted_v029,
            "beats_zip_size": candidate_bytes < comparators["zip"]["archive_bytes"],
            "beats_zstd19_size": candidate_bytes < comparators["zstd19"]["archive_bytes"],
            "verified_create_beats_zip": candidate_median < comparators["zip"]["median_create_s"],
            "verified_create_beats_zstd19": candidate_median < comparators["zstd19"]["median_create_s"],
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_hash_not_policy_input": True,
            "exact_size_projection": candidate_bytes == int(projected_bytes),
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-policy-distillation-v2",
        "candidate": "C25EG08",
        "accepted_v029_bytes": int(accepted_v029),
        "policy_inputs": ["raw_bytes", "level1_ratio"],
        "forbidden_policy_inputs": ["sha256", "path", "workload_label", "benchmark_name"],
        "predecessor_single_rule_family_falsified": True,
        "selected_policy": {"rules": selected_rules, "overlap_resolution": "max_level"},
        "search_family": {
            "max_rules": 2,
            "levels": list(LEVELS),
            "size_edges": list(SIZE_EDGES),
            "ratio_thresholds": list(RATIO_THRESHOLDS),
            "single_rules": len(rules),
            "two_rule_pairs": len(rules) * (len(rules) - 1) // 2,
            "candidate_policies_clearing_size_floors": len(candidates),
        },
        "measured_candidate": {
            "archive_bytes": int(candidate_bytes),
            "projected_archive_bytes": int(projected_bytes),
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": float(candidate_median),
            "raw_verified_create_s": samples,
            "selected_high_effort_packs": int(last["selected_high_effort_packs"]),
            "selected_levels": list(next(iter(selected_level_vectors))),
            "max_member_read_amplification": float(last["locality"]["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(last["locality"]["max_decode_unit_bytes"]),
        },
        "comparators": comparators,
        "strict": strict,
        "claim_boundary": (
            "Research-only second-generation policy distillation. The v1 single-threshold family is retained as "
            "negative evidence. v2 permits at most two generic regions over raw_bytes and level1_ratio; it still "
            "cannot use pack/content identity. All-15/adversarial generalization, selector ownership, native/Android "
            "parity and strict release authority remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v2.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_policy": result.get("selected_policy"), "measured_candidate": result.get("measured_candidate"), "comparators": result.get("comparators"), "strict": result["strict"]}, indent=2), flush=True)
    if not result["strict"]["passed"]:
        raise SystemExit("C25EG08 two-region content-agnostic policy distillation failed")


if __name__ == "__main__":
    main()
