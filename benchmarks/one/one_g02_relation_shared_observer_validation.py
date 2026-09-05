"""ONE-G0.2 generator-distinct validation: nominate relation proof from existing reuse evidence.

Preregistered after an exploratory causal replay, before these validation generators run.

The fixed-band relation nominator is cheap but a four-edit hostile construction can defeat
all four public bands while the exact relation proof still accepts the pair. Rather than
building a second, more elaborate relation index, this validation asks whether the source
identity already produced by ONE's promoted Gear/minimizer exact-reuse observer is enough
to nominate relation proof in the regimes where the relation is economically meaningful.

No new content index is created here. We replay the exact Python reference semantics of the
current rightmost-minimum Gear observer, but expose one fact it already knows internally:
a successful exact reuse audition whose source lies in the prior object and target lies in
the current object. That cross-object event nominates the pair for the existing sparse
relation falsifier + exact safe proof.

Exploratory envelope to validate on new seeds:
- ordinary shifted, quarter-damaged and four-fixed-band-hostile positives are nominated at
  every tested size;
- fragmented-every96 positives are nominated from 16 KiB upward, while 4/8 KiB remain an
  explicit small-regime opportunity debt;
- every32 fragmented and independent-random exact-proof negatives produce no cross-object
  exact-reuse nomination.

Validation sizes: 4, 8, 16, 64 and 256 KiB; three generator-distinct seeds each. The exact
safe relation dispatcher is the oracle. The validation advances shared-observer nomination
iff every exact-proof positive outside the predeclared 4/8 KiB fragmented96 debt is
nominated, every hostile-band positive is nominated even at 4/8 KiB, and no exact-proof
negative is nominated. The small fragmented debt is reported, never hidden.

Claim boundary: structural/concept-compression evidence only. Python timing is not product
speed authority; no stored-byte, reader, comparator or release claim is granted.
"""
from __future__ import annotations

from collections import OrderedDict, deque
import ctypes
import json
import os
import random
import subprocess
import tempfile
from pathlib import Path

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _U64_MASK, _extend_left, _extend_right,
    GEAR_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW,
)

SIZES = (4*1024, 8*1024, 16*1024, 64*1024, 256*1024)
SEEDS = (3, 17, 41)
MINIMIZER_SPAN = 4096
LOCAL_ENTRIES = 64


class Result(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64), ("zero_shift_matches", ctypes.c_uint64),
        ("coverage_compared_bytes", ctypes.c_uint64), ("best_hits", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64), ("proof_attempts", ctypes.c_uint64),
        ("exact_proofs", ctypes.c_uint64), ("proof_compared_bytes", ctypes.c_uint64),
        ("strata_with_support", ctypes.c_uint64),
    ]


def _build_safe():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-shared-observer-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
        str(here / "one_g02_shift_branch_bound_relation_restrict_kernel.c"),
        str(here / "one_g02_shift_relation_safe_dispatch_kernel.c"), "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    c = ctypes.CDLL(str(lib))
    fn = c.one_g02_shift_relation_safe_dispatch
    fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                   ctypes.c_size_t, ctypes.POINTER(Result)]
    fn.restype = ctypes.c_int
    return fn, td


def _shifted(source: bytes, *, spacing: int | None = None, damage_quarter: bool = False) -> bytes:
    target = bytearray(b"X" + source[:-1])
    if spacing:
        for j in range(16, len(target), spacing):
            target[j] ^= 0xA7
    if damage_quarter:
        lo = len(target)//3
        hi = min(len(target), lo + len(target)//4)
        for j in range(lo, hi):
            target[j] ^= (0x6B + j*13) & 0xFF
    return bytes(target)


def _band_positions(n: int) -> tuple[int, ...]:
    return tuple(max(2, min(n-3, ((i+1)*n)//17)) for i in range(16))


def _hostile_band_break(source: bytes) -> bytes:
    target = bytearray(b"X" + source[:-1])
    positions = _band_positions(len(source))
    for band in range(4):
        target[positions[band*4] + 1] ^= 0x5A
    return bytes(target)


def _cases(size: int, seed: int) -> dict[str, tuple[bytes, bytes]]:
    source = random.Random(51000 + size*29 + seed*1009).randbytes(size)
    return {
        "shift_plus1": (source, _shifted(source)),
        "damage_quarter": (source, _shifted(source, damage_quarter=True)),
        "fragmented_every96": (source, _shifted(source, spacing=96)),
        "hostile_fixed_bands": (source, _hostile_band_break(source)),
        "fragmented_every32": (source, _shifted(source, spacing=32)),
        "independent_random": (source, random.Random(52000 + size*31 + seed*1013).randbytes(size)),
    }


def _safe_result(fn, source: bytes, target: bytes) -> tuple[bool, int, int]:
    a = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    b = (ctypes.c_uint8 * len(target)).from_buffer_copy(target)
    out = Result()
    rc = fn(a, b, len(source), ctypes.byref(out))
    if rc < 0:
        raise RuntimeError(f"safe relation dispatcher failed: {rc}")
    return int(out.exact_proofs) >= 4, int(out.best_shift), int(out.exact_proofs)


def _cross_object_reuse_nominations(source: bytes, target: bytes) -> tuple[int, int, int]:
    data = source + target
    boundary = len(source)
    global_index: dict[int, int] = {}
    local_index: OrderedDict[int, int] = OrderedDict()
    minima: deque[tuple[int, int]] = deque()
    minimizer_enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    peak_queue = 0
    last_emitted_position = -1
    h = 0
    run_value = data[0]
    run_length = 0
    covered_until = 0
    cross_auditions = 0
    cross_exact = 0

    def audition(start: int, prior: int | None) -> None:
        nonlocal covered_until, cross_auditions, cross_exact
        if prior is None or start < covered_until:
            return
        is_cross = prior < boundary <= start
        if is_cross:
            cross_auditions += 1
        if data[prior:prior+WINDOW] != data[start:start+WINDOW]:
            return
        left, _ = _extend_left(data, prior, start, covered_until)
        right, _ = _extend_right(data, prior, start)
        target_start = max(start-left, covered_until)
        target_end = start+right
        if target_end > target_start:
            if is_cross:
                cross_exact += 1
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
            prior = local_index.get(h)
            audition(start, prior)
            if prior is None:
                local_index[h] = start
                local_index.move_to_end(h)
                if len(local_index) > LOCAL_ENTRIES:
                    local_index.popitem(last=False)

        if not minimizer_enabled:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        peak_queue = max(peak_queue, len(minima))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        if first_valid < WINDOW - 1:
            continue
        signal, anchor_position = minima[0]
        anchor_start = anchor_position + 1 - WINDOW
        if anchor_position == last_emitted_position:
            continue
        last_emitted_position = anchor_position
        prior = global_index.get(signal)
        audition(anchor_start, prior)
        if prior is None and len(global_index) < GEAR_MAX_INDEX_ENTRIES:
            global_index[signal] = anchor_start

    return cross_exact, cross_auditions, peak_queue


def run() -> dict[str, object]:
    safe, td = _build_safe()
    rows = []
    required_positive_misses = []
    allowed_small_debt = []
    false_nominations = []
    try:
        for size in SIZES:
            for seed in SEEDS:
                for name, (source, target) in _cases(size, seed).items():
                    enabled, best_shift, proofs = _safe_result(safe, source, target)
                    cross_exact, cross_auditions, peak_queue = _cross_object_reuse_nominations(source, target)
                    nominated = cross_exact > 0
                    allowed_debt = enabled and name == "fragmented_every96" and size <= 8*1024
                    required = enabled and not allowed_debt
                    if required and not nominated:
                        required_positive_misses.append((size, seed, name))
                    if allowed_debt and not nominated:
                        allowed_small_debt.append((size, seed, name))
                    if not enabled and nominated:
                        false_nominations.append((size, seed, name))
                    rows.append({
                        "relation_bytes": size, "seed": seed, "case": name,
                        "exact_relation_enabled": enabled, "best_shift": best_shift,
                        "exact_proofs": proofs, "cross_object_exact_reuse_nominations": cross_exact,
                        "cross_object_reuse_auditions": cross_auditions,
                        "pair_nominated": nominated, "predeclared_small_fragment_debt": allowed_debt,
                        "peak_minimizer_queue_entries": peak_queue,
                    })
        passed = not required_positive_misses and not false_nominations
        return {
            "schema": "cmpct-one-g02-relation-shared-observer-validation-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES), "frozen_seeds": list(SEEDS),
            "decision": "advance_shared_observer_pair_nomination" if passed else "reject_shared_observer_pair_nomination_envelope",
            "required_positive_misses": required_positive_misses,
            "predeclared_small_fragment_misses": allowed_small_debt,
            "false_nominations": false_nominations,
            "claim_boundary": "structural concept-compression evidence only; existing observer source identity is reused, Python timing is not product-speed authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_shared_observer_pair_nomination" else 1)
