"""Source-exact Writer × forensic-salvage interaction on one real r24 archive.

This court grants neither authenticated salvage nor lock-free snapshot semantics.
It proves that the Writer's commit namespace and the *physical* header-candidate
enumerator can coexist without silently upgrading historical candidates into
committed objects or requiring a second unsafe writer pathway.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx


def _setup(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    rnd = random.Random(263266)
    obsolete = rnd.randbytes(8192)
    current = rnd.randbytes(8192)
    (root / "obsolete.bin").write_bytes(obsolete)
    (root / "current.bin").write_bytes(current)
    archive = tmp_path / "source.cmpct"
    Builder(root, workers=1).build(archive)
    return archive, obsolete, current


def _rows(archive: Path):
    found = tx.recover_blob_records(archive)
    assert found, "actual CMPCT Builder must produce physical framed candidates"
    assert all(row["verification"] == "unverified" for row in found)
    assert all(row["generation_membership"] == "unknown" for row in found)
    assert all(isinstance(row["offset"], int) and row["offset"] >= 0 for row in found)
    assert [row["offset"] for row in found] == sorted(row["offset"] for row in found)
    return found


def test_committed_namespace_evolves_but_old_physical_candidates_remain_unverified(tmp_path):
    archive, obsolete, current = _setup(tmp_path)
    initial = _rows(archive)
    with CMPCT(archive) as reader:
        assert reader.read("obsolete.bin") == obsolete
        assert reader.read("current.bin") == current
        reader.verify()

    tx.append_delete(archive, "obsolete.bin")
    after_delete = _rows(archive)
    # A committed deletion does not retroactively erase older physical blobs.
    initial_claims = {(r["offset"], r["sha256"]) for r in initial}
    assert initial_claims <= {(r["offset"], r["sha256"]) for r in after_delete}
    with CMPCT(archive) as reader:
        with pytest.raises(KeyError):
            reader.read("obsolete.bin")
        assert reader.read("current.bin") == current
        reader.verify()

    replacement = tmp_path / "replacement.bin"
    replacement_payload = random.Random(263267).randbytes(12288)
    replacement.write_bytes(replacement_payload)
    result = tx.append_update(archive, "current.bin", replacement)
    assert result["member"] == "current.bin"
    tx.append_rename(archive, "current.bin", "final.bin")

    final = _rows(archive)
    assert {(r["offset"], r["sha256"]) for r in after_delete} <= {
        (r["offset"], r["sha256"]) for r in final
    }
    assert all(row["generation_membership"] == "unknown" for row in final)
    with CMPCT(archive) as reader:
        assert reader.read("final.bin") == replacement_payload
        for absent in ("obsolete.bin", "current.bin"):
            with pytest.raises(KeyError):
                reader.read(absent)
        reader.verify()


def test_forensic_cli_can_read_while_writer_owns_transaction_lease(tmp_path):
    archive, _, _ = _setup(tmp_path)
    expected = _rows(archive)
    # A read-only forensic enumerator never tries to acquire an exclusive
    # writer lock. On Windows the real writer owns its distant lock sentinel;
    # on POSIX it owns the inode-wide advisory flock.
    with tx._cooperative_writer_lease(archive):
        during = _rows(archive)
        proc = subprocess.run(
            [sys.executable, "-m", "cmpct.cli", "recover-blobs", str(archive)],
            text=True, capture_output=True, timeout=30, check=True,
        )
    assert during == expected
    assert json.loads(proc.stdout) == expected
    assert proc.stdout == json.dumps(expected, indent=2) + "\n"
    assert all(row["verification"] == "unverified" for row in json.loads(proc.stdout))
