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


def test_exact_immutable_parent_and_combined_writer_emit_identical_supported_archive_bytes(tmp_path):
    """A/B executes #311's exact parent code, not a same-function monkeypatch."""
    import subprocess
    import types
    import sys
    from cmpct import transactions

    archive = _archive(tmp_path)
    frozen_base = "c1e75370281ca6b721ef10edf1ed15e6c5ef48f7"
    # A generic CI checkout can be shallow and omit the exact historical
    # parent Git object. Preserve the original *entire source* as a fixture,
    # independently enforcing its Git blob SHA, rather than silently skipping
    # this strongest A/B comparison or using an invented historical stub.
    frozen_fixture = Path(__file__).with_name("o53_frozen_311_transactions.py")
    try:
        historical_bytes = subprocess.check_output(
            ["git", "show", frozen_base + ":src/cmpct/transactions.py"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        historical_bytes = frozen_fixture.read_bytes()
    import hashlib
    blob_header = b"blob " + str(len(historical_bytes)).encode("ascii") + b"\0"
    assert hashlib.sha1(blob_header + historical_bytes).hexdigest() == (
        "a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee"
    ), "frozen #311 original Writer blob mismatch"
    historical_src = historical_bytes.decode("utf-8")
    # Compile the frozen historical Writer with real installed cmpct dependencies.
    # Keep every #311 lock/salvage/Reader behavior, replacing only admission in O53.
    module = types.ModuleType("cmpct._o53_exact_parent")
    module.__file__ = "<git:" + frozen_base + ":src/cmpct/transactions.py>"
    module.__package__ = "cmpct"
    sys.modules[module.__name__] = module
    try:
        exec(compile(historical_src, module.__file__, "exec"), module.__dict__)
        baseline = tmp_path / "original-writer.cmpct"
        candidate = tmp_path / "descriptor-writer.cmpct"
        original = archive.read_bytes()
        baseline.write_bytes(original)
        candidate.write_bytes(original)
        source = tmp_path / "stable-update.bin"
        content = bytes((i * 41 + 13) & 255 for i in range(21_073))
        source.write_bytes(content)
        module.append_update(baseline, "current.bin", source)
        transactions.append_update(candidate, "current.bin", source)
        assert baseline.read_bytes() == candidate.read_bytes(), (
            "exact historical #311 vs O53 emitted different complete r24 bytes"
        )
        with CMPCT(candidate) as reader:
            assert reader.read("current.bin") == content
            reader.verify()

        # Held-out structural transfer: the same real historical-vs-composed
        # Writer A/B must survive the >4*CHUNK CDC path and a second
        # mostly-reused CDC generation. Do not infer generality from RAW-only
        # small-file parity.
        from cmpct.codec import CHUNK, S_CDC
        large = bytearray(bytes((i * 37 + 11) & 255 for i in range(256))
                          * (5 * CHUNK // 256 + 1))
        large = large[:5 * CHUNK + 173]
        assert len(large) > 4 * CHUNK
        for round_id in range(2):
            if round_id:
                large[len(large) // 2] ^= 0x7f
            source.write_bytes(large)
            module.append_update(baseline, "current.bin", source)
            transactions.append_update(candidate, "current.bin", source)
            old_bytes, new_bytes = baseline.read_bytes(), candidate.read_bytes()
            assert old_bytes == new_bytes, (
                "CDC/update physical archive bytes differ from actual #311 parent",
                round_id, len(old_bytes), len(new_bytes)
            )
            with CMPCT(candidate) as reader:
                assert reader.read("current.bin") == large
                assert reader.by["current.bin"][6][0] == S_CDC
                reader.verify()
            print(f"O53_CDC_ROUND_{round_id}_ARCHIVE_BYTES={len(new_bytes)}")
    finally:
        sys.modules.pop(module.__name__, None)
