from __future__ import annotations

"""Exact progressive G0-G4 futility oracle with bounded speculative work.

Research/evidence tool only. It does not change canonical archive grammar, reader
semantics, transform admission, or release thresholds.

The proof is an optimistic physical-byte lower bound over the current G0-G4 overlay:

    LB = HDR + FTR + PH * N
         + sum(payload bytes of records ineligible for every current G0-G4 transform)
         + sum(chosen payload bytes of completed eligible auditions)

Both metadata copies and every not-yet-completed eligible payload are gifted to zero
bytes. Therefore LB can only under-estimate any legal completed overlay. Once
LB >= the accepted-v0.29 floor, a strict byte win is impossible and remaining
eligible auditions are provably futile.

The shipping scheduler currently submits the complete iterable to ``Executor.map``.
This oracle instead keeps at most W auditions outstanding. The proof is monotone
under arbitrary completion order; after the completion that first makes LB decisive,
at most W-1 previously submitted auditions can remain. Shipping W is capped at four.
"""

from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, ThreadPoolExecutor, wait
from dataclasses import dataclass
import multiprocessing as mp
import os
from pathlib import Path
import time
from typing import Any, Iterable


@dataclass
class ProgressiveFloor:
    """Monotone optimistic byte floor for one G0-G4 overlay attempt."""

    fixed_framing_bytes: int
    invariant_payload_bytes: int
    floor_bytes: int
    chosen_payload_bytes: int = 0

    @property
    def lower_bound_bytes(self) -> int:
        return int(self.fixed_framing_bytes + self.invariant_payload_bytes + self.chosen_payload_bytes)

    @property
    def decisive(self) -> bool:
        return self.lower_bound_bytes >= int(self.floor_bytes)

    def observe_chosen_payload(self, payload_bytes: int) -> int:
        payload_bytes = int(payload_bytes)
        if payload_bytes < 0:
            raise ValueError("chosen payload bytes must be non-negative")
        self.chosen_payload_bytes += payload_bytes
        return self.lower_bound_bytes


def max_post_decision_outstanding(worker_count: int) -> int:
    """Hard bound on already-submitted work after a completion first triggers the proof."""
    worker_count = int(worker_count)
    if worker_count < 0:
        raise ValueError("worker count must be non-negative")
    return max(0, worker_count - 1)


def _record_is_g04_eligible(shared: Any, record: tuple, member_lengths: Iterable[int]) -> tuple[bool, float]:
    """Apply the exact common current G0-G4 size/locality gate without re-decoding.

    ``strict._read_source_records`` has already decoded/authenticated every source record
    and rejects a logical-size mismatch before returning it. ``record[1]`` is therefore
    the validated pre-transform byte count needed by the current common gate.
    """

    raw_size = int(record[1])
    lengths = [max(1, int(length)) for length in member_lengths]
    amp = max((raw_size / length for length in lengths), default=float("inf"))
    eligible = (
        shared.O.MIN_RECORD_BYTES <= raw_size <= shared.O.MAX_OVERLAY_RECORD
        and amp <= shared.O.MAX_MEMBER_READ_AMP
    )
    return bool(eligible), float(amp)


def _ineligible_outcome(record_id: int, record: tuple, amp: float) -> tuple[tuple, None, dict]:
    """Return the exact historical no-transform result for a provably ineligible record."""

    return (
        record,
        None,
        {
            "record_id": int(record_id),
            "raw_bytes": int(record[1]),
            "baseline_payload_bytes": len(record[2]),
            "max_member_read_amplification": float(amp),
            "selected": "none",
            "payload_saving_bytes": 0,
            "progressive_ineligible_fast_path": True,
        },
    )


def progressive_overlay(
    graph_path: Path,
    floor_bytes: int,
    overlay_path: Path,
    *,
    worker_cap: int | None = None,
) -> dict:
    """Run exact current G0-G4 auditions with monotone futility feedback.

    If the lower bound fires, no overlay is written because no legal completion can be
    strictly smaller than ``floor_bytes``. If it never fires, every eligible record is
    auditioned by the current canonical worker and outcomes are restored to record-id
    order before calling the unchanged current G0-G4 writer.

    This function intentionally imports shipping modules lazily so the algebraic helpers
    above remain dependency-light and directly unit-testable.
    """

    from experiments import entropygraph_v030_release_product as product

    started = time.perf_counter()
    graph_path = Path(graph_path)
    overlay_path = Path(overlay_path)
    floor_bytes = int(floor_bytes)
    if floor_bytes < 0:
        raise ValueError("floor bytes must be non-negative")

    shared = product.C.SHARED
    source_format, _source, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))
    total_records = len(graph_records)
    outcomes: list[tuple | None] = [None] * total_records
    eligible_ids: list[int] = []
    invariant_payload_bytes = 0

    for record_id, record in enumerate(graph_records):
        eligible, amp = _record_is_g04_eligible(shared, record, users[record_id])
        if eligible:
            eligible_ids.append(record_id)
        else:
            invariant_payload_bytes += len(record[2])
            outcomes[record_id] = _ineligible_outcome(record_id, record, amp)

    proof = ProgressiveFloor(
        fixed_framing_bytes=(
            shared.G.HDR.size
            + shared.G.FTR.size
            + total_records * shared.G.PH.size
        ),
        invariant_payload_bytes=invariant_payload_bytes,
        floor_bytes=floor_bytes,
    )
    initial_lower_bound = proof.lower_bound_bytes

    process_pool = bool(graph_records) and product._g04_process_pool_eligible(graph_path, graph_records)
    default_workers = min(
        product.G04_AUDITION_MAX_WORKERS,
        len(eligible_ids),
        max(1, os.cpu_count() or 1),
    ) if eligible_ids else 0
    if worker_cap is None:
        worker_count = default_workers
    else:
        worker_cap = int(worker_cap)
        if worker_cap < 1 and eligible_ids:
            raise ValueError("worker_cap must be >= 1 when eligible records exist")
        worker_count = min(default_workers, worker_cap) if eligible_ids else 0

    scheduler = (
        "bounded-feedback-spawn-process-pool-v1"
        if process_pool and worker_count
        else "bounded-feedback-thread-pool-v1"
        if worker_count
        else "ineligible-only"
    )

    submitted_ids: list[int] = []
    completed_ids: list[int] = []
    canceled_ids: list[int] = []
    decision_outstanding = 0
    stopped = proof.decisive

    if not stopped and eligible_ids:
        if process_pool:
            ctx = mp.get_context("spawn")
            executor = ProcessPoolExecutor(max_workers=worker_count, mp_context=ctx)
        else:
            executor = ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-v030-g04-bound")

        pending: dict[Future, int] = {}
        next_index = 0

        def submit_one(record_id: int) -> None:
            if process_pool:
                future = executor.submit(
                    product._g04_audition_worker,
                    (record_id, graph_records[record_id], users[record_id]),
                )
            else:
                future = executor.submit(
                    shared.G._audition_record,
                    record_id,
                    graph_records[record_id],
                    users[record_id],
                )
            pending[future] = record_id
            submitted_ids.append(record_id)

        try:
            while next_index < len(eligible_ids) and len(pending) < worker_count:
                submit_one(eligible_ids[next_index])
                next_index += 1

            while pending:
                done, _ = wait(tuple(pending), return_when=FIRST_COMPLETED)
                for future in done:
                    record_id = pending.pop(future)
                    outcome = future.result()
                    outcomes[record_id] = outcome
                    completed_ids.append(record_id)
                    proof.observe_chosen_payload(len(outcome[0][2]))

                if proof.decisive:
                    stopped = True
                    decision_outstanding = len(pending)
                    for future, record_id in list(pending.items()):
                        if future.cancel():
                            canceled_ids.append(record_id)
                            pending.pop(future)
                    break

                while next_index < len(eligible_ids) and len(pending) < worker_count:
                    submit_one(eligible_ids[next_index])
                    next_index += 1
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

    unsubmitted_ids = [record_id for record_id in eligible_ids if record_id not in submitted_ids]
    common = {
        "source_format": source_format,
        "floor_bytes": floor_bytes,
        "initial_lower_bound_bytes": initial_lower_bound,
        "decision_lower_bound_bytes": proof.lower_bound_bytes,
        "records_total": total_records,
        "eligible_records": len(eligible_ids),
        "ineligible_records": total_records - len(eligible_ids),
        "invariant_payload_bytes": invariant_payload_bytes,
        "submitted_eligible_records": len(submitted_ids),
        "completed_eligible_records": len(completed_ids),
        "unsubmitted_eligible_records": len(unsubmitted_ids),
        "decision_outstanding_records": decision_outstanding,
        "canceled_records": len(canceled_ids),
        "audition_workers": worker_count,
        "audition_scheduler": scheduler,
        "max_outstanding_by_construction": worker_count,
        "max_possible_outstanding_after_trigger": max_post_decision_outstanding(worker_count),
        "elapsed_s": time.perf_counter() - started,
    }

    if stopped:
        if decision_outstanding > max_post_decision_outstanding(worker_count):
            raise RuntimeError("progressive scheduler exceeded bounded post-decision speculation")
        return {
            **common,
            "provably_futile": True,
            "overlay_written": False,
            "write_stats": None,
            "auditions": None,
        }

    if any(outcome is None for outcome in outcomes):
        raise RuntimeError("progressive G0-G4 scheduler omitted a required record outcome")

    ordered = [outcome for outcome in outcomes if outcome is not None]
    records = [row[0] for row in ordered]
    transforms = [row[1] for row in ordered]
    auditions = [row[2] for row in ordered]
    annotated_meta = dict(graph_meta)
    annotated_meta["overlay_source_format"] = source_format
    write_stats = shared.G._write_overlay(annotated_meta, records, transforms, overlay_path)
    return {
        **common,
        "provably_futile": False,
        "overlay_written": True,
        "write_stats": write_stats,
        "auditions": auditions,
    }
