from __future__ import annotations

"""Full-frontier generic C25EG08 office policy search.

The v3/v4 policy family proved that content identity is unnecessary: a one-rule policy
(``raw_bytes >= 64 KiB -> Zstd-19``) clears every frozen office size floor.  However,
the v3 search stops at the *first rule depth* containing any feasible policy.  That is
an evidence-friendly discovery shortcut, not an encoder-quality objective: it can
select a broad one-rule policy even when two or more generic rules would achieve the
same byte target with substantially less high-effort compression.

This experiment keeps the exact same permitted features, atomic rules, payload-size
table, archive grammar, verification, locality accounting and comparators.  It changes
only policy search.  A branch-and-bound search continues through all four reviewed rule
depths and minimizes the existing modeled effort tuple globally.  Search pruning is
safe because combining rules is monotone: a later rule can only keep or raise each
pack's compression level, so selected-pack count and summed compression effort can
never decrease.

The selected policy is then handed to the unchanged v4 exact-byte parallel executor.
It receives no credit unless the resulting archive is byte/SHA-identical to its serial
reference and still satisfies every immutable office size/locality requirement.  A
performance miss remains valid negative evidence; this file cannot authorize selector,
native/Android, or release promotion.
"""

import argparse
import json
from pathlib import Path
import shutil

from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v4 as V4


def _primary_cost(vector: tuple[int, ...]) -> tuple[int, int, int]:
    selected = [int(level) for level in vector if int(level) != 1]
    return (
        len(selected),
        sum(level - 1 for level in selected),
        max(selected, default=1),
    )


def _can_still_beat(vector: tuple[int, ...], best_cost: tuple | None) -> bool:
    if best_cost is None:
        return True
    # Rule composition is max-per-pack.  These first three components therefore form
    # an admissible lower bound on every descendant state's final _rule_cost.
    return _primary_cost(vector) < tuple(best_cost[:3])


def _search_full_frontier(
    features: list[dict],
    meta_comp: bytes,
    payload_table: list[dict[int, int]],
    size_ceiling: int,
) -> tuple[list[dict] | None, tuple[int, ...] | None, int | None, dict]:
    atomic = V3._deduplicated_atomic_states(features)
    baseline = tuple(1 for _ in features)
    states: dict[tuple[int, ...], list[dict]] = {baseline: []}
    best: tuple[tuple, int, list[dict], tuple[int, ...]] | None = None
    state_counts = [1]
    expanded_counts: list[int] = []
    feasible_by_depth: list[int] = []

    for depth in range(1, V3.MAX_RULES + 1):
        next_states: dict[tuple[int, ...], list[dict]] = dict(states)
        expanded = 0
        for base_vector, base_rules in states.items():
            if len(base_rules) >= depth:
                continue
            if best is not None and not _can_still_beat(base_vector, best[0]):
                continue
            expanded += 1
            for atomic_vector, rule in atomic:
                vector = tuple(max(a, b) for a, b in zip(base_vector, atomic_vector))
                if vector == base_vector:
                    continue
                rules = base_rules + [rule]
                cost = V3._rule_cost(rules, vector)
                if best is not None and tuple(cost[:3]) > tuple(best[0][:3]):
                    continue
                existing = next_states.get(vector)
                if existing is None or cost < V3._rule_cost(existing, vector):
                    next_states[vector] = rules

        states = next_states
        state_counts.append(len(states))
        expanded_counts.append(expanded)
        feasible = 0
        for vector, rules in states.items():
            if not rules or len(rules) > depth:
                continue
            archive_bytes = V3._exact_archive_bytes(meta_comp, payload_table, vector)
            if archive_bytes >= size_ceiling:
                continue
            feasible += 1
            item = (V3._rule_cost(rules, vector), int(archive_bytes), rules, vector)
            if best is None or (item[0], item[1]) < (best[0], best[1]):
                best = item
        feasible_by_depth.append(feasible)

    if best is None:
        return None, None, None, {
            "search_mode": "full-depth-branch-and-bound",
            "deduplicated_atomic_rules": len(atomic),
            "state_counts_by_depth": state_counts,
            "expanded_states_by_depth": expanded_counts,
            "feasible_states_by_depth": feasible_by_depth,
            "clearing_states": 0,
        }

    cost, archive_bytes, rules, vector = best
    return rules, vector, int(archive_bytes), {
        "search_mode": "full-depth-branch-and-bound",
        "deduplicated_atomic_rules": len(atomic),
        "state_counts_by_depth": state_counts,
        "expanded_states_by_depth": expanded_counts,
        "feasible_states_by_depth": feasible_by_depth,
        "clearing_states": sum(feasible_by_depth),
        "selected_modeled_cost": list(cost[:4]),
    }


def run(work_root: Path) -> dict:
    original = V3._search
    try:
        V3._search = _search_full_frontier
        result = dict(V4.run(work_root))
    finally:
        V3._search = original

    policy = result.get("selected_policy", {})
    measured = result.get("measured_candidate", {})
    predecessor_high_effort = 15
    selected_high_effort = int(measured.get("selected_high_effort_packs", 0))
    result["schema"] = "cmpct-v030-eg08-policy-distillation-v5"
    result["search_upgrade"] = {
        "predecessor": "first-feasible-rule-depth",
        "candidate": "full-depth-branch-and-bound",
        "max_rules": int(V3.MAX_RULES),
        "monotone_pruning_proof": (
            "rule composition is max-per-pack; selected-pack count, summed level effort "
            "and maximum selected level cannot decrease in descendants"
        ),
        "predecessor_selected_high_effort_packs": predecessor_high_effort,
        "selected_high_effort_packs": selected_high_effort,
        "strictly_reduces_high_effort_pack_count": selected_high_effort < predecessor_high_effort,
    }
    result["selected_policy"] = policy
    result["claim_boundary"] = (
        "Research evidence only. The search is content-identity-free and uses the unchanged v3 feature/rule family. "
        "A green result cannot authorize selector/native/Android/release promotion; ordinary all-15 and strict "
        "release authority remain mandatory."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v5-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-policy-v5.json"))
    args = parser.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_policy": result.get("selected_policy"),
        "search_upgrade": result.get("search_upgrade"),
        "measured_candidate": result.get("measured_candidate"),
        "strict": result.get("strict"),
    }, indent=2), flush=True)
    if not result.get("strict", {}).get("passed", False):
        raise SystemExit("full-frontier identity-free C25EG08 policy did not satisfy the four-way office contract")


if __name__ == "__main__":
    main()
