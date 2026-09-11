from __future__ import annotations

import math
from pathlib import Path

from benchmarks.one.one_g03_block_adaptive_statistical_law import (
    ALPHA,
    ALPHABET,
    BLOCK_BYTES,
    FRAME_BYTES_PER_BLOCK,
    MODEL_STATE_BYTES,
    kt_block_bits,
    observe_workload,
)


def _sequential_reference(data: bytes) -> float:
    if not data:
        return 0.0
    bits = 8.0
    counts: dict[tuple[int, int], int] = {}
    totals: dict[int, int] = {}
    for left, right in zip(data, data[1:]):
        count = counts.get((left, right), 0)
        total = totals.get(left, 0)
        probability = (count + ALPHA) / (total + ALPHABET * ALPHA)
        bits -= math.log2(probability)
        counts[(left, right)] = count + 1
        totals[left] = total + 1
    return bits


def test_kt_count_identity_matches_sequential_reader_update() -> None:
    for data in (b"A", b"AAAAAA", b"ABABABAB", bytes(range(32)), b"ABCABCABCABC"):
        assert math.isclose(kt_block_bits(data), _sequential_reference(data), rel_tol=0.0, abs_tol=1e-9)


def test_block_observer_charges_fixed_resets_and_exact_source_bytes(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    payload = b"A" * (BLOCK_BYTES + 17)
    (root / "a.bin").write_bytes(payload)
    (root / "empty.bin").write_bytes(b"")

    result = observe_workload(root)

    assert result["regular_files"] == 2
    assert result["measured_bytes"] == len(payload)
    assert result["observation_passes"] == 1
    assert result["nonempty_blocks"] == 2
    assert result["framing_charge_bytes"] == 2 * FRAME_BYTES_PER_BLOCK
    assert result["stored_learned_model_bytes"] == 0
    assert result["bounded_model_state_bytes"] == MODEL_STATE_BYTES
    assert result["modeled_payload_bytes"] < result["measured_bytes"]
