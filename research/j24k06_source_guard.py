#!/usr/bin/env python3
"""J24K06 source-exact transfer referee: only a bounded range_vzip patch is permitted.

This is read-only instrumentation against separately checked-out exact parent
source, not a claim about general product or release correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OLD = """        if outpos+csize>start and outpos<end:
            seg=get_content(rawref) if method==zipfile.ZIP_STORED else get_stream(stream_mode,streamref,level)
            a=max(start,outpos)-outpos;b=min(end,outpos+csize)-outpos;out.append(seg[a:b])
        outpos+=csize"""

NEW = """        if outpos+csize>start and outpos<end:
            seg=get_content(rawref) if method==zipfile.ZIP_STORED else get_stream(stream_mode,streamref,level)
            # The signed csize is an offset claim, not proof of an actual stream
            # boundary. A correct-length slice can contain the wrong bytes.
            if len(seg)!=csize:
                raise IOError('virtual ZIP selective reconstruction length mismatch')
            a=max(start,outpos)-outpos;b=min(end,outpos+csize)-outpos;out.append(seg[a:b])
        elif method==zipfile.ZIP_DEFLATED and stream_mode==2 and outpos<end:
            # Regenerated Deflate has no stored csize oracle. To locate a later
            # literal correctly, verify every *preceding* mode2 stream exactly.
            # Preserve lazy reads that end before this stream and never retain
            # an unselected reconstructed stream in the result.
            if len(get_stream(stream_mode,streamref,level))!=csize:
                raise IOError('virtual ZIP selective reconstruction length mismatch')
        outpos+=csize"""

PRESERVED = (
    "src/cmpct/reader.py",
    "src/cmpct/validation.py",
    "tests/test_j24c07c_signed_mode2_regeneration.py",
    "tests/test_j24c07_vzip_guard_composition.py",
    "tests/conformance/v24-virtual-zip-deflate-mode1.json",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--parent", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    # Windows Git checkouts can choose CRLF; compare canonical text, not checkout EOL.
    norm = lambda b: b.replace(b"\\r\\n", b"\\n")
    base = norm((a.parent / "src/cmpct/codec.py").read_bytes())
    now = norm((a.candidate / "src/cmpct/codec.py").read_bytes())
    old, new = OLD.encode(), NEW.encode()
    assert base.count(old) == 1, "frozen parent has unexpected codec source"
    assert now == base.replace(old, new), "candidate codec differs beyond preregistered patch"
    hashes = {}
    for name in PRESERVED:
        lhs, rhs = norm((a.parent / name).read_bytes()), norm((a.candidate / name).read_bytes())
        assert lhs == rhs, f"unexpected inherited change to {name}"
        hashes[name] = hashlib.sha256(rhs).hexdigest()
    receipt = {
        "claim": "J24K06_exact_candidate_codec_patch",
        "parent_codec_sha256": hashlib.sha256(base).hexdigest(),
        "candidate_codec_sha256": hashlib.sha256(now).hexdigest(),
        "inherited_unchanged_sha256": hashes,
        "exact_substitution_count": 1,
        "decision": "PASS",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24K06_SOURCE_CUSTODY_PASS=" + json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
