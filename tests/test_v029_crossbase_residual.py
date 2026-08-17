from __future__ import annotations

"""Focused invariants for the cross-base residual-packing experiment."""

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "entropygraph_v029_crossbase_residual.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_crossbase_residual_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _program(target_id: int, base_id: int, raw: bytes, target_len: int = 4096) -> dict:
    return {
        "target_id": target_id,
        "base_id": base_id,
        "record_id": target_id,
        "target_len": target_len,
        "expected": b"x" * 32,
        "raw_delta": raw,
        "raw_delta_bytes": len(raw),
        "separate_physical_bytes": 300,
    }


def test_crossbase_plan_can_mix_direct_bases_without_changing_member_identity(monkeypatch) -> None:
    mod = _module()
    programs = [
        _program(1, 0, b"A" * 128),
        _program(3, 2, b"A" * 128),
        _program(5, 4, b"A" * 128),
    ]
    monkeypatch.setattr(mod.PACK, "_compress_record", lambda raw, level=12: (mod.PACK.CODEC_RAW, raw[:32]))
    plan = mod._plan_crossbase(programs, 4096, "target")
    assert plan["mixed_base_groups"] == 1
    assert plan["mixed_base_members"] == 3
    assert plan["max_amp"] <= mod.PACK.MAX_ADDITIONAL_RECIPE_AMP
    assert [row["base_id"] for row in plan["eligible"][0]["programs"]] == [0, 2, 4]


def test_crossbase_plan_still_rejects_member_overread_above_2x(monkeypatch) -> None:
    mod = _module()
    programs = [
        _program(1, 0, b"A" * 900, target_len=1000),
        _program(3, 2, b"B" * 900, target_len=1000),
        _program(5, 4, b"C" * 900, target_len=1000),
    ]
    monkeypatch.setattr(mod.PACK, "_compress_record", lambda raw, level=12: (mod.PACK.CODEC_RAW, raw[:16]))
    plan = mod._plan_crossbase(programs, 4096, "target")
    assert plan["max_amp"] <= 2.0
    assert all(len(group["raw"]) <= 2000 for group in plan["eligible"])


def test_crossbase_chooser_keeps_attempt5_on_equal_net_even_with_lower_crossbase_amp(monkeypatch) -> None:
    mod = _module()
    programs = [_program(1, 0, b"A" * 64), _program(3, 2, b"B" * 64)]
    baseline = {"limit": 4096, "groups": [], "eligible": [], "net": 500, "max_amp": 1.5}
    monkeypatch.setattr(mod, "_ORIGINAL_CHOOSE_PLAN", lambda rows: baseline)
    monkeypatch.setattr(
        mod, "_plan_crossbase",
        lambda rows, limit, strategy: {
            "strategy": strategy, "limit": limit, "groups": [], "eligible": [], "net": 500,
            "max_amp": 0.5, "mixed_base_groups": 1, "mixed_base_members": 2,
        },
    )
    assert mod._choose_plan_crossbase(programs) is baseline
    assert mod._LAST_PLAN_DIAG["selected_crossbase_plan"] is False
    assert mod._LAST_PLAN_DIAG["strategy"] == "attempt5-same-base-fallback"


def test_crossbase_chooser_records_causal_mixed_base_diagnostics(monkeypatch) -> None:
    mod = _module()
    programs = [_program(1, 0, b"A" * 64), _program(3, 2, b"A" * 64)]
    baseline = {"limit": 4096, "groups": [], "eligible": [], "net": 100, "max_amp": 1.0}
    monkeypatch.setattr(mod, "_ORIGINAL_CHOOSE_PLAN", lambda rows: baseline)

    def fake_plan(rows, limit, strategy):
        return {
            "strategy": strategy,
            "limit": limit,
            "groups": [],
            "eligible": [{"programs": rows}],
            "net": 200 if strategy == "target" and limit == 4096 else 150,
            "max_amp": 1.25,
            "mixed_base_groups": 1,
            "mixed_base_members": 2,
        }

    monkeypatch.setattr(mod, "_plan_crossbase", fake_plan)
    chosen = mod._choose_plan_crossbase(programs)
    assert chosen["net"] == 200
    assert mod._LAST_PLAN_DIAG == {
        "selected_crossbase_plan": True,
        "strategy": "target",
        "limit": 4096,
        "estimated_net_saving": 200,
        "max_amp": 1.25,
        "mixed_base_groups": 1,
        "mixed_base_members": 2,
        "eligible_groups": 1,
    }
