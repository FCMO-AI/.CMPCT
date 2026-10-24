#!/usr/bin/env python3
"""Signed conflicting hardlink xattr counterexample for detached O1 (not CMPCT)."""
import json
import os
import tempfile

from v031_posix_byte_tree_o1 import inventory, materialize, preflight, rows_to_wire, seal, source_fixture, unseal


def run():
    if os.name != "posix":
        return {"status": "SKIPPED", "reason": "POSIX only"}
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        source = os.fsencode(directory) + b"/src"
        os.mkdir(source)
        if not source_fixture(source, "portable"):
            return {"status": "SKIPPED", "reason": "Linux xattrs unavailable"}
        expected = inventory(source)
        for grammar in ("typed", "escaped"):
            manifest = rows_to_wire(expected, grammar)
            alias = next(row for row in manifest[1] if row[0] == "h")
            assert alias[4] and alias[4][0][1] != b"CONFLICT"
            alias[4][0][1] = b"CONFLICT"
            packed, sha, _ = seal(manifest)
            signed = unseal(packed, sha)
            preflight(signed, grammar)  # Negative: impossible inode-wide semantics admitted.
            with tempfile.TemporaryDirectory() as temp:
                root = os.fsencode(temp)
                materialize(signed, grammar, root)
                observed = inventory(root)
            if observed == expected:
                raise AssertionError("conflicting hardlink xattr did not alter source semantics")
            rows_before = {item[0]: item for item in expected["rows"]}
            rows_after = {item[0]: item for item in observed["rows"]}
            assert set(rows_before) == set(rows_after)
            assert all(a[:4] == rows_after[path][:4] for path, a in rows_before.items())
            assert observed["hardlink_groups"] == expected["hardlink_groups"]
            owner = next(group[0] for group in expected["hardlink_groups"])
            assert rows_before[owner][4] != rows_after[owner][4], "inode metadata unexpectedly preserved"
            results[grammar] = {"signed_preflight": "ACCEPTED_INCOHERENT",
                                "file_bytes_and_links": "UNCHANGED",
                                "owner_xattrs": "CHANGED_BY_ALIAS"}
    return {"status": "FALSIFIED",
            "question": "Does O1 reject conflicting inode-owned metadata across authenticated hardlink names?",
            "result": results,
            "scope": "detached reference model only, not proven CMPCT flaw",
            "decision": "An inode alias is not an independent xattr owner. Validate owner/alias metadata equivalence or define canonical inode-level metadata before writes."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
