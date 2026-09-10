from __future__ import annotations

import copy

import pytest

from benchmarks.one.one_genesis_physical_seal_identity import canonical_identity, receipt


def _seal(root: str = "/tmp/runner-a/gate") -> dict:
    rows = []
    for suite, count in (("neutral_hostile_v1", 10), ("resemblance_hostile_v1", 5)):
        for index in range(count):
            rows.append(
                {
                    "suite": suite,
                    "name": f"w{index:02d}",
                    "files": index + 1,
                    "logical_bytes": 1024 + index,
                    "tree_sha256": f"{index + (0 if suite == 'neutral_hostile_v1' else 32):064x}",
                }
            )
    return {
        "schema": "cmpct-one-genesis-physical-input-seal-v1",
        "claim_boundary": "exact physical input identity only; no contender measurement or scoring",
        "all_15_identities_exact": True,
        "work_root": root,
        "rows": rows,
    }


def test_scientific_digest_is_independent_of_absolute_work_root() -> None:
    a = receipt(_seal("/home/runner/work/a"))
    b = receipt(_seal("/mnt/ephemeral/completely-different-root"))
    assert a["scientific_identity_sha256"] == b["scientific_identity_sha256"]
    assert a["diagnostic_work_root"] != b["diagnostic_work_root"]
    assert a["work_root_in_scientific_digest"] is False


def test_scientific_digest_is_independent_of_row_order() -> None:
    a = _seal()
    b = copy.deepcopy(a)
    b["rows"] = list(reversed(b["rows"]))
    assert receipt(a)["scientific_identity_sha256"] == receipt(b)["scientific_identity_sha256"]


def test_tree_identity_mutation_changes_scientific_digest() -> None:
    a = _seal()
    b = copy.deepcopy(a)
    b["rows"][0]["tree_sha256"] = "f" * 64
    assert receipt(a)["scientific_identity_sha256"] != receipt(b)["scientific_identity_sha256"]


def test_missing_or_duplicate_workload_fails_closed() -> None:
    missing = _seal()
    missing["rows"].pop()
    with pytest.raises(RuntimeError, match="exactly 15"):
        canonical_identity(missing)

    duplicate = _seal()
    duplicate["rows"][-1] = copy.deepcopy(duplicate["rows"][0])
    with pytest.raises(RuntimeError, match="duplicate"):
        canonical_identity(duplicate)


def test_bad_suite_distribution_fails_closed() -> None:
    seal = _seal()
    seal["rows"][-1]["suite"] = "neutral_hostile_v1"
    seal["rows"][-1]["name"] = "extra-neutral"
    with pytest.raises(RuntimeError, match="suite distribution"):
        canonical_identity(seal)


def test_receipt_cannot_imply_measurement_or_scoring() -> None:
    result = receipt(_seal())
    assert result["contender_measurement_executed"] is False
    assert result["comparisons_executed"] is False
    assert result["scoring_executed"] is False
    assert result["winner_selected"] is False
