"""J24G49: independent name-keyed metamorphic oracle for J24G47 journal fsmeta rekey.

This has no on-disk or product release credit: only the real installed _apply_journal_ops
is tested against an independent name-keyed reference model. All commands are cloned
before execution because the helper intentionally uses mutable row objects.
"""
from __future__ import annotations

from copy import deepcopy
import random

import pytest

from cmpct.reader import _apply_journal_ops

SEED = 0xC0A47
NAMES = tuple(f"f{i:02}.bin" for i in range(15))
TRIALS = 100_000


def _actual(index):
    names = [row[0] for row in index["files"]]
    assert names == sorted(set(names)), names
    actual = {"files": {row[0]: row for row in index["files"]}}
    for field in ("xattrs", "owner_overrides"):
        table = {}
        for record in index["fsmeta"][field]:
            ordinal = record[0]
            assert type(ordinal) is int and 0 <= ordinal < len(names)
            name = names[ordinal]
            assert name not in table, (field, name, "duplicate signed ordinal")
            table[name] = record[1:]
        actual[field] = table
    return actual


def _ground_truth(model):
    return {
        "files": {name: info["row"] for name, info in model.items()},
        **{
            field: {name: info[field] for name, info in model.items()
                    if info[field] is not None}
            for field in ("xattrs", "owner_overrides")
        }
    }


def _assert_matches(index, model):
    assert _actual(index) == _ground_truth(model)


def test_name_keyed_journal_rekey_100k_batch_split_metamorphic():
    rng = random.Random(SEED)
    executed = 0
    trace_classes = set()
    controls_tested = 0
    for trial in range(TRIALS):
        initial_names = sorted(rng.sample(NAMES, rng.randint(0, 9)))
        model = {}
        for i, name in enumerate(initial_names):
            model[name] = {
                "row": [name, 0],
                "xattrs": [[["user.j24g49", name.encode()]]] if rng.randrange(3) else None,
                "owner_overrides": [100 + i, 200 + i] if rng.randrange(3) else None,
            }
        idx = {
            "files": [deepcopy(model[name]["row"]) for name in initial_names],
            "fsmeta": {
                field: [[i, *deepcopy(model[name][field])]
                        for i, name in enumerate(initial_names)
                        if model[name][field] is not None]
                for field in ("xattrs", "owner_overrides")
            },
        }
        ops = []
        for step in range(rng.randint(1, 9)):
            kinds = ["put"]
            if model:
                kinds.append("del")
            if model and len(model) < len(NAMES):
                kinds.append("ren")
            kind = rng.choice(kinds)
            if kind == "put":
                name = rng.choice(NAMES)
                row = [name, trial * 10 + step + 1]
                if name in model:
                    model[name]["row"] = deepcopy(row)
                else:
                    model[name] = {
                        "row": deepcopy(row), "xattrs": None,
                        "owner_overrides": None,
                    }
                ops.append(["put", row])
            elif kind == "del":
                name = rng.choice(tuple(model))
                del model[name]
                ops.append(["del", name])
            else:
                old = rng.choice(tuple(model))
                new = rng.choice(tuple(name for name in NAMES if name not in model))
                model[new] = model.pop(old)
                model[new]["row"] = [new, model[new]["row"][1]]
                ops.append(["ren", old, new])
            executed += 1

        # The original operation objects must NOT be replayed after they may have
        # been mutated by aliasing the list rows into the target index.
        frozen_ops = deepcopy(ops)
        batched = _apply_journal_ops(deepcopy(idx), deepcopy(frozen_ops))
        sequential = deepcopy(idx)
        for op in frozen_ops:
            _apply_journal_ops(sequential, [deepcopy(op)])
        _assert_matches(batched, model)
        _assert_matches(sequential, model)
        assert batched == sequential, (trial, "batch-vs-split")
        trace_classes.add("".join(x[0][0].upper() for x in frozen_ops))

        # Independently rooted fail-closed oracle sensitivity. Use different
        # negative mutations as data availability permits, never skip an actual
        # detected mismatch just to satisfy a counter quota.
        if trial == 0:
            negative = {"files": [["a", 0], ["b", 0]],
                        "fsmeta": {"xattrs": [[0, [["user.t", b"A"]]], [1, [["user.t", b"B"]]]],
                                   "owner_overrides": [[0, 10, 20], [1, 30, 40]]}}
            expected = {
                "a": {"row": ["a", 0], "xattrs": [[["user.t", b"A"]]], "owner_overrides": [10, 20]},
                "b": {"row": ["b", 0], "xattrs": [[["user.t", b"B"]]], "owner_overrides": [30, 40]},
            }
            _assert_matches(negative, expected)
            wrong = deepcopy(negative)
            wrong["fsmeta"]["xattrs"][0][1], wrong["fsmeta"]["xattrs"][1][1] = (
                wrong["fsmeta"]["xattrs"][1][1], wrong["fsmeta"]["xattrs"][0][1])
            with pytest.raises(AssertionError):
                _assert_matches(wrong, expected)
            wrong = deepcopy(negative)
            wrong["fsmeta"]["owner_overrides"][0][1] += 1
            with pytest.raises(AssertionError):
                _assert_matches(wrong, expected)
            wrong = deepcopy(negative)
            wrong["fsmeta"]["xattrs"].append(deepcopy(wrong["fsmeta"]["xattrs"][0]))
            with pytest.raises(AssertionError):
                _assert_matches(wrong, expected)
            controls_tested = 3

    assert executed >= 400_000, executed
    assert len(trace_classes) >= 10_000, len(trace_classes)
    assert controls_tested == 3
    print(f"J24G49_COURT_PASS trials={TRIALS} operations={executed} "
          f"distinct_traces={len(trace_classes)} hostile_controls={controls_tested} "
          f"seed={SEED} source=installed-J24G47")
