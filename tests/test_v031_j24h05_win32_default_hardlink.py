"""J24H05 source-exact product court: first-party Writer forward hardlinks + default metadata.

Preregistered at 817125d0c64297d0e095be37f109e26b8d9b544b.
Real Builder -> authenticated Writer.append_rename -> Reader.extractall(metadata=True).
The known Windows metadata=False route is intentionally NOT an accepted alternative.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path

from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.core import Builder, CMPCT
from cmpct.transactions import append_rename
from cmpct.validation import preflight_archive

STAMP_NS = 1_580_643_296_000_000_000
TOLERANCE_NS = 3_000_000_000
CONTENT = b"J24H05 exact first-party hardlink with metadata\x00" * 29
OTHER = b"independent ordinary member" * 17


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _same_inode(a: Path, b: Path) -> bool:
    return os.path.samefile(a, b)


def _assert_time(path: Path, expected: int) -> int:
    actual = path.stat().st_mtime_ns
    assert abs(actual - expected) <= TOLERANCE_NS, (
        f"physical timestamp mismatch: {path}: actual={actual}, signed={expected}"
    )
    return actual


def test_default_metadata_writer_forward_hardlink_full_contract(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    owner, alias, independent = (src / p for p in ("b-owner", "z-alias", "x-independent"))
    owner.write_bytes(CONTENT)
    os.link(owner, alias)
    independent.write_bytes(CONTENT)
    assert _same_inode(owner, alias) and not _same_inode(owner, independent)
    os.utime(owner, ns=(STAMP_NS, STAMP_NS))
    os.utime(independent, ns=(STAMP_NS, STAMP_NS))
    nested = src / "nested"
    nested.mkdir()
    child = nested / "other.bin"
    child.write_bytes(OTHER)
    os.utime(child, ns=(STAMP_NS, STAMP_NS))
    os.utime(nested, ns=(STAMP_NS, STAMP_NS))

    original = tmp_path / "original.cmpct"
    Builder(src, workers=1, reproducible=False).build(original)
    assert original.read_bytes().startswith(b"CMPCT24\x00")
    assert preflight_archive(original)["files"] == 5
    with CMPCT(original) as reader:
        assert reader.verify() == 4
        assert reader.by["b-owner"][1] == K_FILE
        assert reader.by["z-alias"][1] == K_HARDLINK
        assert reader.by["z-alias"][6] == ["b-owner"]
        assert reader.by["x-independent"][1] == K_FILE
        assert reader.read_range("z-alias", 7, 19) == CONTENT[7:26]
        assert abs(reader.by["b-owner"][3] - STAMP_NS) <= TOLERANCE_NS
        assert abs(reader.by["nested"][3] - STAMP_NS) <= TOLERANCE_NS
        before = tmp_path / "original-extract"
        reader.extractall(before)  # DEFAULT metadata=True: no workaround.
        assert (before / "b-owner").read_bytes() == CONTENT
        assert (before / "z-alias").read_bytes() == CONTENT
        assert _same_inode(before / "b-owner", before / "z-alias")
        assert not _same_inode(before / "b-owner", before / "x-independent")
        _assert_time(before / "b-owner", reader.by["b-owner"][3])
        _assert_time(before / "nested", reader.by["nested"][3])

    renamed = tmp_path / "renamed.cmpct"
    renamed.write_bytes(original.read_bytes())
    append_rename(renamed, "z-alias", "a-alias")
    assert preflight_archive(renamed)["files"] == 5
    with CMPCT(renamed) as reader:
        assert reader.delta_depth >= 1
        assert sorted(reader.by) == ["a-alias", "b-owner", "nested", "nested/other.bin", "x-independent"]
        assert reader.by["a-alias"][1] == K_HARDLINK
        assert reader.by["a-alias"][6] == ["b-owner"]
        assert reader.by["b-owner"][1] == K_FILE
        assert reader.verify() == 4
        assert reader.read("a-alias") == reader.read("b-owner") == CONTENT
        assert reader.read_range("a-alias", 2, 17) == CONTENT[2:19]
        assert reader.file_sha256("a-alias") == hashlib.sha256(CONTENT).digest()
        output = tmp_path / "forward-extract"
        reader.extractall(output)  # DEFAULT public API on Win32 too.
        assert (output / "a-alias").read_bytes() == CONTENT
        assert (output / "b-owner").read_bytes() == CONTENT
        assert (output / "x-independent").read_bytes() == CONTENT
        assert (output / "nested" / "other.bin").read_bytes() == OTHER
        assert _same_inode(output / "a-alias", output / "b-owner")
        assert not _same_inode(output / "x-independent", output / "b-owner")
        file_time = _assert_time(output / "a-alias", reader.by["b-owner"][3])
        dir_time = _assert_time(output / "nested", reader.by["nested"][3])
        child_time = _assert_time(output / "nested" / "other.bin", reader.by["nested/other.bin"][3])

    assert _sha256(original) != _sha256(renamed), "Writer generation not persisted"
    receipt = {
        "host": platform.platform(),
        "original_archive_bytes": original.stat().st_size,
        "renamed_archive_bytes": renamed.stat().st_size,
        "original_sha256": _sha256(original),
        "renamed_sha256": _sha256(renamed),
        "logical_sha256": hashlib.sha256(CONTENT).hexdigest(),
        "metadata_true": True,
        "entries": 5,
        "verified_non_directory_rows": 4,
        "owner_and_alias_same_inode": True,
        "identical_independent_content_distinct_inode": True,
        "file_mtime_ns": file_time,
        "dir_mtime_ns": dir_time,
        "child_mtime_ns": child_time,
        "timestamp_tolerance_ns": TOLERANCE_NS,
        "result": "DEFAULT_METADATA_WRITER_FORWARD_HARDLINK_RECONSTRUCTED",
    }
    print("J24H05_RESULT=" + json.dumps(receipt, sort_keys=True), flush=True)
    output_dir = os.environ.get("J24H05_RECEIPTS")
    if output_dir:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / "j24h05-default-extract.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n"
        )
