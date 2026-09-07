"""ONE-G0.2 morphology-aware fused-observation gate.

This is writer-side discovery policy only. It does not add a reader-visible opcode or
change ONE reconstruction semantics. The gate exists to falsify a measured regression:
on strongly numeric ASCII roots, generic reuse fingerprinting can cost more than the
opportunities it discovers.
"""
from __future__ import annotations

from dataclasses import dataclass

from .observe import Observation, ObservationStats, RunOpportunity, observe

_NUMERIC_ASCII = frozenset(b"0123456789+-.eE,;:|/ _\t\r\n")
_DIGITS = frozenset(b"0123456789")


@dataclass(frozen=True)
class MorphologyGateDecision:
    gated: bool
    sample_bytes: int
    numeric_like_bytes: int
    digit_bytes: int
    numeric_fraction: float
    digit_fraction: float
    sampled_chunks: int
    unique_sampled_chunks: int
    unique_chunk_fraction: float


@dataclass(frozen=True)
class MorphologyObservation:
    observation: Observation
    gate: MorphologyGateDecision


def classify_numeric_ascii(
    data: bytes,
    *,
    sample_limit: int = 4096,
    minimum_input: int = 16384,
    diversity_chunk_size: int = 64,
    minimum_numeric_fraction: float = 0.985,
    minimum_digit_fraction: float = 0.35,
    minimum_unique_chunk_fraction: float = 0.90,
) -> MorphologyGateDecision:
    """Return a bounded decision for strongly numeric, locally diverse ASCII roots.

    Morphology alone is not sufficient: repetitive numeric tables can contain excellent
    reuse Laws. The bounded prefix therefore must also have high exact chunk diversity
    before reuse fingerprinting is skipped. Tiny roots are never gated because the
    classification pass is hard to amortize there.
    """
    if type(data) is not bytes:
        raise TypeError("ONE morphology input must be bytes")
    for name, value in {
        "sample_limit": sample_limit,
        "minimum_input": minimum_input,
        "diversity_chunk_size": diversity_chunk_size,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    for name, value in {
        "minimum_numeric_fraction": minimum_numeric_fraction,
        "minimum_digit_fraction": minimum_digit_fraction,
        "minimum_unique_chunk_fraction": minimum_unique_chunk_fraction,
    }.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")

    sample = data[: min(len(data), sample_limit)]
    sample_bytes = len(sample)
    if sample_bytes == 0:
        return MorphologyGateDecision(False, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0)

    numeric_like = sum(value in _NUMERIC_ASCII for value in sample)
    digits = sum(value in _DIGITS for value in sample)
    numeric_fraction = numeric_like / sample_bytes
    digit_fraction = digits / sample_bytes

    complete_bytes = sample_bytes - (sample_bytes % diversity_chunk_size)
    chunks = tuple(
        sample[offset : offset + diversity_chunk_size]
        for offset in range(0, complete_bytes, diversity_chunk_size)
    )
    sampled_chunks = len(chunks)
    unique_sampled_chunks = len(set(chunks))
    unique_chunk_fraction = (
        unique_sampled_chunks / sampled_chunks if sampled_chunks else 0.0
    )

    gated = (
        len(data) >= minimum_input
        and numeric_fraction >= minimum_numeric_fraction
        and digit_fraction >= minimum_digit_fraction
        and sampled_chunks >= 4
        and unique_chunk_fraction >= minimum_unique_chunk_fraction
    )
    return MorphologyGateDecision(
        gated,
        sample_bytes,
        numeric_like,
        digits,
        numeric_fraction,
        digit_fraction,
        sampled_chunks,
        unique_sampled_chunks,
        unique_chunk_fraction,
    )


def _observe_runs_only(data: bytes, *, min_run: int, classifier_bytes: int) -> Observation:
    """Preserve cheap run discovery while deliberately omitting reuse fingerprinting."""
    runs: list[RunOpportunity] = []
    if data:
        run_start = 0
        run_value = data[0]
        run_length = 1
        for position in range(1, len(data)):
            value = data[position]
            if value == run_value:
                run_length += 1
            else:
                if run_length >= min_run:
                    runs.append(RunOpportunity(run_start, run_length, run_value))
                run_start = position
                run_value = value
                run_length = 1
        if run_length >= min_run:
            runs.append(RunOpportunity(run_start, run_length, run_value))

    # Classification is a real extra source read and is charged explicitly.
    scan_bytes = len(data) + classifier_bytes
    run_bytes = sum(item.length for item in runs)
    return Observation(
        runs=tuple(runs),
        reuse=(),
        stats=ObservationStats(
            input_bytes=len(data),
            source_scan_bytes=scan_bytes,
            chunk_fingerprints=0,
            hash_lookups=0,
            collision_verifications=0,
            verification_read_bytes=0,
            total_source_read_bytes=scan_bytes,
            run_candidates=len(runs),
            run_opportunity_bytes=run_bytes,
            reuse_candidates=0,
            reuse_opportunity_bytes=0,
            peak_index_entries=0,
            retained_index_payload_bytes=0,
        ),
    )


def observe_morphology_gated(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
    sample_limit: int = 4096,
    minimum_input: int = 16384,
    diversity_chunk_size: int = 64,
    minimum_numeric_fraction: float = 0.985,
    minimum_digit_fraction: float = 0.35,
    minimum_unique_chunk_fraction: float = 0.90,
) -> MorphologyObservation:
    """Observe with generic fusion unless strong numeric morphology rejects reuse work.

    A gated root still receives one full run-observation pass. The bounded classifier
    read is separately charged. An ungated root delegates to the existing observer
    exactly, so this experiment does not perturb generic opportunity semantics.
    """
    decision = classify_numeric_ascii(
        data,
        sample_limit=sample_limit,
        minimum_input=minimum_input,
        diversity_chunk_size=diversity_chunk_size,
        minimum_numeric_fraction=minimum_numeric_fraction,
        minimum_digit_fraction=minimum_digit_fraction,
        minimum_unique_chunk_fraction=minimum_unique_chunk_fraction,
    )
    if decision.gated:
        observation = _observe_runs_only(
            data,
            min_run=min_run,
            classifier_bytes=decision.sample_bytes,
        )
    else:
        observation = observe(
            data,
            min_run=min_run,
            chunk_size=chunk_size,
            max_index_entries=max_index_entries,
        )
    return MorphologyObservation(observation=observation, gate=decision)
