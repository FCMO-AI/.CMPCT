#!/usr/bin/env python3
"""J24I36c detached physical referee for the frozen WAV and dictionary CRC court.

No CMPCT Builder, Reader, validator or codec import. Authenticates the original
golden bytes and proves that only one physical CRC32 bit changed. This auditor
does not independently decode FLAC/dictionary payloads; installed Python/native
checks provide decoded-content evidence separately.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct

HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
VECTORS = (
    ("wav", "v24-wavflac.json", 2),
    ("dict", "v24-zstd-dictionary.json", 3),
)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def physical_rows(blob: bytes) -> list[tuple[int, tuple]]:
    magic, revision, flags, cs, us, span, _ = HEADER.unpack_from(blob)
    assert (magic, revision, flags) == (b"CMPCT24" + bytes([0]), 24, 0)
    assert 0 < cs < 1024 * 1024 and 0 < us < 1024 * 1024
    start = HEADER.size + cs
    end = start + span
    assert HEADER.size < start <= end <= len(blob) - 64
    out = []
    while start < end:
        assert start + BLOB.size <= end
        fields = BLOB.unpack_from(blob, start)
        assert (fields[0], fields[2], fields[3]) == (b"CMA4", 0, 0)
        _, _, _, _, usz, csz, meta, _, _ = fields
        assert usz < 8 * 1024 * 1024 and csz < 8 * 1024 * 1024 and meta < 1024 * 1024
        pos = start + BLOB.size + meta + csz
        assert start < pos <= end
        out.append((start, fields))
        start = pos
    assert start == end
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", required=True, type=Path)
    args = ap.parse_args()
    fixtures = Path(__file__).resolve().parents[2] / "tests" / "conformance"
    observations = []
    for stem, filename, codec in VECTORS:
        vector = json.loads((fixtures / filename).read_text())["vector"]
        fixed = base64.b64decode(vector["archive_base64"], validate=True)
        original = (args.case_dir / (stem + "-original.cmpct")).read_bytes()
        changed = (args.case_dir / (stem + "-crc-wrong.cmpct")).read_bytes()
        assert original == fixed
        assert digest(original) == vector["archive_sha256"]
        assert len(original) == len(changed) == vector["archive_bytes"]
        differing = [i for i, (a, b) in enumerate(zip(original, changed)) if a != b]
        before = physical_rows(original)
        after = physical_rows(changed)
        assert len(before) == len(after)
        selected = [(a, b) for a, b in zip(before, after) if a[1][1] == codec]
        assert len(selected) == 1
        (pos, physical), (other_pos, mutant) = selected[0]
        assert pos == other_pos
        assert differing == [pos + 28]
        assert original[pos + 28] ^ changed[pos + 28] == 1
        assert (physical[:7] + physical[8:]) == (mutant[:7] + mutant[8:])
        assert (physical[7] ^ mutant[7]) == 1
        assert physical[4] == vector["logical_size"]
        assert physical[8].hex() == vector["logical_sha256"]
        assert (original[:pos + 28] == changed[:pos + 28]
                and original[pos + 29:] == changed[pos + 29:])
        observations.append({
            "name": vector["name"],
            "physical_codec": codec,
            "physical_blob_count": len(before),
            "mutated_crc_offset": pos + 28,
            "original_crc32": physical[7],
            "mutated_crc32": mutant[7],
            "original_archive_sha256": digest(original),
            "mutated_archive_sha256": digest(changed),
            "physical_sha_and_index_and_footer_unchanged": True,
            "decoded_content_independent_verification": "not measured by this detached referee",
        })
    result = {"schema": "j24i36c-detached-heldout-physical-referee-v1",
              "result": "PASS", "cases": observations}
    (args.case_dir / "heldout-detached-referee.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
