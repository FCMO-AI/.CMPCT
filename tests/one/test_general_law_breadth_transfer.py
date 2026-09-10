from __future__ import annotations

from pathlib import Path

from benchmarks.one import one_g02_general_law_breadth_transfer as breadth


def test_preregistered_transfer_exercises_every_current_general_law_family(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(breadth, "OUT", tmp_path / "result.json")
    payload = breadth.run()

    assert payload["decision"] == "ADVANCE_GENERAL_LAW_BREADTH_ONLY"
    assert payload["gates"] == {
        "surprise_present": True,
        "fill_present": True,
        "exact_reuse_present": True,
        "add8_present": True,
        "xor_present": True,
        "whole_tree_semantics_exact": True,
        "deterministic_wire": True,
        "generic_reader_ontology_only": True,
    }
    assert set(payload["reader_ops"]) <= breadth.ALLOWED_OPS
    stats = payload["stats"]
    assert stats["surprise_roots"] > 0
    assert stats["fill_roots"] > 0
    assert stats["exact_reuse_roots"] > 0
    assert stats["add8_roots"] > 0
    assert stats["xor_roots"] > 0
    assert breadth.OUT.is_file()


def test_transfer_tree_keeps_relation_islands_predictor_local(tmp_path: Path):
    root = tmp_path / "tree"
    breadth._build_transfer_tree(root)

    add_base = (root / "00-add-base.bin").read_bytes()
    add_target = (root / "01-add-target.bin").read_bytes()
    xor_base = (root / "02-xor-base.bin").read_bytes()
    xor_target = (root / "03-xor-target.bin").read_bytes()
    exact_base = (root / "04-exact-base.bin").read_bytes()
    exact_copy = (root / "05-exact-copy.bin").read_bytes()

    assert len(add_base) == len(add_target)
    assert all(((left + 37) & 0xFF) == right for left, right in zip(add_base, add_target, strict=True))
    assert len(xor_base) == len(xor_target)
    assert all((left ^ 0xA5) == right for left, right in zip(xor_base, xor_target, strict=True))
    assert exact_base == exact_copy
    assert len(add_target) != len(xor_base)
    assert len(xor_target) != len(exact_base)
