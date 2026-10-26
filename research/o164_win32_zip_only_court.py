"""O164: source-exact Windows ZIP-only namespace diagnostic, NOT a full extraction court.

This does not modify or bypass the original O160 metadata=True gate.
The inherited Windows timestamp failure remains separately red.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

from cmpct.reader import CMPCT
from o160_zip_name_parity_court import (
    GOLDEN, HDR, digest, rename_authenticated,
)


def independent_tree(root: Path) -> dict[str, str]:
    """Physical tree from independent stdlib ZIP extraction, not CMPCT.extractall."""
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*") if p.is_file()
    }


def execute() -> dict:
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    assert len(manifest["vectors"]) == 3
    observations: list[dict] = []
    collisions: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o164-win32-") as td:
        workspace = Path(td)
        for vector in manifest["vectors"]:
            original = base64.b64decode(vector["archive_base64"], validate=True)
            assert digest(original).hex() == vector["archive_sha256"]
            assert len(original) == vector["archive_bytes"]
            _, _, _, orig_index_size, _, span_size, _ = HDR.unpack_from(original)
            span = original[HDR.size + orig_index_size:HDR.size + orig_index_size + span_size]
            for spelling, logical in (
                ("unchanged", vector["name"]),
                ("slash", "nested/leaf.bin"),
                ("backslash", "nested\\leaf.bin"),
            ):
                if spelling == "unchanged":
                    archive = original
                    preserved_span = span
                else:
                    archive, preserved_span = rename_authenticated(original, logical)
                assert preserved_span == span
                case_root = workspace / f"{vector['codec']}-{spelling}"
                case_root.mkdir()
                source = case_root / "source.cmpct"
                source.write_bytes(archive)
                expected_name = vector["name"] if spelling == "unchanged" else "nested/leaf.bin"
                with CMPCT(source) as reader:
                    assert len(reader.files) == 1
                    assert reader.files[0][0] == logical
                    assert digest(reader.read(logical)).hex() == vector["logical_sha256"]
                    for serializer in ("fast", "forced_stdlib"):
                        if serializer == "forced_stdlib":
                            reader._zip64_offset_fallback_required = lambda: True
                        output = case_root / f"{serializer}.zip"
                        physical = case_root / f"stdlib-extract-{serializer}"
                        assert reader.export_zip(output) == output
                        with zipfile.ZipFile(output) as z:
                            assert z.testzip() is None
                            assert z.namelist() == [expected_name], (logical, z.namelist())
                            assert digest(z.read(expected_name)).hex() == vector["logical_sha256"]
                            z.extractall(physical)
                        assert independent_tree(physical) == {
                            expected_name: vector["logical_sha256"]
                        }
                        assert source.read_bytes() == archive
                        observations.append({
                            "codec": vector["codec"],
                            "spelling": spelling,
                            "serializer": serializer,
                            "logical": logical,
                            "zip_member": expected_name,
                            "archive_sha256": digest(archive).hex(),
                            "zip_sha256": digest(output.read_bytes()).hex(),
                            "physical_exact": True,
                        })
            duplicate, _ = rename_authenticated(
                original, "nested/leaf.bin", alias_name="nested\\leaf.bin"
            )
            source = workspace / f"collision-{vector['codec']}.cmpct"
            target = workspace / f"collision-{vector['codec']}.zip"
            source.write_bytes(duplicate)
            try:
                with CMPCT(source) as reader:
                    reader.export_zip(target)
            except IOError as exc:
                assert "duplicate canonical logical path" in str(exc), str(exc)
            else:
                raise AssertionError("canonical collision admitted")
            assert not target.exists()
            collisions.append({"codec": vector["codec"], "refused": True})
    assert len(observations) == 18
    assert len(collisions) == 3
    assert len({x["codec"] for x in observations}) == 3
    assert {x["serializer"] for x in observations} == {"fast", "forced_stdlib"}
    assert {x["spelling"] for x in observations} == {"unchanged", "slash", "backslash"}
    return {
        "schema": "cmpct-o164-windows-zip-only-v1",
        "decision": "ZIP_ONLY_NAMESPACE_SCOPED_PASS",
        "host": os.name,
        "cases": observations,
        "collision_refusals": collisions,
        "direct_extract_metadata_validated": False,
        "original_o160_win32_red_preserved": True,
        "full_product_acceptance": False,
        "release_credit": False,
    }


def main() -> None:
    out = Path("o164-evidence")
    out.mkdir(exist_ok=True)
    try:
        evidence = execute()
    except BaseException as exc:
        (out / "result.json").write_text(
            json.dumps({
                "schema": "cmpct-o164-windows-zip-only-v1",
                "decision": "INCOMPLETE_OR_FAILED",
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:400],
                "release_credit": False,
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise
    (out / "result.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("O164_DECISION=" + evidence["decision"], flush=True)
    print("O164_CASES=" + str(len(evidence["cases"])), flush=True)


if __name__ == "__main__":
    main()
