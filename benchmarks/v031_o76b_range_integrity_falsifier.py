"""O76b: physical VZIP mode-0/2 corruption and selective-read proof-tier falsifier.

Adversarial follow-up; does not change O76's preregistered economic threshold.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.codec import BHDR, CODEC_DEFLATE, S_VZIP
from cmpct.reader import CMPCT

from v031_o76_vzip_retention_oracle import make_zip, source_payload


def digest(value):
    return hashlib.sha256(value).hexdigest()


def original_and_mutation_location(archive, wanted_mode):
    with CMPCT(archive) as r:
        row = r.by["sample.zip"]
        assert row[6][0] == S_VZIP
        pr = r.recipes[row[6][1]][2][0]
        rawidx, method, actual_mode, streamref, stream_size, level = pr
        assert actual_mode == wanted_mode, (actual_mode, wanted_mode)
        if wanted_mode == 0:
            assert rawidx == streamref
            blobidx = streamref
        else:
            blobidx = rawidx
        off, uncompressed_size, compressed_size, codec, meta_len = r.blobs[blobidx]
        if wanted_mode == 0:
            assert codec == CODEC_DEFLATE, codec
            assert compressed_size == stream_size
            byte_index = 16
        else:
            byte_index = compressed_size // 2
        assert compressed_size > byte_index
        byte_position = r.record_base + off + BHDR.size + meta_len + byte_index
        assert byte_position < archive.stat().st_size
        return {
            "storage_mode": int(actual_mode),
            "record_blob_index": int(blobidx),
            "physical_offset": int(byte_position),
            "encoded_blob_size": int(compressed_size),
            "logical_blob_size": int(uncompressed_size),
            "blob_codec": int(codec),
            "byte_inside_encoded_blob": int(byte_index),
        }


def mutated_archive(original, dest, location):
    shutil.copyfile(original, dest)
    content = bytearray(dest.read_bytes())
    at = location["physical_offset"]
    old = content[at]
    content[at] ^= 0x01
    assert content[at] != old
    dest.write_bytes(content)
    return {"before": old, "after": content[at], "sha256": digest(content)}


def read_probe(archive, begin):
    try:
        with CMPCT(archive) as r:
            data = r.read_range("sample.zip", begin, 64)
        return {"outcome": "returned", "sha256": digest(data), "bytes_hex": data.hex()}
    except Exception as exc:
        return {"outcome": "rejected", "type": type(exc).__name__, "message": str(exc)[:300]}


def verify_probe(archive):
    try:
        with CMPCT(archive) as r:
            return {"outcome": "accepted", "count": int(r.verify())}
    except Exception as exc:
        return {"outcome": "rejected", "type": type(exc).__name__, "message": str(exc)[:300]}


def main():
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o76b-") as td:
        root = Path(td)
        for case in ("repeat2m", "periodic8m"):
            srcdir = root / case / "src"
            srcdir.mkdir(parents=True)
            physical_zip, begin, _ = make_zip(source_payload(case))
            (srcdir / "sample.zip").write_bytes(physical_zip)
            expected = physical_zip[begin:begin+64]
            clean_paths = {}
            corrupted_paths = {}
            modes = {}
            for label, limit, mode in (("regenerate", 65536, 2), ("retained", 0, 0)):
                archive = root / case / (label + ".cmpct")
                Builder(srcdir, deflate_reuse_min=limit, workers=1, reproducible=True).build(archive)
                with CMPCT(archive) as reader:
                    assert reader.verify() == 1
                    assert reader.read_range("sample.zip", begin, 64) == expected
                location = original_and_mutation_location(archive, mode)
                broken = root / case / (label + "-mutated.cmpct")
                change = mutated_archive(archive, broken, location)
                clean_paths[label] = archive
                corrupted_paths[label] = broken
                modes[label] = {
                    "source_sha256": digest(archive.read_bytes()),
                    "location": location,
                    "mutation": change,
                    "selective_read": read_probe(broken, begin),
                    "full_verify": verify_probe(broken),
                }
            retained = modes["retained"]
            regenerated = modes["regenerate"]
            assert retained["selective_read"]["outcome"] == "returned", retained
            assert retained["selective_read"]["sha256"] != digest(expected), retained
            assert retained["full_verify"]["outcome"] == "rejected", retained
            assert regenerated["selective_read"]["outcome"] == "rejected", regenerated
            assert regenerated["full_verify"]["outcome"] == "rejected", regenerated
            record = {
                "case": case,
                "original_zip_sha256": digest(physical_zip),
                "original_selective_sha256": digest(expected),
                "selected_range": [begin, 64],
                "branches": modes,
                "decision": "INTEGRITY_TIER_MISMATCH_ON_CORRUPTED_PHYSICAL_SOURCE",
            }
            cases.append(record)
            print("O76B_CASE=" + case + " O76B_DECISION=" + record["decision"], flush=True)
    receipt = {
        "schema": "cmpct-o76b-hostile-integrity-v1",
        "builder_blob": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
        "reader_blob": "e716233403dabd0966863c45635e18fa5ac6afb8",
        "codec_blob": "29526db4203723d83523fc95d074c346b63d7587",
        "cases": cases,
        "decision": "VALID_SOURCE_SPEEDUP_WITH_UNEQUAL_CORRUPTION_DETECTION",
    }
    Path("o76b-evidence.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("O76B_DECISION=" + receipt["decision"], flush=True)


if __name__ == "__main__":
    main()
