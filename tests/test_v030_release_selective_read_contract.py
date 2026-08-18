from __future__ import annotations

"""Fast policy tests for the canonical selective-read evidence harness."""

from benchmarks import v030_release_performance as PERF
from benchmarks import v030_release_selective_read_canonical as S


def test_selective_read_reuses_frozen_runtime_targets_and_locality_ceiling() -> None:
    assert S.MAX_MEMBER_READ_AMP == 8.0
    assert PERF.TARGETS == (
        ("resemblance_hostile_v1", "01_shifted_versions"),
        ("neutral_hostile_v1", "05_logs_and_telemetry"),
        ("neutral_hostile_v1", "09_ml_artifacts"),
    )
    assert S.OPERATION_ORDER == (("member", "extract"), ("extract", "member"))


def test_selective_ratio_is_measurement_not_post_hoc_release_threshold() -> None:
    assert S._ratio(2.0, 4.0) == 0.5
    assert not hasattr(S, "MAX_SELECTIVE_TIME_RATIO")
    assert not hasattr(S, "MAX_SELECTIVE_RSS_RATIO")

    # Footnote: adding a threshold after observing CI would convert diagnostic timing into benchmark gaming.
    # A future numeric selective-read speed gate must be preregistered in release policy before its first run.
