from __future__ import annotations

from pathlib import Path

import pytest

import benchmarks.one.one_genesis_adapter_manifest_builder as mod

HARNESS_SHA = "b" * 40


def _dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    candidate = tmp_path / "candidate"
    v029 = tmp_path / "v029"
    v030 = tmp_path / "v030"
    for root in (candidate, v029, v030):
        root.mkdir()
    return candidate, v029, v030


def _heads(candidate: Path, v029: Path, v030: Path, candidate_sha: str) -> dict[Path, str]:
    return {
        candidate.resolve(): candidate_sha,
        v029.resolve(): mod.V029_SHA,
        v030.resolve(): mod.V030_SHA,
        mod.ROOT.resolve(): HARNESS_SHA,
    }


def test_manifest_binds_exact_three_sources_without_authorization(monkeypatch, tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    candidate_sha = "a" * 40
    heads = _heads(candidate, v029, v030, candidate_sha)
    monkeypatch.setattr(mod, "_head", lambda checkout: heads[checkout.resolve()])
    payload = mod.build_manifest(
        candidate_sha=candidate_sha,
        candidate_checkout=candidate,
        v029_checkout=v029,
        v030_checkout=v030,
        python_executable="/usr/bin/python3",
    )
    assert payload["schema"] == "cmpct-one-genesis-adapters-v1"
    assert payload["harness_sha"] == HARNESS_SHA
    assert set(payload["adapters"]) == {"cmpct1", "v0.29", "v0.30"}
    assert payload["execution_authorized"] is False
    assert payload["scoring_executed"] is False
    assert payload["winner_selected"] is False
    commands = [row["command"] for row in payload["adapters"].values()]
    assert all(command[0] == "/usr/bin/python3" and len(command) == 2 for command in commands)
    assert len({command[1] for command in commands}) == 1
    assert Path(commands[0][1]) == (mod.ROOT / mod.CERTIFIED_ADAPTER_REL).resolve()
    assert payload["adapters"]["cmpct1"]["checkout"] == str(candidate.resolve())
    assert payload["adapters"]["v0.29"]["checkout"] == str(v029.resolve())
    assert payload["adapters"]["v0.30"]["checkout"] == str(v030.resolve())


def test_candidate_head_mismatch_fails_closed(monkeypatch, tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    heads = _heads(candidate, v029, v030, "f" * 40)
    monkeypatch.setattr(mod, "_head", lambda checkout: heads[checkout.resolve()])
    with pytest.raises(RuntimeError, match="CMPCT1 checkout HEAD"):
        mod.build_manifest(
            candidate_sha="a" * 40,
            candidate_checkout=candidate,
            v029_checkout=v029,
            v030_checkout=v030,
        )


def test_frozen_v029_substitution_fails_closed(monkeypatch, tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    candidate_sha = "a" * 40
    heads = _heads(candidate, v029, v030, candidate_sha)
    heads[v029.resolve()] = "f" * 40
    monkeypatch.setattr(mod, "_head", lambda checkout: heads[checkout.resolve()])
    with pytest.raises(RuntimeError, match="v0.29 checkout HEAD"):
        mod.build_manifest(
            candidate_sha=candidate_sha,
            candidate_checkout=candidate,
            v029_checkout=v029,
            v030_checkout=v030,
        )


def test_frozen_v030_substitution_fails_closed(monkeypatch, tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    candidate_sha = "a" * 40
    heads = _heads(candidate, v029, v030, candidate_sha)
    heads[v030.resolve()] = "e" * 40
    monkeypatch.setattr(mod, "_head", lambda checkout: heads[checkout.resolve()])
    with pytest.raises(RuntimeError, match="v0.30 checkout HEAD"):
        mod.build_manifest(
            candidate_sha=candidate_sha,
            candidate_checkout=candidate,
            v029_checkout=v029,
            v030_checkout=v030,
        )


def test_malformed_candidate_sha_fails_before_binding(tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    with pytest.raises(RuntimeError, match="40-hex"):
        mod.build_manifest(
            candidate_sha="not-a-sha",
            candidate_checkout=candidate,
            v029_checkout=v029,
            v030_checkout=v030,
        )


def test_candidate_checkout_does_not_supply_harness_adapter(monkeypatch, tmp_path: Path):
    candidate, v029, v030 = _dirs(tmp_path)
    candidate_sha = "a" * 40
    # Deliberately leave the candidate checkout without any Genesis adapter script.
    heads = _heads(candidate, v029, v030, candidate_sha)
    monkeypatch.setattr(mod, "_head", lambda checkout: heads[checkout.resolve()])
    payload = mod.build_manifest(
        candidate_sha=candidate_sha,
        candidate_checkout=candidate,
        v029_checkout=v029,
        v030_checkout=v030,
    )
    command_path = Path(payload["adapters"]["cmpct1"]["command"][1])
    assert command_path == (mod.ROOT / mod.CERTIFIED_ADAPTER_REL).resolve()
    assert not str(command_path).startswith(str(candidate.resolve()))
