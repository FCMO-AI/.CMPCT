#!/usr/bin/env python3
"""J24I40 science only: mutate one internal FLAC STREAMINFO MD5 bit.

The authenticated original archive and decoded audio frames are deliberately untouched.
This is a codec-metadata falsifier, NOT an archive-integrity bypass instrument.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_offsets(a: bytes, b: bytes) -> list[int]:
    assert len(a) == len(b)
    return [i for i, (left, right) in enumerate(zip(a, b)) if left != right]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    args = p.parse_args()
    base = args.case_dir
    manifest = json.loads((base / "stream-manifest.json").read_text())
    assert manifest["schema"] == "j24i39-independent-split-v1"
    record = manifest["records"]["8"]
    original = (base / record["flac_path"]).read_bytes()
    assert sha(original) == record["flac_sha256"], "unmodified audited FLAC"
    assert original[:4] == b"fLaC"
    block_header = original[4:8]
    assert len(block_header) == 4 and block_header[0] & 0x7f == 0
    assert int.from_bytes(block_header[1:4], "big") == 34, "STREAMINFO must be 34 bytes"
    # Xiph STREAMINFO: 18-byte geometry/samples followed by 16-byte PCM MD5.
    offset = 4 + 4 + 18
    md5 = original[offset:offset + 16]
    assert len(md5) == 16 and any(md5), "this genuine source has no MD5 to falsify"
    wrong = bytearray(original)
    wrong[offset] ^= 1
    absent = bytearray(original)
    absent[offset:offset + 16] = bytes(16)
    cases = {"valid": original, "md5_flip": bytes(wrong), "md5_zero": bytes(absent)}
    rows = {}
    for name, content in cases.items():
        changed = changed_offsets(original, content)
        if name == "valid":
            assert not changed
        if name == "md5_flip":
            assert changed == [offset] and (original[offset] ^ content[offset]) == 1
        if name == "md5_zero":
            assert changed and all(offset <= i < offset + 16 for i in changed)
        assert content[:offset] == original[:offset]
        assert content[offset + 16:] == original[offset + 16:], "audio frames must be identical"
        path = base / f"md5-{name}.flac"
        path.write_bytes(content)
        rows[name] = {
            "file": path.name, "sha256": sha(content), "encoded_bytes": len(content),
            "changed_offsets": changed,
            "streaminfo_md5_hex": content[offset:offset + 16].hex(),
        }
    result = {
        "schema": "j24i40-streaminfo-md5-v1",
        "original_archive_sha256": record["archive_sha256"],
        "original_flac_sha256": record["flac_sha256"],
        "logical_wav_sha256": record["payload_sha256"],
        "logical_crc32": record["crc32"],
        "streaminfo_md5_offset": offset,
        "original_streaminfo_md5_hex": md5.hex(),
        "audio_frames_byte_identical": True,
        "cases": rows,
    }
    (base / "md5-manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
