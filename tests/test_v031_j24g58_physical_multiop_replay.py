"""J24G58 real r24 Builder->signed footer->Reader/preflight transfer.

This is installed-source physical product correctness for large accepted operation
batches, NOT a compression/release/RSS claim. The frozen parent helper is the
independent reference for the identical authenticated base-state mutation.
"""
from __future__ import annotations

import copy
import hashlib
import runpy
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import preflight_archive


def _parent():
    path = Path(__file__).resolve().parents[1] / "research" / "j24g58_frozen_parent_replay.py"
    data = path.read_bytes()
    assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest() == (
        "03743ca2a06c022c2ec64243a90fe373cf91e899"
    )
    return runpy.run_path(str(path))["_apply_journal_ops"]


@pytest.mark.parametrize("family", ["rename_all", "delete_reinsert"])
def test_large_authenticated_signed_journal_equals_exact_parent(tmp_path, family):
    source = tmp_path / "source"
    source.mkdir()
    payloads = {}
    for i in range(128):
        name = f"old{i:06}.bin"
        content = (f"exact-{i:06}-".encode() * 16) + bytes([i])
        (source / name).write_bytes(content)
        payloads[name] = content
    archive = tmp_path / "base.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as base:
        assert base.verify() == 128
        parent_state = copy.deepcopy(base.index)
        original_footer = base.latest_footer_pos
    assert preflight_archive(archive)["files"] == 128

    if family == "rename_all":
        ops = [["ren", f"old{i:06}.bin", f"new{i:06}.bin"] for i in range(128)]
        expected_payloads = {f"new{i:06}.bin": payloads[f"old{i:06}.bin"]
                             for i in range(128)}
    else:
        ops = [["del", f"old{i:06}.bin"] for i in range(64)]
        old_rows = {row[0]: row for row in parent_state["files"]}
        for i in range(64):
            row = copy.deepcopy(old_rows[f"old{i:06}.bin"])
            row[0] = f"fresh{i:06}.bin"
            ops.append(["put", row])
        expected_payloads = {
            **{f"old{i:06}.bin": payloads[f"old{i:06}.bin"] for i in range(64, 128)},
            **{f"fresh{i:06}.bin": payloads[f"old{i:06}.bin"] for i in range(64)},
        }

    # Compare exact helper semantics *before* reading the physical new index.
    reference = _parent()(copy.deepcopy(parent_state), copy.deepcopy(ops), max_files=128)
    latest, _ = _append_generation(archive, {"blobs": [], "ops": ops}, original_footer)
    assert latest > original_footer
    assert preflight_archive(archive)["files"] == 128
    with CMPCT(archive) as reader:
        assert reader.latest_footer_pos == latest
        assert reader.index == reference
        assert set(reader.by) == set(expected_payloads)
        assert reader.verify() == 128
        for name in sorted(expected_payloads)[::17]:
            assert reader.read(name) == expected_payloads[name]
