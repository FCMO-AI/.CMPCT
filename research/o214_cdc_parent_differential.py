#!/usr/bin/env python3
"""O214 independent-process parent-vs-candidate S_CDC admission falsifier.

Only Linux CI installs two real Git source trees into distinct site targets.
No Reader monkeypatching, no regenerated input between the two interpreters.
This is a causal, one-family research court, not a release benchmark.
"""
from __future__ import annotations
import argparse
import binascii
import hashlib
import inspect
import json
from pathlib import Path
import os

def _wire(declared: int) -> bytes:
    import msgpack
    from cmpct.codec import MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR, CODEC_RAW, K_FILE, S_CDC, zc, sha
    data = b"ABCD"
    idx = {
        "v": VERSION,
        "files": [["cdc.bin", K_FILE, 0o644, 946684800000000000,
                   len(data), sha(data), [S_CDC, [[declared, 0]]]]],
        "blobs": [[0, len(data), len(data), CODEC_RAW, 0]],
        "recipes": [], "dict_blob": None, "fsmeta": {},
    }
    raw = msgpack.packb(idx, use_bin_type=True)
    compressed = zc(raw, 12)
    digest = sha(raw)
    record = BHDR.pack(BMAGIC, CODEC_RAW, 0, 0, len(data), len(data), 0,
                       binascii.crc32(data) & 0xffffffff, sha(data)) + data
    return (HDR.pack(MAGIC, VERSION, 0, len(compressed), len(raw), len(record), digest)
            + compressed + record + compressed
            + FTR.pack(FMAGIC, 0, 1, 0, 0, len(compressed), len(raw), 0, digest))


def _attempt(call):
    try:
        return {"ok": True, "result": call()}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}


def _probe(root: Path, installed_reader: Path, tag: str, out: Path):
    import cmpct.reader as r
    import cmpct.validation as v
    real = Path(inspect.getfile(r)).resolve()
    expected = installed_reader.resolve()
    norm = lambda data: data.replace(b"\r\n", b"\n")
    if real == expected or norm(real.read_bytes()) != norm(expected.read_bytes()):
        raise AssertionError(("not independent installed source", str(real), str(expected)))
    findings = {"tag": tag, "installed_reader_sha256": hashlib.sha256(norm(real.read_bytes())).hexdigest(),
                "source_sha256": hashlib.sha256(norm(expected.read_bytes())).hexdigest(), "cases": {}}
    for name in ("valid.cmpct", "bad.cmpct"):
        ap = root / name
        wire = ap.read_bytes()
        before = hashlib.sha256(wire).hexdigest()
        result = {"archive_sha256": before, "physical_bytes": len(wire),
                  "strict_preflight": _attempt(lambda: v.preflight_archive(ap)["files"])}
        try:
            with r.CMPCT(ap) as archive:
                result["reader_open"] = {"ok": True}
                result["verify"] = _attempt(archive.verify)
                result["read"] = _attempt(lambda: archive.read("cdc.bin").hex())
                result["late_range"] = _attempt(lambda: archive.read_range("cdc.bin", 2, 2).hex())
        except Exception as exc:
            result["reader_open"] = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}
        if hashlib.sha256(ap.read_bytes()).hexdigest() != before:
            raise AssertionError(("reader changed source", name))
        findings["cases"][name] = result
    out.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n")
    print("O214_PROBE=" + json.dumps(findings, sort_keys=True))


def _compare(root: Path, parent_path: Path, candidate_path: Path):
    p = json.loads(parent_path.read_text())
    c = json.loads(candidate_path.read_text())
    assert p["tag"] == "parent" and c["tag"] == "candidate"
    assert p["installed_reader_sha256"] == p["source_sha256"]
    assert c["installed_reader_sha256"] == c["source_sha256"]
    assert p["source_sha256"] != c["source_sha256"]
    pv, pb = p["cases"]["valid.cmpct"], p["cases"]["bad.cmpct"]
    cv, cb = c["cases"]["valid.cmpct"], c["cases"]["bad.cmpct"]
    for name in ("valid.cmpct", "bad.cmpct"):
        assert p["cases"][name]["archive_sha256"] == c["cases"][name]["archive_sha256"]
        assert p["cases"][name]["archive_sha256"] == hashlib.sha256((root/name).read_bytes()).hexdigest()
    for v in (pv, cv):
        assert v["strict_preflight"] == {"ok": True, "result": 1}
        assert v["reader_open"]["ok"] is True
        assert v["verify"] == {"ok": True, "result": 1}
        assert v["read"] == {"ok": True, "result": "41424344"}
        assert v["late_range"] == {"ok": True, "result": "4344"}
    for bad in (pb, cb):
        assert bad["strict_preflight"]["ok"] is False
        assert bad["strict_preflight"]["error"].startswith("ValidationError:")
    assert pb["reader_open"]["ok"] is True
    assert pb["verify"] == {"ok": True, "result": 1}
    assert pb["read"] == {"ok": True, "result": "41424344"}
    assert pb["late_range"] == {"ok": True, "result": ""}
    assert cb["reader_open"]["ok"] is False
    assert cb["reader_open"]["error"].startswith("ValidationError:")
    print("O214_DIFFERENTIAL=PASS")
    print("O214_DECISION=ROOT_VERSIONED_CDC_WRONG_RANGE_REJECTED_BY_CANDIDATE")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "probe", "compare"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--tag", default="")
    parser.add_argument("--source-reader", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    if args.action == "create":
        for name, length in (("valid.cmpct", 4), ("bad.cmpct", 1)):
            (args.root / name).write_bytes(_wire(length))
        print("O214_WIRE_SOURCES=" + json.dumps({
            name: hashlib.sha256((args.root / name).read_bytes()).hexdigest()
            for name in ("valid.cmpct", "bad.cmpct")
        }, sort_keys=True))
    elif args.action == "probe":
        assert args.out and args.source_reader and args.tag in ("parent", "candidate")
        _probe(args.root, args.source_reader, args.tag, args.out)
    else:
        assert args.parent and args.candidate
        _compare(args.root, args.parent, args.candidate)


if __name__ == "__main__":
    main()
