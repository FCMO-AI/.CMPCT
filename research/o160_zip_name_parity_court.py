"""O160 independent positive ZIP canonical-namespace acceptance court.

Preregistered at docs/v031-research/2026-10-26-o160-zip-name-parity-prereg.md.
This instrument changes only authenticated logical names in independent golden
archives. It exercises installed product ZIP serializers without modifying original O156 negative evidence.
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


def rename_authenticated(golden: bytes, new_name: str, alias_name: str | None = None) -> tuple[bytes, bytes]:
    magic, version, flags, csize, usize, span, index_hash = HDR.unpack_from(golden)
    assert (magic, version, flags) == (b"CMPCT24\0", 24, 0)
    primary = golden[HDR.size:HDR.size + csize]
    decoded = zstd.ZstdDecompressor().decompress(primary, max_output_size=usize)
    assert len(decoded) == usize and digest(decoded) == index_hash
    index = msgpack.unpackb(decoded, raw=False)
    assert len(index["files"]) == 1
    index["files"][0][0] = new_name
    if alias_name is not None:
        alias = list(index["files"][0])
        alias[0] = alias_name
        index["files"].append(alias)
    updated = msgpack.packb(index, use_bin_type=True)
    compressed = zstd.ZstdCompressor(level=12).compress(updated)
    original_span = golden[HDR.size + csize:HDR.size + csize + span]
    assert len(original_span) == span
    tail = FTR.pack(b"CMPTF24\0", 0, 1, 0, 0, len(compressed), len(updated), 0, digest(updated))
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
    from cmpct.codec import K_DIR, K_FILE, K_SYMLINK
    # These standalone kind checks complement (not replace) genuine physical archive tests.
    assert CMPCT._zip_member_name("nested\\folder", K_DIR) == "nested/folder/"
    assert CMPCT._zip_member_name("nested\\leaf", K_FILE) == "nested/leaf"
    assert CMPCT._zip_member_name("nested\\link", K_SYMLINK) == "nested/link"
    cases = []
    collision_checks = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o160-") as td:
        workspace = Path(td)
        for vector in manifest["vectors"]:
            original = base64.b64decode(vector["archive_base64"], validate=True)
            assert digest(original).hex() == vector["archive_sha256"]
            assert len(original) == vector["archive_bytes"]
            assert vector["logical_sha256"] and vector["name"]
            for case, stored_name in (
                ("unchanged", vector["name"]),
                ("slash", "nested/leaf.bin"),
                ("backslash", "nested\\leaf.bin"),
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
                expected = vector["name"] if case == "unchanged" else "nested/leaf.bin"
                with CMPCT(source) as reader:
                    assert len(reader.files) == 1
                    assert reader.files[0][0] == stored_name
                    assert digest(reader.read(stored_name)).hex() == vector["logical_sha256"]
                    reader.extractall(direct_root)
                    for strategy in ("fast", "forced_stdlib"):
                        out = case_root / f"{strategy}.zip"
                        zip_root = case_root / f"extracted-{strategy}"
                        if strategy == "forced_stdlib":
                            # Only redirects the ZIP64 fallback decision, never changes bytes, code, or evaluator.
                            reader._zip64_offset_fallback_required = lambda: True
                        reader.export_zip(out)
                        with zipfile.ZipFile(out) as decoded:
                            assert decoded.testzip() is None
                            assert decoded.namelist() == [expected], (stored_name, decoded.namelist())
                            assert digest(decoded.read(expected)).hex() == vector["logical_sha256"]
                            decoded.extractall(zip_root)
                        direct = tree_files(direct_root)
                        exported = tree_files(zip_root)
                        assert direct == {expected: vector["logical_sha256"]}
                        assert exported == direct, (vector["codec"], case, strategy, direct, exported)
                        cases.append({
                            "codec": vector["codec"],
                            "case": case,
                            "serializer": strategy,
                            "stored_name": stored_name,
                            "exported_name": expected,
                            "archive_sha256": digest(archive).hex(),
                            "physical_span_sha256": digest(original_span).hex(),
                            "zip_sha256": digest(out.read_bytes()).hex(),
                            "zip_bytes": out.stat().st_size,
                            "namespace_agreement": True,
                            "content_exact": True,
                        })
            # A different authenticated spelling cannot create a second ZIP entry with the same
            # canonical destination: ordinary Reader open must reject it before any ZIP is opened.
            clash, _ = rename_authenticated(original, "nested/leaf.bin", alias_name="nested\\leaf.bin")
            clash_source = workspace / f"clash-{vector['codec']}.cmpct"
            clash_output = workspace / f"clash-{vector['codec']}.zip"
            clash_source.write_bytes(clash)
            try:
                with CMPCT(clash_source) as reader:
                    reader.export_zip(clash_output)
            except IOError as exc:
                assert "duplicate canonical logical path" in str(exc), str(exc)
            else:
                raise AssertionError("canonical-name collision was accepted")
            assert not clash_output.exists(), clash_output
            collision_checks.append(vector["codec"])
    assert len(cases) == 18, len(cases)
    assert len(collision_checks) == len(manifest["vectors"]) == 3, collision_checks
    outcome = {
        "schema": "cmpct-o160-zip-name-parity-court-v1",
        "status": "ZIP_CANONICAL_NAMES_POSITIVE_SCOPED",
        "source": "independent-committed-v24-direct-codec-goldens",
        "release_credit": False,
        "host": os.uname().sysname if hasattr(os, "uname") else os.name,
        "cases_count": len(cases),
        "collision_refusals": collision_checks,
        "cases": cases,
    }
    out = Path("o160-evidence")
    out.mkdir(exist_ok=True)
    (out / "result.json").write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print("O160_RESULT=" + json.dumps({"status": outcome["status"], "cases_count": len(cases), "collision_refusals": collision_checks}, sort_keys=True))


if __name__ == "__main__":
    main()
