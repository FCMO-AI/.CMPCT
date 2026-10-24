"""O1 independent reference semantics for signed journal replay optimization.

The slow reference below deliberately reimplements the *unchanged* historical
linear-list operations; it never calls the production indexed helper. These
checks do not replace fully authenticated revision-24 product archive tests.
"""
from __future__ import annotations

import copy
import random

import pytest

from cmpct.validation import ParserLimits, ResourceLimitError, ValidationError, _apply_delta


def _legacy(index, delta, limits):
    blobs = index["blobs"]
    files = index["files"]
    new_blobs = delta.get("blobs", [])
    ops = delta.get("ops", [])
    if not isinstance(new_blobs, list) or not isinstance(ops, list):
        raise ValidationError("transaction delta blobs/ops must be arrays")
    if len(blobs) + len(new_blobs) > limits.max_blobs:
        raise ResourceLimitError("blob count exceeds parser limit")
    blobs.extend(new_blobs)
    for op in ops:
        if not isinstance(op, list) or not op:
            raise ValidationError("malformed transaction operation")
        tag = op[0]
        if tag == "put" and len(op) == 2:
            row = op[1]
            if not isinstance(row, list) or not row or not isinstance(row[0], str):
                raise ValidationError("malformed put operation")
            for i, current in enumerate(files):
                if isinstance(current, list) and current and current[0] == row[0]:
                    files[i] = row
                    break
            else:
                files.append(row)
                if len(files) > limits.max_files:
                    raise ResourceLimitError("file count exceeds parser limit")
        elif tag == "del" and len(op) == 2 and isinstance(op[1], str):
            files[:] = [
                row for row in files
                if not (isinstance(row, list) and row and row[0] == op[1])
            ]
        elif tag == "ren" and len(op) == 3 and all(isinstance(x, str) for x in op[1:]):
            for row in files:
                if isinstance(row, list) and row and row[0] == op[1]:
                    row[0] = op[2]
                    break
        else:
            raise ValidationError(f"unsupported transaction operation {tag!r}")


def _agree(files, ops, *, max_files=256):
    original = {"files": copy.deepcopy(files), "blobs": []}
    candidate = copy.deepcopy(original)
    delta = {"ops": copy.deepcopy(ops), "blobs": []}
    limits = ParserLimits(max_files=max_files)
    failures = []
    for func, index in ((_legacy, original), (_apply_delta, candidate)):
        try:
            func(index, copy.deepcopy(delta), limits)
            failures.append(None)
        except Exception as exc:
            failures.append((type(exc), str(exc)))
    assert failures[0] == failures[1]
    if failures[0] is None:
        assert original == candidate
    return failures[0] is None


def test_indexed_replay_matches_independent_reference_on_10000_seeded_sequences():
    rng = random.Random(0xC0C72026)
    names = [f"f{i}" for i in range(27)] + ["a", "b", "c", "z"]
    accepted = rejected = 0
    for _ in range(10000):
        rows = [[rng.choice(names), 0, rng.randrange(10000)] for _ in range(rng.randint(64, 120))]
        ops = []
        for j in range(rng.randint(8, 70)):
            action = rng.choice(("put", "ren", "del"))
            src = rng.choice(names)
            if action == "put":
                ops.append(["put", [src, 0, j + 1234]])
            elif action == "ren":
                ops.append(["ren", src, rng.choice(names)])
            else:
                ops.append(["del", src])
        if _agree(rows, ops):
            accepted += 1
        else:
            rejected += 1
    assert accepted >= 5000
    assert rejected >= 0


def test_indexed_replay_collision_first_match_delete_all_and_append_order():
    rows = [["a", 0, "old-first"], ["b", 0, "second"], ["a", 0, "old-last"]]
    rows += [[f"extra-{i}", 0, i] for i in range(64)]
    ops = [
        ["ren", "a", "b"], ["put", ["b", 0, "replacement"]],
        ["ren", "a", "b"], ["del", "b"], ["put", ["a", 0, "new"]],
        ["ren", "a", "z"], ["ren", "z", "z"], ["put", ["z", 0, "final"]],
    ]
    assert _agree(rows, ops)
    assert _agree(rows, [["del", "a"]] * 9)
    assert _agree(rows, [["ren", "absent", "b"]] * 9)


@pytest.mark.parametrize("op", [
    ["nope"], ["put", ["p"]], ["ren", "p", 3], ["del", 3],
    [], ["ren", "p"], ["put"], ["del", "p", "extra"],
])
def test_indexed_replay_preserves_failure_class_and_message(op):
    files = [[f"file-{i}", 0, i] for i in range(75)]
    _agree(files, [["ren", "file-0", "file-0"]] * 8 + [op])


def test_indexed_replay_enforces_intermediate_file_ceiling_even_if_later_deleted():
    files = [[f"f-{i}", 0, i] for i in range(64)]
    ops = [["put", [f"new-{i}", 0, i]] for i in range(9)]
    ops += [["del", f"new-{i}"] for i in range(9)]
    assert not _agree(files, ops, max_files=70)


def test_short_generation_retains_simple_scan_behavior():
    files = [[f"file-{i}", 0, i] for i in range(64)]
    assert _agree(files, [["ren", "file-0", "file-2"]], max_files=100)
    assert _agree(files, [["put", ["new", 0, 2]], ["del", "file-3"]], max_files=100)
