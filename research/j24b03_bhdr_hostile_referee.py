#!/usr/bin/env python3
"""J24B03-H detached stdlib referee: compare unchanged versus patched source.

The referee consumes fixed observations, never imports CMPCT, and does not
change the original J24B03 instrument, thresholds or 24-case verdict.
"""
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = ("magic", "codec", "usize", "csize", "mlen")
EXPECTED_HEX = ((b"safe-target-0123456789/" * 8)[:128])[7:15].hex()


def audit(old_file, new_file):
    a, b = (json.loads(Path(p).read_text()) for p in (old_file, new_file))
    assert a["experiment"] == b["experiment"] == "J24B03-H"
    assert a["mode"] == "vulnerable" and b["mode"] == "repaired"
    assert a["valid_controls"] == b["valid_controls"] == 2
    assert "frozen-baseline" in a["reader"] and "frozen-baseline" not in b["reader"]
    assert len(a["items"]) == len(b["items"]) == 10
    pairs = set()
    for old, new in zip(a["items"], b["items"]):
        assert old["kind"] == new["kind"] and old["fault"] == new["fault"]
        assert old["archive_sha256"] == new["archive_sha256"]
        assert len(old["archive_sha256"]) == 64
        key = (old["kind"], old["fault"])
        assert key not in pairs
        pairs.add(key)
        assert old["preflight"]["status"] == new["preflight"]["status"] == "REJECT"
        assert old["range"]["status"] == "ACCEPT" and new["range"]["status"] == "REJECT"
        assert old["range"]["hex"] == EXPECTED_HEX
        assert old["range"]["sha256"] == hashlib.sha256(bytes.fromhex(EXPECTED_HEX)).hexdigest()
    assert {x[1] for x in pairs} == set(EXPECTED)
    assert len({x[0] for x in pairs}) == 2
    verdict = {"experiment": "J24B03-H", "referee": "PASS", "paired_faults": 10,
               "valid_controls": 2, "candidate_rejections": 10,
               "historical_unchecked_header_ranges": 10,
               "promotable": False}
    print(json.dumps(verdict, sort_keys=True))
    return verdict


if __name__ == "__main__":
    audit(sys.argv[1], sys.argv[2])
