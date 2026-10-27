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

def evaluate(rows):
    if len(rows)!=len(CASES)*len(MODES)*3:
        return {"decision":"INSTRUMENT_INCOMPLETE","observations":len(rows)}
    report=[]
    for name in CASES:
        groups={}
        for mode in MODES:
            rr=[r for r in rows if r["name"]==name and r["mode"]==mode]
            assert sorted(r["rep"] for r in rr)==[0,1,2]
            assert len({r["sha"] for r in rr})==1
            assert len({r["selected"] for r in rr})==1
            assert len({r["full"]["archive_sha"] for r in rr})==1
            assert all(r["verified"] and r["full"]["verified"] for r in rr)
            groups[mode]=dict(selected=rr[0]["selected"],
                bytes=rr[0]["full"]["bytes"],archive_sha=rr[0]["full"]["archive_sha"],
                wall_ns=statistics.median(r["total_wall_ns"] for r in rr),
                cpu_ns=statistics.median(r["total_cpu_ns"] for r in rr),
                peak_kib=statistics.median(r["peak_vmhwm_kib"] for r in rr))
        assert groups["admitted"]["archive_sha"]==groups[groups["admitted"]["selected"]]["archive_sha"]
        best=min(groups["fixed"]["bytes"],groups["native"]["bytes"])
        report.append(dict(name=name,heldout=name in TEST,results=groups,
            gifted_best_bytes=best,regret=groups["admitted"]["bytes"]/best-1,
            rss_extra_kib=groups["admitted"]["peak_kib"]-groups["fixed"]["peak_kib"]))
    heldout=[x for x in report if x["heldout"]]
    add=lambda mode,field:sum(x["results"][mode][field] for x in heldout)
    fixed=add("fixed","bytes");selected=add("admitted","bytes")
    oracle=sum(x["gifted_best_bytes"] for x in heldout)
    gap=fixed-oracle
    capture=(fixed-selected)/gap if gap>0 else None
    wall_ratio=add("admitted","wall_ns")/add("fixed","wall_ns")
    cpu_ratio=add("admitted","cpu_ns")/add("fixed","cpu_ns")
    max_regret=max(x["regret"] for x in heldout)
    rss_extra=max(x["rss_extra_kib"] for x in heldout)
    byte_pass=gap>0 and capture>=.75 and max_regret<=.25
    cost_pass=wall_ratio<=1.5 and cpu_ratio<=1.5 and rss_extra<=10240
    decision=("PREFIX_PREDICTOR_FALSIFIED" if not byte_pass else
              "BYTE_HEADROOM_EXECUTION_DEBT" if not cost_pass else
              "BOUNDED_CHUNKER_ADMISSION_SEED")
    return dict(decision=decision,profile_summary=report,heldout_fixed_bytes=fixed,
        heldout_selected_bytes=selected,heldout_gifted_bytes=oracle,
        gifted_gap_bytes=gap,gifted_gap_capture=capture,max_byte_regret=max_regret,
        charged_wall_ratio=wall_ratio,charged_cpu_ratio=cpu_ratio,
        max_rss_extra_kib=rss_extra,byte_gate_pass=byte_pass,cost_gate_pass=cost_pass,
        independent_process_observations=len(rows))
def main(output):
    if HELPER is None:raise RuntimeError("INSTRUMENT_INVALID: optional native CDC absent")
    this=Path(__file__).resolve()
    native=this.parents[1]/"native"/"cmpct_cdc.c"
    helper=Path(codec.__file__).with_name("libcmpct_cdc.so")
    data=dict(schema="cmpct-o229-prefix-admission-v1",
        status="RESEARCH_ONLY_NO_PRODUCT_CREDIT",python=sys.version,
        source_sha256=h(this.read_bytes()),native_c_sha256=h(native.read_bytes()),
        helper_sha256=h(helper.read_bytes()),sample_bytes=SAMPLE,full_bytes=N,
        rows=[],summary={"decision":"INSTRUMENT_INCOMPLETE"})
    for name in CASES:
        for mode in MODES:
            for rep in range(3):
                args=[sys.executable,str(this),"--child",name,mode,str(rep)]
                proc=subprocess.run(args,capture_output=True,text=True,timeout=180)
                if proc.returncode:
                    Path(output).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
                    raise RuntimeError(f"INSTRUMENT_INVALID {name}/{mode}/{rep}: {proc.stderr[-1300:]}")
                row=json.loads(proc.stdout.strip().splitlines()[-1])
                data["rows"].append(row)
                Path(output).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
                print(name,mode,rep,row["full"]["bytes"],row["selected"],
                      file=sys.stderr,flush=True)
    data["summary"]=evaluate(data["rows"])
    Path(output).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data["summary"].items() if k!="profile_summary"},
                     sort_keys=True))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--child",nargs=3)
    p.add_argument("--output")
    a=p.parse_args()
    if a.child:
        print(json.dumps(child(a.child[0],a.child[1],int(a.child[2])),sort_keys=True))
    elif a.output:main(a.output)
    else:p.error("supply --child or --output")
