from __future__ import annotations

import copy

import pytest

from experiments import entropygraph_v030_release_reader as base
from experiments import entropygraph_v030_release_reader_policy as policy


def _pg_meta() -> dict:
    raw_a = b"alpha"
    raw_b = b"bravo"
    return {
        "v": 1,
        "engine": "PrefixGraph-depth1-v1",
        "tree_sha256": "0" * 64,
        "max_dependency_depth": 1,
        "files": ["a.bin", "b.bin"],
        "records": [
            ["direct", -1, len(raw_a), 1, base.PG.H(b"x"), base.PG.H(raw_a)],
            ["direct", -1, len(raw_b), 1, base.PG.H(b"y"), base.PG.H(raw_b)],
        ],
    }


def test_prefixgraph_requires_canonical_path_order() -> None:
    meta = _pg_meta()
    meta["files"] = ["b.bin", "a.bin"]
    with pytest.raises(RuntimeError, match="canonical path order"):
        policy._strict_pg_validate(meta)


def test_prefixgraph_direct_base_rejects_string_coercion() -> None:
    meta = _pg_meta()
    meta["records"][0][1] = "-1"
    # Footnote: the research reader historically used int(base), which makes a textual "-1" look valid.
    # Promotion treats type identity as part of the grammar and refuses coercion.
    with pytest.raises(RuntimeError, match="exact integer -1"):
        policy._strict_pg_validate(meta)


def test_prefixgraph_dependency_depth_rejects_bool_and_string() -> None:
    for invalid in (True, "1", 1.0):
        meta = _pg_meta()
        meta["max_dependency_depth"] = invalid
        with pytest.raises(RuntimeError, match="exact integer 0/1"):
            policy._strict_pg_validate(meta)


def test_policy_installation_is_idempotent() -> None:
    before_pg = base._validate_pg_meta
    before_g04 = base._validate_g04_meta
    policy.install_policy()
    assert base._validate_pg_meta is before_pg
    assert base._validate_g04_meta is before_g04
