from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def _run(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "benchmarks.one.one_genesis_cmpct1_product_worker", *args],
        text=True,
        capture_output=True,
        env=env,
    )


def test_transfer_fixture_build_whole_and_selective_are_exact(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    base = bytes(range(256)) * 32
    (root / "a.bin").write_bytes(base)
    (root / "copy.bin").write_bytes(base)
    nested = root / "nested"
    nested.mkdir()
    (nested / "fill.bin").write_bytes(b"F" * 8192)

    archive = tmp_path / "candidate.one"
    build_json = tmp_path / "build.json"
    whole_json = tmp_path / "whole.json"
    selective_json = tmp_path / "selective.json"

    build = _run([
        "--mode", "build", "--root", str(root), "--archive", str(archive),
        "--output", str(build_json), "--transfer-fixture",
    ])
    assert build.returncode == 0, build.stderr
    created = json.loads(build_json.read_text())
    assert created["phase"] == "creation"
    assert created["stored_bytes"] == archive.stat().st_size
    assert created["cpu_s"] >= 0
    assert created["wall_s"] >= 0
    assert created["peak_rss_bytes"] > 0
    assert created["authorization"] == {"transfer_fixture": True, "production_authorized": False}

    whole = _run([
        "--mode", "whole", "--root", str(root), "--archive", str(archive),
        "--output", str(whole_json), "--transfer-fixture",
    ])
    assert whole.returncode == 0, whole.stderr
    restored = json.loads(whole_json.read_text())
    assert restored["exact"] is True
    assert restored["integrity_checked_by_reader"] is True
    assert restored["returned_bytes"] == sum(p.stat().st_size for p in (root / "a.bin", root / "copy.bin", nested / "fill.bin"))

    selective = _run([
        "--mode", "selective", "--root", str(root), "--archive", str(archive),
        "--member", "nested/fill.bin", "--output", str(selective_json), "--transfer-fixture",
    ])
    assert selective.returncode == 0, selective.stderr
    selected = json.loads(selective_json.read_text())
    assert selected["exact"] is True
    assert selected["requested_bytes"] == 8192
    assert selected["access"]["fallback"] is False
    assert selected["scoring_executed"] is False
    assert selected["winner_selected"] is False


def test_production_worker_fails_closed_without_executor_authorization(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "x").write_bytes(b"x")
    env = os.environ.copy()
    env.pop("CMPCT_GENESIS_REAL_GATE_AUTHORIZED", None)
    result = _run([
        "--mode", "build", "--root", str(root), "--archive", str(tmp_path / "a.one"),
        "--output", str(tmp_path / "out.json"),
    ], env=env)
    assert result.returncode != 0
    assert "executor authorization" in result.stderr


def test_executor_authorization_cannot_bypass_uncertified_candidate_boundary(tmp_path: Path):
    """The calendar/executor gate must not silently choose an ineligible ONE product surface."""
    root = tmp_path / "tree"
    root.mkdir()
    (root / "x").write_bytes(b"x")
    env = os.environ.copy()
    env["CMPCT_GENESIS_REAL_GATE_AUTHORIZED"] = "1"
    env["CMPCT_GENESIS_SOURCE_SHA"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    result = _run([
        "--mode", "build", "--root", str(root), "--archive", str(tmp_path / "a.one"),
        "--output", str(tmp_path / "out.json"),
    ], env=env)
    assert result.returncode != 0
    assert "candidate boundary is not certified" in result.stderr
    assert not (tmp_path / "a.one").exists()
