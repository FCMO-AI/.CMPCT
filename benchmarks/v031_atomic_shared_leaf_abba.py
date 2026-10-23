#!/usr/bin/env python3
"""Bounded genuine CMPCT Reader ABBA court for optional atomic leaf publication.

Product-like measurement of the *target API*, not a full release gate:
A=unshared direct overwrite; B=shared hardlink opt-in fresh inode;
C=unshared opt-in (must take old hot path). Same input archive/corpus each time.
Different existing inode semantics forbid equal-semantics speed claims.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import resource
import shutil
import statistics
import tempfile
import time
import zipfile
from datetime import datetime, timezone

from cmpct.builder import Builder
from cmpct.codec import S_BLOB, S_PACK, S_SPARSE
from cmpct.reader import CMPCT

REPS=7
CASES={
    "blob_64KiB":S_BLOB,
    "sparse_16MiB":S_SPARSE,
    "pack_eight_ZIPs":S_PACK,
}


def build(root:pathlib.Path,case:str):
    src=root/"source";src.mkdir()
    if case=="blob_64KiB":
        rel="z-member.bin"
        (src/rel).write_bytes(b"bounded-archive-payload-"*3000)
    elif case=="sparse_16MiB":
        rel="z-member.bin"
        with (src/rel).open("wb") as f:
            f.write(b"A"*4096)
            f.seek(16*1024*1024-4096)
            f.write(b"B"*4096)
    else:
        rel="z-member.zip"
        for i in range(8):
            p=(src/rel) if i==7 else src/f"zip-{i:02d}.zip"
            with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("member.txt",bytes([i])*1536)
    archive=root/"real.cmpct"
    Builder(src,workers=1,reproducible=True).build(archive)
    return archive,rel


def one(root:pathlib.Path,archive:pathlib.Path,rel:str,variant:str,rep:int):
    dest=root/f"dest-{variant}-{rep}"
    dest.mkdir()
    leaf=dest/rel
    outside=None
    if variant=="B_shared_atomic":
        outside=root/f"outside-{variant}-{rep}"
        outside.write_bytes(b"preserve-external-inode")
        os.link(outside,leaf)
    else:
        leaf.write_bytes(b"preexisting-single-link")
    old_inode=leaf.stat().st_ino
    with CMPCT(archive) as reader:
        start_cpu=time.process_time_ns()
        start_wall=time.perf_counter_ns()
        reader.extractall(dest,metadata=False,atomic_shared_leaf=variant!="A_single_default")
        wall=(time.perf_counter_ns()-start_wall)/1e6
        cpu=(time.process_time_ns()-start_cpu)/1e6
        expected=reader.read(rel)
        got=leaf.read_bytes()
        assert hashlib.sha256(got).digest()==hashlib.sha256(expected).digest()
    sentinel=(outside.read_bytes()==b"preserve-external-inode") if outside else None
    if outside: assert sentinel and leaf.stat().st_ino!=outside.stat().st_ino
    if variant=="C_single_optin":assert leaf.stat().st_ino==old_inode
    assert not list(dest.glob(".cmpct-part-*"))
    return {"wall_ms":wall,"cpu_ms":cpu,"logical_bytes":leaf.stat().st_size,
            "physical_bytes_st_blocks":leaf.stat().st_blocks*512,"outside_unchanged":sentinel,
            "new_inode":leaf.stat().st_ino!=old_inode}


def main():
    assert os.name=="posix"
    result={
        "experiment":"v031 genuine CMPCT opt-in conditional shared leaf ABBA",
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "source_expected_reader_blob":"562b6af136c252ddc8ff25f968c5c1d4d3760408",
        "semantics":"A/C are unshared in-place writers; B owns an extra outside hardlink and must publish fresh inode. Archive input is identical, output logical bytes identical, filesystem inode semantics differ. This is *not* the r24 release-parity gate.",
        "host":"GitHub Actions when run there; library extractall only, process open excluded",
        "repetitions":REPS,
        "corpora":{}
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-atomic-abba-") as temp:
        root=pathlib.Path(temp)
        for case,expected in CASES.items():
            test=root/case;test.mkdir()
            archive,rel=build(test,case)
            with CMPCT(archive) as reader:
                assert reader.by[rel][6][0]==expected, "unexpected genuine Builder representation"
                sha=hashlib.sha256(reader.read(rel)).hexdigest()
            rows={"A_single_default":[],"B_shared_atomic":[],"C_single_optin":[]}
            # Rotated ABBA-like three-arm ordering prevents systematic first-run bias.
            orders=[
                ("A_single_default","B_shared_atomic","C_single_optin"),
                ("B_shared_atomic","C_single_optin","A_single_default"),
                ("C_single_optin","A_single_default","B_shared_atomic"),
            ]
            for rep in range(REPS):
                for variant in orders[rep%len(orders)]:
                    rows[variant].append(one(test,archive,rel,variant,rep))
            result["corpora"][case]={
                "archive_bytes":archive.stat().st_size,
                "source_logical_sha256":sha,
                "repetitions":rows,
                "median_wall_ms":{k:statistics.median(x["wall_ms"] for x in r) for k,r in rows.items()},
                "median_cpu_ms":{k:statistics.median(x["cpu_ms"] for x in r) for k,r in rows.items()},
            }
    result["maxrss_kib_process"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    pathlib.Path("benchmark-artifacts").mkdir(exist_ok=True)
    pathlib.Path("benchmark-artifacts/atomic_shared_leaf_abba.json").write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8")
    for case,x in result["corpora"].items():
        print(case, "archive_bytes",x["archive_bytes"],
              "median_wall_ms",x["median_wall_ms"],"median_cpu_ms",x["median_cpu_ms"])
    print("GENUINE_PRODUCT_ABBA_RESEARCH_COMPLETE; not equivalent inode semantics, no release gate credit")

if __name__=="__main__":
    main()
