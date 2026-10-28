from __future__ import annotations

import pytest

from cmpct.mosaic import mosaic_delta_decode, mosaic_delta_encode, used_base_slots
from cmpct.resemblance import delta_encode


def test_mosaic_reconstructs_from_two_independent_roots():
    left = (b"LEFT-BRANCH-SECTION|" * 9000)[:160_000]
    right = (b"RIGHT-BRANCH-SECTION|" * 9000)[:160_000]
    target = left[:80_000] + b"MERGE|" * 17 + right[80_000:]
    result = mosaic_delta_encode([left, right], target)
    restored = mosaic_delta_decode([left, right], result.payload, expected_size=len(target))
    assert restored == target
    assert set(used_base_slots(result.stats)) == {0, 1}
    assert result.stats.copied_bytes > len(target) * 0.9


def test_mosaic_is_deterministic_and_flat():
    roots = [
        (f"root={index}|".encode() * 30000)[:180_000]
        for index in range(3)
    ]
    target = roots[0][:60_000] + roots[1][60_000:120_000] + roots[2][120_000:]
    first = mosaic_delta_encode(roots, target)
    second = mosaic_delta_encode(roots, target)
    assert first == second
    assert mosaic_delta_decode(roots, first.payload, expected_size=len(target)) == target
    # Footnote: used roots are slots in a caller-provided direct-root set.  The payload has no opcode
    # that can identify or recurse through another delta object, so dependency depth is structurally 1.
    assert set(used_base_slots(first.stats)) == {0, 1, 2}


def test_mosaic_rejects_missing_and_out_of_bounds_roots():
    base = b"A" * 8192
    result = mosaic_delta_encode([base], base)
    with pytest.raises(ValueError):
        mosaic_delta_decode([], result.payload, expected_size=len(base))
    with pytest.raises(ValueError):
        mosaic_delta_encode([b"x" * 1024] * 5, b"target", max_bases=4)
    with pytest.raises(ValueError):
        mosaic_delta_encode([b"x" * 4096, b"y" * 4096], b"target", max_source_index=4096)


def test_malformed_mosaic_copy_fails_closed():
    # tag=2, base_slot=4, offset=0, length=1; only one base exists.
    with pytest.raises(ValueError):
        mosaic_delta_decode([b"x"], b"\x02\x04\x00\x01", max_output=1024)
    # tag=2, base_slot=0, offset=127, length=127; source is only one byte.
    with pytest.raises(ValueError):
        mosaic_delta_decode([b"x"], b"\x02\x00\x7f\x7f", max_output=1024)


def test_source_checksum_collision_fanout_is_bounded_and_exact():
    roots = [b"A" * 96_000, b"A" * 96_000, b"A" * 96_000, b"B" * 96_000]
    target = b"A" * 48_000 + b"B" * 48_000
    result = mosaic_delta_encode(roots, target, max_matches_per_key=3)
    assert mosaic_delta_decode(roots, result.payload, expected_size=len(target)) == target
    assert result.stats.indexed_source_bytes == sum(map(len, roots))


def test_single_parent_control_does_not_require_mosaic_to_be_correct():
    best = b"prefix|" * 20000
    target = best[:50_000] + b"small edit" + best[50_010:]
    distractor = b"unrelated|" * 15000
    single = delta_encode(best, target)
    mosaic = mosaic_delta_encode([best, distractor], target)
    assert mosaic_delta_decode([best, distractor], mosaic.payload, expected_size=len(target)) == target
    # Footnote: this is intentionally not a size assertion.  The benchmark portfolio is responsible
    # for rejecting a multi-root representation when the best single-parent representation is cheaper.
    assert single.stats.copied_bytes > len(target) * 0.8
