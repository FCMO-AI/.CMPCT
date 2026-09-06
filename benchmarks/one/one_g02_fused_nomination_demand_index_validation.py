"""ONE-G0.2 bounded demand-grown event-index semantic/resource gate."""
from __future__ import annotations

import ctypes
import json
import os

from benchmarks.one.one_g02_fused_native_nomination_validation import _build, _fused
from benchmarks.one.one_g02_native_nomination_trace_bridge import _native_anchor_positions
from benchmarks.one.one_g02_native_nomination_event_consumer_validation import _consume
from benchmarks.one.one_g02_relation_shared_observer_validation import _cases

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (7, 29, 53)
LOCAL_ENTRIES = 64
GLOBAL_HARD_CAP = 8192
FIXED_EVENT_INDEX_BYTES = 198_144
MAX_256K_EVENT_INDEX_BYTES = 16_896


class IndexEntryLayout(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_uint64),
        ("start", ctypes.c_size_t),
        ("used", ctypes.c_int),
    ]


SELECTOR_SEMANTIC_FIELDS = (
    "emitted",
    "final_state",
    "positions_considered",
    "derived_state_reads",
    "suffix_blocks_built",
    "suffix_blocks_skipped_dead",
    "suffix_value_indirect_loads",
)


def _sig(x, fields):
    return tuple(int(getattr(x, name)) for name in fields)


def run() -> dict[str, object]:
    selector, consumer, fused, td = _build()
    entry_bytes = ctypes.sizeof(IndexEntryLayout)
    rows = []
    selector_mismatches = []
    trace_mismatches = []
    nomination_mismatches = []
    capacity_errors = []
    state_regressions = []
    false_exact_nominations = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    data = source + target
                    anchors, baseline_selector = _native_anchor_positions(selector, data)
                    baseline_consumer = _consume(consumer, data, len(source), anchors)
                    candidate, trace = _fused(fused, data, len(source), collect_trace=True)
                    candidate_no_trace, _ = _fused(fused, data, len(source), collect_trace=False)

                    if _sig(candidate, SELECTOR_SEMANTIC_FIELDS) != _sig(
                        baseline_selector, SELECTOR_SEMANTIC_FIELDS
                    ):
                        selector_mismatches.append((size, seed, name))
                    if trace != anchors:
                        trace_mismatches.append((size, seed, name))

                    nomination_fields = (
                        "cross_auditions", "cross_exact", "local_peak_entries",
                        "global_peak_entries", "verification_read_bytes", "extension_read_bytes",
                    )
                    if _sig(candidate, nomination_fields) != _sig(baseline_consumer, nomination_fields):
                        nomination_mismatches.append((size, seed, name))
                    if _sig(candidate, tuple(n for n, _ in type(candidate)._fields_)) != _sig(
                        candidate_no_trace, tuple(n for n, _ in type(candidate_no_trace)._fields_)
                    ):
                        nomination_mismatches.append((size, seed, name + ":trace_dependency"))
                    if int(baseline_consumer.cross_exact) == 0 and int(candidate.cross_exact) != 0:
                        false_exact_nominations.append((size, seed, name))

                    minimizer_state_bytes = int(baseline_selector.reserved_state_bytes)
                    total_state_bytes = int(candidate.reserved_state_bytes)
                    event_index_bytes = total_state_bytes - minimizer_state_bytes
                    if event_index_bytes < LOCAL_ENTRIES * entry_bytes or event_index_bytes % entry_bytes:
                        capacity_errors.append((size, seed, name, "layout", event_index_bytes))
                        global_capacity = -1
                    else:
                        global_capacity = event_index_bytes // entry_bytes - LOCAL_ENTRIES
                        if global_capacity not in (0, 64, 128, 256, 512, 1024, 2048, 4096, 8192):
                            capacity_errors.append((size, seed, name, "growth_law", global_capacity))
                        if global_capacity > GLOBAL_HARD_CAP:
                            capacity_errors.append((size, seed, name, "hard_cap", global_capacity))
                        if int(candidate.global_peak_entries) > global_capacity:
                            capacity_errors.append((size, seed, name, "peak_over_capacity", global_capacity))

                    if event_index_bytes > FIXED_EVENT_INDEX_BYTES:
                        state_regressions.append((size, seed, name, event_index_bytes))
                    if size == 256 * 1024 and event_index_bytes > MAX_256K_EVENT_INDEX_BYTES:
                        state_regressions.append((size, seed, name + ":256k_bound", event_index_bytes))

                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "anchor_count": len(anchors),
                        "cross_auditions": int(candidate.cross_auditions),
                        "cross_exact": int(candidate.cross_exact),
                        "local_peak_entries": int(candidate.local_peak_entries),
                        "global_peak_entries": int(candidate.global_peak_entries),
                        "global_capacity_entries": global_capacity,
                        "entry_bytes": entry_bytes,
                        "minimizer_state_bytes": minimizer_state_bytes,
                        "event_index_reserved_bytes": event_index_bytes,
                        "total_reserved_state_bytes": total_state_bytes,
                        "fixed_prototype_event_index_bytes": FIXED_EVENT_INDEX_BYTES,
                        "event_index_over_fixed": event_index_bytes / FIXED_EVENT_INDEX_BYTES,
                    })

        passed = not (
            selector_mismatches or trace_mismatches or nomination_mismatches
            or capacity_errors or state_regressions or false_exact_nominations
        )
        return {
            "schema": "cmpct-one-g02-fused-nomination-demand-index-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "entry_bytes": entry_bytes,
            "fixed_prototype_event_index_bytes": FIXED_EVENT_INDEX_BYTES,
            "selector_mismatches": selector_mismatches,
            "trace_mismatches": trace_mismatches,
            "nomination_mismatches": nomination_mismatches,
            "capacity_errors": capacity_errors,
            "state_regressions": state_regressions,
            "false_exact_nominations": false_exact_nominations,
            "max_event_index_reserved_bytes": max(int(r["event_index_reserved_bytes"]) for r in rows),
            "max_256k_event_index_reserved_bytes": max(
                int(r["event_index_reserved_bytes"]) for r in rows if r["relation_bytes"] == 256 * 1024
            ),
            "decision": "advance_bounded_demand_nomination_index" if passed else "repair_bounded_demand_nomination_index",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_bounded_demand_nomination_index" else 1)
