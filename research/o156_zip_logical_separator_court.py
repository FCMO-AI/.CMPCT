"""O156 prospective ZIP namespace-parity court.

The prediction is frozen in docs/v031-research/2026-10-26-o156-zip-logical-separator-prereg.md.
This instrument changes only authenticated logical names in independent golden
archives. It makes no claims about writer code, release qualification or speed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
import tempfile
import zipfile
from pathlib import Path

import msgpack
import zstandard as zstd
from cmpct.reader import CMPCT

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests/conformance/v24-direct-codecs.json"
HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def rename_authenticated(golden: bytes, new_name: str) -> tuple[bytes, bytes]:
    magic, version, flags, csize, usize, span, index_hash = HDR.unpack_from(golden)
    assert (magic, version, flags) == (b"CMPCT24\\0", 24, 0)
    primary = golden[HDR.size:HDR.size + csize]
    decoded = zstd.ZstdDecompressor().decompress(primary, max_output_size=usize)
    assert len(decoded) == usize and digest(decoded) == index_hash
    index = msgpack.unpackb(decoded, raw=False)
    assert len(index["files"]) == 1
    index["files"][0][0] = new_name
    updated = msgpack.packb(index, use_bin_type=True)
    compressed = zstd.ZstdCompressor(level=12).compress(updated)
    original_span = golden[HDR.size + csize:HDR.size + csize + span]
    assert len(original_span) == span
    tail = FTR.pack(b"CMPTF24\\0", 0, 1, 0, 0, len(compressed), len(updated), 0, digest(updated))
    result = (
        HDR.pack(magic, version, flags, len(compressed), len(updated), span, digest(updated))
        + compressed + original_span + compressed + tail
    )
    assert result[HDR.size + len(compressed):HDR.size + len(compressed) + span] == original_span
    assert zstd.ZstdDecompressor().decompress(compressed) == updated
    assert FTR.unpack_from(result, len(result) - FTR.size)[-1] == digest(updated)
    return result, original_span


def tree_files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path.read_bytes()).hex()
        for path in root.rglob("*") if path.is_file()
    }


def main() -> None:
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o156-") as td:
        workspace = Path(td)
        for vector in manifest["vectors"]:
            original = base64.b64decode(vector["archive_base64"], validate=True)
            assert digest(original).hex() == vector["archive_sha256"]
            assert len(original) == vector["archive_bytes"]
            assert vector["logical_sha256"] and vector["name"]
            for case, stored_name in (
                ("unchanged", vector["name"]),
                ("slash", "nested/leaf.bin"),
                ("backslash", "nested\\\\leaf.bin"),
            ):
                if case == "unchanged":
                    archive = original
                    _, _, _, ci, _, span, _ = HDR.unpack_from(original)
                    original_span = original[HDR.size + ci:HDR.size + ci + span]
                else:
                    archive, original_span = rename_authenticated(original, stored_name)
                _, _, _, orig_ci, _, orig_span, _ = HDR.unpack_from(original)
                assert original_span == original[HDR.size + orig_ci:HDR.size + orig_ci + orig_span]
                case_root = workspace / f"{vector['codec']}-{case}"
                case_root.mkdir()
                source = case_root / "source.cmpct"
                source.write_bytes(archive)
                direct_root = case_root / "direct"
                zip_root = case_root / "zip"
                zip_path = case_root / "out.zip"
                with CMPCT(source) as reader:
                    assert len(reader.files) == 1
                    assert reader.files[0][0] == stored_name
                    assert digest(reader.read(stored_name)).hex() == vector["logical_sha256"]
                    reader.extractall(direct_root)
                    reader.export_zip(zip_path)
                with zipfile.ZipFile(zip_path) as reader_zip:
                    assert reader_zip.testzip() is None
                    assert reader_zip.namelist() == [stored_name]
                    assert digest(reader_zip.read(stored_name)).hex() == vector["logical_sha256"]
                    reader_zip.extractall(zip_root)
                direct = tree_files(direct_root)
                exported = tree_files(zip_root)
                expected_direct = vector["name"] if case == "unchanged" else "nested/leaf.bin"
                expected_zip = stored_name
                assert direct == {expected_direct: vector["logical_sha256"]}
                assert exported == {expected_zip: vector["logical_sha256"]}
                agreed = direct == exported
                assert agreed == (case != "backslash"), (
                    vector["codec"], case, direct, exported
                )
                cases.append({
                    "codec": vector["codec"],
                    "case": case,
                    "stored_name": stored_name,
                    "source_archive_sha256": digest(archive).hex(),
                    "original_physical_span_sha256": digest(original_span).hex(),
                    "zip_sha256": digest(zip_path.read_bytes()).hex(),
                    "zip_bytes": zip_path.stat().st_size,
                    "direct_tree": direct,
                    "zip_tree": exported,
                    "content_exact": True,
                    "namespace_agreement": agreed,
                })
    expected = 3 * len(manifest["vectors"])
    assert len(cases) == expected
    observed = [x for x in cases if x["case"] == "backslash" and not x["namespace_agreement"]]
    assert len(observed) == len(manifest["vectors"])
    outcome = {
        "schema": "cmpct-o156-zip-logical-separator-court-v1",
        "status": "POSIX_ZIP_LOGICAL_NAMESPACE_DISCREPANCY_CONFIRMED",
        "release_credit": False,
        "source": "independent-committed-v24-direct-codec-goldens",
        "host": os.uname().sysname,
        "cases_count": len(cases),
        "backslash_disagreement_count": len(observed),
        "cases": cases,
    }
    out = Path("o156-evidence")
    out.mkdir(exist_ok=True)
    (out / "result.json").write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()
