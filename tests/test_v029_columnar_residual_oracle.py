from __future__ import annotations

"""Focused reversibility and accounting tests for the detached columnar residual oracle."""

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "entropygraph_v029_columnar_residual_oracle.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_columnar_residual_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _program(target_id: int, raw: bytes, target_len: int = 4096) -> dict:
    return {"target_id": target_id, "base_id": 0, "raw_delta": raw, "target_len": target_len}


def test_columnar_roundtrip_preserves_canonical_recipe_bytes() -> None:
    mod = _module()
    recipes = [
        b"\x00\x03abc\x01\x05\x0a",
        b"\x01\x00\x7f\x00\x02hi",
        b"\x00\x00",
    ]
    programs = [_program(index, raw) for index, raw in enumerate(recipes)]
    blob = mod._columnar_encode(programs)
    assert mod._columnar_decode(blob) == recipes


def test_columnar_locality_rejects_materialization_over_2x(monkeypatch) -> None:
    mod = _module()
    programs = [_program(0, b"\x00\x64" + b"x" * 100, target_len=16), _program(1, b"\x01\x00\x10", target_len=16)]
    group = {
        "programs": programs,
        "raw": b"".join(row["raw_delta"] for row in programs),
        "packed_physical_bytes": 1000,
    }
    row = mod._measure_group(group)
    assert row["admissible"] is False
    assert row["reason"] == "columnar-locality-bound"
    assert row["saving_bytes"] == 0


def test_columnar_saving_pays_conservative_transition_charge(monkeypatch) -> None:
    mod = _module()
    programs = [_program(0, b"\x01\x00\x10"), _program(1, b"\x01\x00\x10")]
    group = {
        "programs": programs,
        "raw": b"".join(row["raw_delta"] for row in programs),
        "packed_physical_bytes": 500,
    }
    monkeypatch.setattr(mod.PACK, "_compress_record", lambda raw, level=12: (mod.PACK.CODEC_RAW, b"z" * 10))
    row = mod._measure_group(group)
    expected = 500 - (mod.PH.size + 10) - (mod.COLUMNAR_GROUP_CHARGE + 2 * mod.COLUMNAR_MEMBER_CHARGE)
    assert row["saving_bytes"] == expected
    assert row["roundtrip_exact"] is True


def test_oracle_never_changes_attempt5_plan(monkeypatch) -> None:
    mod = _module()
    baseline = {"limit": 4096, "eligible": []}
    monkeypatch.setattr(mod, "_ORIGINAL_CHOOSE_PLAN", lambda rows: baseline)
    assert mod._choose_plan_with_oracle([]) is baseline
    assert mod._LAST_ORACLE["columnar_estimated_saving_bytes"] == 0
    assert mod._LAST_ORACLE["research_gate_pass"] is False
