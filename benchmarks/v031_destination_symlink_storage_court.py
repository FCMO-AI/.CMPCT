"""Second independent v0.31 POSIX destination-link storage-kind court.

The first baseline remains immutable. This script tests an independently
preregistered CDC ancestor/leaf contrast plus a symlink row leaf control.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile

from cmpct.builder import Builder
from cmpct.codec import CHUNK, K_SYMLINK, S_CDC
from cmpct.reader import CMPCT


def cdc_case(pivot: str):
    payload = hashlib.shake_256(b"cmpct-cdc-symlink-boundary-v2").digest(4*CHUNK + 8192)
    with tempfile.TemporaryDirectory(prefix="cmpct-cdc-dest-boundary-") as temp:
        root = Path(temp)
        source = root / "source"
        (source / "nested").mkdir(parents=True)
        (source / "nested" / "large.bin").write_bytes(payload)
        archive = root / "archive.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            assert reader.by["nested/large.bin"][6][0] == S_CDC
            assert reader.read("nested/large.bin") == payload
            assert reader.verify() >= 1
            outside = root / "outside"
            outside.mkdir()
            victim = outside / "large.bin"
            before = b"VICTIM_UNTOUCHED:" + pivot.encode()
            victim.write_bytes(before)
            dest = root / "dest"
            dest.mkdir()
            if pivot == "ancestor":
                (dest / "nested").symlink_to(outside, target_is_directory=True)
            elif pivot == "leaf":
                (dest / "nested").mkdir()
                (dest / "nested" / "large.bin").symlink_to(victim)
            else:
                raise ValueError(pivot)
            assert victim.read_bytes() == before
            reader.extractall(dest, safe_symlinks=True)
            after = victim.read_bytes()
            assert (after == payload) == (pivot == "ancestor"), pivot
            assert (after == before) == (pivot == "leaf"), pivot
            assert (dest / "nested" / "large.bin").read_bytes() == payload
            return dict(case="cdc_"+pivot, storage="S_CDC",
                        outside_modified=(after != before),
                        extracted_sha256=hashlib.sha256(payload).hexdigest(),
                        final_victim_sha256=hashlib.sha256(after).hexdigest(),
                        status="OBSERVED")


def symlink_row_control():
    with tempfile.TemporaryDirectory(prefix="cmpct-linkrow-control-") as temp:
        root = Path(temp)
        source = root / "source"
        source.mkdir()
        (source / "reference.bin").write_bytes(b"source")
        (source / "alias").symlink_to("reference.bin")
        archive = root / "archive.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as reader:
            assert reader.by["alias"][1] == K_SYMLINK
            assert reader.verify() >= 2
            outside = root / "outside"
            outside.mkdir()
            victim = outside / "victim.bin"
            victim.write_bytes(b"UNCHANGED_OUTSIDE")
            dest = root / "dest"
            dest.mkdir()
            (dest / "alias").symlink_to(victim)
            reader.extractall(dest, safe_symlinks=True)
            assert victim.read_bytes() == b"UNCHANGED_OUTSIDE"
            assert (dest / "alias").is_symlink()
            assert (dest / "alias").readlink().as_posix() == "reference.bin"
            return dict(case="symlink_row_leaf", storage="K_SYMLINK",
                        outside_modified=False, status="OBSERVED")


if __name__ == "__main__":
    outcomes=[cdc_case("ancestor"),cdc_case("leaf"),symlink_row_control()]
    assert [x["outside_modified"] for x in outcomes] == [True,False,False]
    print(json.dumps({
        "schema":"cmpct-destination-symlink-storage-v2",
        "result":"ATOMIC_LEAF_PROTECTION_DOES_NOT_CONTAIN_PARENT_SYMLINK",
        "cases":outcomes,
        "scope":"POSIX small synthetic corpus, no concurrency or portability claim",
    },indent=2,sort_keys=True))
