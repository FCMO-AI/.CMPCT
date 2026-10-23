"""Held-out authentic CMPCT VZIP journal product cost O1; diagnostic ABBA, not release."""
from __future__ import annotations
import argparse, hashlib, json, os, resource, statistics, subprocess, sys, tempfile, time, zipfile, zlib
from pathlib import Path

BASE="369255f63aaa6a9c5c5c03eae2d57f8d1776662e"
PARENT="e4e382315311ae36ed7ca6878c5828d066f19f9b"
BLOB_A="663ef0922992b1fbb8f19e6eea88d55c10a56044"
BLOB_B="745b05ded92bbf84a681a4b159ac7a3c341858c5"
READER="c548a2ae4d650e928eb46ed1c2431423e49765b5"
FINAL=b"Stage VZIP candidate with repeated tokens and punctuation.\n"*700

def git(cwd,*cmd):
    return subprocess.check_output(["git",*cmd],cwd=cwd,text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def fingerprint(root):
    h=hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel=p.relative_to(root).as_posix().encode();b=p.read_bytes()
        h.update(len(rel).to_bytes(4,"little")+rel+len(b).to_bytes(8,"little")+b)
    return h.hexdigest()

def corpus(root,late,reused):
    root.mkdir()
    zpath=root/"10-container.zip"
    orig=zipfile._get_compressor
    def fixed(compression,level=None):
        if compression==zipfile.ZIP_DEFLATED:
            return zlib.compressobj(6,zlib.DEFLATED,-15,zlib.DEF_MEM_LEVEL,zlib.Z_FIXED)
        return orig(compression,level)
    with zipfile.ZipFile(zpath,"w") as zf:
        for i in range(192):
            b=hashlib.shake_256(f"cmpct-o1-zip-member-{i}".encode()).digest(384)
            zf.writestr(f"payload-{i:03d}.dat",b,compress_type=zipfile.ZIP_STORED)
            if i<reused:(root/f"00-loose-{i:03d}.bin").write_bytes(b)
        try:
            if late:zipfile._get_compressor=fixed
            zf.writestr("zz-final.txt",FINAL,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        finally:zipfile._get_compressor=orig
    with zipfile.ZipFile(zpath) as zf:
        assert len(zf.infolist())==193
        assert zf.read("zz-final.txt")==FINAL
    return dict(tree_sha256=fingerprint(root),zip_sha256=sha(zpath.read_bytes()),zip_bytes=zpath.stat().st_size,late=late,reused=reused)

def child(args):
    from cmpct.builder import Builder
    from cmpct.codec import _compressed_payload,deflate_level_for,S_BLOB,S_VZIP
    from cmpct.reader import CMPCT
    root=Path(args.source);out=Path(args.archive);zpath=root/"10-container.zip"
    with zipfile.ZipFile(zpath) as zf:
        stream=_compressed_payload(zpath,zf.infolist()[-1])
        level=deflate_level_for(FINAL,stream)
    assert (level is None)==args.late
    t=time.perf_counter_ns();cpu=time.process_time_ns()
    Builder(root,workers=1,reproducible=True).build(out)
    wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-cpu
    with CMPCT(out) as ar:
        assert ar.verify()
        assert ar.read("10-container.zip")==zpath.read_bytes()
        assert ar.by["10-container.zip"][6][0]==(S_BLOB if args.late else S_VZIP)
        if args.reused:assert ar.read("00-loose-000.bin")==(root/"00-loose-000.bin").read_bytes()
    print(json.dumps(dict(engine=args.engine,case=args.case,tree_sha256=fingerprint(root),create_wall_ns=wall,create_cpu_ns=cpu,archive_bytes=out.stat().st_size,archive_sha256=sha(out.read_bytes()),whole_process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,deflate_level=level)))

def driver(args):
    repo=Path(__file__).resolve().parent.parent;base=Path(args.base).resolve();dest=Path(args.output).resolve();dest.mkdir(parents=True,exist_ok=True)
    head=git(repo,"rev-parse","HEAD")
    subprocess.check_call(["git","merge-base","--is-ancestor",PARENT,head],cwd=repo)
    assert git(base,"rev-parse","HEAD")==BASE
    for src,expected in [(repo,BLOB_B),(base,BLOB_A)]:
        assert git(src,"hash-object","src/cmpct/builder.py")==expected
        assert git(src,"hash-object","src/cmpct/reader.py")==READER
    inputs={};obs=[]
    cases=[("success-reuse64",False,64),("reject-reuse0",True,0),("reject-reuse64",True,64)]
    with tempfile.TemporaryDirectory(prefix="cmpct-vzip-journal-o1-") as t:
        temporary=Path(t)
        for name,late,reused in cases:
            root=temporary/name;inputs[name]=corpus(root,late,reused)
            for repeat in range(args.repeats):
                four=[]
                for seq,engine in enumerate("ABBA"):
                    source=base if engine=="A" else repo
                    archive=temporary/f"archive-{name}-{repeat}-{seq}-{engine}.cmpct"
                    command=[sys.executable,str(Path(__file__).resolve()),"--child","--source",str(root),"--archive",str(archive),"--case",name,"--engine",engine,"--reused",str(reused)]
                    if late:command.append("--late")
                    env=dict(os.environ,PYTHONPATH=str(source/"src"),CMPCT_ENCODE_WORKERS="1")
                    result=subprocess.run(command,cwd=repo,env=env,text=True,capture_output=True,timeout=180)
                    if result.returncode:
                        print(result.stdout,result.stderr,file=sys.stderr)
                        raise RuntimeError(f"child failed {name}/{repeat}/{engine}: {result.returncode}")
                    row=json.loads(result.stdout.strip().splitlines()[-1])
                    assert row["tree_sha256"]==inputs[name]["tree_sha256"]
                    row.update(repeat=repeat,sequence=seq)
                    four.append(row);obs.append(row);archive.unlink()
                aa=[o for o in four if o["engine"]=="A"];bb=[o for o in four if o["engine"]=="B"]
                assert len(set(r["archive_sha256"] for r in aa))==1
                assert len(set(r["archive_sha256"] for r in bb))==1
                if late:
                    assert bb[0]["archive_bytes"]<=aa[0]["archive_bytes"]
                else:
                    assert bb[0]["archive_sha256"]==aa[0]["archive_sha256"]
    metrics={}
    for name,_,_ in cases:
        group=[r for r in obs if r["case"]==name]
        a=[r for r in group if r["engine"]=="A"];b=[r for r in group if r["engine"]=="B"]
        metrics[name]=dict(base_bytes=a[0]["archive_bytes"],candidate_bytes=b[0]["archive_bytes"],base_wall_median_ms=statistics.median(r["create_wall_ns"] for r in a)/1e6,candidate_wall_median_ms=statistics.median(r["create_wall_ns"] for r in b)/1e6,base_cpu_median_ms=statistics.median(r["create_cpu_ns"] for r in a)/1e6,candidate_cpu_median_ms=statistics.median(r["create_cpu_ns"] for r in b)/1e6,base_process_peak_rss_kib=max(r["whole_process_peak_rss_kib"] for r in a),candidate_process_peak_rss_kib=max(r["whole_process_peak_rss_kib"] for r in b))
    report=dict(tier="held-out genuine installed-source CMPCT Builder diagnostic, NOT official release gate",commit=head,base=BASE,source_git_blobs=dict(base_builder=BLOB_A,candidate_builder=BLOB_B,reader_both=READER),order="ABBA",repetitions=args.repeats,process_boundary="fresh Python process per observation, only Builder.build CPU/wall timed",corpora=inputs,results=metrics,observations=obs,limitations=["process peak RSS is whole child not incremental Builder","single hosted runner, synthetic ZIP-rich input and no statistical significance claim","not a substitute for official ABBA, native portability or release evidence"])
    (dest/"vzip-journal-o1.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--child",action="store_true")
    p.add_argument("--source");p.add_argument("--archive");p.add_argument("--case");p.add_argument("--engine")
    p.add_argument("--late",action="store_true");p.add_argument("--reused",type=int,default=0)
    p.add_argument("--base");p.add_argument("--output");p.add_argument("--repeats",type=int,default=3)
    a=p.parse_args()
    child(a) if a.child else driver(a)
