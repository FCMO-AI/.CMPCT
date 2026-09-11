"""ONE-G0.2 preregistered validation of a tiny content-local Gear certificate.

See docs/one/evidence/ONE_G02_LOCAL_GEAR_CERTIFICATE_PREREG_2026-09-05.md.

This is structural nomination evidence, not product-speed authority.  The relation oracle is
still the existing exact safe dispatcher.  The candidate merely ORs two writer-side evidence
classes: cross-object exact reuse already emitted by the promoted Gear observer, and one
bounded bottom-8 rolling Gear certificate.  No reader-visible ONE operation is added.
"""
from __future__ import annotations

import heapq
import json
import os
import random

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _U64_MASK
from benchmarks.one.one_g02_relation_shared_observer_validation import (
    _cross_object_reuse_nominations,
    _hostile_band_break,
    _safe_result,
    _shifted,
    _build_safe,
)

SIZES = (4 * 1024, 8 * 1024, 16 * 1024, 64 * 1024, 256 * 1024)
SEEDS = (5, 23, 47)
CERT_WINDOW = 32
CERT_K = 8
MODELED_INCREMENTAL_STATE_BYTES = CERT_K * (8 + 4) + CERT_WINDOW + 8


def _rotl64(value: int, amount: int) -> int:
    amount &= 63
    return ((value << amount) | (value >> (64 - amount))) & _U64_MASK


def _rolling_gear_windows(data: bytes):
    """Yield (content-local Gear buzhash, start) for every 32-byte window in one pass."""
    if len(data) < CERT_WINDOW:
        return
    h = 0
    for b in data[:CERT_WINDOW]:
        h = _rotl64(h, 1) ^ _GEAR[b]
    yield h, 0
    outgoing_rotation = CERT_WINDOW & 63
    for end in range(CERT_WINDOW, len(data)):
        old = data[end - CERT_WINDOW]
        h = (
            _rotl64(h, 1)
            ^ _rotl64(_GEAR[old], outgoing_rotation)
            ^ _GEAR[data[end]]
        ) & _U64_MASK
        yield h, end + 1 - CERT_WINDOW


def _source_certificate(source: bytes) -> list[tuple[int, int]]:
    """Bottom-8 content-local witnesses; fixed-size state, no unbounded dedup table."""
    heap: list[tuple[int, int, int]] = []
    for h, pos in _rolling_gear_windows(source):
        item = (-h, -pos, h)
        if len(heap) < CERT_K:
            heapq.heappush(heap, item)
        elif h < heap[0][2]:
            heapq.heapreplace(heap, item)
    return sorted((entry[2], -entry[1]) for entry in heap)


def _certificate_nomination(source: bytes, target: bytes) -> tuple[bool, int, int]:
    cert = _source_certificate(source)
    by_hash: dict[int, list[int]] = {}
    for h, pos in cert:
        by_hash.setdefault(h, []).append(pos)
    windows = 0
    exact_compares = 0
    for h, target_pos in _rolling_gear_windows(target):
        windows += 1
        for source_pos in by_hash.get(h, ()):
            exact_compares += 1
            if target[target_pos:target_pos + CERT_WINDOW] == source[source_pos:source_pos + CERT_WINDOW]:
                return True, windows, exact_compares
    return False, windows, exact_compares


def _certificate_targeted(source: bytes) -> bytes:
    target = bytearray(_shifted(source))
    for _, source_pos in _source_certificate(source):
        # +1 shift maps source window [p:p+W] to target [p+1:p+1+W].
        target_pos = source_pos + 1 + CERT_WINDOW // 2
        if 0 <= target_pos < len(target):
            target[target_pos] ^= 0xD3
    return bytes(target)


def _cases(size: int, seed: int) -> dict[str, tuple[bytes, bytes]]:
    source = random.Random(61000 + size * 37 + seed * 1019).randbytes(size)
    return {
        "shift_plus1": (source, _shifted(source)),
        "damage_quarter": (source, _shifted(source, damage_quarter=True)),
        "fragmented_every96": (source, _shifted(source, spacing=96)),
        "hostile_fixed_bands": (source, _hostile_band_break(source)),
        "certificate_targeted": (source, _certificate_targeted(source)),
        "fragmented_every32": (source, _shifted(source, spacing=32)),
        "independent_random": (
            source,
            random.Random(62000 + size * 41 + seed * 1021).randbytes(size),
        ),
    }


def run() -> dict[str, object]:
    safe, td = _build_safe()
    rows: list[dict[str, object]] = []
    required_positive_misses: list[tuple[int, int, str]] = []
    false_nominations: list[tuple[int, int, str]] = []
    certificate_targeted_misses: list[tuple[int, int, str]] = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    enabled, best_shift, proofs = _safe_result(safe, source, target)
                    cross_exact, cross_auditions, peak_queue = _cross_object_reuse_nominations(source, target)
                    shared = cross_exact > 0
                    cert, target_windows, cert_exact_compares = _certificate_nomination(source, target)
                    hybrid = shared or cert
                    if enabled and not hybrid:
                        required_positive_misses.append((size, seed, name))
                        if name == "certificate_targeted":
                            certificate_targeted_misses.append((size, seed, name))
                    if not enabled and hybrid:
                        false_nominations.append((size, seed, name))
                    rows.append({
                        "relation_bytes": size,
                        "seed": seed,
                        "case": name,
                        "exact_relation_enabled": enabled,
                        "best_shift": best_shift,
                        "exact_proofs": proofs,
                        "shared_observer_nominated": shared,
                        "shared_cross_object_exact_reuse_nominations": cross_exact,
                        "shared_cross_object_reuse_auditions": cross_auditions,
                        "certificate_nominated": cert,
                        "certificate_target_windows_scanned": target_windows,
                        "certificate_exact_window_compares": cert_exact_compares,
                        "hybrid_nominated": hybrid,
                        "peak_existing_minimizer_queue_entries": peak_queue,
                    })
        passed = not required_positive_misses and not false_nominations
        return {
            "schema": "cmpct-one-g02-local-gear-certificate-validation-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_seeds": list(SEEDS),
            "certificate_window_bytes": CERT_WINDOW,
            "certificate_entries": CERT_K,
            "modeled_incremental_state_bytes": MODELED_INCREMENTAL_STATE_BYTES,
            "required_positive_misses": required_positive_misses,
            "certificate_targeted_misses": certificate_targeted_misses,
            "false_nominations": false_nominations,
            "decision": "advance_local_gear_certificate_hybrid" if passed else "reject_local_gear_certificate_hybrid",
            "claim_boundary": "structural nomination evidence only; rolling work and 136 B modeled state are charged, Python timing is not product-speed authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_local_gear_certificate_hybrid" else 1)
