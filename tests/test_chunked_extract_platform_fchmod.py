"""Cross-host regression for Windows Python's absent os.fchmod on staged chunk extraction.

The archive fixtures below are independently frozen revision-24 bytes (not Builder self-round-trips).
The explicit absence simulation exercises the exact Windows failure on POSIX CI as well.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from cmpct.reader import CMPCT


VECTORS = Path(__file__).with_name("conformance") / "v24-chunk-maps.json"


def _records() -> list[dict]:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    assert data["schema"] == "cmpct-v24-golden-chunk-maps-v1"
    assert data["format_revision"] == 24
    assert {r["storage_kind"] for r in data["vectors"]} == {1, 5}  # S_CHUNKS, S_CDC
    return data["vectors"]


def _archive(tmp_path: Path, record: dict) -> Path:
    raw = base64.b64decode(record["archive_base64"], validate=True)
    assert len(raw) == record["archive_bytes"]
    assert hashlib.sha256(raw).hexdigest() == record["archive_sha256"]
    source = tmp_path / f"golden-{record['storage_kind']}.cmpct"
    source.write_bytes(raw)
    return source


@pytest.mark.parametrize("record", _records(), ids=lambda r: r["name"])
@pytest.mark.parametrize("without_fchmod", [False, True], ids=["native-api", "missing-fchmod"])
def test_chunked_golden_extracts_without_optional_fchmod(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: dict, without_fchmod: bool
) -> None:
    """Both storage kinds and mixed RAW/Zstd/Deflate chunks must restore exact bytes.

    Footnote: removing the module attribute models Windows' documented missing `os.fchmod`.
    The Reader must not try a `chmod(stage_path)` workaround that reopens pathname custody.
    """
    source = _archive(tmp_path, record)
    out = tmp_path / "out"
    with CMPCT(source) as ar:
        assert ar.verify() == 1
        expected = ar.read(record["name"])
        assert hashlib.sha256(expected).hexdigest() == record["logical_sha256"]
        mode = int(ar.by[record["name"]][2])
        with monkeypatch.context() as m:
            if without_fchmod:
                m.delattr(os, "fchmod", raising=False)
            ar.extractall(out, metadata=False)
    target = out / record["name"]
    assert target.read_bytes() == expected
    assert hashlib.sha256(target.read_bytes()).hexdigest() == record["logical_sha256"]
    assert not list(out.glob(".*.cmpct-part-*"))
    if os.name == "posix" and hasattr(os, "fchmod") and not without_fchmod:
        assert stat.S_IMODE(target.stat().st_mode) == stat.S_IMODE(mode or 0o666)


@pytest.mark.parametrize("record", _records(), ids=lambda r: r["name"])
def test_missing_fchmod_does_not_weaken_corrupt_chunk_atomicity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: dict
) -> None:
    """Stage creation/corruption rejection must preserve an already-existing output."""
    source = _archive(tmp_path, record)
    out = tmp_path / "out"
    out.mkdir()
    target = out / record["name"]
    target.write_bytes(b"PRESERVE-EXISTING")
    with CMPCT(source) as ar:
        storage = ar.by[record["name"]][6]
        ids = storage[1] if storage[0] == 1 else [entry[1] for entry in storage[1]]
        assert ids
        victim = ids[0]
        original_blob = ar._blob

        def corrupt_one(idx: int) -> bytes:
            content = original_blob(idx)
            if idx != victim or not content:
                return content
            return bytes([content[0] ^ 0x01]) + content[1:]

        ar._blob = corrupt_one
        with monkeypatch.context() as m:
            m.delattr(os, "fchmod", raising=False)
            with pytest.raises(IOError, match="file integrity failure"):
                ar.extractall(out, metadata=False)
    assert target.read_bytes() == b"PRESERVE-EXISTING"
    assert not list(out.glob(".*.cmpct-part-*"))
