#!/usr/bin/env python3
"""J24G37: installed-r24-compaction pre-open directory-entry interposition court.

This research intentionally expects certain BAD outcomes, documenting their physical
effect, and must never be represented as a product-candidate PASS/release gate.
All writes and interpositions are confined to one TemporaryDirectory.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import tempfile
from unittest.mock import patch

from cmpct.builder import Builder
from cmpct.reader import CMPCT
import cmpct.transactions as transactions


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path) -> dict:
    with CMPCT(path) as ar:
        assert ar.verify()
        return {
            "rows": [(r[0], r[1], r[2], r[3], r[4]) for r in ar.files],
            "sha": {r[0]: ar.file_sha256(r[0]).hex() for r in ar.files if r[1] != 1},
        }


def main() -> None:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise RuntimeError("J24G37 POSIX-only scientific court; no Windows claims")
    observations = []
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g37-product-") as tmp:
        root = Path(tmp)
        source_tree = root / "source-tree"
        source_tree.mkdir()
        (source_tree / "primary.txt").write_bytes((b"exact-archive" * 128) + b"\x00\xfe")
        os.link(source_tree / "primary.txt", source_tree / "alias.txt")
        source_archive = root / "source.cmpct"
        Builder(source_tree, workers=1, reproducible=True).build(source_archive)
        original_sha = sha(source_archive)
        original_snapshot = snapshot(source_archive)

        outside = root / "outside"
        outside.mkdir()
        outside_leaf = outside / "payload.cmpct"
        outside_leaf.write_bytes(b"OUTSIDE MUST REMAIN UNCHANGED")
        outside_sha = sha(outside_leaf)
        actual_open = os.open
        cases = (
            ("no-rebind", "ok"),
            ("symlink-rebind", "reject"),
            ("mode-0755", "reject"),
            ("mode-0755-planted", "reject"),
            ("same-uid-0700", "ok"),
            ("same-uid-0700-planted", "reject"),
        )
        for case, outcome in cases:
            parent = root / case
            parent.mkdir()
            destination = parent / "finished.cmpct"
            initial = b"PREEXISTING-DESTINATION-KEEP"
            destination.write_bytes(initial)
            original_destination_sha = sha(destination)
            touched = []
            planted_marker = b"UNOWNED-PREPLANTED-BY-ACTOR"
            planted_path = None
            renamed_original = None

            def intercepted_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal planted_path, renamed_original
                if (
                    not touched
                    and dir_fd is not None
                    and isinstance(path, str)
                    and ".compact-private-" in path
                    and (flags & os.O_DIRECTORY)
                    and (flags & os.O_NOFOLLOW)
                ):
                    entry = parent / path
                    assert entry.is_dir() and not entry.is_symlink(), "hook must be post-mkdir/pre-dirfd"
                    renamed_original = parent / (path + "-moved")
                    entry.rename(renamed_original)
                    assert renamed_original.is_dir()
                    if case == "symlink-rebind":
                        entry.symlink_to(outside, target_is_directory=True)
                    else:
                        entry.mkdir(mode=0o700)
                        if case.startswith("mode-0755"):
                            entry.chmod(0o755)
                        if "planted" in case:
                            planted_path = entry / "payload.cmpct"
                            planted_path.write_bytes(planted_marker)
                    touched.append({"entry": path, "rebound": case})
                return actual_open(path, flags, mode, dir_fd=dir_fd)

            error = None
            if case == "no-rebind":
                transactions.compact_archive(source_archive, destination)
            else:
                with patch.object(transactions.os, "open", intercepted_open):
                    try:
                        transactions.compact_archive(source_archive, destination)
                    except OSError as exc:
                        error = f"{type(exc).__name__}:{exc.errno}:{exc.strerror}"

            assert sha(source_archive) == original_sha, f"{case}: source mutated"
            assert sha(outside_leaf) == outside_sha, f"{case}: outside sentinel mutated"
            assert destination.is_file() and not destination.is_symlink(), f"{case}: destination type changed"
            assert (len(touched) == 0 if case == "no-rebind" else len(touched) == 1), case
            if outcome == "reject":
                assert error is not None, f"{case}: unexpected acceptance"
                assert sha(destination) == original_destination_sha, f"{case}: existing destination mutated"
            else:
                assert error is None, f"{case}: unexpected rejection {error}"
                assert snapshot(destination) == original_snapshot, f"{case}: logical archive mismatch"

            if planted_path is not None:
                # Negative evidence: candidate cleanup unlinks a payload that the
                # candidate did NOT create after it failed to open its own FD.
                # The actor-created directory may also get removed if now empty.
                observed_planted_preserved = planted_path.is_file()
                assert not observed_planted_preserved, (
                    f"{case}: cleanup behavior changed; re-evaluate preregistered mechanism"
                )
            else:
                observed_planted_preserved = None

            observations.append({
                "case": case,
                "expected_operation": outcome,
                "operation_accepted": error is None,
                "error": error,
                "source_unchanged": sha(source_archive) == original_sha,
                "outside_unchanged": sha(outside_leaf) == outside_sha,
                "destination_unchanged_on_rejection": (
                    sha(destination) == original_destination_sha if outcome == "reject" else None
                ),
                "archive_valid_if_accepted": (
                    snapshot(destination) == original_snapshot if outcome == "ok" else None
                ),
                "interposition_hit": len(touched),
                "actor_preplanted_leaf_preserved": observed_planted_preserved,
                "stage_original_was_moved": renamed_original is not None and renamed_original.is_dir(),
            })
        assert len(observations) == len(cases)
        assert sum(not r["operation_accepted"] for r in observations) == 4
        assert sum(r["actor_preplanted_leaf_preserved"] is False for r in observations) == 2
        assert all(r["source_unchanged"] and r["outside_unchanged"] for r in observations)
    print(json.dumps({
        "schema": "J24G37-preopen-r24-product-court-v1",
        "evidence_class": "UNRELEASED_PRODUCT_CANDIDATE_ADVERSARIAL_RESEARCH",
        "decision": "PREOPEN_NAMESPACE_REJECTION_BUT_UNOWNED_STAGE_LEAF_DELETION_ON_FAILURE",
        "host": platform.platform(),
        "uid": os.geteuid(),
        "source_sha256": original_sha,
        "results": observations,
        "unmeasured": [
            "different-UID attacker with writable parent",
            "Windows HANDLE-based ownership",
            "power-failure and fsync durability",
            "full inherited compaction/conformance",
            "same-UID post-verification archive mutation",
            "archive size/CPU/RSS/temp-I/O full product parity",
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
