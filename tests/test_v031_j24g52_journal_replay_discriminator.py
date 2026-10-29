"""J24G52 narrow same-source replay discrepancy probe: never edit frozen validators.

This is a source-level negative discriminator, not evidence that a whole on-disk
multi-generation archive reconstructs incorrectly under preflight. It tests
an adjacent ownership boundary so the next activation can choose a physical
falsifier instead of silently assuming Reader and preflight agree.
"""
from __future__ import annotations

import copy

from cmpct.reader import _apply_journal_ops
from cmpct.validation import _apply_delta, ParserLimits


def test_signed_sparse_xattrs_have_different_ordinals_after_delete():
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
    # Preserve the actual independently checked source result rather than
    # assuming correctness. This test will fail if the mechanism changes;
    # the physical archive still needs an independent hosted test.
    assert preflight[2][0] is None
    assert reader[1][0] == "z-alias"
    assert preflight != reader
