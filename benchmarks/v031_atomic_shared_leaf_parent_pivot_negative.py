#!/usr/bin/env python3
"""Actual CMPCT Reader deterministic post-preflight parent-symlink race falsifier.

Research-only NEGATIVE court. Success proves the candidate is NOT race safe,
not that it is safe. Never use this to claim security, sandboxing or release.
All paths and victims are within isolated TemporaryDirectory.
"""
import hashlib
import os
import pathlib
import tempfile

from cmpct.builder import Builder
from cmpct.codec import S_BLOB
from cmpct.reader import CMPCT


def main():
    assert os.name=="posix"
    with tempfile.TemporaryDirectory(prefix="cmpct-atomic-race-negative-") as td:
        root=pathlib.Path(td)
        source=root/"source"
        (source/"nested").mkdir(parents=True)
        new_bytes=b"CMPCT-NEW-ARCHIVE-CONTENT-"*2048
        rel="nested/z-last.bin"
        (source/rel).write_bytes(new_bytes)
        (source/"a-first.bin").write_bytes(b"early-member")
        archive=root/"payload.cmpct"
        Builder(source,workers=1,reproducible=True).build(archive)

        dest=root/"dest"
        (dest/"nested").mkdir(parents=True)
        outside=root/"outside"
        outside.mkdir()
        original=outside/"original-inode.bin"
        original.write_bytes(b"OUTSIDE-ALIAS-CONTENT-PRESERVED")
        outside_leaf=outside/"z-last.bin"
        os.link(original,outside_leaf)
        inside_leaf=dest/"nested"/"z-last.bin"
        os.link(original,inside_leaf)
        original_ino=original.stat().st_ino
        original_sha=hashlib.sha256(original.read_bytes()).digest()
        assert original.stat().st_nlink==3

        with CMPCT(archive) as reader:
            assert reader.by[rel][6][0]==S_BLOB
            preflight=reader._preflight_existing_destination_links
            def pivot(*args,**kwargs):
                observed=preflight(*args,**kwargs)
                assert ("nested","z-last.bin") in observed
                # Legal interleaving: initial static path inspection was
                # correct, but a different actor substitutes its parent.
                os.rename(dest/"nested",dest/"moved")
                (dest/"nested").symlink_to(outside,target_is_directory=True)
                return observed
            reader._preflight_existing_destination_links=pivot
            reader.extractall(dest,metadata=False,atomic_shared_leaf=True)
            assert outside_leaf.read_bytes()==new_bytes
        assert original.stat().st_ino==original_ino
        assert hashlib.sha256(original.read_bytes()).digest()==original_sha
        assert (dest/"moved"/"z-last.bin").read_bytes()==b"OUTSIDE-ALIAS-CONTENT-PRESERVED"
        assert outside_leaf.stat().st_ino!=original_ino
        print("REAL_READER_RACE_NEGATIVE_CONFIRMED: outside directory entry replaced after valid preflight; original outside inode preserved")
        print("CLASSIFICATION=RESEARCH_FALSIFIER_NOT_PRODUCT_SECURITY_PASS")
        print("CAUSE=mutable ancestor pathname between preflight and os.replace; directory-capability design needed")


if __name__=="__main__":
    main()
