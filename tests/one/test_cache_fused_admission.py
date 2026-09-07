from dataclasses import replace

from benchmarks.one.one_g02_full_ingest_fused_cache import _update_cases
from experiments.one.cache_fused_admission import (
    _sample_indices,
    classify_fused_cache_admission,
    observe_admitted,
)
from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.observe import observe


BLOCK = 4096
CHUNK = 64
MIN_RUN = 8


def _seed(size: int):
    source, cases = _update_cases(size)
    seed = observe_incremental(source, min_run=MIN_RUN, chunk_size=CHUNK, block_size=BLOCK)
    return source, cases, seed


def test_stratified_indices_are_bounded_unique_and_include_ends() -> None:
    for blocks in (1, 2, 7, 16, 64, 257):
        indices = _sample_indices(blocks, 8)
        assert len(indices) == min(blocks, 8)
        assert len(set(indices)) == len(indices)
        assert indices[0] == 0
        assert indices[-1] == blocks - 1
        assert all(0 <= index < blocks for index in indices)


def test_frozen_matrix_admission_classification() -> None:
    for size in (64 << 10, 256 << 10):
        _, cases, seed = _seed(size)
        expected = {
            "exact_repeat": True,
            "one_block_edit": True,
            "eight_block_edit": True,
            "shift_plus1": False,
            "independent_random": False,
        }
        for case, admitted in expected.items():
            decision = classify_fused_cache_admission(
                cases[case],
                previous=seed.cache,
                block_size=BLOCK,
                chunk_size=CHUNK,
                min_run=MIN_RUN,
            )
            assert decision.admitted is admitted, (size, case, decision)
            assert decision.sampled_blocks == 8
            assert decision.probe_read_bytes == 8 * BLOCK
            assert decision.probe_hash_bytes == decision.probe_read_bytes


def test_admitted_and_fallback_paths_equal_fresh_observer() -> None:
    for size in (64 << 10, 256 << 10):
        _, cases, seed = _seed(size)
        for case, current in cases.items():
            candidate = observe_admitted(
                current,
                previous=seed.cache,
                block_size=BLOCK,
                chunk_size=CHUNK,
                min_run=MIN_RUN,
            )
            oracle = observe(current, min_run=MIN_RUN, chunk_size=CHUNK)
            assert candidate.observation.runs == oracle.runs
            assert candidate.observation.reuse == oracle.reuse
            if candidate.admission.admitted:
                assert candidate.incremental is not None
                assert candidate.cache is not None
            else:
                assert candidate.incremental is None
                assert candidate.cache is None


def test_corrupt_payload_cannot_gain_semantic_authority_from_admission() -> None:
    source, cases, seed = _seed(64 << 10)
    # Keep the sampled identity intact but poison one cached feature seal. Admission is
    # allowed to say "try cache"; the underlying cache validator must still reject the
    # poisoned block and recompute it, preserving the fresh oracle.
    target = cases["exact_repeat"]
    blocks = list(seed.cache.blocks)
    poisoned = replace(blocks[0], seal=b"X" * 32)
    blocks[0] = poisoned
    poisoned_cache = replace(seed.cache, blocks=tuple(blocks))
    candidate = observe_admitted(
        target,
        previous=poisoned_cache,
        block_size=BLOCK,
        chunk_size=CHUNK,
        min_run=MIN_RUN,
    )
    oracle = observe(source, min_run=MIN_RUN, chunk_size=CHUNK)
    assert candidate.admission.admitted
    assert candidate.incremental is not None
    assert candidate.incremental.stats.recomputed_blocks >= 1
    assert candidate.observation.runs == oracle.runs
    assert candidate.observation.reuse == oracle.reuse


def test_incompatible_policy_falls_back_without_probe_or_cache_state() -> None:
    _, cases, seed = _seed(64 << 10)
    incompatible = replace(seed.cache, policy_id="other-policy")
    candidate = observe_admitted(
        cases["exact_repeat"],
        previous=incompatible,
        block_size=BLOCK,
        chunk_size=CHUNK,
        min_run=MIN_RUN,
    )
    assert not candidate.admission.compatible_previous
    assert not candidate.admission.admitted
    assert candidate.admission.sampled_blocks == 0
    assert candidate.admission.probe_read_bytes == 0
    assert candidate.cache is None
