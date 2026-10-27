#!/usr/bin/env python3
"""J24B03-H3 detached stdlib physical-wire referee; no CMPCT imports."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

BHDR = struct.Struct("<4sBBHQQII32s")
PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]
START, LENGTH = 7, 8
FAULTS = {"flags-1": (2, 1), "flags-128": (2, 128),
          "reserved-1": (3, 1), "reserved-65535": (3, 65535)}
KINDS = {"file": "direct.bin", "symlink": "link"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(corpus: Path, baseline: Path, candidate: Path, out: Path):
    manifest_bytes = (corpus / "manifest.json").read_bytes()
    m = json.loads(manifest_bytes)
    a = json.loads(baseline.read_text())
    b = json.loads(candidate.read_text())
    assert m["experiment"] == a["experiment"] == b["experiment"] == "J24B03-H3"
    assert a["arm"] == "baseline" and b["arm"] == "candidate"
    assert a["reader_sha256"] != b["reader_sha256"]
    assert a["manifest_sha256"] == b["manifest_sha256"] == sha(manifest_bytes)
    assert Path(a["reader_file"]).resolve() == Path("frozen-baseline/src/cmpct/reader.py").resolve()
    assert Path(b["reader_file"]).resolve() == Path("src/cmpct/reader.py").resolve()
    for r in (a, b):
        assert sha(Path(r["reader_file"]).read_bytes()) == r["reader_sha256"]
    assert len(m["controls"]) == len(a["controls"]) == len(b["controls"]) == 2
    assert len(m["hostiles"]) == len(a["hostiles"]) == len(b["hostiles"]) == 8
    assert m["expected_payload_sha256"] == sha(PAYLOAD)
    assert m["expected_selected_hex"] == PAYLOAD[START:START + LENGTH].hex()
    source = {}
    for spec, old, new in zip(m["controls"], a["controls"], b["controls"]):
        label = spec["kind"]
        assert label in KINDS and spec["member"] == KINDS[label] and label not in source
        good = (corpus / spec["file"]).read_bytes()
        pos = spec["offset"]
        assert sha(good) == spec["sha256"] and pos >= 0
        assert good[pos + BHDR.size:pos + BHDR.size + len(PAYLOAD)] == PAYLOAD
        header = BHDR.unpack_from(good, pos)
        assert header[0] == b"CMA4" and header[1] == 0
        assert header[2] == header[3] == 0
        assert header[4] == header[5] == len(PAYLOAD) and header[6] == 0
        for record in (old, new):
            assert record["sha256"] == spec["sha256"] and record["kind"] == label
            assert record["preflight"]["status"] == "ACCEPT"
            assert record["selected"]["hex"] == m["expected_selected_hex"]
            assert record["whole"]["sha256"] == sha(PAYLOAD)
            assert record["verified"]["status"] == "ACCEPT"
        source[label] = (good, pos, header)
    seen = set()
    observed = []
    for spec, old, new in zip(m["hostiles"], a["hostiles"], b["hostiles"]):
        label, fault = spec["kind"], spec["fault"]
        assert label in KINDS and fault in FAULTS and (label, fault) not in seen
        seen.add((label, fault))
        assert spec["member"] == KINDS[label]
        field, value = FAULTS[fault]
        assert (spec["field"], spec["value"]) == (field, value)
        good, pos, original = source[label]
        bad = (corpus / spec["file"]).read_bytes()
        assert sha(bad) == spec["sha256"] and sha(good) == spec["good_sha256"]
        assert spec["offset"] == pos and len(bad) == len(good)
        assert bad[:pos] == good[:pos]
        assert bad[pos + BHDR.size:] == good[pos + BHDR.size:]
        changed = BHDR.unpack_from(bad, pos)
        assert changed[field] == value
        assert [i for i in range(len(original)) if original[i] != changed[i]] == [field]
        # Logical authenticated primary/tail bytes are identical; the payload/CRC/SHA remain untouched.
        assert original[7:] == changed[7:]
        for record in (old, new):
            assert record["sha256"] == spec["sha256"]
            assert record["kind"] == label and record["fault"] == fault
            assert record["preflight"]["status"] == "REJECT"
        for operation in ("selected", "whole", "verified"):
            assert new[operation]["status"] == "REJECT", (label, fault, operation, new)
        observed.append({"kind": label, "fault": fault, "historical": {
            op: old[op]["status"] for op in ("selected", "whole", "verified")},
            "candidate": "REJECT", "archive_sha256": spec["sha256"]})
    assert seen == {(kind, fault) for kind in KINDS for fault in FAULTS}
    verdict = {"experiment": "J24B03-H3", "audit": "PASS",
               "paired_sources_verified": True, "valid_controls": 2,
               "unsupported_controls": len(seen), "candidate_rejections": len(seen) * 3,
               "original_h_negative_untouched": True, "format_changed": False,
               "release_authority": False, "observations": observed}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in verdict.items() if k != "observations"}, sort_keys=True))
    return verdict


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--baseline", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    audit(a.corpus, a.baseline, a.candidate, a.out)
