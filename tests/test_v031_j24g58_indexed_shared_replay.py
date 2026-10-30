"""J24G58: exact frozen-parent replay differential, including hostile collisions.

This lower-rung helper court does not establish physical archive semantics, process
memory safety, or complete release economics. Never mutate the frozen reference.
"""
from __future__ import annotations

import copy
import hashlib
import random
import runpy
from pathlib import Path

import pytest

from cmpct.journal_replay import _apply_journal_ops

_PARENT_BLOB = "03743ca2a06c022c2ec64243a90fe373cf91e899"
_REF_FILE = Path(__file__).resolve().parents[1] / "research" / "j24g58_frozen_parent_replay.py"


def _original():
    raw = _REF_FILE.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\\x00" + raw).hexdigest()
    assert git_blob == _PARENT_BLOB, "Frozen J24G57 semantic oracle was modified"
    return runpy.run_path(str(_REF_FILE))["_apply_journal_ops"]


def _compare(original, index, ops, max_files=None):
    results = []
    for implementation in (original, _apply_journal_ops):
        state, instructions = copy.deepcopy(index), copy.deepcopy(ops)
        try:
            returned = implementation(state, instructions, max_files=max_files)
        except Exception as exc:
            results.append(("error", type(exc).__name__, str(exc), state))
        else:
            assert returned is state
            results.append(("ok", state))
    # On failure, partial in-place state is intentionally not part of the
    # public operation contract: both must reject with the same type/message.
    if results[0][0] == "error" and results[1][0] == "error":
        assert results[0][:3] == results[1][:3]
    else:
        assert results[0] == results[1]


@pytest.mark.parametrize("count", [1, 16, 63, 64, 65, 127, 512])
def test_fixed_collision_and_identity_cases(count):
    original = _original()
    names = [f"a{i:06}" for i in range(count)]
    base = {
        "files": [[name, 9, i] for i, name in enumerate(names)],
        "fsmeta": {
            "xattrs": [[i, [[b"user.source", name.encode()]]]
                       for i, name in enumerate(names) if i % 3 == 0],
            "owner_overrides": [[i, 1000+i, 3000+i]
                                for i, name in enumerate(names) if i % 7 == 0],
        },
    }
    opsets = [
        [["ren", name, f"z{i:06}"] for i, name in enumerate(names)],
        [["del", name] for name in names],
        [["put", [f"z{i:06}", 9, i]] for i in range(count)],
        [["del", names[0]], ["put", [names[0], 9, 99]]] * max(1, count//2),
        [["ren", names[0], names[-1]]] * max(1, count),
        [["put", [names[0], 9, i]] for i in range(count)],
    ]
    for ops in opsets:
        _compare(original, base, ops)
        _compare(original, base, ops, max_files=count+10)


def test_replay_randomized_path_and_metadata_identity():
    original = _original()
    rng = random.Random(20261030)
    # Diverse, deterministic sequences, with intentional ambiguous renames,
    # deletes/recreates, put replacement, index limits and metadata density.
    for case in range(1800):
        n = rng.choice([0, 1, 3, 7, 16, 64, 65, 128, 256])
        names = [f"v{i:04}" for i in range(n)]
        index = {"files": [[p, 9, i] for i, p in enumerate(names)]}
        if rng.randrange(4) != 0:
            index["fsmeta"] = {
                "xattrs": [[i, [[b"user.k", bytes([i % 256])]]]
                           for i in range(n) if rng.randrange(4) == 0],
                "owner_overrides": [[i, i + 1, i + 2]
                                    for i in range(n) if rng.randrange(8) == 0],
            }
        pool = names + [f"extra{i:04}" for i in range(30)]
        if not pool:
            pool = ["extra0000"]
        ops = []
        for j in range(rng.randint(0, 85)):
            kind = rng.choice(["put", "put", "ren", "del"])
            a, b = rng.choice(pool), rng.choice(pool)
            if kind == "put":
                ops.append(["put", [a, rng.randrange(4), j]])
            elif kind == "ren":
                ops.append(["ren", a, b])
            else:
                ops.append(["del", a])
        cap = rng.choice([None, n, n+3, n+30, n+80])
        _compare(original, index, ops, max_files=cap)


def test_invalid_and_over_budget_rejection_parity():
    original = _original()
    names = [f"n{i:05}" for i in range(100)]
    base = {"files": [[x, 9] for x in names],
            "fsmeta": {"xattrs": [[1, [[b"k", b"v"]]]]}}
    for suffix in (
        [["future_op", names[0]], ["del", names[0]]],
        [["ren", names[0]]],
        [["put", 10]],
        [["put", [f"new{i}", 9]] for i in range(22)],
    ):
        _compare(original, base, suffix, max_files=105)
    malformed = copy.deepcopy(base)
    malformed["fsmeta"]["xattrs"] = [[200, [[b"k", b"v"]]]]
    _compare(original, malformed, [["ren", names[0], "far"]] * 20)


def test_large_accepted_rename_oracle():
    original = _original()
    count = 4096
    base = {"files": [[f"old{i:06}", 9] for i in range(count)],
            "fsmeta": {"xattrs": [[0, [[b"user.id", b"0"]]],
                                   [count-1, [[b"user.id", b"last"]]]],
                       "owner_overrides": [[count//2, 101, 202]]}}
    ops = [["ren", f"old{i:06}", f"new{i:06}"] for i in range(count)]
    _compare(original, base, ops, max_files=count)
