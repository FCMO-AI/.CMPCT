#!/usr/bin/env python3
"""O5 research: RFC1951 byte identity can change without logical content changing.

Scientific fork: output logical-SHA staging vs wire-epoch source consistency.
No CMPCT product modifications.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
import zlib
from pathlib import Path

from cmpct.reader import CMPCT
from v031_deflate_mmap_mutation_o2_court import (
    digest, independent_zip_verdict, make_archive,
)
from v031_deflate_staged_output_o3_court import (
    freeze_expected_source, stage_then_verify,
)
from v031_deflate_wire_identity_o4_court import (
    publish_if_wire_equal, verify_once_with_wire_sha,
)


def padding_flip(source: Path, facts: dict) -> dict:
    """Toggle unused RFC1951 stored-block alignment bit 3; keep logical bytes."""
    i = facts["physical_start"]
    data = source.read_bytes()
    before = data[i]
    assert before & 0x07 == 1, "BFINAL=1 BTYPE=00 expected"
    altered = before ^ 0x08
    assert altered & 0x07 == 1
    with open(source, "r+b", buffering=0) as writable:
        writable.seek(i)
        assert writable.write(bytes([altered])) == 1
        os.fsync(writable.fileno())
    actual = source.read_bytes()
    wire = actual[i:i+len(facts["stream"])]
    decoded = zlib.decompress(wire, -15)
    assert decoded == facts["raw"]
    assert digest(wire) != digest(facts["stream"])
    assert len(wire) == len(facts["stream"])
    return {
        "index": i, "before": before, "after": altered,
        "source_sha256": digest(actual),
        "physical_wire_sha256": digest(wire),
        "logical_sha256": digest(decoded),
        "logical_equal_to_original": True,
    }


def scenario(root: Path, which: str) -> dict:
    folder = root / which
    folder.mkdir()
    source, target = folder / "source.cmpct", folder / "output.zip"
    facts = make_archive(source, ("member.bin",))
    prior = b"existing-user-artifact"
    target.write_bytes(prior)
    details = {
        "case": which,
        "original_wire_sha256": digest(facts["stream"]),
        "original_logical_sha256": digest(facts["raw"]),
        "source_original_sha256": facts["source_initial_sha"],
    }
    if which == "static_alt":
        details["mutation"] = padding_flip(source, facts)
    with CMPCT(source) as reader:
        assert reader.read("member.bin") == facts["raw"]
        if which == "static_alt":
            reader.export_zip(target)
            details["status"] = "published"
        elif which == "postcheck_o3":
            commitments = freeze_expected_source(reader)
            verifier = reader._verify_direct_deflate_blob

            def after_verifier(index):
                verifier(index)
                details["mutation"] = padding_flip(source, facts)
                assert reader.mm[facts["physical_start"]] == details["mutation"]["after"]

            reader._verify_direct_deflate_blob = after_verifier
            stage_then_verify(reader, target, commitments, details)
            details["status"] = "published"
        elif which == "postcheck_o4":
            wire = verify_once_with_wire_sha(reader, 0)
            details["original_preflight_wire_sha256"] = wire["wire_sha256"]
            details["mutation"] = padding_flip(source, facts)
            assert reader.mm[facts["physical_start"]] == details["mutation"]["after"]
            try:
                publish_if_wire_equal(reader, target, wire, details)
                details["status"] = "published"
            except IOError as exc:
                details["status"] = "rejected"
                details["reject_class"] = type(exc).__name__
        else:
            raise AssertionError(which)
    details["user_target_preserved"] = target.read_bytes() == prior
    if target.read_bytes() != prior:
        details["zip"] = independent_zip_verdict(target, ("member.bin",))
        assert details["zip"]["members"]["member.bin"]["read"] == "accepted"
        assert details["zip"]["members"]["member.bin"]["independent_inflate_sha256"] == details["original_logical_sha256"]
        assert details["zip"]["members"]["member.bin"]["raw_deflate_sha256"] == details["mutation"]["physical_wire_sha256"]
        with zipfile.ZipFile(target) as reader:
            assert reader.read("member.bin") == facts["raw"]
    details["temp_leaks"] = [x.name for x in folder.iterdir() if x.name.startswith((".cmpct-wire-stage-", ".cmpct-zip-o3-"))]
    return details


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="deflate-mutation-evidence/o5-result.json")
    args = parser.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-deflate-equal-wire-") as tmp:
        root = Path(tmp)
        cases = [
            scenario(root, "static_alt"),
            scenario(root, "postcheck_o3"),
            scenario(root, "postcheck_o4"),
        ]
    result = {
        "question": "Does exact source-wire consistency reject semantically equivalent concurrent change that emitted-output logical SHA accepts?",
        "source_head": os.environ.get("GITHUB_SHA", "local-unbound"),
        "source": "authentic independent r24 archive; RFC1951 stored-block alignment padding toggle",
        "cases": cases,
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    a, b, c = cases
    assert a["status"] == "published" and b["status"] == "published"
    assert not a["user_target_preserved"] and not b["user_target_preserved"]
    assert c["status"] == "rejected" and c["user_target_preserved"]
    assert c["copied_wire_sha256"] == c["mutation"]["physical_wire_sha256"]
    assert c["original_preflight_wire_sha256"] != c["copied_wire_sha256"]
    assert not any(x["temp_leaks"] for x in cases)
    print(json.dumps({
        "outcome": "WIRE_EPOCH_REJECTS_EQUIVALENT_DEFLATE_WHILE_OUTPUT_LOGICAL_PROOF_ACCEPTS",
        "source_head": result["source_head"],
        "cases": [{"case": x["case"], "status": x["status"],
                   "existing_target_preserved": x["user_target_preserved"]}
                  for x in cases],
        "evidence_path": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
