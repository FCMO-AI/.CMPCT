#!/usr/bin/env python3
"""J24K02 prospective acceptance court: real installed Reader on authentic hostile S_PACK.

Do not modify J24K01's frozen falsifier. Both original RAW and Zstd PACK physical
vectors and their reauthenticated hostile indexes are independently assembled
from committed bytes, not CMPCT's Builder or the Reader.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_pack_auth_index_abi import authenticated_mutation, GOLDEN  # noqa: E402
from cmpct.reader import CMPCT  # noqa: E402
from cmpct.validation import ValidationError, preflight_archive  # noqa: E402

SCHEMA = "cmpct-j24k02-pack-selective-repair-v1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mutators(capacity: int, actual: int):
    return (
        ("oversized-slice", lambda row, idx: row[6].__setitem__(3, actual + 1)),
        ("past-physical-end", lambda row, idx: row[6].__setitem__(2, capacity - actual + 1)),
        ("huge-offset", lambda row, idx: row[6].__setitem__(2, (1 << 64) - 1)),
        ("negative-offset", lambda row, idx: row[6].__setitem__(2, -1)),
        ("missing-owner", lambda row, idx: row[6].__setitem__(1, len(idx["blobs"]))),
        ("negative-length", lambda row, idx: row[6].__setitem__(3, -1)),
        ("noninteger-owner", lambda row, idx: row[6].__setitem__(1, "0")),
        ("boolean-offset", lambda row, idx: row[6].__setitem__(2, True)),
    )


def court():
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert {v["physical_codec"] for v in manifest["vectors"]} == {0, 1}
    controls, attacks = [], []
    with tempfile.TemporaryDirectory(prefix="j24k02-pack-") as td:
        for vector in manifest["vectors"]:
            wire = base64.b64decode(vector["archive_base64"], validate=True)
            assert digest(wire) == vector["archive_sha256"]
            archive = Path(td) / f"{vector['name']}-valid.cmpct"
            archive.write_bytes(wire)
            assert preflight_archive(archive)["files"] == 4
            with CMPCT(archive) as reader:
                assert reader.verify() == 4
                for name, expected in vector["files"].items():
                    raw = bytes.fromhex(expected["hex"])
                    assert reader.read(name) == raw
                    for start, length in ((0, 0), (0, len(raw)), (len(raw) - 1, 1), (len(raw), 0)):
                        assert reader.read_range(name, start, length) == raw[start:start+length]
                controls.append({
                    "vector": vector["name"], "physical_codec": vector["physical_codec"],
                    "archive_sha256": digest(wire), "members": 4, "verify": 4,
                    "range_checks": 16,
                })
            expected = bytes.fromhex(vector["files"]["omega.bin"]["hex"])
            assert len(expected) > 1
            for label, change in mutators(vector["packed_blob_uncompressed_bytes"], len(expected)):
                invalid, idx = authenticated_mutation(wire, change)
                target = next(row for row in idx["files"] if row[0] == "omega.bin")
                outfile = Path(td) / f"{vector['name']}-{label}.cmpct"
                outfile.write_bytes(invalid)
                try:
                    preflight_archive(outfile)
                except ValidationError as exc:
                    strict_error = str(exc)
                else:
                    raise AssertionError(("preflight accepted", vector["name"], label))
                with CMPCT(outfile) as reader:
                    # Rejection must occur without reading/decompressing even the valid physical owner.
                    def unexpected_blob(owner):
                        raise AssertionError(("decoded physical blob before PACK geometry check", owner))
                    reader._blob = unexpected_blob
                    rejected = []
                    for start, length in ((0, len(expected)), (0, 0), (len(expected), 0)):
                        try:
                            reader.read_range("omega.bin", start, length)
                        except OSError as exc:
                            assert "packed storage geometry failure" in str(exc), (label, str(exc))
                            rejected.append(type(exc).__name__)
                        else:
                            raise AssertionError(("selective accepted invalid signed metadata",
                                                  vector["name"], label, start, length))
                assert len(rejected) == 3
                attacks.append({
                    "vector": vector["name"], "physical_codec": vector["physical_codec"],
                    "label": label, "archive_sha256": digest(invalid),
                    "archive_base64": base64.b64encode(invalid).decode(),
                    "original_archive_sha256": digest(wire), "storage": target[6],
                    "logical_bytes": len(expected), "preflight_rejected": bool(strict_error),
                    "rejected_queries": rejected, "decode_calls": 0
                })
    assert len(controls) == 2 and len(attacks) == 16
    return {"schema": SCHEMA, "source": "installed-Python-Reader", "controls": controls,
            "attacks": attacks, "decision": "CANDIDATE_GUARD_PASS"}


if __name__ == "__main__":
    print(json.dumps(court(), sort_keys=True))
