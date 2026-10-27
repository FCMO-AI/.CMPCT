#!/usr/bin/env python3
"""Independent J24P04 receipt auditor; checks raw structure and regenerated payload facts.

Does not import the test instrument or replay Linux syscalls. Validates that the
instrument's original structured receipt supports only its narrow temporal claim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def strict_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON member: " + key)
        out[key] = value
    return out


def reject_constant(x):
    raise ValueError("nonfinite JSON literal: " + x)


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    record = json.loads(
        Path(sys.argv[1]).read_text(encoding="utf8"),
        object_pairs_hook=strict_pairs,
        parse_constant=reject_constant,
    )
    count = 0
    def check(ok, label):
        nonlocal count
        require(bool(ok), label)
        count += 1

    check(record["schema"] == "j24p04-postlink-namespace-v1", "schema")
    check(record["host"].startswith("linux"), "host")
    check(isinstance(record["git_head"], str) and len(record["git_head"]) == 40, "git head")
    check(record["installed_reader_blob"] == "83c6600fa6cc951c1e6a136d239a39bb2c5d836b", "pinned reader")
    check(isinstance(record["uid"], int) and record["uid"] > 0, "nonroot")
    check(len(record["cases"]) == 8, "case count")
    check(record["decision"] == "DIRECT_FD_LINK_AUTHENTIC_AT_SYSCALL_NOT_PERPETUAL_PATH_CUSTODY", "decision")
    tuples = set()
    for c in record["cases"]:
        key = (c["kind"], c["directory_mode"], c["hostile"])
        check(key not in tuples, f"duplicate trial {key}")
        tuples.add(key)
        kind, mode, hostile = key
        check(kind in (1, 5), "storage class")
        check(mode in ("0o700", "0o300"), "mode")
        check(type(hostile) is bool, "hostility type")
        chunks = [hashlib.shake_256(f"j24p04-{kind}-{i}".encode()).digest(72191 + i * 257) for i in range(3)]
        original = b"".join(chunks)
        original_hash = sha(original)
        foreign_hash = sha(b"F" * len(original))
        check(c["expected_logical_sha"] == original_hash, "original independent digest")
        check(c["extract_returned_success"] is True, "extract success")
        check(isinstance(c["source_archive_sha"], str) and len(c["source_archive_sha"]) == 64, "archive hash shape")
        p = c["publication"]
        source = tuple(p["source_fd_inode"])
        link = tuple(p["link_inode"])
        final = tuple(c["final_inode"])
        check(len(source) == 2 and all(type(x) is int and x > 0 for x in source), "physical fd")
        check(source == link, "linkat linearization identity")
        check(p["linked_sha"] == original_hash, "source-linked digest")
        check(p["source_fd_sha"] == original_hash, "held descriptor digest")
        check(p["link_method"] in ("AT_EMPTY_PATH", "PROC_SELF_FD_FOLLOW"), "kernel link mode")
        if hostile:
            actor = p["actor"]
            check(actor["uid"] == record["uid"], "actor same UID")
            check(type(actor["pid"]) is int and actor["pid"] > 0, "actor pid")
            check(tuple(actor["quarantine_inode"]) == source, "authenticated quarantine")
            check(tuple(actor["replacement_inode"]) == final and final != source, "foreign final inode")
            check(actor["quarantine_sha"] == original_hash, "quarantine bytes intact")
            check(actor["replacement_sha"] == foreign_hash, "actor foreign content")
            check(c["final_sha"] == foreign_hash, "foreign output content")
            check(c["final_is_original_verified_inode"] is False, "foreign identity flag")
            check(c["decision"] == "SUCCESS_RETURN_FOREIGN_PATH", "hostile disposition")
        else:
            check("actor" not in p, "no actor on control")
            check(final == source, "control preserves inode")
            check(c["final_sha"] == original_hash, "control exact content")
            check(c["final_is_original_verified_inode"] is True, "control identity flag")
            check(c["decision"] == "SUCCESS_RETURN_AUTHENTIC_PATH", "control disposition")
    check(tuples == {(k, m, h) for k in (1, 5) for m in ("0o700", "0o300") for h in (False, True)}, "full cross product")
    print(json.dumps({"status": "PASS", "checks": count, "cases": len(tuples),
                      "limitations": "receipt consistency, not independent syscall replay"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
