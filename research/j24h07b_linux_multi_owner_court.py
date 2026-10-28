"""J24H07b: host-side, source-exact, first-party multi-owner and CDC/sparse hardlink court.

This is NOT a full system benchmark. Product source is from J24H07 child of #629.
Preserve real file content, on-disk format, source ownership, and all negative cases.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
import time
from unittest import mock

from cmpct.codec import K_FILE, K_HARDLINK, S_CDC, S_SPARSE
from cmpct.core import Builder, CMPCT
from cmpct import reader as reader_mod


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fd_count():
    return len(os.listdir("/proc/self/fd"))


def execute(root):
    src=root/"source"; src.mkdir()
    pairs=[]
    for n in range(24):
        a=src/f"group-{n:02d}-a.bin"
        z=src/f"group-{n:02d}-z.bin"
        raw=(f"owner {n} /".encode()*1003)
        a.write_bytes(raw);os.link(a,z)
        pairs.append((a.name,z.name,raw))
    # Greater than 4*CHUNK=1MiB to force true CDC on ordinary dense input.
    dense=b"".join(hashlib.sha256(n.to_bytes(4,"little")).digest()
                   for n in range(40000))[:1_200_000]
    a=src/"cdc-a.bin";z=src/"cdc-z.bin";a.write_bytes(dense);os.link(a,z)
    pairs.append((a.name,z.name,dense))
    # Real sparse extent, not a synthetic list/byte-array pretending to be holes.
    a=src/"sparse-a.bin";z=src/"sparse-z.bin"
    with a.open("wb") as f:
        f.write(b"PHYSICAL-BEGIN");f.seek(2_000_000);f.write(b"PHYSICAL-END")
    os.link(a,z);pairs.append((a.name,z.name,a.read_bytes()))

    archive=root/"multi.cmpct"
    t0=time.perf_counter()
    Builder(src,workers=1,reproducible=False).build(archive)
    create_wall=time.perf_counter()-t0
    with CMPCT(archive) as reader:
        by=reader.by
        types={p[0]:by[p[0]][6][0] for p in pairs}
        assert by["cdc-a.bin"][1]==K_FILE
        assert types["cdc-a.bin"]==S_CDC, types
        # Sparse support varies by FS: report whether the real Builder selected it.
        assert all(by[a][1]==K_FILE and by[z][1]==K_HARDLINK
                   for a,z,_ in pairs)
        assert reader.verify()==len(pairs)*2
        original=reader_mod._linux_link_owner_fd
        max_fd=fd_count()
        invocations=0
        def record_link(fd,alias, *, parent_fd=None):
            nonlocal max_fd,invocations
            invocations+=1
            st=os.fstat(fd)
            assert st.st_nlink>=1
            max_fd=max(max_fd,fd_count())
            return original(fd,alias,parent_fd=parent_fd)
        out=root/"out"
        fd_baseline=fd_count()
        t1=time.perf_counter()
        with mock.patch("cmpct.reader._linux_link_owner_fd",side_effect=record_link):
            reader.extractall(out,metadata=True)
        extract_wall=time.perf_counter()-t1
    checks=[]
    for a,z,raw in pairs:
        aa=out/a;zz=out/z
        assert aa.read_bytes()==zz.read_bytes()==raw,(a,z)
        assert os.path.samefile(aa,zz),(a,z)
        assert not aa.is_symlink() and not zz.is_symlink()
        assert aa.stat().st_mtime_ns==zz.stat().st_mtime_ns
        checks.append({"owner":a,"alias":z,"bytes":len(raw),"sha256":sha(raw),
                       "same_inode":True})
    assert invocations==len(pairs),(invocations,len(pairs))
    # One-owner-at-a-time fd scheduling, not one fd per archived owner.
    assert max_fd<=fd_baseline+16,(max_fd,fd_baseline)
    return {"hypothesis":"J24H07B-MULTI-OWNER","platform":platform.platform(),
            "archive_bytes":archive.stat().st_size,
            "archive_sha256":sha(archive.read_bytes()),
            "CDC_storage_true":types["cdc-a.bin"]==S_CDC,
            "sparse_storage_true":types["sparse-a.bin"]==S_SPARSE,
            "physical_hardlink_pairs":len(pairs),
            "actual_kernel_link_calls":invocations,
            "fd_baseline":fd_baseline,"fd_peak_at_link":max_fd,
            "fd_amplification":max_fd-fd_baseline,
            "create_wall_seconds":create_wall,
            "extract_wall_seconds":extract_wall,
            "cases":checks,"result":"PASS_WITHIN_HOST_SCOPE"}


if __name__=="__main__":
    if platform.system()!="Linux":raise SystemExit("Linux-only source fd oracle")
    with tempfile.TemporaryDirectory(prefix="cmpct-j24h07b-") as temp:
        result=execute(Path(temp))
    directory=os.environ.get("J24H07_ARTIFACTS")
    if directory:
        p=Path(directory);p.mkdir(parents=True,exist_ok=True)
        (p/"portfolio.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24H07B_MULTI_STORAGE="+json.dumps(result,sort_keys=True),flush=True)
