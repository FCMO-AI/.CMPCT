"""Positive boundary test: a missing Reader fsmeta cache must not hide malformed indexed fsmeta.

The older tests/test_path_policy.py intentionally constructs a Reader without __init__,
with neither index nor fsmeta; retain that old synthetic-path rejection behavior.
This supplemental court makes sure that when an *actual opened archive index* exists,
removing the Python convenience cache cannot bypass the index's malformed metadata.
"""
from __future__ import annotations

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.validation import ValidationError


def test_missing_cache_still_validates_existing_index_before_any_write(tmp_path):
    src = tmp_path / "input"
    src.mkdir()
    (src / "payload.bin").write_bytes(b"EXACT-LOGICAL-PAYLOAD" * 64)
    archive = tmp_path / "original.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.read("payload.bin") == b"EXACT-LOGICAL-PAYLOAD" * 64
        reader.index["fsmeta"] = {
            "owner": [0, 0], "owner_overrides": [],
            "xattrs": [[0, [["user.malformed", "NOT-BYTES"]]]],
        }
        assert "fsmeta" in reader.__dict__ and "index" in reader.__dict__
        del reader.fsmeta
        destination = tmp_path / "not-created"
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.extractall(destination, metadata=False)
        assert not destination.exists()
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.verify()


def test_existing_explicit_malformed_cache_is_never_overridden_by_valid_index(tmp_path):
    src = tmp_path / "input"
    src.mkdir()
    (src / "a.bin").write_bytes(b"A" * 32)
    archive = tmp_path / "original.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        reader.fsmeta = None  # explicitly invalid cache; must not silently fall back
        destination = tmp_path / "not-created"
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.extractall(destination)
        assert not destination.exists()
        with pytest.raises(ValidationError, match="fsmeta"):
            reader.verify()
