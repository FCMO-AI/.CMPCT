"""J24G52 regression: signed sparse inode metadata must replay identically.

The historical version of this court expected a ghost ordinal after delete and
correctly failed once shared replay repaired that defect. Retain the exact hostile
input, but now require both independent admission routes to bind xattrs to the
same surviving physical owner and alias. This complements, not substitutes for,
the real 63-generation archive court on the stacked Reader.
"""
from __future__ import annotations

import copy

from cmpct.reader import _apply_journal_ops
from cmpct.validation import _apply_delta, ParserLimits


def test_signed_sparse_xattrs_preserve_same_logical_owners_after_delete():
    original = {
        "files": [
            ["a-owner", 0, 0, 0, 0, None, None],
            ["b-delete", 0, 0, 0, 0, None, None],
            ["z-alias", 3, 0, 0, 0, None, ["a-owner"]],
        ],
        "blobs": [], "recipes": [],
        "fsmeta": {
            "owner": [0, 0], "owner_overrides": [],
            "xattrs": [
                [0, [["user.same", b"same"]]],
                [2, [["user.same", b"same"]]],
            ],
        },
    }
    delta = {"blobs": [], "ops": [["del", "b-delete"]]}
    preflight_index = copy.deepcopy(original)
    reader_index = copy.deepcopy(original)
    _apply_delta(preflight_index, delta, ParserLimits())
    _apply_journal_ops(reader_index, delta["ops"])

    def names_and_xattrs(index):
        rows = index["files"]
        result = {}
        for ordinal, attrs in index["fsmeta"]["xattrs"]:
            result[ordinal] = (rows[ordinal][0] if ordinal < len(rows) else None, attrs)
        return result

    preflight = names_and_xattrs(preflight_index)
    reader = names_and_xattrs(reader_index)
    print("J24G52_JOURNAL_PREFLIGHT", preflight)
    print("J24G52_JOURNAL_READER", reader)
    # A signed deletion moves the surviving alias from ordinal 2 to ordinal 1.
    # Both paths must migrate the authenticated xattrs, not leave stale ordinals
    # that either disappear or bind metadata to the wrong physical inode.
    expected = {
        0: ("a-owner", [["user.same", b"same"]]),
        1: ("z-alias", [["user.same", b"same"]]),
    }
    assert preflight == expected
    assert reader == expected
    assert preflight == reader
    assert preflight_index["files"] == reader_index["files"]
    assert preflight_index["fsmeta"]["xattrs"] == reader_index["fsmeta"]["xattrs"]
    assert len(preflight_index["files"]) == 2
    assert 2 not in preflight and 2 not in reader
