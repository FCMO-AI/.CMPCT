"""J24G55: fixed-candidate acceptance of physical J24G54b in-range case.

Historic negative-reproduction tests #786 are not rewritten. This new test
requires the preflight effective index and native Reader to agree by identity.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete
from cmpct.validation import _load_effective_index, ParserLimits, preflight_archive

KEY = "com.fcmo.cmpct.j24g54b" if sys.platform == "darwin" else "user.cmpct_j24g54b"
VALUE = b"j24g54b-inrange\x00\xff"
FILES = ("a-early.bin", "b-delete.bin", "c-owned.bin", "z-late.bin")


def _native_set(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", KEY, VALUE.hex(), str(path)],
                       check=True, capture_output=True, text=True)
    else:
        os.setxattr(path, KEY, VALUE, follow_symlinks=False)


def _native_get(path: Path) -> bytes | None:
    try:
        if sys.platform == "darwin":
            result = subprocess.run(["/usr/bin/xattr", "-px", KEY, str(path)],
                                    capture_output=True, text=True)
            return bytes.fromhex("".join(result.stdout.split())) if result.returncode == 0 else None
        return os.getxattr(path, KEY, follow_symlinks=False)
    except OSError:
        return None


def _attrs_by_path(index: dict) -> dict:
    return {index["files"][ordinal][0]: attrs
            for ordinal, attrs in index.get("fsmeta", {}).get("xattrs", [])}


@pytest.mark.skipif(sys.platform not in ("darwin", "linux"), reason="native xattrs required")
@pytest.mark.parametrize("marked", [True, False], ids=["inrange_xattr", "no_xattr_control"])
def test_signed_inrange_ordinal_preserves_owner_in_preflight(tmp_path: Path, marked: bool):
    tree = tmp_path / "tree"
    tree.mkdir()
    for name in FILES:
        (tree / name).write_bytes((name.encode() + b"\x00\xff") * 29)
    if marked:
        _native_set(tree / "c-owned.bin")
        assert _native_get(tree / "c-owned.bin") == VALUE

    archive = tmp_path / "original.cmpct"
    Builder(tree, workers=1, reproducible=False).build(archive)
    first = archive.read_bytes()
    assert preflight_archive(archive)["files"] == 4
    with CMPCT(archive) as reader:
        assert reader.verify() == 4
        old = _attrs_by_path(reader.index)
        assert set(old) == ({"c-owned.bin"} if marked else set())
        if marked:
            assert reader.fsmeta["xattrs"][0][0] == 2

    append_delete(archive, "b-delete.bin")
    second = archive.read_bytes()
    assert second.startswith(first) and len(second) > len(first)
    validated = preflight_archive(archive)
    assert validated["files"] == 3, "in-range signed ordinal must pass structural validity"
    with archive.open("rb") as fp:
        effective_preflight, _, footer, depth = _load_effective_index(
            fp, os.fstat(fp.fileno()).st_size, ParserLimits())
    assert footer and depth == 1
    with CMPCT(archive) as reader:
        assert reader.verify() == 3
        assert [row[0] for row in reader.files] == ["a-early.bin", "c-owned.bin", "z-late.bin"]
        effective_reader = reader.index
        result_reader = _attrs_by_path(effective_reader)
        output = tmp_path / "out"
        reader.extractall(output, metadata=True, require_xattrs=marked)
    result_preflight = _attrs_by_path(effective_preflight)
    if marked:
        assert set(result_reader) == {"c-owned.bin"}
        assert set(result_preflight) == {"c-owned.bin"}, result_preflight
        assert result_reader == result_preflight
        assert _native_get(output / "c-owned.bin") == VALUE
        assert _native_get(output / "z-late.bin") is None
    else:
        assert result_reader == result_preflight == {}
    for name in FILES:
        if name == "b-delete.bin":
            assert not (output / name).exists()
        else:
            assert (output / name).read_bytes() == (tree / name).read_bytes()

    where = os.environ.get("J24G55_EVIDENCE_DIR")
    if where:
        root = Path(where)
        root.mkdir(parents=True, exist_ok=True)
        tag = "inrange_xattr" if marked else "inrange_control"
        (root / f"{tag}-before.cmpct").write_bytes(first)
        (root / f"{tag}-after.cmpct").write_bytes(second)
        (root / f"{tag}-receipt.json").write_text(json.dumps({
            "tag": tag,
            "original_sha256": hashlib.sha256(first).hexdigest(),
            "after_sha256": hashlib.sha256(second).hexdigest(),
            "preflight_accepted": True,
            "preflight_bound_paths": sorted(result_preflight),
            "reader_bound_paths": sorted(result_reader),
            "actual_native_owner": "c-owned.bin" if marked else None,
            "depth": depth, "host": sys.platform,
        }, indent=2, sort_keys=True) + "\n")
    print("J24G55_INRANGE", marked, "preflight", sorted(result_preflight), "reader", sorted(result_reader))
