from __future__ import annotations

import pytest

from experiments import entropygraph_v030_attractor_substrate as S
from experiments import entropygraph_v030_attractor_substrate_safe as SAFE


class _DummyStream:
    def close(self) -> None:
        pass


def _install_meta(monkeypatch, meta: dict, records: int = 1) -> None:
    monkeypatch.setattr(S, "_open", lambda _path: (_DummyStream(), meta, 0, list(range(records))))


def _base_meta() -> dict:
    return {
        "phrases": [[0, 0, 3, b"x" * 32, 1]],
        "files": {"a.txt": [[0], 3, b"y" * 32]},
    }


def test_preflight_accepts_small_bounded_shape(monkeypatch) -> None:
    _install_meta(monkeypatch, _base_meta())
    SAFE._preflight("ignored")


def test_preflight_rejects_declared_file_materialization_bomb(monkeypatch) -> None:
    meta = _base_meta()
    meta["files"]["a.txt"][1] = SAFE.MAX_LOGICAL_FILE + 1
    _install_meta(monkeypatch, meta)
    with pytest.raises(RuntimeError, match="logical file materialization"):
        SAFE._preflight("ignored")


def test_preflight_rejects_phrase_larger_than_writer_contract(monkeypatch) -> None:
    meta = _base_meta()
    meta["phrases"][0][2] = S.MAX_PHRASE + 1
    _install_meta(monkeypatch, meta)
    with pytest.raises(RuntimeError, match="phrase resource"):
        SAFE._preflight("ignored")


def test_preflight_rejects_excessive_record_count(monkeypatch) -> None:
    _install_meta(monkeypatch, _base_meta(), records=SAFE.MAX_RECORDS + 1)
    with pytest.raises(RuntimeError, match="record-count"):
        SAFE._preflight("ignored")


def test_preflight_rejects_total_reference_bomb(monkeypatch) -> None:
    meta = _base_meta()
    # Use many small file parses so no single parse crosses the per-file phrase cap first.
    refs_per_file = S.MAX_PHRASES
    file_count = SAFE.MAX_TOTAL_REFERENCES // refs_per_file + 1
    meta["files"] = {
        f"f{index}": [[0] * refs_per_file, 0, b"z" * 32]
        for index in range(file_count)
    }
    _install_meta(monkeypatch, meta)
    with pytest.raises(RuntimeError, match="reference budget"):
        SAFE._preflight("ignored")


def test_safe_resource_contract_is_explicit() -> None:
    limits = SAFE.RESOURCE_LIMITS
    assert limits["max_decode_unit"] == 8 * 1024 * 1024
    assert limits["max_logical_file"] <= 64 * 1024 * 1024
    assert limits["max_materialized_tree"] <= 256 * 1024 * 1024
    assert limits["max_total_references"] <= 1_000_000
    assert limits["max_records"] <= 64
    assert limits["max_phrase_bytes"] <= 8192
