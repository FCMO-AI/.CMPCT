from __future__ import annotations

"""Workload-blind admission seam for the bounded-drift v0.30 research candidate.

This module intentionally cannot see filenames, paths, workload names, frozen hashes, or
benchmark identities. It accepts only already-priced physical/runtime observations plus
release-law resource facts. It therefore answers one narrow D5 question: if a bounded-drift
candidate has been honestly built, is it safe to prefer over the internal fallback without
creating a byte/runtime/resource regression?

It does *not* authorize candidate construction itself and grants no release credit. A future
execution policy must prove that any pre-admission work and any losing candidate construction
are included in product creation timing.
"""

from dataclasses import dataclass

MAX_DECODE_UNIT_BYTES = 8 * 1024 * 1024
MAX_MEMBER_READ_AMPLIFICATION = 8.0


@dataclass(frozen=True)
class CandidateObservation:
    physical_bytes: int
    create_ns: int
    max_decode_unit_bytes: int
    max_member_read_amplification: float
    exact_tree_verified: bool
    corruption_rejection_verified: bool


@dataclass(frozen=True)
class AdmissionDecision:
    selected: str
    reason: str
    release_credit: bool = False


def decide(
    *,
    bounded_drift: CandidateObservation,
    fallback: CandidateObservation,
) -> AdmissionDecision:
    """Prefer bounded drift only on strict, fully observed internal domination.

    Ties deliberately keep the fallback. The API is closed over physical evidence and cannot
    branch on workload identity. Both candidates' create_ns values are expected to include
    their complete construction/publication accounting; this function does not hide that cost.
    """
    for label, obs in (("bounded_drift", bounded_drift), ("fallback", fallback)):
        if obs.physical_bytes < 0 or obs.create_ns < 0 or obs.max_decode_unit_bytes < 0:
            return AdmissionDecision("fallback", f"invalid_{label}_measurement")
        if obs.max_member_read_amplification < 0:
            return AdmissionDecision("fallback", f"invalid_{label}_locality")

    if not bounded_drift.exact_tree_verified:
        return AdmissionDecision("fallback", "bounded_drift_tree_unverified")
    if not bounded_drift.corruption_rejection_verified:
        return AdmissionDecision("fallback", "bounded_drift_corruption_unverified")
    if bounded_drift.max_decode_unit_bytes > MAX_DECODE_UNIT_BYTES:
        return AdmissionDecision("fallback", "bounded_drift_decode_unit_exceeded")
    if bounded_drift.max_member_read_amplification > MAX_MEMBER_READ_AMPLIFICATION:
        return AdmissionDecision("fallback", "bounded_drift_locality_exceeded")

    # Accepted fallback remains the internal product floor. A candidate must strictly improve
    # bytes and must not cost more measured creation time. Equal bytes are a regression by law;
    # equal runtime is permitted only because the candidate has already strictly improved bytes.
    if bounded_drift.physical_bytes >= fallback.physical_bytes:
        return AdmissionDecision("fallback", "no_strict_byte_improvement")
    if bounded_drift.create_ns > fallback.create_ns:
        return AdmissionDecision("fallback", "runtime_regression")

    return AdmissionDecision("bounded_drift", "strict_internal_domination")
