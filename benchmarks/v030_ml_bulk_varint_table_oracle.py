from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
ROOT=Path(__file__).resolve().parents[1]
ORDERS=(("control","bulk"),("bulk","control"))*2

def install_bulk():
    C=PRODUCT._BASE_IMPL.C; O=C.SHARED.G.O
    MAX_RUNS=1024
    def inverse(encoded:bytes,logical_size:int)->bytes:
        if not encoded.startswith(b"DGO1") or len(encoded)<6 or logical_size<0 or logical_size>O.MAX_OVERLAY_RECORD: raise RuntimeError("invalid Geometry overlay delimiter descriptor")
        delimiter=encoded[4]; count,pos=O._get_varint(encoded,5)
        if count<1 or count>O.MAX_DELIMITER_SEGMENTS: raise RuntimeError("Geometry overlay delimiter segment count")
        # DGO1 ML descriptors overwhelmingly encode sub-128 field lengths.  bytes.isascii()
        # proves the entire candidate table has no continuation bit in one C-level pass.
        end=pos+count; table=encoded[pos:end]
        if len(table)==count and table.isascii():
            lengths=list(table); pos=end; logical_members=sum(table); max_len=max(table,default=0)
        else:
            lengths=[]; logical_members=0; max_len=0
            for _ in range(count):
                length,pos=O._get_varint(encoded,pos)
                if length>O.MAX_OVERLAY_RECORD or logical_members+length>O.MAX_OVERLAY_RECORD: raise RuntimeError("Geometry overlay delimiter length budget")
                lengths.append(length); logical_members+=length; max_len=max(max_len,length)
        if logical_members+count-1!=logical_size: raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
        if count*max_len>O.MAX_DELIMITER_CELL_SCANS: raise RuntimeError("Geometry overlay delimiter cell-work budget")
        body=encoded[pos:]
        if len(body)!=logical_members: raise RuntimeError("Geometry overlay delimiter body-size mismatch")
        starts=[0]*count; output_cursor=0
        for index,length in enumerate(lengths):
            starts[index]=output_cursor; output_cursor+=length+(1 if index+1<count else 0)
        if output_cursor!=logical_size: raise RuntimeError("Geometry overlay delimiter output-shape mismatch")
        out=bytearray(logical_size)
        for index in range(count-1): out[starts[index]+lengths[index]]=delimiter
        runs=[]; first=0
        while first<count and len(runs)<=MAX_RUNS:
            length=lengths[first]; end=first+1
            while end<count and lengths[end]==length: end+=1
            runs.append((first,end,length)); first=end
        use=first==count and len(runs)<=MAX_RUNS
        body_cursor=0; active_cells=0
        for column in range(max_len):
            if use:
                for first,end,length in runs:
                    if length<=column: continue
                    run_len=end-first; source_end=body_cursor+run_len
                    if source_end>len(body): raise RuntimeError("short Geometry overlay delimiter body")
                    out[starts[first]+column:starts[end-1]+column+1:length+1]=body[body_cursor:source_end]
                    body_cursor=source_end; active_cells+=run_len
                continue
            index=0
            while index<count:
                while index<count and lengths[index]<=column: index+=1
                if index>=count: break
                length=lengths[index]; first=index; index+=1
                while index<count and lengths[index]==length: index+=1
                run_len=index-first; source_end=body_cursor+run_len
                if source_end>len(body): raise RuntimeError("short Geometry overlay delimiter body")
                out[starts[first]+column:starts[index-1]+column+1:length+1]=body[body_cursor:source_end]
                body_cursor=source_end; active_cells+=run_len
        if body_cursor!=len(body) or active_cells!=logical_members: raise RuntimeError("Geometry overlay delimiter trailing/body accounting mismatch")
        return bytes(out)
    C.SHARED.G.O.delimiter_inverse=inverse
    if getattr(C.POLICY.R.G04,"O",None) is not None: C.POLICY.R.G04.O.delimiter_inverse=inverse

def worker(arm,archive,dst):
    if arm=="bulk": install_bulk()
    start_cpu=time.process_time(); start=time.perf_counter(); PRODUCT.extract(archive,dst); wall=time.perf_counter()-start; cpu=time.process_time()-start_cpu
    return {'arm':arm,'wall_s':wall,'cpu_s':cpu,'tree_sha256':PRODUCT.treehash(dst)}
def fresh(arm,archive,dst):
    env=os.environ.copy(); env['PYTHONPATH']=str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',arm,'--archive',str(archive),'--dst',str(dst)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
    return json.loads([x for x in cp.stdout.splitlines() if x.strip()][-1])
def run(root):
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); src=PERF._build_corpora(root/'corpora')[("neutral_hostile_v1","09_ml_artifacts")]; archive=root/'ml.cmpct'; PRODUCT.build(src,archive); expected=PRODUCT.treehash(src); pairs=[]
    for rep,order in enumerate(ORDERS):
        rows={a:fresh(a,archive,root/f'r{rep}-{a}') for a in order}
        if any(r['tree_sha256']!=expected for r in rows.values()): raise RuntimeError('tree drift')
        c,f=rows['control'],rows['bulk']; pairs.append({'rep':rep,'order':list(order),'rows':rows,'wall_improvement_pct':(c['wall_s']-f['wall_s'])/c['wall_s']*100,'cpu_improvement_pct':(c['cpu_s']-f['cpu_s'])/c['cpu_s']*100})
    vals=sorted(p['wall_improvement_pct'] for p in pairs); med=(vals[1]+vals[2])/2
    return {'schema':'cmpct-v030-ml-bulk-varint-table-oracle-v1','release_credit':False,'source_sha':os.environ.get('EVIDENCE_HEAD'),'pairs':pairs,'median_wall_improvement_pct':med,'required_relative_improvement_for_median_1_10':8.038808244732154,'decision':'advance' if med>8.038808244732154 else 'kill-or-combine','claim_boundary':'research extraction oracle; exact tree required; multi-byte fallback preserved'}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--worker',choices=('control','bulk')); ap.add_argument('--archive',type=Path); ap.add_argument('--dst',type=Path); ap.add_argument('--root',type=Path,default=Path('benchmark-artifacts/v030-ml-bulk-varint')); args=ap.parse_args()
    if args.worker: print(json.dumps(worker(args.worker,args.archive,args.dst),separators=(',',':')))
    else:
        result=run(args.root); out=Path('benchmark-artifacts/v030-ml-bulk-varint.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
