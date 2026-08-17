from __future__ import annotations

"""Focused regression tests for the v0.29 structural-competitor measurement boundary.

Footnote: these tests intentionally avoid invoking optional external compressors. They pin the evidence
contract that failed in the first structural sweep: a valid repository tree must recover a positive byte
measurement, while an execution-success/zero-byte anomaly must remain explicit negative evidence rather
than aborting CMPCT's own acceptance gate or inventing a competitor size.
"""

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "mosaic_v029_structural_competitors.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_v029_structural_measurement_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_storage_probe_counts_nested_repository_bytes_without_following_symlink(tmp_path: Path) -> None:
    mod = _module()
    repo = tmp_path / "repo"
    (repo / "data" / "0").mkdir(parents=True)
    (repo / "config").write_bytes(b"config-bytes")
    (repo / "data" / "0" / "segment").write_bytes(b"segment-bytes" * 17)

    # Footnote: a symlink is metadata, not a second copy of its target. The probe uses lstat accounting
    # and therefore cannot inflate a competitor by recursively walking a symlinked directory.
    (repo / "alias").symlink_to(repo / "data", target_is_directory=True)

    result = mod._storage_probe(repo)

    assert result["path_exists"] is True
    assert result["regular_files"] == 2
    assert result["symlinks"] == 1
    assert result["apparent_bytes"] >= len(b"config-bytes") + len(b"segment-bytes" * 17)


def test_repair_measurement_recovers_positive_repository_measurement(tmp_path: Path) -> None:
    mod = _module()
    repo = tmp_path / "borg-repo"
    repo.mkdir()
    (repo / "config").write_bytes(b"borg-config")
    (repo / "index.1").write_bytes(b"index" * 29)

    row = {
        "available": True,
        "bytes": 0,
        "create_s": 1.25,
        "semantics": "synthetic structural repository",
    }
    repaired = mod._repair_measurement("borg", row, repo)

    assert repaired["available"] is True
    assert repaired["bytes"] > 0
    assert repaired["measurement_repaired"] is True
    assert repaired["measurement_status"] == "recovered_from_filesystem_probe"


def test_repair_measurement_retains_zero_byte_anomaly_as_negative_evidence(tmp_path: Path) -> None:
    mod = _module()
    missing = tmp_path / "missing-repo"
    row = {
        "available": True,
        "bytes": 0,
        "create_s": 0.75,
        "semantics": "synthetic structural repository",
    }

    repaired = mod._repair_measurement("borg", row, missing)

    assert repaired["available"] is False
    assert repaired["tool_executed"] is True
    assert repaired["measurement_status"] == "invalid_zero_byte_measurement"
    assert repaired["measurement_probe"]["path_exists"] is False
    assert "no defensible positive repository-byte measurement" in repaired["reason"]
