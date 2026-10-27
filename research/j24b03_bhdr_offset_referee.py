#!/usr/bin/env python3
"""J24B03-H2 detached stdlib-only referee; imports no CMPCT modules.

Reopen actual archived wires; validate that each hostile variant mutates just one
physical header, preserve the historical negative, verify all candidate rejections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BHDR = struct.Struct("<4sBBHQQII32s")
PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]
START, LENGTH = 7, 8
FIELDS = {"magic": 0, "codec": 1, "usize": 4, "csize": 5, "mlen": 6}
KINDS = {"file", "symlink"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def audit(root: Path, old_path: Path, new_path: Path, output: Path):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    old, new = load(old_path), load(new_path)
    assert manifest["experiment"] == old["experiment"] == new["experiment"] == "J24B03-H2"
    assert old["arm"] == "baseline" and new["arm"] == "candidate"
    assert old["reader_sha256"] != new["reader_sha256"]
    assert old["manifest_sha256"] == new["manifest_sha256"] == sha(manifest_bytes)
    assert Path(old["reader_file"]).resolve() == Path("frozen-baseline/src/cmpct/reader.py").resolve()
    assert Path(new["reader_file"]).resolve() == Path("src/cmpct/reader.py").resolve()
    assert sha(Path(old["reader_file"]).read_bytes()) == old["reader_sha256"]
    assert sha(Path(new["reader_file"]).read_bytes()) == new["reader_sha256"]

    assert len(manifest["controls"]) == len(old["valid"]) == len(new["valid"]) == 2
    assert len(manifest["faults"]) == len(old["faults"]) == len(new["faults"]) == 10
    assert set(x["kind"] for x in manifest["controls"]) == KINDS
    assert manifest["expected_normal_hex"] == PAYLOAD[START:START + LENGTH].hex()
    assert manifest["predicted_shift_hex"] == PAYLOAD[START + 1:START + 1 + LENGTH].hex()

    original = {}
    for spec, a, b in zip(manifest["controls"], old["valid"], new["valid"]):
        for item in (a, b):
            assert item["sha256"] == spec["sha256"]
            assert item["file"] == spec["file"] and item["kind"] == spec["kind"]
            assert item["preflight"]["status"] == "ACCEPT"
            assert item["selected"]["status"] == "ACCEPT"
            assert item["selected"]["hex"] == manifest["expected_normal_hex"]
            assert item["whole"]["sha256"] == sha(PAYLOAD)
            assert item["verification"]["status"] == "ACCEPT"
        data = (root / spec["file"]).read_bytes()
        assert sha(data) == spec["sha256"]
        pos = spec["frame_offset"]
        assert pos >= 0 and pos + BHDR.size + len(PAYLOAD) <= len(data)
        h = BHDR.unpack_from(data, pos)
        assert h[0] == b"CMA4" and h[1] == 0 and h[4] == len(PAYLOAD)
        assert h[5] == len(PAYLOAD) and h[6] == 0
        assert data[pos + BHDR.size:pos + BHDR.size + len(PAYLOAD)] == PAYLOAD
        assert spec["kind"] not in original
        original[spec["kind"]] = (data, pos)

    seen = set()
    observed = []
    for spec, a, b in zip(manifest["faults"], old["faults"], new["faults"]):
        key = (spec["kind"], spec["fault"])
        assert key not in seen and spec["fault"] in FIELDS and spec["kind"] in KINDS
        seen.add(key)
        assert spec["name"] == ("direct.bin" if spec["kind"] == "file" else "link")
        good, pos = original[spec["kind"]]
        bad = (root / spec["file"]).read_bytes()
        assert sha(bad) == spec["sha256"]
        assert sha(good) == spec["good_sha256"]
        assert pos == spec["frame_offset"] and len(bad) == len(good)
        assert bad[:pos] == good[:pos]
        assert bad[pos + BHDR.size:] == good[pos + BHDR.size:]
        assert spec["previous_header_hex"] == good[pos:pos + BHDR.size].hex()
        assert spec["altered_header_hex"] == bad[pos:pos + BHDR.size].hex()
        before, after = BHDR.unpack_from(good, pos), BHDR.unpack_from(bad, pos)
        changing = [i for i in range(len(before)) if before[i] != after[i]]
        assert changing == [FIELDS[spec["fault"]]], (key, changing)
        assert after[7] == before[7] and after[8] == before[8]
        assert bad[pos + BHDR.size:pos + BHDR.size + len(PAYLOAD)] == PAYLOAD

        for item in (a, b):
            assert item["kind"] == spec["kind"] and item["fault"] == spec["fault"]
            assert item["file"] == spec["file"] and item["sha256"] == spec["sha256"]
            assert item["preflight"]["status"] == "REJECT"
        assert b["selected"]["status"] == "REJECT", (key, b)
        assert a["selected"]["status"] in ("ACCEPT", "REJECT")
        if a["selected"]["status"] == "ACCEPT":
            raw = bytes.fromhex(a["selected"]["hex"])
            assert a["selected"]["length"] == len(raw)
            assert a["selected"]["sha256"] == sha(raw)
        observed.append({"kind": key[0], "fault": key[1],
                         "baseline": a["selected"], "candidate": b["selected"]["status"],
                         "archive_sha256": spec["sha256"]})

    assert seen == {(k, f) for k in KINDS for f in FIELDS}
    baseline_accepted = sum(x["baseline"]["status"] == "ACCEPT" for x in observed)
    rml_rows = [x for x in observed if x["fault"] == "mlen"]
    predicted_shift = all(x["baseline"]["status"] == "ACCEPT" and
                          x["baseline"].get("hex") == manifest["predicted_shift_hex"]
                          for x in rml_rows)
    verdict = {
        "experiment": "J24B03-H2", "audit": "PASS",
        "original_h_failure_preserved": True, "source_exact": True,
        "identical_authenticated_wire": True, "valid_controls": 2,
        "hostile_cases": 10, "candidate_rejections": 10,
        "baseline_accepted": baseline_accepted,
        "mechanistic_rml_shift": ("CONFIRMED" if predicted_shift else
                                  "FALSIFIED_OR_BLOCKED"),
        "historical_gap": ("PRESENT" if baseline_accepted else "NOT_DEMONSTRATED"),
        "product_promotion": False, "records": observed
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in verdict.items() if k != "records"}, sort_keys=True))
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit(args.corpus, args.baseline, args.candidate, args.out)
