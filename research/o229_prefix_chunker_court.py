#!/usr/bin/env python3
"""O229 frozen-prefix admission science on authentic CMPCT r24 archives."""
import argparse, hashlib, json, random, statistics, subprocess, sys, tempfile, time
from pathlib import Path
import cmpct.codec as codec
from cmpct.core import Builder, CMPCT

N=16<<20; SAMPLE=4<<20
DIAG=("zero","one-period","two-period","shifted","structured","independent")
TEST=("periodic-altseed","two-period-altseed","shifted-altseed","boundary-insertion","mixed-blocks","random-altseed","late-shift")
CASES=DIAG+TEST
MODES=("fixed","native","admitted")
HELPER=codec._cdc
def h(b): return hashlib.sha256(b).hexdigest()
def rand(seed,n): return random.Random(seed).randbytes(n)
def fill(block,n=N): return (block*(n//len(block)+1))[:n]
def source(name):
    p=rand(20261027,1<<20); q=rand(20261028,1<<20)
    if name=="zero": return bytes(N)
    if name=="one-period": return fill(p)
    if name=="two-period": return fill(p+q)
    if name=="shifted": return fill(p+b"inserted-drift"*73)
    if name=="structured": return fill(b"sku=008371|timestamp=2026-10-27|status=active|bytes=0012345\n")
    if name=="independent": return rand(20261029,N)
    if name=="periodic-altseed": return fill(rand(20261101,768<<10))
    if name=="two-period-altseed": return fill(rand(20261102,768<<10)+rand(20261103,768<<10))
    if name=="shifted-altseed": return fill(rand(20261104,768<<10)+b"delta-boundary"*101)
    if name=="boundary-insertion": return fill(rand(20261105,1<<20)+rand(20261106,8<<10))
    if name=="mixed-blocks": return fill(rand(20261107,1<<20),8<<20)+rand(20261108,4<<20)+fill(rand(20261109,768<<10)+b"drift"*31,4<<20)
    if name=="random-altseed": return rand(20261110,N)
    if name=="late-shift": return rand(20261111,4<<20)+fill(rand(20261112,768<<10)+b"late-drift"*79,12<<20)
    raise ValueError(name)
def rss():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmHWM:"):return int(line.split()[1])
    raise RuntimeError("No process RSS witness")
def archive(root,payload,mode,label):
    codec._cdc=HELPER if mode=="native" else None
    assert (codec._cdc is not None)==(mode=="native")
    src=root/(label+"-tree");src.mkdir()
    (src/"data.bin").write_bytes(payload)
    dst=root/(label+".cmpct")
    t=time.perf_counter_ns();c=time.process_time_ns()
    stats=Builder(src,workers=1,reproducible=True).build(dst)
    wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-c
    with CMPCT(dst) as r:
        assert r.verify()==1 and r.read("data.bin")==payload
        for off in (0,len(payload)//2-64,len(payload)-64):
            assert r.read_range("data.bin",off,64)==payload[off:off+64]
        store=r.index["files"][0][6]
        assert store[0]==codec.S_CDC
        lengths=[int(x[0]) for x in store[1]]
        assert sum(lengths)==len(payload)
    return dict(mode=mode,bytes=dst.stat().st_size,archive_sha=h(dst.read_bytes()),source_sha=h(payload),
                wall_ns=wall,cpu_ns=cpu,chunk_count=len(lengths),
                chunk_lengths_sha=h(json.dumps(lengths).encode()),
                physical_data_bytes=stats.get("data_bytes"),
                compressed_index_bytes=stats.get("index_bytes"),verified=True)
def child(name,mode,rep):
    assert HELPER is not None and name in CASES and mode in MODES and rep in range(3)
    raw=source(name);assert len(raw)==N
    with tempfile.TemporaryDirectory(prefix="o229-") as td:
        root=Path(td);parts=[]
        if mode=="admitted":
            fixed=archive(root,raw[:SAMPLE],"fixed","sample-fixed")
            native=archive(root,raw[:SAMPLE],"native","sample-native")
            parts.extend((fixed,native))
            selected="native" if native["bytes"]*5<=fixed["bytes"]*4 else "fixed"
        else:
            selected=mode;fixed=native=None
        full=archive(root,raw,selected,"full")
        parts.append(full)
    return dict(name=name,mode=mode,rep=rep,selected=selected,full=full,
                sample_fixed=fixed,sample_native=native,sha=h(raw),
                total_wall_ns=sum(x["wall_ns"] for x in parts),
                total_cpu_ns=sum(x["cpu_ns"] for x in parts),
                peak_vmhwm_kib=rss(),verified=True)
