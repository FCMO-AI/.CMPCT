from __future__ import annotations

from pathlib import Path

import pytest

from benchmarks.one.one_genesis_historical_measurement_probe import _selective_probe


class _FakeV030:
    def __init__(self, source: Path, *, decoded_context_bytes=None, amplification=None):
        self.source = source
        self.decoded_context_bytes = decoded_context_bytes
        self.amplification = amplification

    def list_members(self, _archive):
        return [
            {"kind": "file", "path": path.relative_to(self.source).as_posix()}
            for path in sorted(self.source.rglob("*"))
            if path.is_file()
        ]

    def read_member_with_stats(self, _archive, member):
        data = (self.source / member).read_bytes()
        return data, {
            "logical_bytes": len(data),
            "decoded_context_bytes": self.decoded_context_bytes,
            "decoded_context_amplification": self.amplification,
            "format_profile": "fake",
            "locality_accounting": "fake",
        }


def _source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    root.mkdir()
    (root / "a.bin").write_bytes(b"abcdef")
    return root


def test_v029_missing_selective_surface_is_explicit_unavailable(tmp_path: Path):
    result = _selective_probe(object(), tmp_path / "archive", _source(tmp_path), "v0.29")
    assert result["status"] == "unavailable"
    assert "no proven selective-member reader" in result["reason"]


def test_v030_latency_can_be_measured_without_inventing_locality(tmp_path: Path):
    source = _source(tmp_path)
    result = _selective_probe(_FakeV030(source), tmp_path / "archive", source, "v0.30")
    assert result["status"] == "measured-reader-latency-only"
    assert result["direct_locality_available_for_all_members"] is False
    assert result["members"][0]["requested_bytes"] == 6
    assert result["members"][0]["locality"]["decoded_context_bytes"] is None


def test_v030_direct_locality_is_accepted_only_when_internally_consistent(tmp_path: Path):
    source = _source(tmp_path)
    result = _selective_probe(
        _FakeV030(source, decoded_context_bytes=12, amplification=2.0),
        tmp_path / "archive",
        source,
        "v0.30",
    )
    assert result["status"] == "measured-with-direct-locality"
    assert result["direct_locality_available_for_all_members"] is True


def test_v030_inconsistent_amplification_fails_closed(tmp_path: Path):
    source = _source(tmp_path)
    with pytest.raises(RuntimeError, match="internally inconsistent"):
        _selective_probe(
            _FakeV030(source, decoded_context_bytes=12, amplification=1.5),
            tmp_path / "archive",
            source,
            "v0.30",
        )
