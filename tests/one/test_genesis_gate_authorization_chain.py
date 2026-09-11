from __future__ import annotations

import json
from pathlib import Path

import benchmarks.one.one_genesis_gate_measurement_executor as mod


def _exercise(monkeypatch, tmp_path: Path, *, authorized: bool, ambient: str | None) -> dict[str, str]:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    output = tmp_path / "raw.json"
    work = tmp_path / "work"
    work.mkdir()
    source = "a" * 40
    captured: dict[str, str] = {}

    monkeypatch.setattr(mod.subprocess, "check_output", lambda *args, **kwargs: source + "\n")
    if ambient is None:
        monkeypatch.delenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", raising=False)
    else:
        monkeypatch.setenv("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", ambient)

    def fake_run(command, *, cwd, env, check):
        assert command == ["adapter"]
        assert Path(cwd) == checkout.resolve()
        assert check is True
        captured.update(env)
        output.write_text(json.dumps({"ok": True}), encoding="utf-8")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    result = mod._adapter_output(
        "cmpct1",
        source,
        {"command": ["adapter"], "checkout": str(checkout)},
        work,
        output,
        real_gate_authorized=authorized,
    )
    assert result == {"ok": True}
    return captured


def test_explicit_real_gate_authorization_is_propagated(monkeypatch, tmp_path: Path):
    env = _exercise(monkeypatch, tmp_path, authorized=True, ambient=None)
    assert env["CMPCT_GENESIS_REAL_GATE_AUTHORIZED"] == "1"
    assert env["CMPCT_GENESIS_CONTENDER"] == "cmpct1"
    assert env["CMPCT_GENESIS_SOURCE_SHA"] == "a" * 40


def test_ambient_authorization_is_stripped_without_explicit_executor_authority(monkeypatch, tmp_path: Path):
    env = _exercise(monkeypatch, tmp_path, authorized=False, ambient="1")
    assert "CMPCT_GENESIS_REAL_GATE_AUTHORIZED" not in env


def test_noncanonical_ambient_authorization_is_also_stripped(monkeypatch, tmp_path: Path):
    env = _exercise(monkeypatch, tmp_path, authorized=False, ambient="yes")
    assert "CMPCT_GENESIS_REAL_GATE_AUTHORIZED" not in env
