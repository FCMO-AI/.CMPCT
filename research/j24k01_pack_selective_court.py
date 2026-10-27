#!/usr/bin/env python3
"""J24K01: actual Python Reader selective-geometry court on authenticated hostile PACK wire.

The original archives are immutable Builder-independent bytes owned by PR #307.
Index mutation uses PR #314's independent authenticated rewriter; CMPCT Builder is never imported.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tests"))

from native_pack_auth_index_abi import authenticated_mutation, GOLDEN  # noqa: E402
from cmpct.reader import CMPCT  # noqa: E402
from cmpct.validation import ValidationError, preflight_archive  # noqa: E402

SCHEMA = "cmpct-j24k01-pack-selective-court-v1"
LABELS = ("oversized-slice", "past-physical-end", "huge-offset")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _changes(name: str, row: list, idx: dict, capacity: int) -> None:
    assert row[0] == "omega.bin" and row[6][:2] == [4, 0]
    if name == "oversized-slice":
        row[6][3] = row[4] + 1
    elif name == "past-physical-end":
        row[6][2] = capacity - row[4] + 1
    elif name == "huge-offset":
        row[6][2] = (1 << 64) - 1
    else:
        raise AssertionError(name)


def court() -> dict:
    fixture = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert fixture["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert {x["physical_codec"] for x in fixture["vectors"]} == {0, 1}
    record = {"schema": SCHEMA, "source_kind": "unchanged-shipping-Python-Reader",
              "original_golden": "tests/conformance/v24-pack.json",
              "controls": [], "mutations": []}
    with tempfile.TemporaryDirectory(prefix="j24k01-pack-") as td:
        root = Path(td)
        for vector in fixture["vectors"]:
            wire = base64.b64decode(vector["archive_base64"], validate=True)
            assert len(wire) == vector["archive_bytes"]
            assert _sha(wire) == vector["archive_sha256"]
            expected = bytes.fromhex(vector["files"]["omega.bin"]["hex"])
            assert len(expected) == vector["files"]["omega.bin"]["size"] > 1
            path = root / f"{vector['name']}-control.cmpct"
            path.write_bytes(wire)
            assert preflight_archive(path)["files"] == 4
            with CMPCT(path) as reader:
                assert reader.verify() == 4
                for name, member in vector["files"].items():
                    contents = bytes.fromhex(member["hex"])
                    assert reader.read(name) == contents
                    assert reader.read_range(name, 0, len(contents)) == contents
                record["controls"].append({
                    "vector": vector["name"], "archive_sha256": _sha(wire),
                    "physical_codec": vector["physical_codec"], "members": 4,
                    "verify": 4, "omega_sha256": _sha(expected)
                })
            for name in LABELS:
                mutant, changed = authenticated_mutation(
                    wire,
                    lambda row, idx, n=name, cap=vector["packed_blob_uncompressed_bytes"]:
                        _changes(n, row, idx, cap)
                )
                target = next(x for x in changed["files"] if x[0] == "omega.bin")
                assert target[4] == len(expected)
                assert target[6][0] == 4 and target[6][1] == 0
                outfile = root / f"{vector['name']}-{name}.cmpct"
                outfile.write_bytes(mutant)
                try:
                    preflight_archive(outfile)
                except ValidationError as e:
                    preflight_rejection = str(e)
                else:
                    raise AssertionError(f"strict preflight accepted {vector['name']} {name}")
                assert "pack slice exceeds blob" in preflight_rejection, preflight_rejection

                with CMPCT(outfile) as reader:
                    try:
                        reader.read("omega.bin")
                    except Exception as e:
                        whole_error = type(e).__name__ + ": " + str(e)
                    else:
                        raise AssertionError(f"full read accepted malformed {vector['name']} {name}")
                    assert "packed file size failure" in whole_error, whole_error
                    try:
                        got = reader.read_range("omega.bin", 0, len(expected))
                    except Exception as e:
                        selective = {"status": "REJECTED", "error": type(e).__name__ + ": " + str(e)}
                    else:
                        selective = {"status": "ACCEPTED", "length": len(got),
                                     "sha256": _sha(got), "hex": got.hex()}
                # These are *prospectively expected* failures in the current Reader.
                # A future candidate fixing the gap should deliberately invert this court's
                # expectations in a distinct version, without silently changing the frozen baseline.
                assert selective["status"] == "ACCEPTED", (name, selective)
                expected_length = len(expected) if name == "oversized-slice" else (
                    len(expected) - 1 if name == "past-physical-end" else 0
                )
                assert selective["length"] == expected_length, (name, selective)
                if name == "oversized-slice":
                    assert selective["sha256"] == _sha(expected)
                record["mutations"].append({
                    "vector": vector["name"], "label": name,
                    "archive_sha256": _sha(mutant), "archive_base64": base64.b64encode(mutant).decode(),
                    "physical_codec": vector["physical_codec"],
                    "original_archive_sha256": _sha(wire),
                    "logical_size": len(expected), "storage": target[6],
                    "preflight": preflight_rejection, "whole_read": whole_error,
                    "selective": selective
                })
    assert len(record["controls"]) == 2 and len(record["mutations"]) == 6
    return record


if __name__ == "__main__":
    outcome = court()
    print(json.dumps(outcome, sort_keys=True))
    print("J24K01: 2 valid PACK families, 6 fully signed hostile tuples; preflight/full-read reject and ordinary selective read silently accepts", file=sys.stderr)
