from __future__ import annotations

from pathlib import Path

import pytest

from cmpct.codec import K_DIR
from cmpct.path_policy import canonical_logical_path
from cmpct.reader import CMPCT
from cmpct.validation import ParserLimits, ValidationError, _validate_index


def _index(paths: list[str]) -> dict:
    return {
        "v": 24,
        "files": [[p, K_DIR, 0o755, 0, 0, b"", None] for p in paths],
        "blobs": [],
        "recipes": [],
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }


def test_backslash_and_slash_share_one_canonical_key():
    assert canonical_logical_path("a/b")[0] == canonical_logical_path("a\\b")[0] == "a/b"


@pytest.mark.parametrize("path", ["a/./b", "a//b", "../b", "/absolute", ""] )
def test_alias_or_unsafe_components_are_rejected(path: str):
    with pytest.raises(ValueError):
        canonical_logical_path(path)


def test_preflight_structure_rejects_cross_separator_aliases():
    with pytest.raises(ValidationError, match="duplicate logical path"):
        _validate_index(_index(["a/b", "a\\b"]), record_base=0, archive_size=0, limits=ParserLimits())


def test_extractor_rejects_aliases_before_creating_members(tmp_path: Path):
    ar = object.__new__(CMPCT)
    ar.files = _index(["a/b", "a\\b"])["files"]
    destination = tmp_path / "out"
    with pytest.raises(IOError, match="duplicate canonical archive path"):
        ar.extractall(destination, metadata=False)
    assert destination.exists()
    assert list(destination.iterdir()) == []
