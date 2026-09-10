from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from benchmarks.one import one_genesis_cmpct1_product_worker as worker


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_genesis_cmpct1_product_worker", *args],
        text=True,
        capture_output=True,
        env=env,
    )


def _runtime_identity() -> dict[str, str]:
    return {
        "creator_path": worker.CREATOR_SURFACE,
        "creator_blob_sha": worker._git_object_sha(worker.CREATOR_SURFACE),
        "reader_path": worker.READER_SURFACE,
        "reader_blob_sha": worker._git_object_sha(worker.READER_SURFACE),
        "runtime_tree_path": worker.RUNTIME_TREE,
        "runtime_tree_sha": worker._git_object_sha(worker.RUNTIME_TREE),
    }


def _write_candidate_manifest(path: Path, *, status: str = worker.CERTIFIED_STATUS, overrides: dict[str, str] | None = None) -> None:
    certified = _runtime_identity()
    certified.update(overrides or {})
    path.write_text(json.dumps({"schema": "cmpct-one-genesis-one-candidate-boundary-v1", "status": status, "certified_candidate": certified}) + "\n", encoding="utf-8")


def _assert_transfer_attestation(row: dict) -> None:
    assert row["genesis_workload_modules_imported"] is False
    assert set(row["forbidden_module_fragments"]) == set(worker.FORBIDDEN_TRANSFER_MODULE_FRAGMENTS)


def test_transfer_fixture_build_whole_and_selective_are_exact(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    base = bytes(range(256)) * 32
    a = root / "a.bin"
    a.write_bytes(base)
    a.chmod(0o640)
    (root / "copy.bin").write_bytes(base)
    nested = root / "nested"
    nested.mkdir()
    nested.chmod(0o750)
    (nested / "fill.bin").write_bytes(b"F" * 8192)
    (root / "a-link").symlink_to("a.bin")

    archive = tmp_path / "candidate.one"
    build_json = tmp_path / "build.json"
    whole_json = tmp_path / "whole.json"
    selective_json = tmp_path / "selective.json"

    build = _run(["--mode", "build", "--root", str(root), "--archive", str(archive), "--output", str(build_json), "--transfer-fixture"])
    assert build.returncode == 0, build.stderr
    created = json.loads(build_json.read_text())
    _assert_transfer_attestation(created)
    assert created["phase"] == "creation"
    assert created["stored_bytes"] == archive.stat().st_size
    assert created["cpu_s"] >= 0
    assert created["wall_s"] >= 0
    assert created["peak_rss_bytes"] > 0
    assert created["authorization"] == {"transfer_fixture": True, "production_authorized": False}

    whole = _run(["--mode", "whole", "--root", str(root), "--archive", str(archive), "--output", str(whole_json), "--transfer-fixture"])
    assert whole.returncode == 0, whole.stderr
    restored = json.loads(whole_json.read_text())
    _assert_transfer_attestation(restored)
    assert restored["exact"] is True
    assert restored["tree_semantics_checked"] is True
    assert restored["tree_entries"] == 5
    assert restored["integrity_checked_by_reader"] is True
    assert restored["returned_bytes"] == sum(p.stat().st_size for p in (a, root / "copy.bin", nested / "fill.bin"))

    selective = _run(["--mode", "selective", "--root", str(root), "--archive", str(archive), "--member", "nested/fill.bin", "--output", str(selective_json), "--transfer-fixture"])
    assert selective.returncode == 0, selective.stderr
    selected = json.loads(selective_json.read_text())
    _assert_transfer_attestation(selected)
    assert selected["exact"] is True
    assert selected["requested_bytes"] == 8192
    assert selected["access"]["fallback"] is False
    assert selected["scoring_executed"] is False
    assert selected["winner_selected"] is False


def test_tree_semantics_reject_mode_target_kind_and_path_drift(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    file_path = root / "file"
    file_path.write_bytes(b"abc")
    file_path.chmod(0o600)
    (root / "link").symlink_to("file")
    source = worker._source_semantic_manifest(root)
    exact = {key: dict(value) for key, value in source.items()}
    worker._assert_tree_semantics(source, exact)
    for field, value in (("mode", 0o777), ("kind", "dir")):
        changed = {key: dict(row) for key, row in exact.items()}
        changed["file"][field] = value
        with pytest.raises(RuntimeError, match="tree semantics differ"):
            worker._assert_tree_semantics(source, changed)
    changed_target = {key: dict(row) for key, row in exact.items()}
    changed_target["link"]["target"] = "elsewhere"
    with pytest.raises(RuntimeError, match="tree semantics differ"):
        worker._assert_tree_semantics(source, changed_target)
    missing = {key: dict(row) for key, row in exact.items() if key != "link"}
    with pytest.raises(RuntimeError, match="path universe differs"):
        worker._assert_tree_semantics(source, missing)


def test_source_semantic_manifest_uses_lstat_and_preserves_symlink_target(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    target = root / "target"
    target.write_bytes(b"payload")
    target.chmod(0o640)
    (root / "link").symlink_to("target")
    rows = worker._source_semantic_manifest(root)
    assert rows["target"]["kind"] == "file"
    assert rows["target"]["mode"] == stat.S_IMODE(target.lstat().st_mode)
    assert rows["link"]["kind"] == "symlink"
    assert rows["link"]["target"] == "target"


def test_transfer_import_attestation_rejects_forbidden_loaded_module(monkeypatch: pytest.MonkeyPatch):
    fake_name = "benchmarks.one.one_genesis_gate_readiness"
    monkeypatch.setitem(sys.modules, fake_name, object())
    with pytest.raises(RuntimeError, match="imported Genesis workload authority"):
        worker._transfer_import_attestation()


def test_production_worker_fails_closed_without_executor_authorization(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "x").write_bytes(b"x")
    env = os.environ.copy()
    env.pop("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", None)
    result = _run(["--mode", "build", "--root", str(root), "--archive", str(tmp_path / "a.one"), "--output", str(tmp_path / "out.json")], env=env)
    assert result.returncode != 0
    assert "executor authorization" in result.stderr


def test_executor_authorization_cannot_bypass_uncertified_candidate_boundary(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "x").write_bytes(b"x")
    env = os.environ.copy()
    env["CMPCT_GENESIS_REAL_GATE_AUTHORIZED"] = "1"
    env["CMPCT_GENESIS_SOURCE_SHA"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    result = _run(["--mode", "build", "--root", str(root), "--archive", str(tmp_path / "a.one"), "--output", str(tmp_path / "out.json")], env=env)
    assert result.returncode != 0
    assert "candidate boundary is not certified" in result.stderr
    assert not (tmp_path / "a.one").exists()


@pytest.mark.parametrize(("field", "bad_value"), [("creator_path", "experiments/one/not-the-certified-creator.py"), ("creator_blob_sha", "1" * 40), ("reader_path", "experiments/one/not-the-certified-reader.py"), ("reader_blob_sha", "2" * 40), ("runtime_tree_path", "experiments/not-one"), ("runtime_tree_sha", "3" * 40)])
def test_candidate_boundary_rejects_runtime_identity_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, field: str, bad_value: str):
    manifest = tmp_path / "candidate.json"
    _write_candidate_manifest(manifest, overrides={field: bad_value})
    monkeypatch.setattr(worker, "CANDIDATE_BOUNDARY_MANIFEST", manifest)
    with pytest.raises(RuntimeError, match=field + " differs from worker runtime"):
        worker._assert_candidate_boundary_certified()


def test_candidate_boundary_accepts_exact_runtime_tree_binding(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    manifest = tmp_path / "candidate.json"
    _write_candidate_manifest(manifest)
    monkeypatch.setattr(worker, "CANDIDATE_BOUNDARY_MANIFEST", manifest)
    certified = worker._assert_candidate_boundary_certified()
    assert certified == _runtime_identity()
