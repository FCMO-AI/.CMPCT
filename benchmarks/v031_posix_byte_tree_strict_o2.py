#!/usr/bin/env python3
"""Research-only *additive* O2 semantic guards over the signed O1 POSIX manifest.

O1 baseline remains intentionally frozen as a reproducible negative control.
This is not a shipping CMPCT parser, cross-platform specification, or release.
"""
from __future__ import annotations

import copy
import json
import os
import tempfile

from v031_posix_byte_tree_o1 import (
    inventory, materialize, preflight, rows_to_wire, seal, source_fixture,
    unseal, validate_target_name,
)


def symlink_host_target(rel: bytes, target: bytes) -> bytes:
    """Interpret a relative target lexically, without resolving host symlinks."""
    if type(target) is not bytes or not target:
        raise ValueError("missing symlink target")
    parts = rel.split(b"/")[:-1]
    for token in target.split(b"/"):
        if token in (b"", b"."):
            continue
        if token == b"..":
            if not parts:
                raise ValueError("target escapes root")
            parts.pop()
        else:
            parts.append(token)
    if not parts:
        raise ValueError("empty root-referenced target")
    return b"/".join(parts)


def strict_preflight(packet, grammar: str, target: str = "posix"):
    """O1 strict+ semantic check; NO writes or path-dependent filesystem I/O."""
    entries, blobs = preflight(packet, grammar, target)
    owners = {}
    for rel, kind, mode, value, xattrs in entries:
        if kind == "f":
            owners[rel] = (mode, xattrs)
        elif kind == "h":
            if value not in owners:
                raise ValueError("hardlink owner absent")
            # Mode/xattrs are inode-owned on POSIX, not independently owned by
            # alias path names. Otherwise one alias silently mutates its owner.
            if owners[value] != (mode, xattrs):
                raise ValueError("conflicting hardlink inode metadata")
        elif kind == "s" and target == "casefold":
            # O1 only validated entry names. A symlink *target* can carry a
            # reserved name, invalid UTF-8 or metacharacters independently.
            normalized = symlink_host_target(rel, value)
            validate_target_name(normalized, set())
    return entries, blobs


def strict_materialize(packet, grammar: str, root: bytes, target: str = "posix"):
    # All structural checks happen before materialize() performs any writes.
    strict_preflight(packet, grammar, target)
    return materialize(packet, grammar, root, target)


def require_rejection(packet, grammar: str, label: str, target="posix"):
    signed_data, sha, _ = seal(packet)
    authenticated = unseal(signed_data, sha)
    # Preserve a negative comparison: original O1 accepted the same signed row.
    preflight(authenticated, grammar, target)
    with tempfile.TemporaryDirectory() as directory:
        directory_b = os.fsencode(directory)
        output = directory_b + b"/output"
        os.mkdir(output)
        witness = directory_b + b"/witness"
        with open(witness, "wb") as stream:
            stream.write(b"UNMODIFIED")
        try:
            strict_materialize(authenticated, grammar, output, target)
        except (ValueError, UnicodeError):
            pass
        else:
            raise AssertionError("strict repair admitted signed counterexample: " + label)
        assert not os.listdir(output), (label, "unexpected preflight write")
        assert open(witness, "rb").read() == b"UNMODIFIED", label
    return label


def court():
    if os.name != "posix":
        return {"status": "SKIPPED", "reason": "requires POSIX byte names"}
    outcomes = {}
    for mode in ("mixed", "utf8", "portable"):
        with tempfile.TemporaryDirectory() as directory:
            source = os.fsencode(directory) + b"/source"
            os.mkdir(source)
            xattrs_supported = source_fixture(source, mode)
            if not xattrs_supported:
                raise AssertionError("xattrs unavailable; do not claim inode metadata coverage")
            expected = inventory(source)
            row = {}
            for grammar in ("typed", "escaped"):
                wire = rows_to_wire(expected, grammar)
                signed_bytes, sha, size = seal(wire)
                authenticated = unseal(signed_bytes, sha)
                strict_preflight(authenticated, grammar, "casefold" if mode == "portable" else "posix")
                with tempfile.TemporaryDirectory() as target_dir:
                    output = os.fsencode(target_dir) + b"/fresh"
                    os.mkdir(output)
                    strict_materialize(authenticated, grammar, output, "casefold" if mode == "portable" else "posix")
                    observed = inventory(output)
                assert observed == expected, (mode, grammar, "positive source bytes changed")
                row[grammar] = {"state": "PASS", "source_entries": len(expected["rows"]),
                                "complete_detached_bytes": len(signed_bytes) + len(sha),
                                "manifest_raw_bytes": size}
            outcomes[mode] = row

    signed_negatives = {}
    with tempfile.TemporaryDirectory() as directory:
        source = os.fsencode(directory) + b"/source"
        os.mkdir(source)
        assert source_fixture(source, "portable")
        expected = inventory(source)
        for grammar in ("typed", "escaped"):
            original = rows_to_wire(expected, grammar)
            negative = []
            symlink_row = next(i for i, row in enumerate(original[1]) if row[0] == "s")
            for name, target in (("invalid-utf8", b"file-\xff"),
                                 ("reserved-device", b"CON"),
                                 ("backslash", b"part\\name"),
                                 ("trailing-dot", b"file-a.")):
                mutated = copy.deepcopy(original)
                mutated[1][symlink_row][3] = target
                negative.append(require_rejection(mutated, grammar, "symlink-" + name, "casefold"))
            hardlink_row = next(i for i, row in enumerate(original[1]) if row[0] == "h")
            modified = copy.deepcopy(original)
            modified[1][hardlink_row][4][0][1] = b"CONFLICT"
            negative.append(require_rejection(modified, grammar, "hardlink-xattr-conflict"))
            modified = copy.deepcopy(original)
            modified[1][hardlink_row][2] = 0o600
            negative.append(require_rejection(modified, grammar, "hardlink-mode-conflict"))
            signed_negatives[grammar] = negative

    return {
        "status": "PASS",
        "tier": "detached O2 semantic repair only; O1 baseline signed negatives intentionally preserved",
        "positive": outcomes,
        "new_signed_rejections": signed_negatives,
        "decision": "O2 repairs two known O1 reference-model admission mechanisms while maintaining the original positive tree byte identity; general platform safety still unproven.",
        "unmeasured": ["genuine CMPCT archive", "real Windows/macOS filesystem",
                       "concurrent symlink pivots", "descriptor-root near-PATH_MAX publication",
                       "native parser", "POSIX full ownership/timestamps/ACL",
                       "updates/recovery", "whole-system costs"],
    }


if __name__ == "__main__":
    print(json.dumps(court(), indent=2, sort_keys=True))
