"""J24G52 historical discriminator, promoted to a current signed-replay parity regression.

The earlier source deliberately asserted Reader/preflight disagreement after a
DELETE shifted a sparse xattr ordinal. #795 repaired the shared replay and
made that old negative expectation obsolete. Preserve historical defect evidence
in Git history, then guard the *correct* identity property prospectively here.
"""
from __future__ import annotations

import copy

from cmpct.reader import _apply_journal_ops
from cmpct.validation import _apply_delta, ParserLimits


def test_signed_sparse_xattrs_remap_with_same_identity_after_delete():
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
    immutable_input = copy.deepcopy(original)
    delta = {"blobs": [], "ops": [["del", "b-delete"]]}
    preflight_index = copy.deepcopy(original)
    reader_index = copy.deepcopy(original)

    _apply_delta(preflight_index, delta, ParserLimits())
    _apply_journal_ops(reader_index, delta["ops"])

    def names_and_xattrs(index):
        rows = index["files"]
        result = {}
        for ordinal, attrs in index["fsmeta"]["xattrs"]:
            assert 0 <= ordinal < len(rows), "no orphaned positional xattr"
            result[ordinal] = (rows[ordinal][0], attrs)
        return result

    expected = {
        0: ("a-owner", [["user.same", b"same"]]),
        1: ("z-alias", [["user.same", b"same"]]),
    }
    assert original == immutable_input, "replay must not mutate caller's source index"
    assert [row[0] for row in reader_index["files"]] == ["a-owner", "z-alias"]
    assert reader_index["files"][1][1] == 3
    assert reader_index["files"][1][-1] == ["a-owner"]
    assert names_and_xattrs(reader_index) == expected
    assert names_and_xattrs(preflight_index) == expected
    assert preflight_index == reader_index, "same signed input must yield the same full logical state"

    # A subsequent signed rename must follow the *remapped identity*, not the
    # deleted ordinal. This protects continuity across separately committed deltas.
    second = {"blobs": [], "ops": [["ren", "z-alias", "zz-alias"]]}
    _apply_delta(preflight_index, second, ParserLimits())
    _apply_journal_ops(reader_index, second["ops"])
    assert [row[0] for row in reader_index["files"]] == ["a-owner", "zz-alias"]
    assert reader_index["files"][1][-1] == ["a-owner"]
    assert names_and_xattrs(reader_index) == {
        0: ("a-owner", [["user.same", b"same"]]),
        1: ("zz-alias", [["user.same", b"same"]]),
    }
    assert preflight_index == reader_index, "later rename must preserve prior signed-xattr remap"
    assert original == immutable_input
