"""J24G55: shared replay semantic, budget and hostile-input regression court.

These are new candidate acceptance tests. Historical J24G52/J24G54 negative
reproduction tests remain frozen in their original research branches.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from cmpct.reader import _apply_journal_ops
from cmpct.validation import _apply_delta, ParserLimits, ResourceLimitError, ValidationError


def row(name: str):
    return [name, 0, 0o600, 123456, 0, None, None]


def initial():
    return {
        "v": 24, "files": [row("a"), row("b"), row("c"), row("z")],
        "blobs": [], "recipes": [],
        "fsmeta": {
            "owner": [7, 8],
            "owner_overrides": [[2, [123, 456]]],
            "xattrs": [[0, [["user.owner", b"A"]]], [2, [["user.owner", b"C"]]]],
        },
    }


def attrs(index, key):
    files = index["files"]
    return {files[ordinal][0]: tail for ordinal, *tail in index["fsmeta"][key]}


@pytest.mark.parametrize(
    "operations,expected_names,expected_attrs",
    [
        ([["del", "b"]], ["a", "c", "z"], {"a", "c"}),
        ([["ren", "c", "d"]], ["a", "b", "d", "z"], {"a", "d"}),
        ([["put", row("aa")]], ["a", "aa", "b", "c", "z"], {"a", "c"}),
        ([["put", row("c")]], ["a", "b", "c", "z"], {"a", "c"}),
        ([["del", "c"], ["put", row("c")]], ["a", "b", "c", "z"], {"a"}),
        ([["del", "b"], ["ren", "c", "bb"], ["put", row("y")]],
         ["a", "bb", "y", "z"], {"a", "bb"}),
    ],
)
def test_validator_and_reader_one_identity_owner(operations, expected_names, expected_attrs):
    old = initial()
    preflight, reader = deepcopy(old), deepcopy(old)
    _apply_delta(preflight, {"blobs": [], "ops": operations}, ParserLimits())
    _apply_journal_ops(reader, operations)
    assert preflight == reader
    assert [f[0] for f in preflight["files"]] == expected_names
    assert set(attrs(preflight, "xattrs")) == expected_attrs
    assert set(attrs(preflight, "owner_overrides")) == (
        {"c"} if "c" in expected_attrs else {"d"} if "d" in expected_attrs else
        {"bb"} if "bb" in expected_attrs else set()
    )


def test_delete_then_fresh_put_same_path_is_not_identity_continuity():
    old = initial()
    old["files"] = [row("a"), row("b"), row("z")]
    old["fsmeta"]["owner_overrides"] = [[1, [123, 456]]]
    old["fsmeta"]["xattrs"] = [[1, [["user.owner", b"old"]]]]
    operations = [["del", "b"], ["put", row("b")]]
    preflight, reader = deepcopy(old), deepcopy(old)
    _apply_delta(preflight, {"blobs": [], "ops": operations}, ParserLimits())
    _apply_journal_ops(reader, operations)
    assert preflight == reader
    assert preflight["fsmeta"]["xattrs"] == []
    assert preflight["fsmeta"]["owner_overrides"] == []


def test_checkpoint_boundary_64_sequential_generations_rekeys_once():
    preflight, reader = initial(), initial()
    for generation in range(64):
        operations = [["put", row("a")]] if generation < 63 else [["del", "b"]]
        _apply_delta(preflight, {"blobs": [], "ops": operations}, ParserLimits())
        _apply_journal_ops(reader, operations)
        assert preflight == reader, generation
    assert [f[0] for f in preflight["files"]] == ["a", "c", "z"]
    assert set(attrs(preflight, "xattrs")) == {"a", "c"}


@pytest.mark.parametrize("operations", [
    [False], [[]], [["put"]], [["put", "text"]],
    [["del", 12]], [["del", "b", "extra"]], [["ren", "b", 12]],
    [["unknown", "b"]], [[None]],
])
def test_validation_keeps_malformed_journal_schema_fail_closed(operations):
    with pytest.raises(ValidationError):
        _apply_delta(initial(), {"blobs": [], "ops": operations}, ParserLimits())


def test_validation_rejects_over_limit_before_extra_file_is_retained():
    index = initial()
    with pytest.raises(ResourceLimitError):
        _apply_delta(index, {"blobs": [], "ops": [["put", row("new")]]}, ParserLimits(max_files=4))


@pytest.mark.parametrize("bad", [-1, True, 99, "2"])
def test_malformed_signed_xattr_ordinal_rejected_at_rekey(bad):
    index = initial()
    index["fsmeta"]["xattrs"][0][0] = bad
    with pytest.raises(ValidationError, match="journal replay"):
        _apply_delta(index, {"blobs": [], "ops": [["del", "b"]]}, ParserLimits())
