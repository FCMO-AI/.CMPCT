"""ONE-G0.2 causal attribution of local/global linear nomination-index probes."""
from __future__ import annotations

from collections import deque
import json
import os

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, _extend_left, _extend_right,
    GEAR_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW,
)
from benchmarks.one.one_g02_relation_shared_observer_validation import (
    LOCAL_ENTRIES, MINIMIZER_SPAN, _cases, _cross_object_reuse_nominations,
)

SIZES = (64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
CASES = (
    "shift_plus1", "damage_quarter", "fragmented_every96",
    "hostile_fixed_bands", "fragmented_every32", "independent_random",
)


def _linear_find(entries: list[tuple[int, int]], key: int) -> tuple[int | None, int]:
    probes = 0
    for candidate, start in entries:
        probes += 1
        if candidate == key:
            return start, probes
    return None, probes


def _replay(source: bytes, target: bytes) -> dict[str, int | float]:
    data = source + target
    boundary = len(source)
    local_index: list[tuple[int, int]] = []
    global_index: list[tuple[int, int]] = []
    minima: deque[tuple[int, int]] = deque()
    minimizer_enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    last_emitted_position = -1
    h = 0
    run_value = data[0]
    run_length = 0
    covered_until = 0

    local_lookup_events = local_probes = 0
    global_lookup_events = global_probes = 0
    local_cross_auditions = local_cross_exact = 0
    global_cross_auditions = global_cross_exact = 0
    local_peak = global_peak = 0

    def audition(layer: str, start: int, prior: int | None) -> None:
        nonlocal covered_until
        nonlocal local_cross_auditions, local_cross_exact
        nonlocal global_cross_auditions, global_cross_exact
        if prior is None or start < covered_until:
            return
        is_cross = prior < boundary <= start
        if is_cross:
            if layer == "local":
                local_cross_auditions += 1
            else:
                global_cross_auditions += 1
        if data[prior:prior + WINDOW] != data[start:start + WINDOW]:
            return
        left, _ = _extend_left(data, prior, start, covered_until)
        right, _ = _extend_right(data, prior, start)
        target_start = max(start - left, covered_until)
        target_end = start + right
        if target_end > target_start:
            if is_cross:
                if layer == "local":
                    local_cross_exact += 1
                else:
                    global_cross_exact += 1
            covered_until = target_end

    for position, value in enumerate(data):
        if not run_length:
            run_value, run_length = value, 1
        elif value == run_value:
            run_length += 1
        else:
            run_value, run_length = value, 1

        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        start = position + 1 - WINDOW
        run_dominated = run_length >= max(MIN_RUN, WINDOW)

        if not run_dominated and (position + 1) % WINDOW == 0:
            local_lookup_events += 1
            prior, probes = _linear_find(local_index, h)
            local_probes += probes
            audition("local", start, prior)
            if prior is None:
                local_index.append((h, start))
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.pop(0)
                local_peak = max(local_peak, len(local_index))

        if not minimizer_enabled:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        if first_valid < WINDOW - 1:
            continue
        signal, anchor_position = minima[0]
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        anchor_start = anchor_position + 1 - WINDOW

        global_lookup_events += 1
        prior, probes = _linear_find(global_index, signal)
        global_probes += probes
        audition("global", anchor_start, prior)
        if prior is None and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
            global_index.append((signal, anchor_start))
            global_peak = max(global_peak, len(global_index))

    total_auditions = local_cross_auditions + global_cross_auditions
    total_exact = local_cross_exact + global_cross_exact
    input_bytes = len(data)
    return {
        "input_bytes": input_bytes,
        "local_lookup_events": local_lookup_events,
        "local_key_comparisons": local_probes,
        "global_lookup_events": global_lookup_events,
        "global_key_comparisons": global_probes,
        "local_cross_auditions": local_cross_auditions,
        "local_cross_exact": local_cross_exact,
        "global_cross_auditions": global_cross_auditions,
        "global_cross_exact": global_cross_exact,
        "total_cross_auditions": total_auditions,
        "total_cross_exact": total_exact,
        "local_peak_entries": local_peak,
        "global_peak_entries": global_peak,
        "local_comparisons_per_input_byte": local_probes / input_bytes,
        "global_comparisons_per_input_byte": global_probes / input_bytes,
        "local_exact_share": (local_cross_exact / total_exact) if total_exact else 0.0,
    }


def run() -> dict[str, object]:
    rows = []
    semantic_mismatches = []
    local_probe_majority_rows = 0
    global_probe_majority_rows = 0
    productive_rows = 0
    local_low_share_productive_rows = 0
    global_low_share_productive_rows = 0

    for size in SIZES:
        for seed in SEEDS:
            generated = _cases(size, seed)
            for name in CASES:
                source, target = generated[name]
                row = _replay(source, target)
                ref_exact, ref_auditions, _ = _cross_object_reuse_nominations(source, target)
                if row["total_cross_exact"] != ref_exact or row["total_cross_auditions"] != ref_auditions:
                    semantic_mismatches.append((size, seed, name))
                if row["local_key_comparisons"] > row["global_key_comparisons"]:
                    local_probe_majority_rows += 1
                elif row["global_key_comparisons"] > row["local_key_comparisons"]:
                    global_probe_majority_rows += 1
                if row["total_cross_exact"]:
                    productive_rows += 1
                    if row["local_exact_share"] < 0.5:
                        local_low_share_productive_rows += 1
                    if row["local_exact_share"] > 0.5:
                        global_low_share_productive_rows += 1
                row.update({"relation_bytes": size, "seed": seed, "case": name})
                rows.append(row)

    row_count = len(rows)
    if semantic_mismatches:
        decision = "repair_probe_attribution_model"
    elif (
        local_probe_majority_rows >= 0.75 * row_count
        and productive_rows
        and local_low_share_productive_rows >= 0.75 * productive_rows
    ):
        decision = "local_lookup_primary_owner_candidate"
    elif (
        global_probe_majority_rows >= 0.75 * row_count
        and productive_rows
        and global_low_share_productive_rows >= 0.75 * productive_rows
    ):
        decision = "global_lookup_primary_owner_candidate"
    else:
        decision = "mixed_lookup_owner"

    return {
        "schema": "cmpct-one-g02-nomination-index-probe-attribution-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "semantic_mismatches": semantic_mismatches,
        "row_count": row_count,
        "productive_rows": productive_rows,
        "local_probe_majority_rows": local_probe_majority_rows,
        "global_probe_majority_rows": global_probe_majority_rows,
        "local_low_share_productive_rows": local_low_share_productive_rows,
        "decision": decision,
        "rows": rows,
        "claim_boundary": "comparison-count attribution only; not CPU timing authority",
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result["semantic_mismatches"] else 1)
