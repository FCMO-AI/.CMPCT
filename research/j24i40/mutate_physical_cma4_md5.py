#!/usr/bin/env python3
"""J24I40b: physical one-bit CMA4 FLAC STREAMINFO MD5 mutation, no CMPCT import."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import msgpack
import zstandard

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
FOOT = struct.Struct("<8sBBBBQQQ32s")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    args = p.parse_args()
    base = args.case_dir
    source_manifest = json.loads((base / "manifest.json").read_text())
    stream_manifest = json.loads((base / "stream-manifest.json").read_text())
    md5_manifest = json.loads((base / "md5-manifest.json").read_text())
    original = (base / "builder-wav-8m.cmpct").read_bytes()
    rec = source_manifest["records"]["8"]
    assert sha(original) == rec["archive_sha256"]
    assert stream_manifest["records"]["8"]["archive_sha256"] == sha(original)
    assert md5_manifest["original_archive_sha256"] == sha(original)
    magic, rev, flags, csize, usize, span, idxsha = HEADER.unpack_from(original)
    assert (magic, rev, flags) == (b"CMPCT24\x00", 24, 0)
    indexcomp = original[HEADER.size:HEADER.size+csize]
    index = zstandard.ZstdDecompressor().decompress(indexcomp, max_output_size=usize)
    assert len(index) == usize and hashlib.sha256(index).digest() == idxsha
    rows = msgpack.unpackb(index, raw=False)
    assert len(rows["files"]) == len(rows["blobs"]) == 1
    blob_offset = HEADER.size+csize
    bmagic, codec, bflags, reserved, logical, encoded, metalen, crc, digest = BLOB.unpack_from(original, blob_offset)
    assert (bmagic, codec, bflags, reserved) == (b"CMA4", 2, 0, 0)
    assert logical == rec["logical_bytes"] and encoded == rec["encoded_bytes"]
    assert crc == rec["crc32"] and digest.hex() == rec["payload_sha256"]
    flac_start = blob_offset + BLOB.size + metalen
    flac_end = flac_start + encoded
    assert span == BLOB.size + metalen + encoded
    assert original[flac_start:flac_start+4] == b"fLaC"
    assert original[flac_end:flac_end+csize] == indexcomp
    footer_offset = flac_end+csize
    assert FOOT.unpack_from(original,footer_offset) == (b"CMPTF24\x00",0,1,0,0,csize,usize,0,idxsha)
    assert footer_offset + FOOT.size == len(original)
    original_flac = (base/"md5-valid.flac").read_bytes()
    mutant_flac = (base/"md5-md5_flip.flac").read_bytes()
    assert original[flac_start:flac_end] == original_flac
    assert len(original_flac)==len(mutant_flac)==encoded
    assert sha(mutant_flac) == md5_manifest["cases"]["md5_flip"]["sha256"]
    assert md5_manifest["cases"]["md5_flip"]["changed_offsets"] == [26]
    absolute = flac_start + 26
    altered = bytearray(original)
    altered[absolute] ^= 1
    assert bytes(altered)[flac_start:flac_end] == mutant_flac
    assert original[absolute] ^ altered[absolute] == 1
    assert original[:absolute] == altered[:absolute] and original[absolute+1:] == altered[absolute+1:]
    orig_path = base / "md5-physical-valid.cmpct"
    mutant_path = base / "md5-physical-flip.cmpct"
    orig_path.write_bytes(original)
    mutant_path.write_bytes(altered)
    result = {
        "schema":"j24i40b-physical-cma4-md5-v1",
        "original_archive_sha256":sha(original),
        "mutant_archive_sha256":sha(altered),
        "unchanged_archive_byte_count":len(original),
        "one_changed_byte_at_absolute_offset":absolute,
        "changed_bit_xor":1,
        "flac_offset":flac_start,
        "flac_streaminfo_md5_offset":26,
        "mutant_flac_sha256":sha(mutant_flac),
        "logical_wav_sha256_unchanged":rec["payload_sha256"],
        "logical_crc32_unchanged":crc,
        "dual_index_bytes_unchanged":True,
        "cma4_descriptor_bytes_unchanged":True,
        "footer_bytes_unchanged":True,
    }
    (base/"physical-md5-manifest.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
