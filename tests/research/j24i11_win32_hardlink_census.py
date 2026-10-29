"""J24I11: installed three-OS hardlink-owner fidelity, not a release benchmark.

Preserve distinct inode classes, not merely deduplicated content or logical SHA.
Retain source and compacted archives physically for independent review.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import cmpct
from cmpct.builder import Builder
from cmpct.codec import K_FILE, K_HARDLINK, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.transactions import compact_archive, _compaction_source_metadata


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inode(path: Path) -> tuple[int, int]:
    st = os.stat(path, follow_symlinks=False)
    return st.st_dev, st.st_ino


def examine(path: Path) -> dict:
    with CMPCT(path) as reader:
        rows = list(reader.files)
        kinds = {row[0]: row[1] for row in rows}
        if kinds != {"a_owner.bin": K_FILE, "b_alias.bin": K_HARDLINK,
                     "c_same_bytes_copy.bin": K_FILE, "d_source_symlink": K_SYMLINK}:
            raise AssertionError("wrong filesystem topology in CMPCT index: " + repr(kinds))
        by_name = {row[0]: row for row in rows}
        if by_name["b_alias.bin"][6] != ["a_owner.bin"]:
            raise AssertionError("hardlink alias lacks expected owner relationship")
        raw = reader.read("a_owner.bin")
        if (reader.read("b_alias.bin") != raw or
                reader.read("c_same_bytes_copy.bin") != raw):
            raise AssertionError("owner/alias/copy content mismatch")
        if reader.read("d_source_symlink") != b"a_owner.bin":
            raise AssertionError("symlink literal changed in archive")
        if reader.verify() != 4:
            raise AssertionError("strong verification did not cover all four entries")
        return {"rows": rows, "metadata": _compaction_source_metadata(reader),
                "file_digest": hashlib.sha256(raw).hexdigest(), "verified": 4}


def extracted_identity(path: Path, destination: Path) -> dict:
    with CMPCT(path) as reader:
        reader.extractall(destination)
    a = destination / "a_owner.bin"
    b = destination / "b_alias.bin"
    c = destination / "c_same_bytes_copy.bin"
    s = destination / "d_source_symlink"
    if inode(a) != inode(b):
        raise AssertionError("extraction did not preserve owner/alias hardlink inode")
    if inode(c) == inode(a):
        raise AssertionError("extraction incorrectly linked independent equal-byte copy")
    if not s.is_symlink() or os.readlink(s) != "a_owner.bin":
        raise AssertionError("extraction lost ordinary safe symlink")
    if a.read_bytes() != b.read_bytes() or a.read_bytes() != c.read_bytes():
        raise AssertionError("extracted logical content changed")
    return {"owner_alias_same_inode": True, "copy_distinct_inode": True,
            "safe_symlink_preserved": True}


def main() -> dict:
    checkout = Path(os.environ["CMPCT_J24I11_CHECKOUT"]).resolve()
    imported = Path(cmpct.__file__).resolve()
    if imported == checkout or checkout in imported.parents:
        raise AssertionError("must use installed wheel, not checkout")
    if os.environ["CMPCT_J24I11_HEAD"] != os.environ["CMPCT_J24I11_EXPECTED_HEAD"]:
        raise AssertionError("exact HEAD mismatch")
    artifacts = Path(os.environ["CMPCT_J24I11_ARTIFACT_DIR"])
    artifacts.mkdir(parents=True, exist_ok=True)
    rec = {"schema": "j24i11-trusted-link-count-v1",
           "source_sha": os.environ["CMPCT_J24I11_HEAD"], "python": sys.version,
           "host": platform.platform(), "installed_module": str(imported),
           "status": "RUNNING", "stage": "start"}
    try:
        with tempfile.TemporaryDirectory(prefix="j24i11-") as tmp:
            work = Path(tmp)
            root = work / "input"
            root.mkdir()
            payload = bytes(range(256))*16 + b"J24I11 source filesystem topology\n"
            (root/"a_owner.bin").write_bytes(payload)
            os.link(root/"a_owner.bin", root/"b_alias.bin")
            (root/"c_same_bytes_copy.bin").write_bytes(payload)
            (root/"d_source_symlink").symlink_to("a_owner.bin")
            st_a = os.stat(root/"a_owner.bin", follow_symlinks=False)
            st_b = os.stat(root/"b_alias.bin", follow_symlinks=False)
            st_c = os.stat(root/"c_same_bytes_copy.bin", follow_symlinks=False)
            with os.scandir(root) as it:
                scan = {e.name: e.stat(follow_symlinks=False) for e in it}
            rec["source_witness"] = {
                "os_stat_nlink": [st_a.st_nlink, st_b.st_nlink, st_c.st_nlink],
                "scandir_nlink": [scan[n].st_nlink for n in
                                 ("a_owner.bin", "b_alias.bin", "c_same_bytes_copy.bin")],
                "os_link_inode_equal": inode(root/"a_owner.bin") == inode(root/"b_alias.bin"),
                "independent_copy_inode_distinct": inode(root/"a_owner.bin") != inode(root/"c_same_bytes_copy.bin"),
                "scandir_link_inode_equal": (
                    scan["a_owner.bin"].st_dev, scan["a_owner.bin"].st_ino) == (
                    scan["b_alias.bin"].st_dev, scan["b_alias.bin"].st_ino),
                # The same physical pathname may expose unequal IDs across the
                # two different Python stat APIs on Win32. Record, don't assume.
                "cross_api_owner_inode_equal": (
                    scan["a_owner.bin"].st_dev, scan["a_owner.bin"].st_ino) == (
                    st_a.st_dev, st_a.st_ino),
                "os_stat_owner_identity": [st_a.st_dev, st_a.st_ino],
                "scandir_owner_identity": [scan["a_owner.bin"].st_dev,
                                            scan["a_owner.bin"].st_ino],
                "symlink_observed": os.readlink(root/"d_source_symlink"),
            }
            if (not rec["source_witness"]["os_link_inode_equal"] or
                    not rec["source_witness"]["independent_copy_inode_distinct"] or
                    not rec["source_witness"]["scandir_link_inode_equal"]):
                raise AssertionError("source filesystem not a trustworthy hardlink/copy control")
            src, dst = work/"source.cmpct", work/"compacted.cmpct"
            rec["stage"] = "build"
            Builder(root, reproducible=True, workers=1).build(src)
            shutil.copyfile(src, artifacts/"source.cmpct")
            before = examine(src)
            rec["source_archive"] = {"sha256": digest(src), "bytes": src.stat().st_size}
            rec["stage"] = "compact"
            compact_archive(src, dst)
            shutil.copyfile(dst, artifacts/"compacted.cmpct")
            after = examine(dst)
            rec["output_archive"] = {"sha256": digest(dst), "bytes": dst.stat().st_size}
            if before != after:
                raise AssertionError("compaction changed hardlink/copy/symlink semantic rows or metadata")
            if digest(src) != rec["source_archive"]["sha256"]:
                raise AssertionError("compaction mutated source")
            rec["stage"] = "physical-extraction"
            rec["source_extract"] = extracted_identity(src, work/"extracted-source")
            rec["output_extract"] = extracted_identity(dst, work/"extracted-output")
            rec["archive_semantics_equal"] = True
            rec["status"] = "HOST_CORRECTNESS_PASS_NOT_RELEASE"
            rec["stage"] = "complete"
            return rec
    except BaseException as exc:
        rec["status"] = "HOST_NONPASS"
        rec["error"] = type(exc).__name__ + ": " + str(exc)
        rec["traceback"] = traceback.format_exc(limit=10)
        raise
    finally:
        Path(os.environ["CMPCT_J24I11_RECEIPT"]).write_text(
            json.dumps(rec, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, default=str))
