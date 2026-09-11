from __future__ import annotations

from pathlib import Path

import pytest

import benchmarks.one.one_genesis_contender_workload_measurement as mod


def _phase(mode: str, index: int = 0) -> dict:
    if mode == "build":
        return {
            "phase": "creation",
            "measured": True,
            "cpu_s": 1.0 + index * 0.1,
            "wall_s": 2.0 + index * 0.1,
            "peak_rss_bytes": 100 + index,
            "stored_bytes": 1234,
            "wire_sha256": "a" * 64,
            "archive_sha256": "b" * 64,
        }
    if mode == "whole":
        return {
            "phase": "whole_read",
            "measured": True,
            "cpu_s": 0.5 + index * 0.01,
            "wall_s": 0.7 + index * 0.01,
            "peak_rss_bytes": 80 + index,
            "returned_bytes": 900,
            "exact": True,
        }
    if mode == "selective":
        return {
            "phase": "selective_access",
            "measured": True,
            "cpu_s": 0.2 + index * 0.01,
            "wall_s": 0.3 + index * 0.01,
            "peak_rss_bytes": 70 + index,
            "member": "largest.bin",
            "requested_bytes": 512,
            "exact": True,
            "access": {"opaque_product_counter": 9},
        }
    raise AssertionError(mode)


def _fixture_dirs(tmp_path: Path) -> tuple[Path, Path]:
    checkout = tmp_path / "checkout"
    root = tmp_path / "workload"
    checkout.mkdir()
    root.mkdir()
    (root / "largest.bin").write_bytes(b"x" * 512)
    return checkout, root


def _sealed_historical_phase(mode: str, index: int, contender: str, checkout: Path) -> dict:
    row = _phase(mode, index)
    row["frozen_source_sha"] = mod.FROZEN[contender]
    row["frozen_cmpct_import_roots"] = {
        "cmpct": str((checkout / "src" / "cmpct" / "__init__.py").resolve())
    }
    return row


def test_five_sample_cmpct1_measurement_retains_samples_and_medians(monkeypatch, tmp_path: Path):
    checkout, root = _fixture_dirs(tmp_path)
    monkeypatch.setattr(
        mod,
        "_authorize",
        lambda contender, checkout, transfer_fixture: {
            "transfer_fixture": True,
            "production_authorized": False,
            "observed_source_sha": "c" * 40,
        },
    )
    counts = {"build": 0, "whole": 0, "selective": 0}

    def fake_worker(**kwargs):
        mode = kwargs["mode"]
        index = counts[mode]
        counts[mode] += 1
        return _phase(mode, index)

    monkeypatch.setattr(mod, "_run_worker", fake_worker)
    result = mod.measure_workload(
        contender="cmpct1",
        checkout=checkout,
        root=root,
        member="largest.bin",
        transfer_fixture=True,
    )

    assert counts == {"build": 5, "whole": 5, "selective": 5}
    assert result["synthetic"] is True
    assert result["production_eligible"] is False
    assert result["scoring_executed"] is False
    measurement = result["measurement"]
    assert measurement["stored_bytes"] == 1234
    assert measurement["creation"]["cpu_s"] == pytest.approx(1.2)
    assert measurement["whole_read"]["cpu_s"] == pytest.approx(0.52)
    assert measurement["selective_access"]["cpu_s"] == pytest.approx(0.22)
    assert len(measurement["creation"]["samples"]) == 5
    assert len(measurement["whole_read"]["samples"]) == 5
    assert len(measurement["selective_access"]["samples"]) == 5
    assert measurement["selective_access"]["touched_bytes"] == {"status": "unavailable"}
    assert measurement["semantics"] == {"status": "unavailable"}
    assert measurement["reader_burden"] == {"status": "unavailable"}
    assert "runtime_source_provenance" not in measurement


def test_v029_selective_is_unavailable_and_never_invoked(monkeypatch, tmp_path: Path):
    checkout, root = _fixture_dirs(tmp_path)
    monkeypatch.setattr(
        mod,
        "_authorize",
        lambda contender, checkout, transfer_fixture: {
            "transfer_fixture": True,
            "production_authorized": False,
            "observed_source_sha": mod.FROZEN["v0.29"],
        },
    )
    counts = {"build": 0, "whole": 0, "selective": 0}

    def fake_worker(**kwargs):
        mode = kwargs["mode"]
        index = counts[mode]
        counts[mode] += 1
        return _sealed_historical_phase(mode, index, "v0.29", checkout)

    monkeypatch.setattr(mod, "_run_worker", fake_worker)
    result = mod.measure_workload(
        contender="v0.29",
        checkout=checkout,
        root=root,
        member="largest.bin",
        transfer_fixture=True,
    )
    assert counts == {"build": 5, "whole": 5, "selective": 0}
    assert result["measurement"]["selective_access"]["status"] == "unavailable"
    provenance = result["measurement"]["runtime_source_provenance"]
    assert provenance["status"] == "source_sealed"
    assert provenance["source_sha"] == mod.FROZEN["v0.29"]
    assert provenance["sample_count"] == 10
    assert provenance["loaded_cmpct_modules"]


def test_deterministic_wire_mismatch_fails_closed():
    rows = [_phase("build", index) for index in range(5)]
    rows[4]["wire_sha256"] = "f" * 64
    with pytest.raises(RuntimeError, match="inconsistent persistent wire"):
        mod._stable_build(rows, "cmpct1")


def test_one_inexact_whole_sample_fails_entire_measurement():
    rows = [_phase("whole", index) for index in range(5)]
    rows[2]["exact"] = False
    with pytest.raises(RuntimeError, match="whole-read sample 2 is not exact"):
        mod._assert_whole_exact(rows)


def test_sample_count_is_part_of_the_frozen_statistic():
    with pytest.raises(RuntimeError, match="exactly 5 samples"):
        mod._timing_family([_phase("whole", index) for index in range(4)])


def test_negative_resource_sample_fails_closed():
    rows = [_phase("whole", index) for index in range(5)]
    rows[3]["peak_rss_bytes"] = -1
    with pytest.raises(RuntimeError, match="invalid non-negative metric peak_rss_bytes"):
        mod._timing_family(rows)


def test_production_authorization_requires_explicit_gate_and_source_binding(monkeypatch, tmp_path: Path):
    checkout, _root = _fixture_dirs(tmp_path)
    monkeypatch.setattr(mod, "_git_head", lambda _checkout: "d" * 40)
    monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    monkeypatch.delenv("CMPCT_GENESIS_SOURCE_SHA", raising=False)
    with pytest.raises(RuntimeError, match="requires executor authorization"):
        mod._authorize("cmpct1", checkout, False)

    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "e" * 40)
    with pytest.raises(RuntimeError, match="not bound"):
        mod._authorize("cmpct1", checkout, False)


def test_frozen_comparator_source_cannot_be_substituted(monkeypatch, tmp_path: Path):
    checkout, _root = _fixture_dirs(tmp_path)
    monkeypatch.setattr(mod, "_git_head", lambda _checkout: "d" * 40)
    monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", "1")
    monkeypatch.setenv("CMPCT_GENESIS_SOURCE_SHA", "d" * 40)
    with pytest.raises(RuntimeError, match="differs from frozen Genesis authority"):
        mod._authorize("v0.30", checkout, False)
