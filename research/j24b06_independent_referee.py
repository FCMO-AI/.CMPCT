#!/usr/bin/env python3
"""Independent J24B06 signed-wire/receipt referee.

Uses only standard Python, the standalone zstd executable, and msgpack.
Never imports the production CMPCT or the candidate experiment.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

import msgpack

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")


def check(p, message):
    if not p:
        raise AssertionError(message)


def h(x):
    return hashlib.sha256(x).hexdigest()


def decompress(comp):
    p = subprocess.run(["zstd", "--decompress", "--stdout", "--quiet"],
                       input=comp, capture_output=True, check=True)
    return p.stdout


def parse(blob: bytes):
    check(len(blob) > HDR.size + FTR.size, "truncated archive")
    magic, version, flags, cs, us, dlen, index_sha = HDR.unpack_from(blob)
    check(magic == b"CMPCT24\x00" and version == 24 and flags == 0,
          "invalid r24 header identity")
    p = HDR.size + cs
    check(p + dlen + cs + FTR.size == len(blob), "incoherent physical span")
    ix_bytes = decompress(blob[HDR.size:p])
    check(len(ix_bytes) == us and hashlib.sha256(ix_bytes).digest() == index_sha,
          "primary index size/hash mismatch")
    fpos = p + dlen + cs
    fm, kind, codec, fflags, reserved, fcs, fus, prev, fsha = FTR.unpack_from(blob, fpos)
    check(fm == b"CMPTF24\x00" and kind == 0 and codec == 1 and prev == 0,
          "wrong footer identity or generation")
    check(fcs == cs and fus == us and fsha == index_sha,
          "footer identity does not match primary index")
    check(blob[p+dlen:p+dlen+cs] == blob[HDR.size:p],
          "primary/tail compressed indexes differ")
    fi = decompress(blob[p+dlen:p+dlen+cs])
    check(fi == ix_bytes, "primary/tail uncompressed indexes differ")
    idx = msgpack.unpackb(ix_bytes, raw=False)
    check(idx.get("v") == 24 and isinstance(idx.get("files"), list),
          "index version/schema mismatch")
    phys = blob[p:p+dlen]
    check(isinstance(idx.get("blobs"), list), "missing physical records")
    for b in idx["blobs"]:
        check(isinstance(b, list) and len(b) == 5, "invalid blob table row")
        off, usz, csz, codec, ml = b
        check(all(type(x) is int and x >= 0 for x in (off, usz, csz, codec, ml)),
              "invalid unsigned blob geometry")
        check(off + BHDR.size + ml + csz <= len(phys), "blob outside physical data")
        bm, cc, fl, reserved, rus, rcs, rml, crc, rh = BHDR.unpack_from(phys, off)
        check(bm == b"CMA4" and cc == codec and rus == usz
              and rcs == csz and rml == ml, "index/BHDR mismatch")
    return {"index": idx, "index_sha": h(ix_bytes),
            "physical_sha": h(phys), "physical": phys,
            "total_bytes": len(blob), "sha256": h(blob)}


def referee(folder):
    folder = Path(folder)
    receipt = json.loads((folder/"receipt.json").read_text())
    check(receipt.get("schema") == "j24b06-signed-budget-v1",
          "wrong receipt schema")
    payload = (folder/"source-payload.bin").read_bytes()
    check(len(payload) == 8192 and h(payload) == receipt["source_payload_sha256"],
          "original source payload discrepancy")
    models = {}
    for label in ("baseline", "negative", "zero"):
        raw = (folder/(label+".cmpct")).read_bytes()
        metadata = receipt["files"][label]
        check(len(raw) == metadata["bytes"] and h(raw) == metadata["sha256"],
              "archive identity mismatch: "+label)
        models[label] = parse(raw)
    b = models["baseline"]
    n = models["negative"]
    z = models["zero"]
    check(b["physical"] == n["physical"] == z["physical"],
          "the hostile archives changed physical records")
    check(len({b["index_sha"], n["index_sha"], z["index_sha"]}) == 3,
          "signed index mutation identities missing")
    base_index = b["index"]
    links = [x for x in base_index["files"] if x[0] == "offset-link"]
    regular = [x for x in base_index["files"] if x[0] == "payload.bin"]
    check(len(links) == len(regular) == 1 and links[0][1] == 2
          and regular[0][1] == 0, "file and symlink not present")
    check(links[0][4] == len("payload.bin") and regular[0][4] == 8192,
          "source file logical geometry wrong")
    for label, want in (("negative", -8192), ("zero", 0)):
        expected = copy.deepcopy(base_index)
        for row in expected["files"]:
            if row[0] == "offset-link":
                row[4] = want
        check(models[label]["index"] == expected,
              label+": changed fields beyond symlink logical size")
    results = receipt.get("results", {})
    check(set(results) == {
        "baseline_budget", "negative_budget", "zero_budget",
        "negative_budget_minus_one"}, "missing or extra budget observations")
    for label in results:
        check(results[label]["verify_count"] == 2, "missing real archive verify()")
    for label in ("baseline_budget","zero_budget","negative_budget_minus_one"):
        check(results[label]["exception_type"] is not None
              and not results[label]["file_written"],
              "negative control did not refuse extraction")
    result = results["negative_budget"]
    if receipt["decision"] == "CONFIRMED_SIGNED_BUDGET_UNDERCOUNT":
        check(result["exception_type"] is None and result["file_written"]
              and result["file_bytes"] == 8192
              and result["file_sha256"] == h(payload)
              and result["symlink_created"], "incorrect confirmed-bypass evidence")
    elif receipt["decision"] == "HYPOTHESIS_FALSIFIED_BY_READER_REFUSAL":
        check(result["exception_type"] is not None
              and not result["file_written"], "incorrect refusal evidence")
    else:
        raise AssertionError("invalid scientific decision")
    return {"decision": receipt["decision"],
            "signed_primary_tail_sha_verified": True,
            "physical_record_equality_verified": True,
            "exactly_one_signed_size_mutation": True,
            "zero_and_original_size_controls": True,
            "archives": {k: {"sha256": v["sha256"], "index_sha256": v["index_sha"],
                             "physical_sha256": v["physical_sha"]}
                         for k,v in models.items()}}


def reject_forgery(folder):
    folder = Path(folder)
    with tempfile.TemporaryDirectory(prefix="j24b06-forgeries-") as t:
        tmp = Path(t)
        import shutil
        for f in folder.iterdir():
            shutil.copy2(f,tmp/f.name)
        genuine = json.loads((tmp/"receipt.json").read_text())
        forgeries = []
        x = copy.deepcopy(genuine); x["source_payload_sha256"] = "0"*64
        forgeries.append(("payload_identity",x))
        x = copy.deepcopy(genuine); x["files"]["negative"]["bytes"] += 1
        forgeries.append(("archive_size",x))
        x = copy.deepcopy(genuine); x["results"]["negative_budget"]["file_bytes"] += 1
        forgeries.append(("result_size",x))
        x = copy.deepcopy(genuine); x["decision"] = "FAKE_PROMOTION_WIN"
        forgeries.append(("decision",x))
        for label, poisoned in forgeries:
            (tmp/"receipt.json").write_text(json.dumps(poisoned,sort_keys=True))
            try:
                referee(tmp)
            except (AssertionError, ValueError, KeyError, TypeError):
                pass
            else:
                raise AssertionError(f"forged {label} receipt accepted")
        (tmp/"receipt.json").write_text(json.dumps(genuine,sort_keys=True))
        bad = bytearray((tmp/"negative.cmpct").read_bytes())
        p = HDR.size + HDR.unpack_from(bad)[3]
        check(p < len(bad)-FTR.size,"empty archive corruption opportunity")
        bad[p] ^= 1
        (tmp/"negative.cmpct").write_bytes(bad)
        try:
            referee(tmp)
        except (AssertionError, ValueError, KeyError, TypeError):
            pass
        else:
            raise AssertionError("altered physical record accepted")
        return len(forgeries)+1


if __name__ == "__main__":
    pa=argparse.ArgumentParser()
    pa.add_argument("artifacts",type=Path)
    args=pa.parse_args()
    result=referee(args.artifacts)
    result["forged_receipts_rejected"]=reject_forgery(args.artifacts)
    (args.artifacts/"referee.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
