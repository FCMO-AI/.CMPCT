from __future__ import annotations

"""Fail-closed normalization for frozen historical Genesis adapter metrics.

This module does not execute contenders.  It only converts already-observed
historical reader statistics into the common raw-measurement contract without
turning missing instrumentation into synthetic zero-cost evidence.
"""

from typing import Any, Mapping


def unavailable_selective(reason: str, *, observed: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not reason.strip():
        raise ValueError("unavailable selective evidence requires a reason")
    result: dict[str, Any] = {"status": "unavailable", "reason": reason}
    if observed:
        result["observed"] = dict(observed)
    return result


def normalize_v030_read_member_stats(
    stats: Mapping[str, Any], *, requested_bytes: int
) -> dict[str, Any]:
    """Normalize frozen-v0.30 ``read_member_with_stats`` evidence.

    r24 archives explicitly report ``decoded_context_bytes=None`` and
    ``amplification=None``.  Those values mean *not instrumented*, not zero.
    r25 may provide decoded-context evidence and can therefore become a
    measured selective-access row.
    """

    if requested_bytes < 0:
        raise ValueError("requested_bytes must be non-negative")

    decoded = stats.get("decoded_context_bytes")
    amplification = stats.get("amplification")
    archive_version = stats.get("archive_version")

    if decoded is None or amplification is None:
        observed = {
            key: stats.get(key)
            for key in (
                "archive_version",
                "stored_bytes",
                "member_stored_bytes",
                "decoded_context_bytes",
                "amplification",
                "note",
            )
            if key in stats
        }
        return unavailable_selective(
            "frozen v0.30 reader returned no decoded-context/amplification instrumentation; preserve as unavailable",
            observed=observed,
        )

    if isinstance(decoded, bool) or not isinstance(decoded, int) or decoded < 0:
        raise ValueError("decoded_context_bytes must be a non-negative integer when measured")
    if isinstance(amplification, bool) or not isinstance(amplification, (int, float)) or amplification < 0:
        raise ValueError("amplification must be a non-negative number when measured")

    expected = (decoded / requested_bytes) if requested_bytes else (0.0 if decoded == 0 else None)
    if expected is None:
        raise ValueError("nonzero decoded context cannot have zero requested bytes")
    tolerance = max(1e-12, abs(expected) * 1e-9)
    if abs(float(amplification) - expected) > tolerance:
        raise ValueError("reported amplification contradicts decoded_context_bytes/requested_bytes")

    result: dict[str, Any] = {
        "measured": True,
        "requested_bytes": requested_bytes,
        "decoded_context_bytes": decoded,
        "amplification": float(amplification),
    }
    if archive_version is not None:
        result["archive_version"] = archive_version
    for key in ("stored_bytes", "member_stored_bytes"):
        value = stats.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a non-negative integer")
            result[key] = value
    return result


def normalize_missing_v029_selective_surface() -> dict[str, Any]:
    """Authority-safe representation until an exact frozen v0.29 surface is proven."""

    return unavailable_selective(
        "no exact selective-reader surface has been proven on frozen v0.29; absence is not zero-cost access"
    )
