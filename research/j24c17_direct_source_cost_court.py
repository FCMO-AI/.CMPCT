"""J24C17 prospective exact-source owner-vs-sealed installed Reader cost court.

A second control distinct from the inherited J24C13 native-only arm. Both
wheels are built from independent exact Git checkouts, and run in independent
fresh Python processes on the identical physical signed r24 archives.
No performance threshold is moved; negative economics remains evidence.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def peak_rss_mib():
    if os.name == "nt":
        return None  # This court is Ubuntu only; do not fabricate Win32 RSS.
    import resource
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw / 1048576 if sys.platform == "darwin" else raw / 1024


def worker(manifest, arm):
    import cmpct.reader as module
    from cmpct.reader import CMPCT
    from cmpct import _chunk_admission as native
    assert arm in ("owner662", "sealed676")
    assert callable(native._scan_refs_index)
    path = Path(manifest["archive"])
    assert digest(path.read_bytes()) == manifest["archive_sha256"]
    package_path = Path(module.__file__).resolve()
    assert "site-packages" in package_path.parts or "dist-packages" in package_path.parts
    begin_wall = time.perf_counter_ns()
    begin_cpu = time.process_time_ns()
    with CMPCT(path) as rd:
        opened_wall = time.perf_counter_ns()
        opened_cpu = time.process_time_ns()
        marks = rd._chunk_range_marks.get("fixed.bin")
        assert marks is not None
        if arm == "owner662":
            assert not hasattr(rd, "_chunk_range_sealed")
            assert type(rd.by["fixed.bin"][6][1]) is list
        else:
            assert type(rd.by["fixed.bin"][6][1]) is tuple
            assert rd._chunk_range_sealed.get("fixed.bin") is not None
        for start, length, expected in manifest["queries"]:
            actual = rd.read_range("fixed.bin", start, length)
            assert digest(actual) == expected
        read_wall = time.perf_counter_ns()
        read_cpu = time.process_time_ns()
    return dict(
        arm=arm,case=manifest["case"],archive_sha256=manifest["archive_sha256"],
        answer_sha256=digest(b"".join(bytes.fromhex(h) for _,_,h in manifest["queries"])),
        q=len(manifest["queries"]),session_wall_ns=read_wall-begin_wall,
        session_cpu_ns=read_cpu-begin_cpu,
        open_wall_ns=opened_wall-begin_wall,open_cpu_ns=opened_cpu-begin_cpu,
        read_wall_ns=read_wall-opened_wall,read_cpu_ns=read_cpu-opened_cpu,
        rss_mib=peak_rss_mib(),source_path=str(package_path),
        python=sys.version.split()[0],host=platform.platform()
    )


def run(args):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
    from test_o215_fixed_chunk_admission import _make_archive
    prior=Path(args.owner_python).resolve()
    new=Path(args.sealed_python).resolve()
    assert prior!=new and prior.exists() and new.exists()
    raw=[]
    with tempfile.TemporaryDirectory(prefix="cmpct-j24c17-direct-cost-") as td:
        root=Path(td)
        for n in (65536,262144):
            for family,owners in (("fixed",(b"A",)),("hetero",(b"A",b"BC",b"DEF"))):
                refs=[i%len(owners) for i in range(n)]
                logical=b"".join(owners[i] for i in refs)
                wire=_make_archive(refs,logical,blobs=owners)
                archive=root/(family+str(n)+".cmpct")
                archive.write_bytes(wire)
                for q,regime in ((1,"early"),(6,"mixed"),(32,"mixed")):
                    starts=[0] if q==1 else [0,len(logical)//2,max(0,len(logical)-1)]
                    rnd=random.Random(241700+n+q+len(owners))
                    while len(starts)<q:
                        starts.append(rnd.randrange(len(logical)+1))
                    queries=[]
                    for start in starts[:q]:
                        length=min(1+start%7,len(logical)-start)
                        queries.append((start,length,digest(logical[start:start+length])))
                    cfg=dict(
                        case=f"{family}-{n}-q{q}-{regime}",archive=str(archive),
                        archive_sha256=digest(wire),queries=queries
                    )
                    config=root/(cfg["case"]+".json")
                    config.write_text(json.dumps(cfg),encoding="utf-8")
                    for rep in range(args.repetitions):
                        order=("owner662","sealed676") if rep%2==0 else ("sealed676","owner662")
                        for arm in order:
                            exe=prior if arm=="owner662" else new
                            begin=time.perf_counter_ns()
                            result=subprocess.run([str(exe),__file__,"--worker",str(config),arm],
                                                  capture_output=True,text=True)
                            duration=time.perf_counter_ns()-begin
                            if result.returncode:
                                raise RuntimeError(f"{cfg['case']}/{arm}: {result.stderr} {result.stdout}")
                            receipt=json.loads(result.stdout)
                            receipt.update(iteration=rep,process_wall_ns=duration)
                            raw.append(receipt)
    groups=defaultdict(list)
    for row in raw:groups[(row["case"],row["arm"])].append(row)
    summaries=[]
    for case in sorted({k[0] for k in groups}):
        for metric in ("session_wall_ns","session_cpu_ns","open_wall_ns","open_cpu_ns","read_wall_ns","read_cpu_ns","rss_mib"):
            a=statistics.median(v[metric] for v in groups[(case,"owner662")] if v[metric] is not None)
            b=statistics.median(v[metric] for v in groups[(case,"sealed676")] if v[metric] is not None)
            summaries.append(dict(case=case,metric=metric,owner662=a,sealed676=b,
                                  sealed_over_owner=(b/a if a else None)))
    doc=dict(schema="j24c17-owner-vs-sealed-v1",source_head=os.getenv("EVIDENCE_SHA","UNBOUND"),
             owner_source="a66fd593a83cc4c71556d3d86d835c51abd20a96",
             repetitions=args.repetitions,raw=raw,summary=summaries,
             decision="RESEARCH_COMPARISON_NOT_RELEASE")
    Path(args.output).write_text(json.dumps(doc,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(dict(
        observations=len(raw),comparison="owner662 vs sealed676",
        q1_and_q6=[x for x in summaries if x["metric"]=="session_wall_ns"],
        decision=doc["decision"]),sort_keys=True))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--worker",nargs=2)
    p.add_argument("--owner-python")
    p.add_argument("--sealed-python")
    p.add_argument("--repetitions",type=int,default=4)
    p.add_argument("--output",default="j24c17-owner-sealed.json")
    a=p.parse_args()
    if a.worker:
        print(json.dumps(worker(json.loads(Path(a.worker[0]).read_text()),a.worker[1])))
    else:
        assert a.owner_python and a.sealed_python
        assert a.repetitions>=3
        run(a)


if __name__=="__main__":
    main()
