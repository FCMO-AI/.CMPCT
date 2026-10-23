#!/usr/bin/env python3
"""Actual Reader metadata compatibility oracle for optional fresh-inode publication.

Output is observational: preserved archive xattrs and *loss of inherited*
destination xattrs both matter. Linux POSIX/user.* xattr premise must hold.
Research only; not an assertion of complete metadata portability.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT

SOURCE_ATTR="user.cmpct_source"
DEST_ATTR="user.cmpct_destination"
SOURCE_BYTES=b"archive-file-source"*2048
OLD_BYTES=b"preexisting-physical-alias"


def getx(path,attr):
    try:return os.getxattr(path,attr)
    except OSError:return None


def main():
    if os.name!="posix" or not hasattr(os,"setxattr"):
        print("XATTR_PREMISE_NOT_AVAILABLE")
        return
    with tempfile.TemporaryDirectory(prefix="cmpct-atomic-metadata-") as td:
        t=pathlib.Path(td)
        src=t/"source";src.mkdir()
        (src/"leaf.bin").write_bytes(SOURCE_BYTES)
        try:os.setxattr(src/"leaf.bin",SOURCE_ATTR,b"source-property")
        except OSError as e:
            print(f"XATTR_PREMISE_UNAVAILABLE_ERRNO={e.errno}")
            return
        archive=t/"actual.cmpct"
        # Fidelity mode is mandatory for the SOURCE xattr court.
        # Builder(reproducible=True) intentionally strips host xattrs by
        # contract; that control cannot test Reader metadata restoration.
        Builder(src,workers=1,reproducible=False).build(archive)
        result={}
        for variant in ("default_single_meta_off","atomic_shared_meta_off","atomic_shared_meta_on"):
            dest=t/variant;dest.mkdir()
            leaf=dest/"leaf.bin"
            outside=t/(variant+"-outside")
            outside.write_bytes(OLD_BYTES)
            os.setxattr(outside,DEST_ATTR,b"preexisting-property")
            if variant=="default_single_meta_off":
                # Single leaf with existing destination xattr; direct writer keeps inode.
                leaf.write_bytes(OLD_BYTES)
                os.setxattr(leaf,DEST_ATTR,b"preexisting-property")
                original_ino=leaf.stat().st_ino
            else:
                os.link(outside,leaf)
                original_ino=outside.stat().st_ino
            with CMPCT(archive) as r:
                r.extractall(dest,metadata=variant.endswith("on"),
                             atomic_shared_leaf=variant.startswith("atomic"))
                assert leaf.read_bytes()==r.read("leaf.bin")
            result[variant]={
                "new_inode":leaf.stat().st_ino!=original_ino,
                "archive_source_xattr_restored":getx(leaf,SOURCE_ATTR)==b"source-property",
                "previous_destination_xattr_on_new_leaf":getx(leaf,DEST_ATTR)==b"preexisting-property",
                "outside_original_inode_content_unchanged":outside.read_bytes()==OLD_BYTES,
                "outside_destination_xattr_unchanged":getx(outside,DEST_ATTR)==b"preexisting-property",
                "leaf_mode_octal":oct(stat.S_IMODE(leaf.stat().st_mode))
            }
        assert result["default_single_meta_off"]["previous_destination_xattr_on_new_leaf"]
        assert not result["atomic_shared_meta_off"]["previous_destination_xattr_on_new_leaf"]
        assert result["atomic_shared_meta_on"]["archive_source_xattr_restored"]
        assert all(v["outside_original_inode_content_unchanged"] for v in result.values())
        result["classification"]="ARCHIVE_XATTR_RESTORED_WITH_METADATA; DESTINATION_XATTR_DROPPED_ON_NEW_INODE_META_OFF; DISCLOSED_COMPATIBILITY_DEBT"
        pathlib.Path("benchmark-artifacts").mkdir(exist_ok=True)
        pathlib.Path("benchmark-artifacts/atomic_shared_leaf_metadata.json").write_text(
            json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
