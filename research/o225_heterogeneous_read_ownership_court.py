#!/usr/bin/env python3
"""O225 prospective heterogeneous-read ownership court; no Reader code patch.

Preregistration 294c9a460a49f8829dd50fe7996c78709ad61b11.
All three arms operate on the SAME installed CMPCT Reader and authenticated r24 source.
"""
from __future__ import annotations
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time
import zlib
import concurrent.futures

PARENT = "c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
READER_BLOB = "dbd4ac576a05a47eae97e1e40de89cf1de440516"
PREREG = "294c9a460a49f8829dd50fe7996c78709ad61b11"
KINDS = ("fixed", "cdc")
FAMILIES = ("raw_repeat", "zstd_distinct", "deflate_distinct", "mixed_distinct", "zstd_reuse")
ARMS = ("eager", "serial", "bounded64")
REPEATS = 3
NAME = "payload.bin"
MTIME_NS = 946684800000000000

def digest(v):
    return hashlib.sha256(v).hexdigest()

def own_memory():
    """Real own-process VmHWM, not inherited getrusage child high-water."""
    vals = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, remainder = line.split(":", 1)
            vals[key + "_kib"] = int(remainder.split()[0])
    if "VmHWM_kib" not in vals or "VmRSS_kib" not in vals:
        raise AssertionError("missing own Linux VmHWM/VmRSS")
    return vals

def payload(i, n):
    """Distinct reproducible entropy-bearing owner; no identical decoded frames."""
    rand = random.Random(225000 + i * 1039)
    pattern = rand.randbytes(4096)
    return (pattern * ((n + len(pattern) - 1)//len(pattern)))[:n]

def workload(family):
    from cmpct.codec import CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE
    if family == "raw_repeat":
        owners = [bytes([65+i]) for i in range(8)]
        codecs = [CODEC_RAW]*8
        refs = [(i*5+i//31)%8 for i in range(65536)]
    elif family == "zstd_reuse":
        owners = [payload(i,32768) for i in range(8)]
        codecs = [CODEC_ZSTD]*8
        refs = [(i*7+i//37)%8 for i in range(2048)]
    else:
        n = 96 if family == "mixed_distinct" else 128
        owners = [payload(i,262144) for i in range(n)]
        if family == "mixed_distinct":
            codecs = [([CODEC_RAW,CODEC_ZSTD,CODEC_DEFLATE][i%3]) for i in range(n)]
        elif family == "zstd_distinct":
            codecs = [CODEC_ZSTD]*n
        elif family == "deflate_distinct":
            codecs = [CODEC_DEFLATE]*n
        else:
            raise ValueError(family)
        refs = list(range(n))
    return owners, codecs, refs

def archive(owners, codecs, refs, kind, corrupt_crc=False):
    """Independent Builder-free two-index authenticated revision-24 physical writer."""
    import msgpack
    from cmpct.codec import (
        MAGIC, VERSION, FMAGIC, BMAGIC, HDR, BHDR, FTR,
        CODEC_RAW, CODEC_ZSTD, CODEC_DEFLATE,
        K_FILE, S_CHUNKS, S_CDC, zc, sha
    )
    assert VERSION == 24
    encoded_blobs = bytearray()
    rows = []
    for i,(raw,codec) in enumerate(zip(owners,codecs)):
        if codec == CODEC_RAW:
            compressed = raw
        elif codec == CODEC_ZSTD:
            compressed = zc(raw,7)
        elif codec == CODEC_DEFLATE:
            enc = zlib.compressobj(6,zlib.DEFLATED,-15)
            compressed = enc.compress(raw) + enc.flush()
        else:
            raise AssertionError("unknown codec")
        rows.append([len(encoded_blobs),len(raw),len(compressed),codec,0])
        crc = binascii.crc32(raw)&0xffffffff
        if corrupt_crc and i == 0:
            crc ^= 1  # Authentic outer index, deliberately invalid physical CRC.
        encoded_blobs.extend(BHDR.pack(
            BMAGIC,codec,0,0,len(raw),len(compressed),0,crc,sha(raw)
        ))
        encoded_blobs.extend(compressed)
    logical = b"".join(owners[i] for i in refs)
    storage = [S_CHUNKS,refs] if kind == "fixed" else [
        S_CDC,[[len(owners[i]),i] for i in refs]
    ]
    index = {
        "v":VERSION,
        "files":[[NAME,K_FILE,0o644,MTIME_NS,len(logical),sha(logical),storage]],
        "blobs":rows,"recipes":[],"dict_blob":None,"fsmeta":{}
    }
    ib = msgpack.packb(index,use_bin_type=True)
    ic = zc(ib,12)
    ih = sha(ib)
    tail = FTR.pack(FMAGIC,0,1,0,0,len(ic),len(ib),0,ih)
    wire = HDR.pack(MAGIC,VERSION,0,len(ic),len(ib),len(encoded_blobs),ih) + ic + encoded_blobs + ic + tail
    return wire,logical

def read_method(reader,kind,arm):
    if arm == "eager":
        return reader.read(NAME)
    row = reader.by[NAME]
    refs = row[6][1] if kind == "fixed" else [ent[1] for ent in row[6][1]]
    if arm == "serial":
        got = b"".join(reader._blob(i) for i in refs)
    elif arm == "bounded64":
        chunks = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4)) as ex:
            for pos in range(0,len(refs),64):
                chunks.extend(ex.map(reader._blob,refs[pos:pos+64]))
        got = b"".join(chunks)
    else:
        raise ValueError(arm)
    if len(got) != row[4] or hashlib.sha256(got).digest() != bytes(row[5]):
        raise IOError("candidate logical length/SHA mismatch")
    return got

def child(args):
    from cmpct.reader import CMPCT
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    with CMPCT(Path(args.archive)) as reader:
        opened_wall = time.perf_counter_ns()
        opened_cpu = time.process_time_ns()
        got = read_method(reader,args.kind,args.arm)
        if len(got)!=args.logical_bytes or digest(got)!=args.logical_sha:
            raise AssertionError("incorrect complete logical reconstruction")
    # Charge the same Reader.close() boundary to every arm. The eager arm owns
    # an internal thread pool that would otherwise shut down AFTER measurement,
    # while bounded64 shuts its pool before returning; omitting this boundary
    # would produce a hidden candidate-asymmetric setup/teardown comparison.
    read_end_wall = time.perf_counter_ns()
    read_end_cpu = time.process_time_ns()
    mem = own_memory()
    result = {
        "kind":args.kind,"family":args.family,"arm":args.arm,
        "logical_sha256":digest(got),"expected_sha256":args.logical_sha,
        "logical_bytes":len(got),"archive_sha256":args.archive_sha,
        "archive_bytes":Path(args.archive).stat().st_size,
        "read_wall_ms":(read_end_wall-opened_wall)/1e6,
        "read_cpu_ms":(read_end_cpu-opened_cpu)/1e6,
        "session_wall_ms":(read_end_wall-start_wall)/1e6,
        "session_cpu_ms":(read_end_cpu-start_cpu)/1e6,
        "open_wall_ms":(opened_wall-start_wall)/1e6,
        "open_cpu_ms":(opened_cpu-start_cpu)/1e6,
        **mem,"pid":os.getpid(),"python":sys.version.split()[0],
        "cpus":os.cpu_count(),
    }
    print(json.dumps(result,sort_keys=True))

def controls(root):
    from cmpct.reader import CMPCT
    from cmpct.codec import CODEC_RAW,CODEC_ZSTD,CODEC_DEFLATE
    owners = [payload(i,13 + (i*i*17)%117) for i in range(13)]
    codecs = [[CODEC_RAW,CODEC_ZSTD,CODEC_DEFLATE][i%3] for i in range(len(owners))]
    refs = [(i*i+7*i+3)%len(owners) for i in range(113)]
    accepted = []
    hostile = []
    for kind in KINDS:
        wire,logical = archive(owners,codecs,refs,kind)
        p=root/("heldout-"+kind+".cmpct")
        p.write_bytes(wire)
        with CMPCT(p) as reader:
            if reader.read(NAME)!=logical or reader.verify()!=1:
                raise AssertionError("heldout valid Reader control")
            for arm in ARMS:
                got=read_method(reader,kind,arm)
                assert got==logical
                accepted.append({"kind":kind,"arm":arm,"sha256":digest(got),"bytes":len(got)})
            for start in (0,1,11,67,len(logical)//2,len(logical)-29,len(logical)):
                length=min(29,len(logical)-start)
                assert reader.read_range(NAME,start,length)==logical[start:start+length]
        tampered,_=archive(owners,codecs,refs,kind,corrupt_crc=True)
        q=root/("hostile-"+kind+".cmpct")
        q.write_bytes(tampered)
        for arm in ARMS:
            try:
                with CMPCT(q) as reader:
                    read_method(reader,kind,arm)
            except (OSError,ValueError):
                hostile.append({"kind":kind,"arm":arm,"rejected":True})
            else:
                raise AssertionError("malformed physical CRC was accepted: "+kind+"/"+arm)
    return accepted,hostile

def run(args):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    workspace=Path(args.workspace).resolve()
    reader_sha=subprocess.check_output(
        ["git","rev-parse","HEAD:src/cmpct/reader.py"],cwd=workspace,text=True
    ).strip()
    if reader_sha!=READER_BLOB:
        raise AssertionError("Reader source HEAD changed; do not silently transplant result")
    samples=[]
    archives=[]
    with tempfile.TemporaryDirectory(prefix="o225-authentic-") as scratch:
        root=Path(scratch)
        positive,hostile=controls(root)
        for family in FAMILIES:
            owners,codecs,refs=workload(family)
            for kind in KINDS:
                wire,logical=archive(owners,codecs,refs,kind)
                p=root/(family+"-"+kind+".cmpct")
                p.write_bytes(wire)
                assert preflight_archive(p,verify_blob_headers=True)["files"]==1
                with CMPCT(p) as reader:
                    assert reader.verify()==1 and reader.read(NAME)==logical
                    for start in (0,len(logical)//2,len(logical)-1):
                        size=min(73,len(logical)-start)
                        assert reader.read_range(NAME,start,size)==logical[start:start+size]
                manifest={
                    "family":family,"kind":kind,"archive_sha256":digest(wire),
                    "logical_sha256":digest(logical),"archive_bytes":len(wire),
                    "logical_bytes":len(logical),"refs":len(refs),
                    "distinct_owners":len(owners),
                    "codec_mix":dict((str(c),codecs.count(c)) for c in sorted(set(codecs)))
                }
                archives.append(manifest)
                for rep in range(REPEATS):
                    order=list(ARMS)
                    random.Random(2250+rep*37+len(family)*13+len(kind)).shuffle(order)
                    for arm in order:
                        cmd=[sys.executable,__file__,"--child","--archive",str(p),
                             "--family",family,"--kind",kind,"--arm",arm,
                             "--logical-bytes",str(len(logical)),
                             "--logical-sha",digest(logical),
                             "--archive-sha",digest(wire)]
                        started=time.perf_counter()
                        child_run=subprocess.run(cmd,cwd=str(root),capture_output=True,text=True,timeout=90)
                        if child_run.returncode:
                            raise RuntimeError("child failed "+repr((family,kind,arm,rep))+"\n"+child_run.stderr[-3000:])
                        row=json.loads(child_run.stdout)
                        row["rep"]=rep
                        row["process_wall_ms"]=(time.perf_counter()-started)*1000
                        samples.append(row)
                        print(json.dumps({"done":len(samples),"family":family,"kind":kind,
                                          "arm":arm,"rep":rep,"read_wall_ms":row["read_wall_ms"]}),
                              file=sys.stderr,flush=True)
        summaries=[]
        for family in FAMILIES:
            for kind in KINDS:
                group={"family":family,"kind":kind,"arms":{}}
                for arm in ARMS:
                    rr=[r for r in samples if (r["family"],r["kind"],r["arm"])==(family,kind,arm)]
                    group["arms"][arm]={field:statistics.median(x[field] for x in rr)
                        for field in ("read_wall_ms","read_cpu_ms","session_wall_ms",
                                      "session_cpu_ms","open_wall_ms","VmHWM_kib")}
                e=group["arms"]["eager"];s=group["arms"]["serial"];b=group["arms"]["bounded64"]
                group["eager_serial_speedup"]=e["session_wall_ms"]/s["session_wall_ms"]
                group["serial_eager_ratio"]=s["session_wall_ms"]/e["session_wall_ms"]
                group["bounded_eager_speedup"]=e["session_wall_ms"]/b["session_wall_ms"]
                group["bounded_serial_speedup"]=s["session_wall_ms"]/b["session_wall_ms"]
                summaries.append(group)
        def selected(family,kind):
            return next(g for g in summaries if (g["family"],g["kind"])==(family,kind))
        tiny=all(selected("raw_repeat",k)["eager_serial_speedup"]>=1.20 for k in KINDS)
        compressed=all(selected(f,k)["serial_eager_ratio"]<=1.10
                       for f in ("zstd_distinct","deflate_distinct") for k in KINDS)
        memory=all(g["arms"]["serial"]["VmHWM_kib"]-g["arms"]["eager"]["VmHWM_kib"]<=8192
                   for g in summaries)
        universal=tiny and compressed and memory
        bounded=[{"family":g["family"],"kind":g["kind"]} for g in summaries
                 if g["family"] in ("zstd_distinct","deflate_distinct","mixed_distinct")
                 and min(g["bounded_eager_speedup"],g["bounded_serial_speedup"])>=1.20
                 and g["arms"]["bounded64"]["VmHWM_kib"] <= min(
                     g["arms"]["eager"]["VmHWM_kib"],g["arms"]["serial"]["VmHWM_kib"])+8192]
        result={
            "schema":"o225-heterogeneous-reader-ownership-v1",
            "source_parent":PARENT,"reader_blob":READER_BLOB,"prereg_commit":PREREG,
            "python":sys.version.split()[0],"families":list(FAMILIES),
            "kinds":list(KINDS),"arms":list(ARMS),
            "archives":archives,"samples":samples,"summary":summaries,
            "heldout_controls":positive,"hostile_controls":hostile,
            "universal_serial_candidate":universal,
            "bounded_subset_seed":bounded,
            "decision":"UNIVERSAL_SERIAL_CANDIDATE" if universal else "SERIAL_GENERALIZATION_NOT_EARNED"
        }
        destination=Path(args.output).resolve()
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"decision":result["decision"],"samples":len(samples),
                           "summary":summaries,"bounded_subset_seed":bounded},sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--output")
    ap.add_argument("--child",action="store_true")
    ap.add_argument("--archive")
    ap.add_argument("--family")
    ap.add_argument("--kind")
    ap.add_argument("--arm")
    ap.add_argument("--logical-bytes",type=int)
    ap.add_argument("--logical-sha")
    ap.add_argument("--archive-sha")
    a=ap.parse_args()
    child(a) if a.child else run(a)
