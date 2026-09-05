from __future__ import annotations

import random

import pytest

from experiments.one.relation_bands import (
    RelationBandCapture,
    RelationBandIndex,
    capture_relation_bands,
)


def test_shifted_relation_features_preserve_band_identity() -> None:
    source = random.Random(91).randbytes(8192)
    target = b"X" + source[:-1]
    source_features = capture_relation_bands(source)
    target_features = capture_relation_bands(target)
    assert source_features is not None
    assert target_features is not None
    assert source_features.retained_feature_bytes == 80
    assert target_features.retained_feature_bytes == 80
    assert source_features.source_bands == target_features.bands_for_shift(1)


def test_band_index_nominates_content_relation_without_pair_identity() -> None:
    source = random.Random(92).randbytes(16384)
    target = b"X" + source[:-1]
    distractor = random.Random(93).randbytes(16384)
    index = RelationBandIndex()

    first = index.nominate_and_insert(0, capture_relation_bands(source))  # type: ignore[arg-type]
    noise = index.nominate_and_insert(1, capture_relation_bands(distractor))  # type: ignore[arg-type]
    relation = index.nominate_and_insert(2, capture_relation_bands(target))  # type: ignore[arg-type]

    assert first.candidate_source_ids == ()
    assert noise.candidate_source_ids == ()
    assert relation.candidate_source_ids == (0,)
    assert relation.candidate_overflow is False
    assert index.stats.objects_indexed == 3
    assert index.stats.emitted_candidate_pairs == 1


def test_saturated_false_pattern_bucket_fails_closed_and_bounds_state() -> None:
    data = b"Q" * 4096
    features = capture_relation_bands(data)
    assert features is not None
    index = RelationBandIndex(max_sources_per_signature=2, max_candidates_per_target=64)

    assert index.nominate_and_insert(0, features).candidate_source_ids == ()
    assert index.nominate_and_insert(1, features).candidate_source_ids == (0,)
    assert index.nominate_and_insert(2, features).candidate_source_ids == (0, 1)
    after_saturation = index.nominate_and_insert(3, features)

    assert after_saturation.candidate_source_ids == ()
    assert after_saturation.saturated_bucket_hits > 0
    assert index.stats.saturated_buckets == 4
    assert index.stats.retained_source_refs == 0


def test_candidate_fanout_overflow_is_explicit_not_silently_truncated() -> None:
    data = b"R" * 4096
    features = capture_relation_bands(data)
    assert features is not None
    index = RelationBandIndex(max_sources_per_signature=8, max_candidates_per_target=2)
    index.nominate_and_insert(0, features)
    index.nominate_and_insert(1, features)
    index.nominate_and_insert(2, features)
    result = index.nominate_and_insert(3, features)
    assert result.candidate_overflow is True
    assert result.candidate_source_ids == ()


def test_tiny_inputs_do_not_allocate_relation_features() -> None:
    assert capture_relation_bands(b"") is None
    assert capture_relation_bands(b"abc") is None
    assert capture_relation_bands(b"z" * 1023) is None
    assert capture_relation_bands(b"z" * 1024) is not None


def test_feed_contract_requires_one_contiguous_forward_pass() -> None:
    capture = RelationBandCapture(1024)
    capture.feed(0, 1)
    with pytest.raises(ValueError, match="contiguous forward pass"):
        capture.feed(2, 2)

    incomplete = RelationBandCapture(1024)
    with pytest.raises(ValueError, match="ended before declared length"):
        incomplete.finish()


def test_invalid_band_budgets_fail_closed() -> None:
    with pytest.raises(ValueError):
        RelationBandIndex(max_sources_per_signature=0)
    with pytest.raises(ValueError):
        RelationBandIndex(max_candidates_per_target=0)
    with pytest.raises(TypeError):
        capture_relation_bands(bytearray(b"x" * 1024))  # type: ignore[arg-type]
