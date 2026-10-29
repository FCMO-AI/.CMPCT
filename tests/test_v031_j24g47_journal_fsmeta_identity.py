"""J24G47: path identity, not sorted row number, must own signed r24 fsmeta.

These are repair acceptance tests, intentionally separate from the unchanged
J24G46 negative research court. No source/format/release waivers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT, _apply_journal_ops
from cmpct.transactions import append_delete, append_rename, append_update

KEY = "com.fcmo.cmpct.j24g47" if sys.platform == "darwin" else "user.cmpct_j24g47"
VALUE = b"J24G47 physical metadata\x00\xff"
NATIVE_XATTRS = sys.platform in ("darwin", "linux")


def _set_native(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", KEY, VALUE.hex(), str(path)],
                       check=True, capture_output=True, text=True)
    else:
        os.setxattr(path, KEY, VALUE, follow_symlinks=False)


def _get_native(path: Path) -> bytes | None:
    if sys.platform == "darwin":
        p = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                           capture_output=True, text=True)
        return bytes.fromhex("".join(p.stdout.split())) if p.returncode == 0 else None
    if sys.platform == "linux":
        try:
            return os.getxattr(path, KEY, follow_symlinks=False)
        except OSError:
            return None
    return None


def _names_metadata(reader: CMPCT, key: str = "xattrs") -> dict:
    return {
        reader.files[i][0]: record[1:]
        for record in reader.fsmeta.get(key, [])
        for i in (record[0],)
    }


def _toy_index() -> dict:
    return {
        "files": [["m.bin", 0], ["z.bin", 0]],
        "fsmeta": {
            "owner": [10, 20],
            "owner_overrides": [[1, 31, 32]],
            "xattrs": [[1, [["user.marker", b"present"]]]],
        },
    }


def test_signed_sparse_tables_follow_name_identity_through_all_op_kinds():
    idx = _toy_index()
    _apply_journal_ops(idx, [["put", ["a.bin", 0]]])
    assert [r[0] for r in idx["files"]] == ["a.bin", "m.bin", "z.bin"]
    assert idx["fsmeta"]["owner_overrides"] == [[2, 31, 32]]
    assert idx["fsmeta"]["xattrs"] == [[2, [["user.marker", b"present"]]]]
    assert idx["fsmeta"]["owner"] == [10, 20]

    _apply_journal_ops(idx, [["ren", "z.bin", "b.bin"]])
    assert [r[0] for r in idx["files"]] == ["a.bin", "b.bin", "m.bin"]
    assert idx["fsmeta"]["owner_overrides"] == [[1, 31, 32]]
    assert idx["fsmeta"]["xattrs"][0][0] == 1

    _apply_journal_ops(idx, [["put", ["b.bin", 0]]])
    assert idx["fsmeta"]["owner_overrides"] == [[1, 31, 32]]

    _apply_journal_ops(idx, [["del", "a.bin"]])
    assert idx["fsmeta"]["owner_overrides"] == [[0, 31, 32]]
    assert idx["fsmeta"]["xattrs"][0][0] == 0

    _apply_journal_ops(idx, [["del", "b.bin"], ["put", ["b.bin", 0]]])
    assert "owner_overrides" in idx["fsmeta"]
    assert idx["fsmeta"]["owner_overrides"] == []
    assert idx["fsmeta"]["xattrs"] == []


@pytest.mark.parametrize("bad", [-1, 2, True, "1"])
def test_ambiguous_or_out_of_range_signed_ordinal_rejected(bad):
    idx = _toy_index()
    idx["fsmeta"]["xattrs"] = [[bad, [["user.marker", b"foreign"]]]]
    with pytest.raises(ValueError, match="invalid signed fsmeta"):
        _apply_journal_ops(idx, [["put", ["a.bin", 0]]])


def test_physical_repair_from_unchanged_negative_reproducer(tmp_path):
    """The J24G46 source-exact probe is preserved; the acceptance result flips."""
    receipt = tmp_path / "physical.json"
    p = subprocess.run(
        [sys.executable, "research/j24g46/probe_journal_xattr_identity.py", str(receipt)],
        capture_output=True, text=True,
    )
    assert p.returncode == 0, p.stdout[-5000:] + p.stderr[-5000:]
    result = json.loads(receipt.read_text())
    assert result["stable_control_correct"] is True or sys.platform == "win32"
    if NATIVE_XATTRS:
        assert result["decision"] == "POSITIONAL_IDENTITY_PRESERVED", result["decision"]
        assert result["insert_metadata_correct"] is True
        assert result["compact_metadata_correct"] is True
        assert result["physical_misapplication"] is False
        key = "com.fcmo.cmpct.j24g46" if sys.platform == "darwin" else "user.cmpct_j24g46"
        for field in ("lexical_insert", "insert_compact"):
            mapping = result[field]["xattrs_by_logical_name"]
            assert key in mapping["z-owner.bin"]
            assert key not in mapping.get("a-inserted.bin", {})
        assert result["restored_native_attributes"]["z-owner.bin"]["binary_value_correct"]
        assert not result["restored_native_attributes"]["a-inserted.bin"]["binary_value_correct"]
    else:
        assert result["decision"] == "WINDOWS_CONTENT_ONLY_NO_XATTR_POSITIVE"


def test_real_rename_delete_and_64th_generation_checkpoint(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    original = source / "z-owner.bin"
    original.write_bytes(b"owned-original\x00" * 30)
    added = tmp_path / "added.bin"
    added.write_bytes(b"new-unrelated\xff" * 20)
    if NATIVE_XATTRS:
        _set_native(original)
        assert _get_native(original) == VALUE
    archive = tmp_path / "journal.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)

    # The 64th update must checkpoint; Reader-only fixes would not suffice.
    for _ in range(63):
        append_update(archive, "z-owner.bin", original)
    append_update(archive, "a-added.bin", added)
    with CMPCT(archive) as ar:
        assert ar.delta_depth == 0, "must have materialized full checkpoint"
        assert ar.verify() == 2
        assert ar.read("z-owner.bin") == original.read_bytes()
        assert ar.read("a-added.bin") == added.read_bytes()
        if NATIVE_XATTRS:
            assert "z-owner.bin" in _names_metadata(ar)
            assert "a-added.bin" not in _names_metadata(ar)

    append_rename(archive, "z-owner.bin", "b-renamed.bin")
    with CMPCT(archive) as ar:
        assert ar.verify() == 2
        if NATIVE_XATTRS:
            assert "b-renamed.bin" in _names_metadata(ar)
            assert "a-added.bin" not in _names_metadata(ar)

    append_delete(archive, "a-added.bin")
    with CMPCT(archive) as ar:
        assert ar.verify() == 1
        assert [r[0] for r in ar.files] == ["b-renamed.bin"]
        if NATIVE_XATTRS:
            assert "b-renamed.bin" in _names_metadata(ar)
        restored = tmp_path / "out"
        ar.extractall(restored, require_xattrs=NATIVE_XATTRS)
    assert (restored / "b-renamed.bin").read_bytes() == original.read_bytes()
    if NATIVE_XATTRS:
        assert _get_native(restored / "b-renamed.bin") == VALUE


def test_seeded_path_identity_state_machine():
    """Independent name-keyed state model across 500 mixed signed journal mutations.

    This is deliberately not another implementation of the positional remap:
    the oracle's ground truth never uses file ordinals.
    """
    import random

    rng = random.Random(20261029)
    names = [f"file-{n:04d}.bin" for n in (30, 70, 110, 150, 190)]
    rows = [[name, 0] for name in names]
    expected_attrs = {name: [["user.seed", name.encode()]] for name in names if name in (names[0], names[-1])}
    expected_owner = {name: [100 + i, 200 + i] for i, name in enumerate(names) if i % 2}
    idx = {
        "files": rows,
        "fsmeta": {
            "owner": [7, 8],
            "owner_overrides": [[names.index(name), *values] for name, values in expected_owner.items()],
            "xattrs": [[names.index(name), records] for name, records in expected_attrs.items()],
        },
    }
    next_serial = 1
    for step in range(500):
        available = sorted(r[0] for r in idx["files"])
        action = rng.choice(("insert", "replace", "delete", "rename", "delete_recreate"))
        if not available or (action == "delete" and len(available) == 1):
            action = "insert"
        if action == "insert":
            name = f"new-{next_serial:06d}.bin"
            next_serial += 1
            ops = [["put", [name, 0]]]
        elif action == "replace":
            name = rng.choice(available)
            ops = [["put", [name, step]]]
        elif action == "delete":
            name = rng.choice(available)
            ops = [["del", name]]
            expected_attrs.pop(name, None)
            expected_owner.pop(name, None)
        elif action == "rename":
            old = rng.choice(available)
            name = f"renamed-{next_serial:06d}.bin"
            next_serial += 1
            ops = [["ren", old, name]]
            if old in expected_attrs:
                expected_attrs[name] = expected_attrs.pop(old)
            if old in expected_owner:
                expected_owner[name] = expected_owner.pop(old)
        else:
            name = rng.choice(available)
            ops = [["del", name], ["put", [name, step]]]
            expected_attrs.pop(name, None)
            expected_owner.pop(name, None)

        _apply_journal_ops(idx, ops)
        new_names = [r[0] for r in idx["files"]]
        assert new_names == sorted(new_names), (step, action)
        assert len(new_names) == len(set(new_names)), (step, action)
        actual_attrs = {new_names[rec[0]]: rec[1] for rec in idx["fsmeta"]["xattrs"]}
        actual_owner = {new_names[rec[0]]: rec[1:] for rec in idx["fsmeta"]["owner_overrides"]}
        assert actual_attrs == expected_attrs, (step, action, actual_attrs, expected_attrs)
        assert actual_owner == expected_owner, (step, action, actual_owner, expected_owner)
        assert idx["fsmeta"]["owner"] == [7, 8]


@pytest.mark.parametrize("mutation", ["delete", "rename"])
def test_depth_64_checkpoint_delete_and_rename_rekey(tmp_path, mutation):
    """Writer must preserve the *other* member's xattr through a full checkpoint.

    This closes the Reader-only-fix gap on 64th-operation delete/rename,
    independently of the depth-64 put case above.
    """
    source = tmp_path / "source"
    source.mkdir()
    earlier = source / "a-unowned.bin"
    earlier.write_bytes(b"unowned-member" * 17)
    owner = source / "z-owner.bin"
    owner.write_bytes(b"owner-member" * 31)
    if NATIVE_XATTRS:
        _set_native(owner)
        assert _get_native(owner) == VALUE
    archive = tmp_path / "checkpoint.cmpct"
    Builder(source, workers=1, reproducible=False).build(archive)

    # 63 same-name writes deliberately do not perturb row order.
    for _ in range(63):
        append_update(archive, "z-owner.bin", owner)

    if mutation == "delete":
        append_delete(archive, "a-unowned.bin")
        expected = ["z-owner.bin"]
    else:
        append_rename(archive, "a-unowned.bin", "zz-after.bin")
        expected = ["z-owner.bin", "zz-after.bin"]

    with CMPCT(archive) as ar:
        assert ar.delta_depth == 0, "64th operation must be a full checkpoint"
        assert [r[0] for r in ar.files] == expected
        assert ar.verify() == len(expected)
        if NATIVE_XATTRS:
            assert "z-owner.bin" in _names_metadata(ar)
            assert not any(k != "z-owner.bin" for k in _names_metadata(ar))
        output = tmp_path / "materialized"
        ar.extractall(output, require_xattrs=NATIVE_XATTRS)
    assert (output / "z-owner.bin").read_bytes() == owner.read_bytes()
    if NATIVE_XATTRS:
        assert _get_native(output / "z-owner.bin") == VALUE
        if mutation == "rename":
            assert _get_native(output / "zz-after.bin") is None
