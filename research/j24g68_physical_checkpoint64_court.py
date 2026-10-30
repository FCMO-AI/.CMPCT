#!/usr/bin/env python3
"""J24G68: authentic public 64th-checkpoint xattr identity and fallback court.

This is an isolated physical research witness, not a product Reader/Writer edit.
The inherited J24G66 instrument builds the exact earlier 63 mixed generations.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

import msgpack

from cmpct import _xattrs, transactions
from cmpct.journal_replay import _apply_journal_ops
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import footer_chain, sha256_file
from j24g66_signed_fsmeta_physical_court import projection, xget_opt

PARENT = "f9246d33748fb97532d711f0a81760c3505a7a4a"
PREREG = "911fe68451dabb5ad8b238e8dc5ea8a798ce37fd"
REPLAY_BLOB = "03743ca2a06c022c2ec64243a90fe373cf91e899"
OLD = "r0000.dat"
NEW = "z-checkpoint-owner.dat"


def attest() -> dict:
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for ancestor in (PARENT, PREREG):
        assert subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                              cwd=root, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0, (ancestor, head)
    blob = subprocess.check_output(
        ["git", "rev-parse", "HEAD:src/cmpct/journal_replay.py"],
        cwd=root, text=True).strip()
    assert blob == REPLAY_BLOB, ("source replay drift", blob)
    return {"head": head, "parent": PARENT, "prereg": PREREG, "replay_blob": blob}


def identical_bytes(left: dict, right: dict) -> None:
    assert left == right, "index object difference"
    assert msgpack.packb(left, use_bin_type=True) == msgpack.packb(
        right, use_bin_type=True), "index MessagePack byte difference"


def main() -> None:
    identity = attest()
    assert sys.platform in ("linux", "darwin"), "xattr host required"
    assert _xattrs.can_list() and _xattrs.can_set(), "xattr capability missing"
    out = Path(os.environ.get("J24G68_EVIDENCE_DIR", "evidence"))
    out.mkdir(parents=True, exist_ok=True)
    before = out / "j24g68-before.cmpct"
    after = out / "j24g68-after.cmpct"
    parent_receipt = out / "j24g68-parent-result.json"
    env = dict(os.environ)
    env.update({
        "J24G66_PHYSICAL": str(before.resolve()),
        "J24G66_RESULT": str(parent_receipt.resolve()),
    })
    parent = subprocess.run(
        [sys.executable, "research/j24g66_signed_fsmeta_physical_court.py"],
        cwd=Path(__file__).resolve().parents[1], env=env,
        capture_output=True, text=True, timeout=240,
    )
    (out / "j24g68-parent-stdout.log").write_text(
        parent.stdout + "\n---stderr---\n" + parent.stderr, encoding="utf-8")
    assert parent.returncode == 0, ("inherited physical J24G66 failed", parent.returncode,
                                    parent.stderr[-1200:])
    prior_receipt = json.loads(parent_receipt.read_text())
    assert prior_receipt["decision"] == "PHYSICAL_SIGNED_XATTR_IDENTITY_PASS"
    assert before.is_file() and prior_receipt["archive_sha256"] == sha256_file(before)
    assert prior_receipt["depth"] == 63 and prior_receipt["footer_count"] == 64
    before_raw = before.read_bytes()
    original_stat = before.stat()
    prior_chain = footer_chain(before)
    assert len(prior_chain) == 64 and prior_chain[0]["kind"] == 1
    assert all(item["kind"] == 1 for item in prior_chain[:63])
    before_tail = prior_chain[0]["offset"]
    with CMPCT(before) as reader:
        assert reader.delta_depth == 63
        before_index = copy.deepcopy(reader.index)
        before_data = {name: reader.read(name) for name in reader.by}
        before_xattrs = projection(reader.index)
        assert len(before_data) == prior_receipt["final_members"] == 118
        assert OLD in before_data and NEW not in before_data
        assert OLD in before_xattrs and before_xattrs[OLD], "tagged rename witness absent"
        assert "f0042.dat" in before_data and "f0042.dat" not in before_xattrs
        assert reader.verify() == 118
    assert len(prior_receipt["final_tagged_paths"]) == 5
    shutil.copyfile(before, after)
    before_after_inode = after.stat().st_ino
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    transactions.append_rename(after, OLD, NEW)
    append_wall_ns = time.perf_counter_ns() - w0
    append_cpu_ns = time.process_time_ns() - c0
    assert after.stat().st_ino == before_after_inode, "public append changed inode"
    after_raw = after.read_bytes()
    assert after_raw.startswith(before_raw), "public checkpoint rewrote signed prefix"
    assert len(after_raw) > len(before_raw), "checkpoint did not append bytes"
    checkpoint_chain = footer_chain(after)
    assert len(checkpoint_chain) == 1 and checkpoint_chain[0]["kind"] == 0
    assert checkpoint_chain[0]["prev"] == before_tail, "new checkpoint not chained to previous commit"
    assert after.stat().st_size == len(after_raw)

    expected = copy.deepcopy(before_index)
    _apply_journal_ops(expected, [["ren", OLD, NEW]])
    expected_data = dict(before_data)
    expected_data[NEW] = expected_data.pop(OLD)
    expected_xattrs = copy.deepcopy(before_xattrs)
    expected_xattrs[NEW] = expected_xattrs.pop(OLD)
    assert "f0042.dat" not in expected_xattrs

    with CMPCT(after) as reader:
        assert reader.delta_depth == 0, "64th update did not checkpoint"
        assert reader.latest_footer_pos == checkpoint_chain[0]["offset"]
        identical_bytes(expected, reader.index)
        assert projection(reader.index) == expected_xattrs
        assert reader.verify() == 118
        assert set(reader.by) == set(expected_data)
        for name, raw in expected_data.items():
            assert reader.read(name) == raw, ("post-checkpoint content", name)
        dest = out / "j24g68-strict-extract"
        reader.extractall(dest, require_xattrs=True)
        tracked = tuple(prior_receipt["xattr_keys"])
        for name, raw in expected_data.items():
            extracted = dest / name
            assert extracted.is_file() and extracted.read_bytes() == raw, ("extract", name)
            for key in tracked:
                assert xget_opt(extracted, key) == expected_xattrs.get(name, {}).get(key), (
                    "signed xattr rekey lost/resurrected", name, key)
    pf = preflight_archive(after)
    assert pf["files"] == 118 and pf["delta_depth"] == 0, pf
    assert sha256_file(before) == prior_receipt["archive_sha256"]

    corrupt = out / "j24g68-corrupt-checkpoint.cmpct"
    shutil.copyfile(after, corrupt)
    with corrupt.open("r+b") as f:
        f.seek(-1, os.SEEK_END)
        tail = f.read(1)
        f.seek(-1, os.SEEK_END)
        f.write(bytes([tail[0] ^ 0x01]))
    assert sha256_file(corrupt) != sha256_file(after)
    with CMPCT(corrupt) as reader:
        assert reader.delta_depth == 63, "corrupt checkpoint did not recover prior signed chain"
        identical_bytes(reader.index, before_index)
        assert projection(reader.index) == before_xattrs
        assert reader.verify() == len(before_data)
        for name, raw in before_data.items():
            assert reader.read(name) == raw, ("recovered original content", name)

    # Avoid uploading hundreds of extracted files: both source archives and
    # source-independent audit receipts remain the durable raw evidence.
    shutil.rmtree(out / "j24g68-strict-extract")
    corrupt.unlink()
    receipt = {
        "schema": "cmpct-j24g68-checkpoint64-v1",
        "decision": "J24G68_PHYSICAL_CHECKPOINT64_FIDELITY_PASS",
        "source": identity, "host": platform.platform(),
        "python": platform.python_version(),
        "parent_receipt_sha256": hashlib.sha256(parent_receipt.read_bytes()).hexdigest(),
        "prior_archive_sha256": sha256_file(before),
        "checkpoint_archive_sha256": sha256_file(after),
        "prior_archive_bytes": len(before_raw),
        "checkpoint_archive_bytes": len(after_raw),
        "checkpoint_appended_bytes": len(after_raw) - len(before_raw),
        "prefix_exact": True, "same_inode_on_append": True,
        "prior_footer_count": len(prior_chain),
        "last_prior_footer_offset": before_tail,
        "checkpoint_footer_offset": checkpoint_chain[0]["offset"],
        "checkpoint_previous_footer_offset": checkpoint_chain[0]["prev"],
        "prior_delta_depth": 63, "new_delta_depth": 0,
        "source_member": OLD, "target_member": NEW,
        "final_members": len(expected_data),
        "logical_final_payload_bytes": sum(map(len, expected_data.values())),
        "final_signed_xattr_records": len(expected_xattrs),
        "final_index_msgpack_sha256": hashlib.sha256(
            msgpack.packb(expected, use_bin_type=True)).hexdigest(),
        "checkpoint_writer_wall_ns": append_wall_ns,
        "checkpoint_writer_cpu_ns": append_cpu_ns,
        "strict_extraction_full_members": 118,
        "corrupt_last_footer_recovers_prior_signed_generation": True,
        "limitations": [
            "No full-product cold-open A/B, create/extract benchmark, or native RSS",
            "No privileged owner override or hardlink inode-alias proof",
            "No simultaneous malicious publication or complete recovery matrix",
            "No Windows physical xattr or official release parity",
            "Unmerged research parent, not released CMPCT behavior",
        ],
    }
    result = out / "j24g68-result.json"
    result.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("J24G68_DECISION", receipt["decision"])
    print("J24G68_HEAD", identity["head"])
    print("J24G68_ARCHIVE_SHA256", receipt["checkpoint_archive_sha256"])
    print("J24G68_WRITER_APPEND_BYTES", receipt["checkpoint_appended_bytes"])


if __name__ == "__main__":
    main()
