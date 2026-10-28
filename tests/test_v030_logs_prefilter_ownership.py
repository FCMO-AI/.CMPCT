from __future__ import annotations

from experiments import entropygraph_v030_release_product as RELEASE
from experiments import entropygraph_v030_release_product_logs_candidate as LOGS_CANDIDATE


def test_release_facade_does_not_overwrite_promoted_logs_prefilter() -> None:
    """The release facade must not mutate the promoted candidate's newer admission proof.

    Full-suite import order previously replaced the deterministic candidate prefilter with
    an older facade-local implementation. That made isolated candidate tests pass while
    the complete release correctness gate failed. Keep ownership explicit so future
    facade imports cannot silently downgrade the candidate implementation again.
    """
    assert LOGS_CANDIDATE.logs_source_prefilter.__module__ == LOGS_CANDIDATE.__name__
    assert LOGS_CANDIDATE.logs_source_prefilter is not RELEASE._logs_streaming_source_prefilter
