from benchmarks.one.one_g02_full_ingest_fused_cache import (
    BLOCK_SIZE,
    CHUNK_SIZE,
    MIN_RUN,
    SIZES,
    _update_cases,
)
from experiments.one.cache_fused_observe import observe_incremental
from experiments.one.observe import observe


def _changed_positions(a: bytes, b: bytes) -> list[int]:
    assert len(a) == len(b)
    return [index for index, (left, right) in enumerate(zip(a, b)) if left != right]


def test_full_ingest_productive_case_geometry_is_exact() -> None:
    """Frozen timing labels must describe the mutations they actually measure."""
    for size in SIZES:
        source, cases = _update_cases(size)
        assert len(source) == size
        assert cases["exact_repeat"] == source

        one = _changed_positions(source, cases["one_block_edit"])
        assert len(one) == 1
        assert len({position // BLOCK_SIZE for position in one}) == 1

        eight = _changed_positions(source, cases["eight_block_edit"])
        expected_blocks = min(8, size // BLOCK_SIZE)
        assert len(eight) == expected_blocks
        assert len({position // BLOCK_SIZE for position in eight}) == expected_blocks

        assert len(cases["shift_plus1"]) == size
        assert len(cases["independent_random"]) == size
        assert cases["shift_plus1"] != source
        assert cases["independent_random"] != source


def test_full_ingest_cache_change_cones_match_case_labels() -> None:
    """The productive gate must really exercise 0/1/8 positional changed blocks."""
    for size in SIZES:
        source, cases = _update_cases(size)
        seed = observe_incremental(
            source,
            min_run=MIN_RUN,
            chunk_size=CHUNK_SIZE,
            block_size=BLOCK_SIZE,
        )
        block_count = size // BLOCK_SIZE
        expected_recomputed = {
            "exact_repeat": 0,
            "one_block_edit": 1,
            "eight_block_edit": min(8, block_count),
        }
        for case, recomputed in expected_recomputed.items():
            candidate = observe_incremental(
                cases[case],
                previous=seed.cache,
                min_run=MIN_RUN,
                chunk_size=CHUNK_SIZE,
                block_size=BLOCK_SIZE,
            )
            oracle = observe(cases[case], min_run=MIN_RUN, chunk_size=CHUNK_SIZE)
            assert candidate.observation.runs == oracle.runs
            assert candidate.observation.reuse == oracle.reuse
            assert candidate.stats.recomputed_blocks == recomputed
            assert candidate.stats.reused_blocks == block_count - recomputed
