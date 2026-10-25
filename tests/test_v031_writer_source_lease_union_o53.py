"""O53: actual source-descriptor admission composed with serialized Writer and salvage.

This is an exact revision-24 product interaction court, not a transactional-snapshot proof.
Independent O51 and #311 original tests remain unchanged and run alongside it.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.transactions as tx


def _archive(tmp_path: Path):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "old.bin").write_bytes(b"old-membership" * 127)
    (root / "current.bin").write_bytes(b"retained-payload" * 211)
    archive = tmp_path / "original.cmpct"
    Builder(root, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        reader.verify()
    return archive


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.skipif(os.name != "posix" or not hasattr(os, "mkfifo"),
                    reason="FIFO is a POSIX-specific blocking-open adversary")
def test_fifo_inside_serialized_writer_preserves_footer_salvage_and_future_progress(tmp_path):
    archive = _archive(tmp_path)
    expected_hash = _digest(archive)
    expected_candidates = tx.recover_blob_records(archive)
    fifo = tmp_path / "no-writer.fifo"
    os.mkfifo(fifo, 0o600)
    child = subprocess.run(
        [sys.executable, "-m", "cmpct", "update", str(archive), "current.bin", str(fifo)],
        capture_output=True, text=True, check=False, timeout=4,
    )
    assert child.returncode != 0, (child.stdout, child.stderr)
    assert "not a regular file" in child.stderr
    assert _digest(archive) == expected_hash, "failed source opened a new generation"
    assert tx.recover_blob_records(archive) == expected_candidates

    # A failed source must release the same archive's cooperative writer lease.
    regular = tmp_path / "replacement.bin"
    payload = bytes((i * 17 + 31) % 256 for i in range(12_345))
    regular.write_bytes(payload)
    updated = subprocess.run(
        [sys.executable, "-m", "cmpct", "update", str(archive), "current.bin", str(regular)],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert updated.returncode == 0, (updated.stdout, updated.stderr)
    with CMPCT(archive) as reader:
        assert reader.read("current.bin") == payload
        assert reader.read("old.bin") == b"old-membership" * 127
        reader.verify()
    # Salvage remains a deliberately UNAUTHENTICATED candidate census.
    candidates = tx.recover_blob_records(archive)
    assert len(candidates) >= len(expected_candidates)
    assert {(r["offset"], r["sha256"]) for r in expected_candidates} <= {
        (r["offset"], r["sha256"]) for r in candidates
    }


@pytest.mark.skipif(os.name != "posix",
                    reason="deterministic flock waiting court is POSIX-specific")
def test_descriptor_update_cannot_preempt_an_existing_archive_writer_lease(tmp_path):
    archive = _archive(tmp_path)
    initial = _digest(archive)
    payload = b"new-under-serialized-lease" * 223
    source = tmp_path / "replace.bin"
    source.write_bytes(payload)
    marker = tmp_path / "attempted-lock.marker"
    # Instrument *outside* the real transaction lease; do not replace its
    # operating-system locking or change the Writer's source admission code.
    child_code = r"""
import sys
from pathlib import Path
import cmpct.transactions as tx
real_lease = tx._cooperative_writer_lease
marker = Path(sys.argv[1])
def marked(archive):
    marker.write_text("attempting lease")
    return real_lease(archive)
tx._cooperative_writer_lease = marked
tx.append_update(Path(sys.argv[2]), "current.bin", Path(sys.argv[3]))
"""
    with tx._cooperative_writer_lease(archive):
        proc = subprocess.Popen(
            [sys.executable, "-c", child_code, str(marker), str(archive), str(source)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 7
            while not marker.exists() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            assert marker.exists(), "child failed before reaching actual lease admission"
            assert proc.poll() is None, "child bypassed the held writer lease"
            assert _digest(archive) == initial, "uncommitted update changed archive"
        finally:
            # The parent's context releases the actual lock on exit below.
            pass
    try:
        stdout, stderr = proc.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("writer did not resume after releasing a cooperative lease")
    assert proc.returncode == 0, (stdout, stderr)
    with CMPCT(archive) as reader:
        assert reader.read("current.bin") == payload
        reader.verify()


def test_source_admission_survives_delete_update_rename_and_physical_salvage(tmp_path):
    archive = _archive(tmp_path)
    initial = tx.recover_blob_records(archive)
    tx.append_delete(archive, "old.bin")
    before = _digest(archive)
    replacement = tmp_path / "new.bin"
    payload = b"mixed-operations-payload" * 911
    replacement.write_bytes(payload)
    tx.append_update(archive, "current.bin", replacement)
    tx.append_rename(archive, "current.bin", "final.bin")
    assert _digest(archive) != before
    with CMPCT(archive) as reader:
        assert reader.read("final.bin") == payload
        with pytest.raises(KeyError):
            reader.read("old.bin")
        with pytest.raises(KeyError):
            reader.read("current.bin")
        reader.verify()
    later = tx.recover_blob_records(archive)
    assert {(r["offset"], r["sha256"]) for r in initial} <= {
        (r["offset"], r["sha256"]) for r in later
    }
    assert all(r["verification"] == "unverified"
               and r["generation_membership"] == "unknown" for r in later)
