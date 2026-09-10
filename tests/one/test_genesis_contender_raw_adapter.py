from __future__ import annotations

from pathlib import Path

import pytest

import benchmarks.one.one_genesis_contender_raw_adapter as mod


def _identity(index: int, suite: str) -> dict:
    return {
        "suite": suite,
        "name": f"w{index:02d}",
        "files": 1,
        "logical_bytes": 16,
        "tree_sha256": f"{index:064x}"[-64:],
    }


def _identities() -> list[dict]:
    return [_identity(i, "neutral_hostile_v1") for i in range(10)] + [
        _identity(i + 10, "resemblance_hostile_v1") for i in range(5)
    ]


def _materialize(root: Path, identities: list[dict]) -> None:
    for row in identities:
        parent = root / ("neutral" if row["suite"] == "neutral_hostile_v1" else "resemblance")
        path = parent / row["name"]
        path.mkdir(parents=True, exist_ok=True)
        (path / "a.bin").write_bytes(b"a" * 8)
        (path / "b.bin").write_bytes(b"b" * 16)


def test_adapter_assembles_exact_15_rows_without_scoring(tmp_path: Path):
    identities = _identities()
    work_root = tmp_path / "work"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _materialize(work_root, identities)
    calls: list[tuple[str, str]] = []

    def fake_measure(**kwargs):
        calls.append((kwargs["contender"], Path(kwargs["root"]).name))
        assert kwargs["member"] == "b.bin"
        assert kwargs["transfer_fixture"] is False
        return {
            "schema": "cmpct-one-genesis-workload-measurement-v1",
            "contender": kwargs["contender"],
            "production_eligible": True,
            "artifact_sha256": "a" * 64,
            "repetitions": 5,
            "statistic": "median",
            "measurement": {
                "stored_bytes": 9,
                "creation": {"measured": True},
                "whole_read": {"measured": True},
                "selective_access": {"measured": True},
                "semantics": {"status": "unavailable"},
                "reader_burden": {"status": "unavailable"},
            },
        }

    rows = mod._assemble_rows(
        contender="cmpct1",
        checkout=checkout,
        work_root=work_root,
        identities=identities,
        measure=fake_measure,
    )
    assert len(rows) == 15
    assert len(calls) == 15
    assert all(row["selective_request"]["relative_path"] == "b.bin" for row in rows)
    assert all(row["workload_measurement_repetitions"] == 5 for row in rows)
    assert all(row["workload_measurement_statistic"] == "median" for row in rows)
    assert all("comparison" not in row for row in rows)


def test_adapter_missing_executor_owned_workload_fails_closed(tmp_path: Path):
    identities = _identities()
    work_root = tmp_path / "work"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _materialize(work_root, identities[:-1])
    with pytest.raises(RuntimeError, match="workload directory missing"):
        mod._assemble_rows(
            contender="v0.30",
            checkout=checkout,
            work_root=work_root,
            identities=identities,
            measure=lambda **_kwargs: {},
        )


def test_production_context_requires_explicit_executor_authorization(monkeypatch):
    monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    with pytest.raises(RuntimeError, match="explicit real-gate executor authorization"):
        mod._production_context()


def test_invalid_workload_measurement_schema_fails_closed(tmp_path: Path):
    identities = [_identity(0, "neutral_hostile_v1")]
    work_root = tmp_path / "work"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _materialize(work_root, identities)
    with pytest.raises(RuntimeError, match="wrong schema"):
        mod._assemble_rows(
            contender="v0.29",
            checkout=checkout,
            work_root=work_root,
            identities=identities,
            measure=lambda **_kwargs: {"schema": "wrong"},
        )


def test_nonproduction_workload_measurement_cannot_enter_raw_adapter(tmp_path: Path):
    identities = [_identity(0, "neutral_hostile_v1")]
    work_root = tmp_path / "work"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _materialize(work_root, identities)
    with pytest.raises(RuntimeError, match="not production-bound"):
        mod._assemble_rows(
            contender="cmpct1",
            checkout=checkout,
            work_root=work_root,
            identities=identities,
            measure=lambda **_kwargs: {
                "schema": "cmpct-one-genesis-workload-measurement-v1",
                "contender": "cmpct1",
                "production_eligible": False,
                "measurement": {},
            },
        )
