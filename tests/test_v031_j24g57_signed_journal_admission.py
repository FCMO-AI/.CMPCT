"""J24G57 acceptance: fail-closed r24 journal operations and footer semantics.

These are real Builder-produced r24 archives with appended digest-consistent
generations. Unlike J24G56's negative court, green means the candidate fixes
the reproduced faults. A separate non-CMPCT referee checks the physical wire.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import struct
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.journal_replay import (
    JournalReplayAdmissionError,
    _apply_journal_ops,
)
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import ValidationError, preflight_archive

_FTR = struct.Struct("<8sBBBBQQQ32s")


def _original(tmp_path: Path):
    tree = tmp_path / "tree"
    tree.mkdir()
    payloads = {"a.bin": b"A" * 117, "z.bin": b"Z" * 231}
    for name, payload in payloads.items():
        (tree / name).write_bytes(payload)
    archive = tmp_path / "case.cmpct"
    Builder(tree, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as original:
        assert original.verify() == 2
        original_footer = original.latest_footer_pos
    assert preflight_archive(archive)["files"] == 2
    return archive, original_footer, payloads


def _record(archive: Path, label: str, prior: int, latest: int, decision: str):
    dirname = os.getenv("J24G57_EVIDENCE_DIR")
    if not dirname:
        return
    root = Path(dirname)
    root.mkdir(parents=True, exist_ok=True)
    name = f"{label}.cmpct"
    shutil.copyfile(archive, root / name)
    state = {
        "case": label,
        "archive": name,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "prior": prior,
        "latest": latest,
        "decision": decision,
    }
    (root / f"{label}.json").write_text(json.dumps(state, indent=2, sort_keys=True))


def _latest_footer(archive: Path, pos: int, previous: int):
    physical = archive.read_bytes()
    magic, kind, codec, flags, reserved, cs, us, prev, digest = _FTR.unpack_from(physical, pos)
    assert magic == b"CMPTF24\\0".replace(b"\\0", b"\x00")
    assert (kind, flags, reserved, prev) == (1, 0, 0, previous)
    assert codec in (0, 1) and cs > 0 and us > 0
    assert pos + _FTR.size == len(physical)
    assert len(digest) == 32


def test_valid_known_delete_remains_admitted(tmp_path):
    archive, prior, payloads = _original(tmp_path)
    latest, _ = _append_generation(archive, {"blobs": [], "ops": [["del", "a.bin"]]}, prior)
    _latest_footer(archive, latest, prior)
    with CMPCT(archive) as ar:
        assert ar.latest_footer_pos == latest
        assert set(ar.by) == {"z.bin"}
        assert ar.verify() == 1
        assert ar.read("z.bin") == payloads["z.bin"]
    pf = preflight_archive(archive)
    assert pf["latest_footer"] == latest and pf["files"] == 1
    _record(archive, "known_delete", prior, latest, "accept_latest")


@pytest.mark.parametrize(
    ("label", "ops"),
    [
        ("unknown_only", [["future_op", "z.bin"]]),
        ("unknown_then_delete", [["future_op", "z.bin"], ["del", "a.bin"]]),
        ("delete_then_unknown", [["del", "a.bin"], ["future_op", "z.bin"]]),
        ("malformed_del", [["del", "a.bin"], ["del"]]),
        ("malformed_ren", [["ren", "a.bin"]]),
    ],
)
def test_signed_unknown_or_malformed_operation_refused(tmp_path, label, ops):
    archive, prior, _ = _original(tmp_path)
    latest, _ = _append_generation(archive, {"blobs": [], "ops": ops}, prior)
    _latest_footer(archive, latest, prior)
    # A SHA-consistent but impossible *committed* instruction is a hard
    # admission failure, not a silently ignored partial transaction.
    with pytest.raises(OSError, match="unsupported committed r24 journal operation"):
        CMPCT(archive)
    with pytest.raises(ValidationError, match="transaction operation|put operation"):
        preflight_archive(archive)
    _record(archive, label, prior, latest, "reject_committed_instruction")


@pytest.mark.parametrize(("field", "byte_index"), [("flags", 10), ("reserved", 11)])
def test_invalid_footer_header_recovers_previous_generation(tmp_path, field, byte_index):
    archive, prior, payloads = _original(tmp_path)
    latest, _ = _append_generation(archive, {"blobs": [], "ops": [["del", "a.bin"]]}, prior)
    _latest_footer(archive, latest, prior)
    physical = bytearray(archive.read_bytes())
    assert physical[latest + byte_index] == 0
    physical[latest + byte_index] = 1
    archive.write_bytes(physical)
    with CMPCT(archive) as ar:
        assert ar.latest_footer_pos == prior
        assert set(ar.by) == set(payloads)
        assert ar.verify() == 2
    pf = preflight_archive(archive)
    assert pf["latest_footer"] == prior and pf["files"] == 2
    _record(archive, f"invalid_{field}", prior, latest, "recover_previous")


def test_sha_corrupt_footer_remains_recoverable(tmp_path):
    archive, prior, payloads = _original(tmp_path)
    latest, _ = _append_generation(archive, {"blobs": [], "ops": [["del", "a.bin"]]}, prior)
    raw = bytearray(archive.read_bytes())
    raw[-1] ^= 1  # only footer digest; real payload and earlier generation unchanged
    archive.write_bytes(raw)
    with CMPCT(archive) as ar:
        assert ar.latest_footer_pos == prior and set(ar.by) == set(payloads)
        assert ar.verify() == 2
    pf = preflight_archive(archive)
    assert pf["latest_footer"] == prior and pf["files"] == 2
    _record(archive, "bad_sha", prior, latest, "recover_previous")


def test_shared_replay_prevalidates_whole_operation_list_before_mutation():
    original = {
        "files": [["a.bin"], ["z.bin"]],
        "fsmeta": {"xattrs": [[1, [["user.tag", b"v"]]]]},
    }
    for bad in (
        [["del", "a.bin"], ["future_op", "z.bin"]],
        [["del", "a.bin"], ["ren", "z.bin"]],
        [["del", "a.bin"], ["del"]],
        [["put", ["z.bin"]], ["future_op", "a.bin"]],
    ):
        index = copy.deepcopy(original)
        with pytest.raises(JournalReplayAdmissionError):
            _apply_journal_ops(index, bad)
        assert index == original
