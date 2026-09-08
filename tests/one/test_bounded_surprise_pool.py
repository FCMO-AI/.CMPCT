from __future__ import annotations

from hashlib import sha256

import pytest

from benchmarks.one.one_g02_end_to_end_direct_emitter_writer import _oracle_plan, _relation_cases
from benchmarks.one.one_g02_post_segment_control_cost_owner import _program_from_plan
from experiments.one.bounded_surprise_pool import pool_geometry, program_from_plan_pooled
from experiments.one.ir import Limits, OneError, Ref, Root
from experiments.one.range_vm import reconstruct_range_unverified
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _root(source: bytes) -> Root:
    return Root(Ref(0), len(source), sha256(source).hexdigest())


def test_pool_geometry_is_structurally_within_hard_node_cap_at_max_output():
    limits = Limits()
    for target_length in (1, 4 * 1024, 256 * 1024, 1 << 20, limits.max_output_bytes):
        geometry = pool_geometry(limits, target_length)
        assert geometry.groups_for_target <= geometry.max_groups
        assert geometry.worst_case_nodes_for_target <= limits.max_nodes
    maximum = pool_geometry(limits, limits.max_output_bytes)
    assert maximum.groups_for_target == maximum.max_groups
    assert maximum.worst_case_nodes_for_target == limits.max_nodes


def test_fragmented_1m_reproduces_legacy_node_overflow_and_pooled_program_validates():
    source, target, _enabled, _shift = _relation_cases(1 << 20)["fragmented_every96"]
    plan = _oracle_plan(source, target)
    previous = _root(source)
    digest = sha256(target).hexdigest()

    legacy, _depth = _program_from_plan(source, target, plan, previous, digest)
    assert len(legacy.nodes) > Limits().max_nodes
    with pytest.raises(OneError, match="node count exceeds declared limit"):
        legacy.validate_shape()

    pooled, stats = program_from_plan_pooled(source, target, plan, previous, digest)
    pooled.validate_shape()
    assert len(pooled.nodes) <= pooled.limits.max_nodes
    assert stats.groups <= stats.max_groups
    assert stats.max_groups == (pooled.limits.max_nodes - 2) // 2


def test_pooled_program_preserves_surprise_bytes_and_canonical_roundtrip():
    for size in (4 * 1024, 256 * 1024, 1 << 20):
        source, target, _enabled, _shift = _relation_cases(size)["fragmented_every96"]
        plan = _oracle_plan(source, target)
        previous = _root(source)
        digest = sha256(target).hexdigest()
        legacy, _depth = _program_from_plan(source, target, plan, previous, digest)
        pooled, _stats = program_from_plan_pooled(source, target, plan, previous, digest)

        legacy_surprise = sum(len(node.surprise) for node in legacy.nodes)
        pooled_surprise = sum(len(node.surprise) for node in pooled.nodes)
        assert pooled_surprise == legacy_surprise

        wire, _wire_stats = encode_program(pooled)
        decoded = decode_program(wire)
        outputs, _vm_stats = evaluate(decoded)
        assert outputs == {"previous": source, "current": target}


def test_pooled_1m_fragmented_range_cone_remains_bounded_and_exact():
    source, target, _enabled, _shift = _relation_cases(1 << 20)["fragmented_every96"]
    plan = _oracle_plan(source, target)
    pooled, _stats = program_from_plan_pooled(
        source,
        target,
        plan,
        _root(source),
        sha256(target).hexdigest(),
    )
    pooled.validate_shape()

    request = 4 * 1024
    for start in (0, (len(target) - request) // 2, len(target) - request):
        value, stats = reconstruct_range_unverified(pooled, "current", start, request)
        assert value == target[start : start + request]
        assert stats.authenticated is False
        assert stats.materialized_bytes / request <= 2.1
        assert stats.work_bytes / request <= 2.1


def test_pooling_rejects_malformed_plan_without_weakening_limits():
    source = b"abcd"
    target = b"wxyz"
    previous = _root(source)
    with pytest.raises(OneError, match="payload length mismatch"):
        program_from_plan_pooled(
            source,
            target,
            (("surprise", 0, 4, b"bad"),),
            previous,
            sha256(target).hexdigest(),
        )

    tiny = Limits(max_nodes=3)
    with pytest.raises(OneError, match="node limit too small"):
        program_from_plan_pooled(
            source,
            target,
            (("surprise", 0, 4, target),),
            previous,
            sha256(target).hexdigest(),
            limits=tiny,
        )
