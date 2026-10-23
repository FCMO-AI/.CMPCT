"""Revision-24 PACK integrity regression: exact independent physical oracle.

Explicit verification must authenticate the *one* durable SHA-256 owner of
micro-packed slices (the physical blob), while normal reads retain CRC fast-path.
"""
from __future__ import annotations

import sys
from pathlib import Path

from cmpct import reader as reader_mod
from cmpct.reader import CMPCT

BENCHMARKS = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARKS))
from v031_pack_physical_sha_court import archive_bytes, run  # noqa: E402


def test_crc_repaired_pack_is_rejected_but_control_files_preserved():
    result = run("reject")
    assert result["status"] == "PASS"
    assert result["pack_control"]["verify"] == "ACCEPT"
    assert result["pack_crc_repaired"]["verify"] == "REJECT"
    assert result["direct_crc_repaired"]["verify"] == "REJECT"


def test_shared_pack_is_strongly_hashed_only_once_per_verify(tmp_path, monkeypatch):
    left = b"a" * 64
    right = b"b" * 64
    pack = left + right
    archive = tmp_path / "pack.cmpct"
    archive.write_bytes(archive_bytes(pack, pack, packed=True))
    original_sha = reader_mod.sha
    seen = []

    def counted_sha(data):
        if data == pack:
            seen.append(1)
        return original_sha(data)

    monkeypatch.setattr(reader_mod, "sha", counted_sha)
    with CMPCT(archive) as reader:
        assert reader.verify() == 2
        assert reader.read("alpha.md") == left
        assert reader.read("beta.md") == right
    assert len(seen) == 1, "one SHA-256 per shared physical pack, not per slice"
