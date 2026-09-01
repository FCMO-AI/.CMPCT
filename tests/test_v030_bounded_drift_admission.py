from __future__ import annotations

from dataclasses import fields

from experiments import entropygraph_v030_bounded_drift_admission as A


def _obs(**overrides: object) -> A.CandidateObservation:
    values = {
        "physical_bytes": 900,
        "create_ns": 900,
        "max_decode_unit_bytes": 1024,
        "max_member_read_amplification": 2.0,
        "exact_tree_verified": True,
        "corruption_rejection_verified": True,
    }
    values.update(overrides)
    return A.CandidateObservation(**values)


def test_api_has_no_benchmark_or_path_identity_fields() -> None:
    names = {f.name for f in fields(A.CandidateObservation)}
    forbidden = {"path", "name", "workload", "benchmark", "hash", "sha256", "fixture"}
    assert not any(any(token in name.lower() for token in forbidden) for name in names)


def test_strict_internal_domination_is_admitted_without_release_credit() -> None:
    d = A.decide(bounded_drift=_obs(physical_bytes=899, create_ns=899), fallback=_obs(physical_bytes=900, create_ns=900))
    assert d.selected == "bounded_drift"
    assert d.reason == "strict_internal_domination"
    assert d.release_credit is False


def test_byte_tie_and_larger_candidate_keep_fallback() -> None:
    fallback = _obs(physical_bytes=900, create_ns=1000)
    assert A.decide(bounded_drift=_obs(physical_bytes=900, create_ns=1), fallback=fallback).selected == "fallback"
    assert A.decide(bounded_drift=_obs(physical_bytes=901, create_ns=1), fallback=fallback).selected == "fallback"


def test_runtime_regression_keeps_fallback_even_when_bytes_win() -> None:
    d = A.decide(
        bounded_drift=_obs(physical_bytes=800, create_ns=1001),
        fallback=_obs(physical_bytes=900, create_ns=1000),
    )
    assert d.selected == "fallback"
    assert d.reason == "runtime_regression"


def test_resource_integrity_and_corruption_debt_keep_fallback() -> None:
    fallback = _obs(physical_bytes=1000, create_ns=1000)
    cases = [
        _obs(physical_bytes=800, max_decode_unit_bytes=A.MAX_DECODE_UNIT_BYTES + 1),
        _obs(physical_bytes=800, max_member_read_amplification=A.MAX_MEMBER_READ_AMPLIFICATION + 0.001),
        _obs(physical_bytes=800, exact_tree_verified=False),
        _obs(physical_bytes=800, corruption_rejection_verified=False),
    ]
    for candidate in cases:
        assert A.decide(bounded_drift=candidate, fallback=fallback).selected == "fallback"


def test_invalid_measurements_fail_closed() -> None:
    fallback = _obs(physical_bytes=1000, create_ns=1000)
    assert A.decide(bounded_drift=_obs(physical_bytes=-1), fallback=fallback).selected == "fallback"
    assert A.decide(bounded_drift=_obs(create_ns=-1), fallback=fallback).selected == "fallback"
    assert A.decide(bounded_drift=_obs(max_member_read_amplification=-1.0), fallback=fallback).selected == "fallback"


def test_admission_does_not_claim_hidden_construction_or_external_authority() -> None:
    d = A.decide(bounded_drift=_obs(physical_bytes=800, create_ns=800), fallback=_obs(physical_bytes=900, create_ns=900))
    assert d.release_credit is False
    # The decision communicates only internal domination. It deliberately cannot claim ZIP,
    # Zstd, accepted-v0.29 common-fingerprint, native, Android, or recovery authority.
    assert "external" not in d.reason
    assert "release" not in d.reason
