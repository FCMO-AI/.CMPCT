"""Independent held-out falsifier of canonical destination collisions on PR #250.

Research/negative evidence only. Uses the exact candidate Writer helper, not a copy,
and keeps all underlying source blobs unchanged. Full archive reconstruction is a
separate promotion condition.
"""

import pytest
from cmpct.codec import K_DIR, K_FILE
from cmpct.path_policy import canonical_logical_path
from cmpct.transactions import _require_valid_rename_destination


def _idx(existing: str):
    return {"files": [
        ["folder", K_DIR, 0, 0, 0, b"", []],
        [existing, K_FILE, 0, 0, 0, b"", []],
        ["other.txt", K_FILE, 0, 0, 0, b"", []],
    ]}


def test_plain_slash_canonical_collision_rejected_control():
    with pytest.raises(FileExistsError):
        _require_valid_rename_destination(_idx("folder/existing.txt"), "other.txt", "folder/existing.txt")


def test_noncolliding_rename_remains_permitted_control():
    _require_valid_rename_destination(_idx("folder/existing.txt"), "other.txt", "folder/another.txt")


def test_single_backslash_existing_key_is_same_canonical_destination_and_must_reject():
    # A single backslash is a legal stored raw archive separator. Reader's
    # canonical_logical_path merges it with a slash-spelled target.
    existing = "folder" + chr(92) + "existing.txt"
    new = "folder/existing.txt"
    assert existing != new
    assert canonical_logical_path(existing)[0] == canonical_logical_path(new)[0]

    # The PR #250 helper currently replaces a TWO-backslash sequence in
    # existing keys, not the canonical Reader's ONE-backslash separator.
    # Thus the helper can approve a mutation that commits duplicate
    # canonical keys and renders the archive unreadable.
    with pytest.raises(FileExistsError):
        _require_valid_rename_destination(_idx(existing), "other.txt", new)
