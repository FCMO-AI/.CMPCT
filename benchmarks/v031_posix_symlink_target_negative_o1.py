#!/usr/bin/env python3
"""Explicit negative witness for O1 target-specific symlink admission.

The O1 detached decoder validates entry names for a casefolding target, but
omits symlink-target component admissibility. Require this unsafe acceptance
as a scientific falsifier; never count it as product success.
"""
import copy
import json
import os
import tempfile

from v031_posix_byte_tree_o1 import inventory, preflight, rows_to_wire, seal, unseal, source_fixture


def run():
    if os.name != "posix":
        return {"status": "SKIPPED", "reason": "requires POSIX physical source"}
    with tempfile.TemporaryDirectory() as work:
        root = os.fsencode(work)
        source_fixture(root, "portable")
        original = inventory(root)
        results = {}
        for grammar in ("typed", "escaped"):
            manifest = rows_to_wire(original, grammar)
            index = next(i for i, row in enumerate(manifest[1]) if row[0] == "s")
            seen = []
            for name, target in (("invalid-utf8", b"unsafe-\xff"),
                                 ("reserved-device", b"CON"),
                                 ("backslash", b"folder\\child"),
                                 ("trailing-dot", b"file-a.")):
                altered = copy.deepcopy(manifest)
                altered[1][index][3] = target
                payload, sha, _ = seal(altered)
                signed = unseal(payload, sha)
                # A valid POSIX target need not be portable to every host.
                preflight(signed, grammar, "posix")
                try:
                    preflight(signed, grammar, "casefold")
                except (ValueError, UnicodeError) as err:
                    raise AssertionError("baseline gap disappeared: " + name) from err
                seen.append(name)
            results[grammar] = seen
        return {"status": "FALSIFIED", "question": "Does casefold target policy validate symlink target bytes?",
                "observation": "The detached O1 casefold model accepts four nonportable symlink targets per grammar despite applying entry-name admission.",
                "scope": "research-model defect, not demonstrated shipping CMPCT behavior",
                "cases": results,
                "decision": "No portable-target safety credit. Add explicit per-target normalization/admission and independent platform conformance before productization."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
