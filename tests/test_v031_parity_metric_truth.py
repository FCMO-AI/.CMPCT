"""The real r24 release comparator must never silently pass invalid measurements.

Independent adversarial court: frozen numeric inputs, actual public evaluator entrypoint,
no duplicate comparison algorithm, and no change to the release threshold.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


CHECKER = Path(__file__).resolve().parents[1] / "tools" / "check_performance_regression.py"
spec = importlib.util.spec_from_file_location("r24_release_comparator_under_test", CHECKER)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _report():
    metric = {"bytes": 1000, "create_s_median": 0.1, "extract_s_median": 0.07}
    return {
        "schema": "cmpct-zip-parity-v1",
        "corpora": {
            "independent_test": {
                "logical_bytes": 1000,
                "library": {"cmpct": copy.deepcopy(metric)},
                "cli": {"cmpct": copy.deepcopy(metric)},
            }
        },
    }


def _invoke(tmp_path, monkeypatch, base, candidate):
    base_path = tmp_path / "base.json"
    candidate_path = tmp_path / "candidate.json"
    # JSON allows NaN and Infinity in the default Python producer/consumer.
    # Deliberately preserve those malformed tokens as a hostile evidence source.
    base_path.write_text(json.dumps(base), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        str(CHECKER), "--base", str(base_path), "--candidate", str(candidate_path)
    ])
    return gate.main()


@pytest.mark.parametrize("side,layer,key,invalid", [
    ("candidate", "library", "create_s_median", float("nan")),
    ("base", "cli", "extract_s_median", float("nan")),
    ("base", "library", "create_s_median", float("inf")),
    ("candidate", "cli", "extract_s_median", float("-inf")),
    ("base", "library", "create_s_median", 0),
    ("base", "cli", "extract_s_median", -0.2),
    ("candidate", "library", "extract_s_median", -0.02),
    ("candidate", "library", "extract_s_median", False),
    ("base", "cli", "create_s_median", "0.1"),
    ("candidate", "library", "bytes", -1),
    ("candidate", "cli", "bytes", 0),
    ("base", "library", "bytes", True),
    ("candidate", "library", "bytes", 999.5),
    ("base", "cli", "bytes", "1000"),
])
def test_invalid_evidence_fails_closed(tmp_path, monkeypatch, side, layer, key, invalid):
    base = _report()
    candidate = _report()
    {"base": base, "candidate": candidate}[side]["corpora"]["independent_test"][layer]["cmpct"][key] = invalid
    with pytest.raises(ValueError, match="expected"):
        _invoke(tmp_path, monkeypatch, base, candidate)


@pytest.mark.parametrize("side", ["base", "candidate"])
def test_zero_corpus_cannot_vacuously_pass(tmp_path, monkeypatch, side):
    base, candidate = _report(), _report()
    {"base": base, "candidate": candidate}[side]["corpora"] = {}
    with pytest.raises(ValueError, match="at least one corpus"):
        _invoke(tmp_path, monkeypatch, base, candidate)


def test_valid_same_source_passes(tmp_path, monkeypatch, capsys):
    base, candidate = _report(), _report()
    assert _invoke(tmp_path, monkeypatch, base, candidate) == 0
    assert "Result: **PASS**" in capsys.readouterr().out


@pytest.mark.parametrize("metric,value,expected", [
    ("bytes", 1001, 1),          # strict zero-byte size tolerance
    ("bytes", 1000, 0),
    ("bytes", 999, 0),
    ("create_s_median", 0.107, 1),  # both +7% and +7ms
    ("create_s_median", 0.102, 0),  # +2ms < 3ms
    ("create_s_median", 0.104, 0),  # +4% < 5%
])
def test_valid_comparator_promotion_law_unchanged(
    tmp_path, monkeypatch, capsys, metric, value, expected
):
    base, candidate = _report(), _report()
    candidate["corpora"]["independent_test"]["library"]["cmpct"][metric] = value
    assert _invoke(tmp_path, monkeypatch, base, candidate) == expected
    assert ("Result: **FAIL**" if expected else "Result: **PASS**") in capsys.readouterr().out


def test_corpus_identity_set_change_remains_rejected(tmp_path, monkeypatch, capsys):
    base, candidate = _report(), _report()
    candidate["corpora"]["renamed"] = candidate["corpora"].pop("independent_test")
    assert _invoke(tmp_path, monkeypatch, base, candidate) == 1
    assert "corpus set changed" in capsys.readouterr().out


@pytest.mark.parametrize("side", ["base", "candidate"])
def test_missing_compared_layer_cannot_pass(tmp_path, monkeypatch, side):
    base, candidate = _report(), _report()
    {"base": base, "candidate": candidate}[side]["corpora"]["independent_test"].pop("cli")
    with pytest.raises(ValueError, match="missing CMPCT"):
        _invoke(tmp_path, monkeypatch, base, candidate)


def test_nonfloat_json_tokens_rejected_without_timing_comparison(tmp_path, monkeypatch):
    base, candidate = _report(), _report()
    candidate["corpora"]["independent_test"]["library"]["cmpct"]["extract_s_median"] = None
    with pytest.raises(ValueError, match="expected finite positive"):
        _invoke(tmp_path, monkeypatch, base, candidate)
