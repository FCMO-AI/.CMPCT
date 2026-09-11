from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.one.one_genesis_candidate_boundary_validator import validate_candidate_receipt


def _manifest() -> dict:
    return json.loads(Path("benchmarks/one/genesis_one_candidate_boundary_v1.json").read_text())


def _eligible() -> dict:
    return {
        "candidate_sha": "1" * 40,
        "surface": "experiments/one/future_complete_product.py",
        "product_claims": {
            "general_arbitrary_tree": True,
            "automatic_law_plus_surprise": True,
            "complete_persistent_bytes_counted": True,
            "whole_reconstruction_exact": True,
            "reader_discovery": False,
            "hidden_legacy_codec": False,
            "same_resource_boundary_as_comparators": True,
            "candidate_sha_frozen_before_execution": True,
        },
        "metric_families": {
            "stored_bytes": "measured",
            "creation": "measured",
            "whole_read": "measured",
            "selective_access": "unavailable",
            "semantics": "measured",
            "reader_burden": "unavailable",
        },
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
    }


def test_structurally_complete_future_boundary_can_pass_without_scoring():
    result = validate_candidate_receipt(_eligible(), _manifest())
    assert result["status"] == "CANDIDATE_BOUNDARY_STRUCTURALLY_ELIGIBLE"
    assert "performance" in result["claim_boundary"]


def test_exact_add8_archive_cannot_be_promoted_as_general_candidate():
    receipt = _eligible()
    receipt["surface"] = "experiments/one/authenticated_law_archive.py"
    with pytest.raises(RuntimeError, match="ineligible standalone"):
        validate_candidate_receipt(receipt, _manifest())


def test_surprise_only_envelope_cannot_be_promoted_as_best_one():
    receipt = _eligible()
    receipt["surface"] = "experiments/one/archive_envelope.py"
    with pytest.raises(RuntimeError, match="ineligible standalone"):
        validate_candidate_receipt(receipt, _manifest())


def test_missing_complete_persistent_byte_accounting_fails_closed():
    receipt = _eligible()
    receipt["product_claims"]["complete_persistent_bytes_counted"] = False
    with pytest.raises(RuntimeError, match="complete_persistent_bytes_counted"):
        validate_candidate_receipt(receipt, _manifest())


def test_reader_discovery_or_hidden_codec_is_forbidden():
    receipt = _eligible()
    receipt["product_claims"]["reader_discovery"] = True
    with pytest.raises(RuntimeError, match="reader discovery"):
        validate_candidate_receipt(receipt, _manifest())
    receipt = _eligible()
    receipt["product_claims"]["hidden_legacy_codec"] = True
    with pytest.raises(RuntimeError, match="hidden legacy"):
        validate_candidate_receipt(receipt, _manifest())


def test_resource_boundary_must_match_comparators():
    receipt = _eligible()
    receipt["product_claims"]["same_resource_boundary_as_comparators"] = False
    with pytest.raises(RuntimeError, match="same_resource_boundary_as_comparators"):
        validate_candidate_receipt(receipt, _manifest())


def test_scoring_before_boundary_certification_fails_closed():
    receipt = _eligible()
    receipt["scoring_executed"] = True
    with pytest.raises(RuntimeError, match="precede Genesis"):
        validate_candidate_receipt(receipt, _manifest())
