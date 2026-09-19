from __future__ import annotations

"""Third-generation identity-free C25EG08 effort-policy distillation.

v1 proved that one monotone (raw_size, level1_ratio) rule is too weak. v2 proved that even two
rectangular regions in that same two-dimensional space cannot clear the immutable office size floors.

v3 expands *features*, not identity.  Every decision may use only cheap properties of the final raw
physical pack that are available to any encoder before final compression:

- raw byte length;
- level-1 compression ratio (already paid by the current final-pack audition);
- Shannon byte entropy;
- zero-byte fraction;
- printable-ASCII fraction.

Pack hashes, paths, filenames, workload labels and benchmark identity are not present in the policy
input rows.  The policy is a max-of-at-most-four simple threshold rules.  Search is dynamic and
selection-vector-deduplicated: rules that make the same pack-level decisions collapse to one state,
so expressiveness can increase without a combinatorial throwaway-archive explosion.

Exact archive bytes are projected from precomputed payload sizes.  Only the lowest modeled-effort
policy that clears every immutable size floor is rebuilt repeatedly through complete creation,
mandatory strong verification and locality accounting.  A green result is still promotion-incomplete:
all-15/adversarial generalization, selector ownership, native/Android parity and strict release
authority remain mandatory.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v2 as V2
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as V5
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EXPECTED_OFFICE_V029 = V1.EXPECTED_OFFICE_V029
ROUNDS = V1.ROUNDS
LEVELS = V1.LEVELS
MAX_RULES = 4

# Fixed, reviewable boundaries.  These are deliberately coarse and have no corpus-specific values.
SIZE_THRESHOLDS = (64 << 10, 128 << 10, 256 << 10, 384 << 10, 512 << 10, 1 << 20, 2 << 20)
RATIO_THRESHOLDS = (0.45, 0.60, 0.72, 0.82, 0.90, 0.97)
ENTROPY_THRESHOLDS = (4.0, 5.0, 6.0, 6.5, 7.0, 7.5, 7.8)
ZERO_THRESHOLDS = (0.001, 0.01, 0.05, 0.10, 0.25, 0.50)
PRINTABLE_THRESHOLDS = (0.25, 0.50, 0.70, 0.85, 0.95)


def _entropy(raw: bytes) -> float:
    if not raw:
        return 0.0
    n = len(raw)
    counts = Counter(raw)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def _pack_features(raws: list[bytes]) -> list[dict]:
    """Return policy-visible features only; content identity is intentionally absent."""
    rows: list[dict] = []
    for index, raw in enumerate(raws):
        n = max(1, len(raw))
        level1 = V25.zc(raw, 1)
        printable = sum(1 for value in raw if value in (9, 10, 13) or 32 <= value <= 126)
        rows.append(
            {
                "index": int(index),
                "raw_bytes": int(len(raw)),
                "level1_ratio": float(len(level1) / n),
                "entropy_bits_per_byte": float(_entropy(raw)),
                "zero_fraction": float(raw.count(0) / n),
                "printable_fraction": float(printable / n),
            }
        )
    return rows


def _atomic_rules() -> list[dict]:
    predicates: list[tuple[str, str, tuple[float | int, ...]]] = [
        ("raw_bytes", ">=", SIZE_THRESHOLDS),
        ("level1_ratio", "<=", RATIO_THRESHOLDS),
        ("entropy_bits_per_byte", "<=", ENTROPY_THRESHOLDS),
        ("zero_fraction", ">=", ZERO_THRESHOLDS),
        ("printable_fraction", ">=", PRINTABLE_THRESHOLDS),
    ]
    rules: list[dict] = []
    for feature, operator, thresholds in predicates:
        for threshold in thresholds:
            for level in LEVELS[1:]:
                rules.append(
                    {
                        "feature": feature,
                        "operator": operator,
                        "threshold": threshold,
                        "level": int(level),
                    }
                )
    return rules


def _matches(row: dict, rule: dict) -> bool:
    value = float(row[rule["feature"]])
    threshold = float(rule["threshold"])
    if rule["operator"] == "<=":
        return value <= threshold
    if rule["operator"] == ">=":
        return value >= threshold
    raise ValueError(f"unsupported policy operator: {rule['operator']!r}")


def _selection_vector(features: list[dict], rules: list[dict]) -> tuple[int, ...]:
    result: list[int] = []
    for row in features:
        level = 1
        for rule in rules:
            if _matches(row, rule):
                level = max(level, int(rule["level"]))
        result.append(level)
    return tuple(result)


def _selection_dict(vector: tuple[int, ...]) -> dict[int, int]:
    return {index: int(level) for index, level in enumerate(vector)}


def _rule_cost(rules: list[dict], vector: tuple[int, ...]) -> tuple:
    selected = [level for level in vector if level != 1]
    return (
        len(selected),
        sum(level - 1 for level in selected),
        max(selected, default=1),
        len(rules),
        tuple((r["feature"], r["operator"], float(r["threshold"]), int(r["level"])) for r in rules),
    )


def _deduplicated_atomic_states(features: list[dict]) -> list[tuple[tuple[int, ...], dict]]:
    best: dict[tuple[int, ...], dict] = {}
    for rule in _atomic_rules():
        vector = _selection_vector(features, [rule])
        if all(level == 1 for level in vector):
            continue
        current = best.get(vector)
        if current is None or _rule_cost([rule], vector) < _rule_cost([current], vector):
            best[vector] = rule
    return [(vector, rule) for vector, rule in best.items()]


def _payload_table(raws: list[bytes]) -> list[dict[int, int]]:
    table: list[dict[int, int]] = []
    for raw in raws:
        row: dict[int, int] = {}
        for level in LEVELS:
            compressed = V25.zc(raw, int(level))
            row[int(level)] = len(compressed) if len(compressed) + 8 < len(raw) else len(raw)
        table.append(row)
    return table


def _exact_archive_bytes(meta_comp: bytes, payload_table: list[dict[int, int]], vector: tuple[int, ...]) -> int:
    return (
        EG08.HDR.size
        + len(meta_comp)
        + sum(EG08.PH.size + payload_table[index][int(vector[index])] for index in range(len(payload_table)))
        + len(meta_comp)
        + EG08.FTR.size
    )


def _search(features: list[dict], meta_comp: bytes, payload_table: list[dict[int, int]], size_ceiling: int) -> tuple[list[dict] | None, tuple[int, ...] | None, int | None, dict]:
    """Dynamic max-rule search, deduplicated by exact pack-level selection vector."""
    atomic = _deduplicated_atomic_states(features)
    baseline = tuple(1 for _ in features)
    states: dict[tuple[int, ...], list[dict]] = {baseline: []}
    clearing: list[tuple[tuple, int, list[dict], tuple[int, ...]]] = []
    state_counts: list[int] = [1]

    for depth in range(1, MAX_RULES + 1):
        next_states: dict[tuple[int, ...], list[dict]] = dict(states)
        for base_vector, base_rules in states.items():
            if len(base_rules) >= depth:
                continue
            for atomic_vector, rule in atomic:
                vector = tuple(max(a, b) for a, b in zip(base_vector, atomic_vector))
                if vector == base_vector:
                    continue
                rules = base_rules + [rule]
                existing = next_states.get(vector)
                if existing is None or _rule_cost(rules, vector) < _rule_cost(existing, vector):
                    next_states[vector] = rules
        states = next_states
        state_counts.append(len(states))
        for vector, rules in states.items():
            if not rules or len(rules) > depth:
                continue
            archive_bytes = _exact_archive_bytes(meta_comp, payload_table, vector)
            if archive_bytes < size_ceiling:
                clearing.append((_rule_cost(rules, vector), archive_bytes, rules, vector))
        if clearing:
            break

    if not clearing:
        return None, None, None, {"deduplicated_atomic_rules": len(atomic), "state_counts_by_depth": state_counts, "clearing_states": 0}
    clearing.sort(key=lambda item: (item[0], item[1]))
    _cost, archive_bytes, rules, vector = clearing[0]
    return rules, vector, int(archive_bytes), {
        "deduplicated_atomic_rules": len(atomic),
        "state_counts_by_depth": state_counts,
        "clearing_states": len(clearing),
    }


def _candidate_once(stage: Path, root: Path, rules: list[dict]) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    raw_eg07, graph_s = V5._tmpfs_capture_raw_final_eg07(stage, root / "capture")
    _meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
    features = _pack_features(raws)
    vector = _selection_vector(features, rules)
    output = root / "policy-v3.c25eg08"
    emitted = V1._emit(raw_eg07, output, _selection_dict(vector))
    verified = EG08.strong_verify(output, expected_tree=EG07._treehash(stage))
    locality = EG08.locality_report(output)
    elapsed = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError("distilled EG08 v3 policy failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("distilled EG08 v3 policy exceeded frozen locality/decode bounds")
    return {
        "archive_bytes": int(emitted["archive_bytes"]),
        "archive_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "verified_create_s": float(elapsed),
        "graph_s": float(graph_s),
        "emit_s": float(emitted["emit_s"]),
        "selected_high_effort_packs": int(emitted["selected_high_effort_packs"]),
        "selected_levels": list(vector),
        "locality": locality,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg08-policy-v3-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")
        raw_eg07, _ = V5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = V4._raw_eg07_parts(raw_eg07)
        features = _pack_features(raws)
        payload_table = _payload_table(raws)
        size_ceiling = min(
            int(accepted_v029),
            int(comparators["zip"]["archive_bytes"]),
            int(comparators["zstd19"]["archive_bytes"]),
        )
        rules, projected_vector, projected_bytes, search = _search(features, meta_comp, payload_table, size_ceiling)

        if rules is None or projected_vector is None or projected_bytes is None:
            return {
                "schema": "cmpct-v030-eg08-policy-distillation-v3",
                "candidate": "C25EG08",
                "accepted_v029_bytes": int(accepted_v029),
                "policy_inputs": ["raw_bytes", "level1_ratio", "entropy_bits_per_byte", "zero_fraction", "printable_fraction"],
                "forbidden_policy_inputs": ["sha256", "path", "filename", "workload_label", "benchmark_name"],
                "predecessor_single_rule_family_falsified": True,
                "predecessor_two_region_family_falsified": True,
                "search_family": {"max_rules": MAX_RULES, **search},
                "comparators": comparators,
                "strict": {"passed": False},
                "claim_boundary": "Negative evidence: bounded identity-free feature rules still cannot clear the office size floors.",
            }

        samples: list[float] = []
        sizes: set[int] = set()
        shas: set[str] = set()
        vectors: set[tuple[int, ...]] = set()
        last = None
        for round_index in range(ROUNDS):
            measured = _candidate_once(stage, root / f"measure-{round_index}", rules)
            samples.append(float(measured["verified_create_s"]))
            sizes.add(int(measured["archive_bytes"]))
            shas.add(str(measured["archive_sha256"]))
            vectors.add(tuple(int(x) for x in measured["selected_levels"]))
            last = measured
        if len(sizes) != 1 or len(shas) != 1 or len(vectors) != 1:
            raise RuntimeError("distilled EG08 v3 policy is nondeterministic")
        candidate_bytes = next(iter(sizes))
        vector = next(iter(vectors))
        if candidate_bytes != projected_bytes:
            raise RuntimeError(f"exact size projection drift: projected={projected_bytes}, measured={candidate_bytes}")
        if vector != projected_vector:
            raise RuntimeError("policy selection drift between search and measurement")
        assert last is not None
        candidate_median = statistics.median(samples)
        strict = {
            "beats_accepted_v029_size": candidate_bytes < accepted_v029,
            "beats_zip_size": candidate_bytes < comparators["zip"]["archive_bytes"],
            "beats_zstd19_size": candidate_bytes < comparators["zstd19"]["archive_bytes"],
            "verified_create_beats_zip": candidate_median < comparators["zip"]["median_create_s"],
            "verified_create_beats_zstd19": candidate_median < comparators["zstd19"]["median_create_s"],
            "within_release_locality_bounds": bool(last["locality"]["within_release_bounds"]),
            "content_identity_not_policy_input": True,
            "exact_size_projection": candidate_bytes == projected_bytes,
            "rule_count_within_bound": len(rules) <= MAX_RULES,
        }
        strict["passed"] = all(strict.values())

    return {
        "schema": "cmpct-v030-eg08-policy-distillation-v3",
        "candidate": "C25EG08",
        "accepted_v029_bytes": int(accepted_v029),
        "policy_inputs": ["raw_bytes", "level1_ratio", "entropy_bits_per_byte", "zero_fraction", "printable_fraction"],
        "forbidden_policy_inputs": ["sha256", "path", "filename", "workload_label", "benchmark_name"],
        "predecessor_single_rule_family_falsified": True,
        "predecessor_two_region_family_falsified": True,
        "selected_policy": {"rules": rules, "overlap_resolution": "max_level"},
        "search_family": {"max_rules": MAX_RULES, **search},
        "measured_candidate": {
            "archive_bytes": int(candidate_bytes),
            "projected_archive_bytes": int(projected_bytes),
            "archive_sha256": next(iter(shas)),
            "median_verified_create_s": float(candidate_median),
            "raw_verified_create_s": samples,
            "selected_high_effort_packs": int(last["selected_high_effort_packs"]),
            "selected_levels": list(vector),
            "max_member_read_amplification": float(last["locality"]["max_member_read_amplification"]),
            "max_decode_unit_bytes": int(last["locality"]["max_decode_unit_bytes"]),
        },
        "comparators": comparators,
        "strict": strict,
        "claim_boundary": (
            "Research-only third-generation policy distillation. Decisions use only cheap pack statistics and at "
            "most four simple threshold rules. Frozen content identity is forbidden. All-15/adversarial "
            "generalization, production selector ownership, native/Android parity and strict release authority "
            "remain mandatory before promotion."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v3-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v3.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"selected_policy": result.get("selected_policy"), "measured_candidate": result.get("measured_candidate"), "comparators": result.get("comparators"), "strict": result["strict"]}, indent=2), flush=True)
    if not result["strict"]["passed"]:
        raise SystemExit("C25EG08 identity-free feature policy distillation failed")


if __name__ == "__main__":
    main()
