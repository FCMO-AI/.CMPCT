from __future__ import annotations

from datetime import datetime

from benchmarks.one.one_genesis_gate_executor_preflight import (
    GATE_TZ,
    _git_head,
    _validate_authorities,
    build_plan,
)


def test_preflight_records_harness_head_and_executes_no_gate_work():
    head = _git_head()
    result = build_plan(head, now=datetime(2026, 9, 10, 23, 59, tzinfo=GATE_TZ))
    assert result["decision"] == "EXECUTOR_PREFLIGHT_READY", result["errors"]
    assert result["candidate_sha"] == head
    assert result["harness_head"] == head
    assert result["candidate_head_exact"] is True
    assert result["authority"]["workload_count"] == 15
    assert result["authority"]["suite_counts"] == {
        "neutral_hostile_v1": 10,
        "resemblance_hostile_v1": 5,
    }
    assert result["gate_clock"]["gate_open"] is False
    assert result["contender_encoding_executed"] is False
    assert result["comparator_encoding_executed"] is False
    assert result["scoring_executed"] is False
    assert result["winner_selected"] is False


def test_clock_opening_changes_permission_state_not_execution_state():
    head = _git_head()
    result = build_plan(head, now=datetime(2026, 9, 11, 0, 0, tzinfo=GATE_TZ))
    assert result["decision"] == "EXECUTOR_PREFLIGHT_READY", result["errors"]
    assert result["gate_clock"]["gate_open"] is True
    # Opening the date boundary must not itself execute or score any contender.
    assert result["contender_encoding_executed"] is False
    assert result["comparator_encoding_executed"] is False
    assert result["scoring_executed"] is False
    assert result["winner_selected"] is False


def test_frozen_candidate_may_differ_from_harness_head_without_substitution():
    head = _git_head()
    candidate = ("0" if head[0] != "0" else "1") + head[1:]
    result = build_plan(candidate, now=datetime(2026, 9, 10, 12, 0, tzinfo=GATE_TZ))
    assert result["decision"] == "EXECUTOR_PREFLIGHT_READY", result["errors"]
    assert result["candidate_sha"] == candidate
    assert result["harness_head"] == head
    assert result["candidate_head_exact"] is False
    assert result["candidate_identity_binding"].startswith("adapter-manifest")


def test_non_hex_candidate_fails_closed():
    errors, _ = _validate_authorities("not-a-commit")
    assert any("40 hexadecimal" in error for error in errors)
