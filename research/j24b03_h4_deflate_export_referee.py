#!/usr/bin/env python3
"""Independent stdlib-only H4 wire/receipt referee, not the Reader under test."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

BHDR = struct.Struct("<4sBBHQQII32s")
FAULTS = {"flags-1": (5, bytes([1])), "flags-128": (5, bytes([128])),
          "reserved-1": (6, bytes([1, 0])),
          "reserved-65535": (6, bytes([255, 255]))}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(root, base_path, cand_path):
    manifest_raw = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest["experiment"] == "J24B03-H4"
    assert len(manifest["controls"]) == 2 and len(manifest["hostiles"]) == 10
    baseline = json.loads(base_path.read_bytes())
    candidate = json.loads(cand_path.read_bytes())
    assert baseline["arm"] == "baseline" and candidate["arm"] == "candidate"
    assert baseline["manifest_sha256"] == candidate["manifest_sha256"] == digest(manifest_raw)
    assert baseline["reader_sha256"] != candidate["reader_sha256"]
    for arm in (baseline, candidate):
        assert len(arm["controls"]) == 2 and len(arm["hostiles"]) == 10
    originals = {}
    for case in manifest["controls"]:
        image = (root / case["file"]).read_bytes()
        assert digest(image) == case["sha256"]
        offset = case["frame_offset"]
        h = BHDR.unpack_from(image, offset)
        assert h[:4] == (b"CMA4", 4, 0, 0), h
        payload = image[offset + BHDR.size:offset + BHDR.size + h[5]]
        assert digest(payload) == case["stream_sha256"]
        originals[case["kind"]] = (image, offset, payload)
    seen = set()
    for spec in manifest["hostiles"]:
        image = (root / spec["file"]).read_bytes()
        assert digest(image) == spec["sha256"]
        assert spec["fault"] not in (None, "")
        seen.add((spec["kind"], spec["fault"]))
        original, off, stream = originals[spec["kind"]]
        hostile_off = spec["frame_offset"]
        h = BHDR.unpack_from(image, hostile_off)
        assert h[0] == b"CMA4" and h[1] == 4
        assert image[hostile_off + BHDR.size:hostile_off + BHDR.size + h[5]] == stream
        if spec["fault"] in FAULTS:
            rel, replacement = FAULTS[spec["fault"]]
            expected = bytearray(original)
            expected[off + rel:off + rel + len(replacement)] = replacement
            assert image == bytes(expected), spec
            assert hostile_off == off
        else:
            assert spec["fault"] == "signed-size-136"
            assert h[2] == 0 and h[3] == 0
            assert image != original
    assert len(seen) == 10
    output = {"experiment": "J24B03-H4", "decision": "UNDETERMINED",
              "controls": 2, "hostiles": 10, "baseline_reader_sha256": baseline["reader_sha256"],
              "candidate_reader_sha256": candidate["reader_sha256"], "cases": []}
    for category in ("controls", "hostiles"):
        expected = {r["file"]: r for r in manifest[category]}
        older = {r["file"]: r for r in baseline[category]}
        newer = {r["file"]: r for r in candidate[category]}
        assert set(expected) == set(older) == set(newer)
        for filename in sorted(expected):
            b, c, m = older[filename], newer[filename], expected[filename]
            assert b["sha256"] == c["sha256"] == m["sha256"]
            assert b["member"] == c["member"] == m["member"]
            if category == "controls":
                assert (b["preflight"], b["read"], b["verify"], b["export"]) == ("ACCEPT",) * 4
                assert (c["preflight"], c["read"], c["verify"], c["export"]) == ("ACCEPT",) * 4
                assert b["zip"] == c["zip"], (b, c)
                assert c["zip"]["logical_sha256"] == manifest["payload_sha256"]
                assert c["zip"]["stream_sha256"] == m["stream_sha256"]
            else:
                assert b["preflight"] == c["preflight"] == "REJECT"
                assert b["export"] == "ACCEPT" and c["export"] == "REJECT", (b, c)
                assert b["zip"]["logical_sha256"] == manifest["payload_sha256"]
            output["cases"].append({"file": filename, "baseline_export": b["export"],
                                    "candidate_export": c["export"]})
    output["decision"] = "H4_DIRECT_DEFLATE_EXPORT_CUSTODY_CONFIRMED"
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = check(a.corpus, a.baseline, a.candidate)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "cases": len(result["cases"])}, sort_keys=True))
