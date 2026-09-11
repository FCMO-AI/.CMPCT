from __future__ import annotations

import ctypes

from benchmarks.one.one_g02_compact_observer_handoff_writer import (
    CONTROLS,
    FAMILIES,
    MIN_RICH_WINS,
    NO_REGRESSION_MAX,
    REPETITIONS,
    RICH,
    RICH_RATIO_MAX,
    SIZES,
    _build_native,
    _case,
    _same_writer_result,
    _writer_once,
)
from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import Segment
from experiments.one.native_observe import observe_native
from experiments.one.native_observe_view import observe_native_view
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program


def test_falsifier_contract_is_frozen_at_decision_scale() -> None:
    assert REPETITIONS == 15
    assert SIZES == (4 * 1024, 256 * 1024, 1 << 20)
    assert RICH == ("structured", "compressed_like", "long_runs")
    assert CONTROLS == ("random", "near_repeats")
    assert set(RICH + CONTROLS) == set(FAMILIES)
    assert RICH_RATIO_MAX == 0.90
    assert NO_REGRESSION_MAX == 1.05
    assert MIN_RICH_WINS == 2


def test_all_frozen_families_have_exact_requested_length() -> None:
    for size in (1, 31, 4096, 8193):
        for family in FAMILIES:
            source, target = _case(family, size)
            assert len(source) == size
            assert len(target) == size


def test_low_opportunity_controls_do_not_accidentally_become_exact_reuse_fixtures() -> None:
    # This is a premise check, not a performance threshold.  The near-repeat control
    # must remain resemblance-like while avoiding the earlier generator bug where the
    # same 64-byte chunk was repeated verbatim and therefore became a high-reuse case.
    for family in CONTROLS:
        _, target = _case(family, 64 * 1024)
        observation = observe_native(target)
        assert len(observation.runs) + len(observation.reuse) <= 8


def test_opportunity_rich_controls_really_include_positive_observer_work() -> None:
    for family in ("structured", "long_runs"):
        _, target = _case(family, 64 * 1024)
        observation = observe_native(target)
        assert len(observation.runs) + len(observation.reuse) > 0


def test_compact_handoff_preserves_small_whole_writer_semantics() -> None:
    size = 4096
    source, target = _case("structured", size)
    assert observe_native_view(target).materialize() == observe_native(target)

    admission_fn, segment_fn, td = _build_native()
    try:
        src_arr = (ctypes.c_uint8 * size).from_buffer_copy(source)
        dst_arr = (ctypes.c_uint8 * size).from_buffer_copy(target)
        seg_buf = (Segment * size)()
        eager = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, False)
        compact = _writer_once(admission_fn, segment_fn, source, target, src_arr, dst_arr, seg_buf, True)
        assert _same_writer_result(eager, compact)
        outputs, _ = evaluate(decode_program(compact["wire"]))
        assert outputs == {"previous": source, "current": target}
    finally:
        td.cleanup()
