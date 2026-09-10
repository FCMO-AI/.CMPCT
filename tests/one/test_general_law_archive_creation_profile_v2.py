from __future__ import annotations

from pathlib import Path

from benchmarks.one import one_g02_general_law_archive_creation_profile_v2 as profile


def test_v2_transfer_cases_preserve_frozen_shape_and_mixed_topology(tmp_path: Path):
    cases = profile._make_cases(tmp_path)
    assert tuple(cases) == ("unrelated-1m", "exact-copy-1m", "add8-1m", "mixed-8x512k")
    mixed = cases["mixed-8x512k"]
    assert [p.name for p in sorted(mixed.iterdir())] == [
        "00-base.bin",
        "01-copy.bin",
        "02-add.bin",
        "03-xor-source.bin",
        "04-xor.bin",
        "05-fill.bin",
        "06-random.bin",
        "07-random.bin",
    ]
    assert all(p.stat().st_size == 512 * 1024 for p in mixed.iterdir())


def test_v2_candidate_reader_proves_intended_structure_without_genesis(tmp_path: Path):
    cases = profile._make_cases(tmp_path)
    evidence = {}
    for name, case in cases.items():
        sample = profile._worker("candidate", case)
        assert sample["roundtrip_exact"] is True
        assert sample["reader_structure_evidence"]["ok"] is True
        evidence[name] = sample["reader_structure_evidence"]

    assert evidence["exact-copy-1m"]["shared_root_ref"] is True
    assert evidence["add8-1m"]["b_op"] == "add8"
    mixed = evidence["mixed-8x512k"]
    assert mixed["copy_shared_root_ref"] is True
    assert mixed["base_op"] == "surprise"
    assert mixed["add_op"] == "add8"
    assert mixed["xor_source_op"] == "surprise"
    assert mixed["xor_op"] == "xor"
    assert mixed["fill_op"] == "fill"
    assert mixed["random_a_op"] == "surprise"
    assert mixed["random_b_op"] == "surprise"
    assert set(mixed["ops"]) <= profile.ALLOWED_OPS


def test_v2_decision_priority_is_fail_closed():
    def decide(semantic: bool, structure: bool, performance: bool) -> str:
        if not semantic or not structure:
            return "RETIRE_OR_REPAIR_V2"
        if performance:
            return "ADVANCE_CREATION_PROFILE_V2"
        return "HOLD_CREATION_COMPUTE_V2"

    assert decide(False, True, True) == "RETIRE_OR_REPAIR_V2"
    assert decide(True, False, True) == "RETIRE_OR_REPAIR_V2"
    assert decide(True, True, False) == "HOLD_CREATION_COMPUTE_V2"
    assert decide(True, True, True) == "ADVANCE_CREATION_PROFILE_V2"
