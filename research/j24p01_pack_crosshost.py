#!/usr/bin/env python3
"""J24P01: source-locked cross-host S_PACK replication, no Builder and no product changes.

Independent frozen wire owned by PR #307. Source and semantic scope frozen in
docs/v031-research/2026-10-28-j24p01-pack-crosshost-prereg.md before this file.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback

import msgpack


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def run() -> dict:
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    expected_head = os.environ["CMPCT_EVIDENCE_HEAD"]
    assert head == expected_head, ("wrong checked-out source", head, expected_head)

    import cmpct
    import cmpct.reader as reader_module
    import cmpct.codec as codec_module
    from cmpct.reader import CMPCT
    from cmpct.codec import BHDR, FTR, HDR, MAGIC, FMAGIC, sha, zc, zd
    from cmpct.validation import preflight_archive

    installed = Path(cmpct.__file__).resolve()
    assert root not in installed.parents, ("in-tree import, not installed package", installed)
    source_hashes = {}
    for filename, module in [
        ("reader.py", reader_module),
        ("codec.py", codec_module),
    ]:
        source = root / "src" / "cmpct" / filename
        actual = Path(module.__file__).resolve()
        assert source.exists() and actual.exists()
        sha_source, sha_installed = digest(norm(source.read_bytes())), digest(norm(actual.read_bytes()))
        assert sha_source == sha_installed, (filename, sha_source, sha_installed)
        source_hashes[filename] = sha_source

    manifest_path = root / "tests" / "conformance" / "v24-pack.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-independent-pack-golden-v1"
    assert manifest["format_revision"] == 24
    assert len(manifest["vectors"]) == 2
    assert {v["physical_codec"] for v in manifest["vectors"]} == {0, 1}
    results = []
    with tempfile.TemporaryDirectory(prefix="j24p01-") as scratch:
        base = Path(scratch)
        for vec in manifest["vectors"]:
            name = vec["name"]
            wire = base64.b64decode(vec["archive_base64"], validate=True)
            assert len(wire) == vec["archive_bytes"]
            assert digest(wire) == vec["archive_sha256"]
            assert wire.startswith(b"CMPCT24\0")
            path = base / (name + ".cmpct")
            path.write_bytes(wire)
            admission = preflight_archive(path)
            assert admission["version"] == 24
            assert admission["files"] == len(vec["files"])
            assert admission["blobs"] == 1

            member_hashes = {}
            with CMPCT(path) as archive:
                assert set(archive.by) == set(vec["files"])
                assert len(archive.blobs) == 1
                assert archive.blobs[0][3] == vec["physical_codec"]
                physical_start = archive.record_base + archive.blobs[0][0]
                physical = BHDR.unpack_from(wire, physical_start)
                assert physical[0] == b"CMA4"
                assert physical[1] == vec["physical_codec"]
                assert physical[4] == vec["packed_blob_uncompressed_bytes"]
                assert physical[5] == vec["packed_blob_compressed_bytes"]
                assert physical[-1].hex() == vec["packed_blob_sha256"]
                for member, facts in vec["files"].items():
                    expected = bytes.fromhex(facts["hex"])
                    assert len(expected) == facts["size"]
                    assert digest(expected) == facts["sha256"]
                    row = archive.by[member]
                    assert row[6][0] == 4 and row[6][1] == 0
                    full = archive.read(member)
                    assert full == expected
                    assert archive.read_range(member, 0, len(expected)) == expected
                    assert archive.read_range(member, len(expected), 0) == b""
                    member_hashes[member] = digest(full)
                assert archive.by["alpha-copy.txt"][6] == archive.by["alpha.txt"][6]
                assert archive.read_range("alpha-copy.txt", 7, 17) == bytes.fromhex(
                    vec["files"]["alpha.txt"]["hex"])[7:24]
                for probe in vec["ranges"]:
                    assert archive.read_range(probe["name"], probe["offset"], probe["length"]) == bytes.fromhex(probe["hex"])
                assert archive.verify() == len(vec["files"])
                dest = base / (name + "-out")
                archive.extractall(dest, metadata=False)
                assert set(f.name for f in dest.iterdir()) == set(vec["files"])
                for member, facts in vec["files"].items():
                    assert (dest / member).read_bytes() == bytes.fromhex(facts["hex"])

            # Physical mutation: unchanged authenticated index and header; read must refuse.
            damaged = bytearray(wire)
            physical_payload = physical_start + BHDR.size + physical[6]
            assert physical_payload + 4 < len(damaged)
            damaged[physical_payload + 4] ^= 0x40
            damaged_path = base / (name + "-corrupt.cmpct")
            damaged_path.write_bytes(damaged)
            refused_physical = False
            with CMPCT(damaged_path) as archive:
                try:
                    archive.read("alpha.txt")
                except (IOError, OSError, ValueError, RuntimeError):
                    refused_physical = True
            assert refused_physical, ("physical corruption admitted", name)

            # Authenticated metadata mutation: keep the physical blob record byte-identical.
            magic, revision, flags, clen, ulen, span, _hash = HDR.unpack_from(wire)
            assert magic == MAGIC and revision == 24
            decoded_index = msgpack.unpackb(zd(wire[HDR.size:HDR.size + clen], ulen), raw=False)
            target = next(row for row in decoded_index["files"] if row[0] == "omega.bin")
            target[6][2] = vec["packed_blob_uncompressed_bytes"] - target[4] + 1
            modified_plain = msgpack.packb(decoded_index, use_bin_type=True)
            modified_comp = zc(modified_plain, 12)
            unchanged_physical = wire[HDR.size + clen:HDR.size + clen + span]
            forged = (
                HDR.pack(MAGIC, 24, flags, len(modified_comp), len(modified_plain),
                         len(unchanged_physical), sha(modified_plain))
                + modified_comp + unchanged_physical + modified_comp
                + FTR.pack(FMAGIC, 0, 1, 0, 0, len(modified_comp),
                           len(modified_plain), 0, sha(modified_plain))
            )
            assert unchanged_physical == wire[HDR.size + clen:HDR.size + clen + span]
            malformed_path = base / (name + "-signed-bad.cmpct")
            malformed_path.write_bytes(forged)
            refused_metadata = False
            try:
                preflight_archive(malformed_path)
            except IOError as e:
                assert "pack slice exceeds blob" in str(e), str(e)
                refused_metadata = True
            assert refused_metadata, ("authenticated invalid PACK tuple admitted", name)

            results.append({
                "name": name, "physical_codec": vec["physical_codec"],
                "archive_sha256": digest(wire), "archive_bytes": len(wire),
                "members": member_hashes, "ranges": len(vec["ranges"]),
                "preflight": True, "full_reads": True, "selective_reads": True,
                "verify": True, "extraction": True,
                "physical_corruption_rejected": refused_physical,
                "authenticated_bad_index_rejected": refused_metadata,
            })
    return {
        "schema": "j24p01-pack-crosshost-v1", "status": "PASS",
        "head": head, "installed": str(installed),
        "source_hashes": source_hashes, "manifest_sha256": digest(manifest_path.read_bytes()),
        "vectors": results,
    }


if __name__ == "__main__":
    output = Path(os.environ.get("CMPCT_J24P01_EVIDENCE", "pack-crosshost-evidence"))
    output.mkdir(parents=True, exist_ok=True)
    try:
        receipt = run()
    except BaseException as exc:
        receipt = {"schema": "j24p01-pack-crosshost-v1", "status": "FAIL",
                   "error": repr(exc), "traceback": traceback.format_exc()}
        (output / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        raise
    (output / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "head": receipt["head"],
                      "vectors": [x["name"] for x in receipt["vectors"]]},
                     sort_keys=True))
