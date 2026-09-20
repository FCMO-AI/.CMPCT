from __future__ import annotations
"""Diagnostic A/B for moving the canonical r25 candidate+verification lifetime behind a process boundary."""
import argparse, hashlib, importlib.util, json, multiprocessing as mp, os, shutil, subprocess, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PAGE_KIB=os.sysconf("SC_PAGE_SIZE")//1024

def _rss(pid):
    try:return int(Path(f"/proc/{pid}/statm").read_text().split()[1])*PAGE_KIB
    except (FileNotFoundError,ProcessLookupError,PermissionError,ValueError,IndexError):return None

def _kids(pid):
    try:t=Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
    except (FileNotFoundError,ProcessLookupError,PermissionError):return []
    return [int(x) for x in t.split() if x]

def _tree(root):
    seen=set(); stack=[root]; total=count=0
    while stack:
        p=stack.pop()
        if p in seen:continue
        seen.add(p); r=_rss(p)
        if r is None:continue
        total+=r; count+=1; stack.extend(_kids(p))
    return total,count

def _sample(stop,rows):
    p=os.getpid()
    while not stop.is_set():
        r=_rss(p) or 0; tr,n=_tree(p); rows.append((r,tr,n)); stop.wait(.005)

def _canonical_r25(staged,out):
    """Run the exact canonical r25 owner, not the stale public compatibility alias.

    release_product.C is the canonical-final module.  Its public `_r25_build` name is overwritten by the
    compatibility bridge in release_product, so calling that alias reaches the research/base builder and emits
    CMPNX.  `C._r25_build_threaded_control` is the preserved canonical-final candidate builder: it emits the same
    final-form r25 bytes as the shipping path, differing only in the already-independent PrefixGraph scheduling
    arm.  Logs/ML are PrefixGraph-ineligible, so this is byte/semantic equivalent for the workloads measured here.
    """
    from experiments import entropygraph_v030_release_product as RP
    C=RP.C
    t=time.perf_counter(); stats=dict(C._r25_build_threaded_control(Path(staged),Path(out))); build=time.perf_counter()-t
    revision,profile=C._profile_for_archive(Path(out))
    if revision != C.REVISION:
        raise RuntimeError(f"canonical seam emitted non-r25 profile: revision={revision!r} profile={profile!r}")
    t=time.perf_counter(); verified=dict(C.strong_verify(Path(out))); verify=time.perf_counter()-t
    if not verified.get("ok"):raise RuntimeError(f"verify failed: {verified!r}")
    return stats,verified,build,verify,profile

def _child_r25(staged,out,conn):
    try:
        stats,verified,build,verify,profile=_canonical_r25(staged,out)
        conn.send({"ok":True,"stats":stats,"verified":verified,"build_s":build,"verify_s":verify,"profile":profile})
    except BaseException as e:conn.send({"ok":False,"error":repr(e)})
    finally:conn.close()

def _arm(source,out,isolated):
    from experiments import entropygraph_v030_release_product as RP
    t0=time.perf_counter(); rows=[]; stop=threading.Event(); th=threading.Thread(target=_sample,args=(stop,rows),daemon=True); th.start(); temp=out.parent/(out.name+".profile"); shutil.rmtree(temp,ignore_errors=True)
    try:
        prepared=RP.C._prepare_profile_tree(source,temp)
        if isolated:
            ctx=mp.get_context("spawn"); parent,child=ctx.Pipe(duplex=False); proc=ctx.Process(target=_child_r25,args=(str(temp),str(out),child)); proc.start(); child.close(); payload=parent.recv(); proc.join()
            if proc.exitcode!=0 or not payload.get("ok"):raise RuntimeError(f"child exit={proc.exitcode}: {payload}")
            stats=payload["stats"]; verified=payload["verified"]; build=payload["build_s"]; verify=payload["verify_s"]; profile=payload["profile"]
        else:
            stats,verified,build,verify,profile=_canonical_r25(temp,out)
        return {"arm":"child" if isolated else "parent","wall_s":time.perf_counter()-t0,"build_s":build,"verify_s":verify,"archive_bytes":out.stat().st_size,"archive_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"tree_sha256":verified.get("tree_sha256"),"selected":stats.get("selected"),"profile":profile,"prepared_entries":prepared.get("entries"),"peak_parent_rss_kib":max((x[0] for x in rows),default=0),"peak_tree_rss_kib":max((x[1] for x in rows),default=0),"max_processes":max((x[2] for x in rows),default=1)}
    finally:stop.set(); th.join(timeout=2); shutil.rmtree(temp,ignore_errors=True)

def _suite(source,outroot):
    outroot.mkdir(parents=True,exist_ok=True); c=_arm(source,outroot/"control.cmpct",False); x=_arm(source,outroot/"candidate.cmpct",True); exact=c["archive_bytes"]==x["archive_bytes"] and c["archive_sha256"]==x["archive_sha256"] and c["tree_sha256"]==x["tree_sha256"] and c["profile"]==x["profile"]
    if not exact:raise RuntimeError("isolation changed exact bytes/tree/profile")
    return {"control":c,"candidate":x,"exact_identity":exact,"parent_rss_ratio":x["peak_parent_rss_kib"]/max(1,c["peak_parent_rss_kib"]),"tree_rss_ratio":x["peak_tree_rss_kib"]/max(1,c["peak_tree_rss_kib"]),"wall_ratio":x["wall_s"]/max(1e-9,c["wall_s"])}

def _invoke(source,outroot):
    p=subprocess.run([sys.executable,__file__,"--child","--source",str(source),"--out-root",str(outroot)],cwd=ROOT,env={**os.environ,"PYTHONPATH":str(ROOT)},capture_output=True,text=True)
    if p.returncode:raise RuntimeError(f"suite rc={p.returncode}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return json.loads([x for x in p.stdout.splitlines() if x.strip()][-1])

def _perf():
    path=ROOT/"benchmarks"/"v030_release_performance.py"; spec=importlib.util.spec_from_file_location("cmpct_perf",path)
    if spec is None or spec.loader is None:raise RuntimeError("cannot load corpus generator")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    a=argparse.ArgumentParser(); a.add_argument("--child",action="store_true"); a.add_argument("--source",type=Path); a.add_argument("--out-root",type=Path); a.add_argument("--work-root",type=Path); a.add_argument("--output",type=Path); z=a.parse_args()
    if z.child:print(json.dumps(_suite(z.source,z.out_root),separators=(",",":")));return
    P=_perf(); shutil.rmtree(z.work_root,ignore_errors=True); z.work_root.mkdir(parents=True); corp=P._build_corpora(z.work_root/"corpus"); rows={}
    for suite,name in (("neutral_hostile_v1","05_logs_and_telemetry"),("neutral_hostile_v1","09_ml_artifacts")):rows[name]=_invoke(corp[(suite,name)],z.work_root/(name+"-arms"))
    result={"schema":"cmpct-v030-r25-child-build-verify-oracle-v2","release_credit":False,"seam":"canonical-final preserved r25 builder + canonical strong_verify","rows":rows,"claim_boundary":"diagnostic exact-final-form-r25 A/B; parent and whole-tree RSS charged; no product/release semantics changed"}; z.output.parent.mkdir(parents=True,exist_ok=True); z.output.write_text(json.dumps(result,indent=2)+"\n"); print(json.dumps(result,indent=2))
if __name__=="__main__":main()
