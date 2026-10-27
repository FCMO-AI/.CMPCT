"""J24H02 prospective cross-source court: first-party Writer forward hardlinks.

Documented BEFORE instrument code at
docs/v031-research/2026-10-27-j24h02-writer-hardlink-transfer-prereg.md.
This is not the historical J24H01 failure-asserting test, and changes no Reader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import platform

from cmpct.core import Builder, CMPCT
from cmpct.codec import K_FILE, K_HARDLINK
from cmpct.transactions import append_rename
from cmpct.validation import preflight_archive
import cmpct.reader as reader_module

CONTENT = b"J24H02 first-party signed forward-reference transfer\x00" * 19
ORIGINAL = "original.cmpct"
RENAMED = "writer-renamed.cmpct"
RECEIPT = "source-receipt.json"


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_bytes(data: bytes) -> str:
    header = ("blob " + str(len(data)) + "\0").encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def reader_source(expected_blob: str) -> dict:
    path = Path(reader_module.__file__).resolve()
    actual_blob = git_blob_bytes(path.read_bytes())
    assert actual_blob == expected_blob, (
        f"source mismatch: expected {expected_blob}, installed {actual_blob} at {path}"
    )
    return {
        "reader_blob": actual_blob,
        "reader_path": str(path),
        "python": sys.version,
        "platform": platform.platform(),
    }


def assert_same_inode(a: Path, b: Path) -> None:
    assert a.is_file() and b.is_file()
    assert a.read_bytes() == b.read_bytes() == CONTENT
    # samefile is implemented using physical device/inode identity, on NTFS as well as POSIX.
    assert os.path.samefile(a, b), f"hardlink identity lost: {a!s}, {b!s}"


def prepare(root: Path, expected_blob: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    assert not (root / ORIGINAL).exists() and not (root / RENAMED).exists(), (
        "prepare must begin from a fresh directory"
    )
    source = root / "source"
    source.mkdir()
    owner = source / "b-owner"
    alias = source / "z-alias"
    owner.write_bytes(CONTENT)
    os.link(owner, alias)
    assert_same_inode(owner, alias)
    def _physical_stats(p: Path) -> dict:
        st = p.stat()
        return {"st_dev": st.st_dev, "st_ino": st.st_ino, "st_nlink": st.st_nlink}
    print("J24H02_HOST_HARDLINK_STAT=" + json.dumps({
        "owner": _physical_stats(owner),
        "alias": _physical_stats(alias),
        "samefile": os.path.samefile(owner, alias),
        "host": platform.platform()
    }, sort_keys=True), flush=True)
    original = root / ORIGINAL
    Builder(source, workers=1, reproducible=True).build(original)
    assert preflight_archive(original)["files"] == 2
    with CMPCT(original) as reader:
        assert reader.verify() == 2
        assert reader.by["b-owner"][1] == K_FILE
        print("J24H02_BUILDER_HARDLINK_ROWS=" + json.dumps({
            "b-owner": {"kind": reader.by["b-owner"][1], "storage": reader.by["b-owner"][6][0]},
            "z-alias": {"kind": reader.by["z-alias"][1], "storage": reader.by["z-alias"][6][0]},
        }, sort_keys=True, default=str), flush=True)
        assert reader.by["z-alias"][1] == K_HARDLINK
        assert reader.by["z-alias"][6] == ["b-owner"]
        assert reader.read("z-alias") == CONTENT
    renamed = root / RENAMED
    shutil.copyfile(original, renamed)
    append_rename(renamed, "z-alias", "a-alias")
    assert preflight_archive(renamed)["files"] == 2
    with CMPCT(renamed) as reader:
        assert reader.delta_depth >= 1
        assert sorted(reader.by) == ["a-alias", "b-owner"]
        assert reader.by["a-alias"][1] == K_HARDLINK
        assert reader.by["a-alias"][6] == ["b-owner"]
        assert reader.verify() == 2
    receipt = {
        **reader_source(expected_blob),
        "case": "first-party-appended-rename",
        "original_sha256": sha_file(original),
        "renamed_sha256": sha_file(renamed),
        "original_bytes": original.stat().st_size,
        "renamed_bytes": renamed.stat().st_size,
        "logical_bytes": len(CONTENT),
        "delta_depth": 1,
    }
    (root / RECEIPT).write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print("J24H02_PREPARE=" + json.dumps(receipt, sort_keys=True))
    return receipt


def check(root: Path, expected_blob: str, mode: str) -> dict:
    custody = reader_source(expected_blob)
    original = root / ORIGINAL
    renamed = root / RENAMED
    recorded = json.loads((root / RECEIPT).read_text())
    assert sha_file(original) == recorded["original_sha256"]
    assert sha_file(renamed) == recorded["renamed_sha256"]
    assert preflight_archive(original)["files"] == 2
    assert preflight_archive(renamed)["files"] == 2

    # Historical positive before Writer mutation must survive BOTH source versions.
    with CMPCT(original) as reader:
        assert reader.verify() == 2
        assert reader.read("z-alias") == CONTENT
        reader.extractall(root / f"{mode}-original", metadata=(os.name != 'nt'))
    assert_same_inode(root / f"{mode}-original" / "b-owner",
                      root / f"{mode}-original" / "z-alias")

    with CMPCT(renamed) as reader:
        assert reader.delta_depth >= 1
        assert reader.verify() == 2
        assert reader.read("a-alias") == reader.read("b-owner") == CONTENT
        assert reader.read_range("a-alias", 7, 15) == CONTENT[7:22]
        assert reader.file_sha256("a-alias") == hashlib.sha256(CONTENT).digest()
        output = root / f"{mode}-renamed"
        if mode == "parent-negative":
            try:
                reader.extractall(output, metadata=(os.name != 'nt'))
            except IOError as exc:
                assert "hardlink target not yet extracted" in str(exc), (
                    f"unexpected historical error: {exc!r}"
                )
                error_text = str(exc)
            else:
                raise AssertionError("historical #261 unexpectedly extracted forward hardlink")
            assert not (output / "a-alias").exists()
            outcome = "EXPECTED_BUG_REPRODUCED"
        else:
            reader.extractall(output, metadata=(os.name != 'nt'))
            assert_same_inode(output / "a-alias", output / "b-owner")
            error_text = None
            outcome = "EXACT_SHARED_INODE_RESTORED"

    assert sha_file(original) == recorded["original_sha256"]
    assert sha_file(renamed) == recorded["renamed_sha256"]
    result = {
        **custody,
        "mode": mode,
        "result": outcome,
        "error": error_text,
        "renamed_sha256": recorded["renamed_sha256"],
        "original_sha256": recorded["original_sha256"],
        "logical_sha256": hashlib.sha256(CONTENT).hexdigest(),
        "delta_depth": 1,
        "verified_rows": 2,
    }
    print("J24H02_RESULT=" + json.dumps(result, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mode", choices=("prepare", "parent-negative", "candidate-positive"), required=True)
    parser.add_argument("--reader-blob", required=True)
    parser.add_argument("--receipt-dir", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.root, args.reader_blob)
    else:
        result = check(args.root, args.reader_blob, args.mode)
    if args.receipt_dir:
        args.receipt_dir.mkdir(parents=True, exist_ok=True)
        (args.receipt_dir / (args.mode + ".json")).write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
