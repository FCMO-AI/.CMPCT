from __future__ import annotations
"""Final-form falsifier for one-pass hidden-ZIP observation/build planning.

Compares the proven information-yield + level-6-first arm with a fused filesystem walk that
collects metadata and ZIP descriptors once, decides admission globally, then consumes the cached
plan. Reader grammar and admission law are unchanged. Research-only.
"""
import argparse, hashlib, json, multiprocessing as mp, os, resource, shutil, stat, statistics, time, zipfile, zlib
from collections import defaultdict
from pathlib import Path
from benchmarks import v030_r4_content_zip_information_yield_gate as YIELD
from benchmarks import v030_release_generalization as GENERAL
from experiments import v030_r4_content_zip_builder as CZ
from experiments.v030_r4_zip_preflight import hidden_zip_preflight
from cmpct import builder as B, codec

LEVEL6_FIRST=(6,0,1,2,3,4,5,7,8,9)
EXPLICIT={'.zip','.whl'}
REPS=3

def _search(raw:bytes,target:bytes):
    for level in LEVEL6_FIRST:
        co=zlib.compressobj(level,zlib.DEFLATED,-15)
        if co.compress(raw)+co.flush()==target:return level
    return None

class FusedInformationYieldBuilder(CZ.ContentZipBuilder):
    """One filesystem walk: metadata + bounded ZIP observation -> immutable regular-file plan -> encode."""
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.information_yield_stats={}

    def scan(self):
        plan=[]; descriptors={}; valid={}; rejects=defaultdict(int); obs_cpu=time.process_time(); files=0
        def walk(absdir:str,prefix:str=''):
            nonlocal files
            with os.scandir(absdir) as it: entries=sorted(it,key=lambda e:e.name)
            for e in entries:
                rel=f'{prefix}/{e.name}' if prefix else e.name
                st=e.stat(follow_symlinks=False); mode=stat.S_IMODE(st.st_mode); self._capture_fs_meta(e.path,rel,st)
                if stat.S_ISLNK(st.st_mode):
                    raw=os.readlink(e.path).encode(); ref=self.add_content(raw,'.symlink'); self.files.append([rel,B.K_SYMLINK,mode,st.st_mtime_ns,len(raw),B.sha(raw),[B.S_BLOB,ref]]); continue
                if stat.S_ISDIR(st.st_mode):
                    self.files.append([rel,B.K_DIR,mode,st.st_mtime_ns,0,b'',None]); walk(e.path,rel); continue
                if not stat.S_ISREG(st.st_mode): continue
                if st.st_nlink>1:
                    ik=(st.st_dev,st.st_ino)
                    if ik in self.inode_first:
                        self.files.append([rel,B.K_HARDLINK,mode,st.st_mtime_ns,st.st_size,None,[self.inode_first[ik]]]); continue
                    self.inode_first[ik]=rel
                files+=1; self.content_zip_observed_files+=1; self.content_zip_sniffed_bytes+=min(4096,st.st_size)
                p=Path(e.path); rp=p.resolve(); ext=p.suffix.lower(); ok=False
                try:
                    if ext not in EXPLICIT:
                        pf=hidden_zip_preflight(p)
                        if not pf.eligible:
                            rejects[pf.reason]+=1; valid[rp]=False; plan.append((p,rel,st,mode,ext)); continue
                    with zipfile.ZipFile(p) as z:
                        infos=[i for i in z.infolist() if not i.is_dir()]
                        if infos and all(i.compress_type in CZ.SUPPORTED for i in infos):
                            descriptors[rp]={(int(i.CRC),int(i.file_size),int(i.compress_type),int(i.compress_size)) for i in infos if i.file_size>0}; ok=True
                except Exception: ok=False
                valid[rp]=ok
                if ok:
                    self.content_zip_valid+=1
                    if ext not in EXPLICIT:self.content_zip_hidden+=1
                plan.append((p,rel,st,mode,ext))
        walk(os.fspath(self.root))
        owners=defaultdict(set)
        for p,ds in descriptors.items():
            for d in ds: owners[d].add(p)
        reuse={p:sum(d[3] for d in ds if len(owners[d])>=2) for p,ds in descriptors.items()}
        hidden={p for p,ok in valid.items() if ok and p.suffix.lower() not in EXPLICIT}
        admitted={p for p in hidden if reuse.get(p,0)>=YIELD.MIN_EXPECTED_REUSE}
        self.information_yield_stats={'files_observed':files,'hidden_valid_zip_files':len(hidden),'admitted_hidden_zip_files':len(admitted),'predicted_reusable_compressed_bytes_by_path':{str(p.relative_to(self.root.resolve())):v for p,v in reuse.items()},'control_cost_bound_bytes':YIELD.CONTROL_COST_BOUND,'safety_multiplier':YIELD.SAFETY_MULTIPLIER,'min_expected_reuse_bytes':YIELD.MIN_EXPECTED_REUSE,'preflight_rejects':dict(rejects),'observation_cpu_s':time.process_time()-obs_cpu,'filesystem_walks':1}
        deferred=[]
        for p,rel,st,mode,ext in plan:
            rp=p.resolve(); virtual=bool(valid.get(rp,False)) and (ext in EXPLICIT or rp in admitted)
            if virtual: deferred.append((p,rel,st,mode)); continue
            if ext in EXPLICIT and not valid.get(rp,False): self.content_zip_parse_fallbacks+=1
            sparse=B._sparse_data_extents(p,st.st_size)
            if sparse is not None:
                ex=[]
                for off,data in sparse:
                    refs=[self.add_content(data[i:i+B.CHUNK],ext) for i in range(0,len(data),B.CHUNK)]; ex.append([off,len(data),refs])
                self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,st.st_size,B._hash_sparse(st.st_size,sparse),[B.S_SPARSE,ex]]); continue
            raw=p.read_bytes()
            if len(raw)>4*B.CHUNK and ext!='.wav':
                parts=B.cdc_chunks(raw); entries=[[len(part),self.add_content(part,ext)] for part in parts]; storage=[B.S_CDC,entries]
            else: storage=[B.S_BLOB,self.add_content(raw,ext)]
            self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,len(raw),B.sha(raw),storage])
        if len(deferred)>=8:
            buf=bytearray(); packed=[]
            for p,rel,st,mode in deferred:
                raw=p.read_bytes(); off=len(buf); buf+=raw; packed.append((rel,st,mode,off,len(raw),B.sha(raw)))
            ph=self.add_content(bytes(buf),'.cmpct-container-pack')
            for rel,st,mode,off,ln,rh in packed:self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,ln,rh,[B.S_PACK,ph,off,ln]])
        else:
            for p,rel,st,mode in deferred:
                try: recipe=B.make_vzip_recipe(p,self.add_content)
                except (zipfile.BadZipFile,EOFError,OSError,ValueError): recipe=None; self.content_zip_parse_fallbacks+=1
                if recipe is None: raw=p.read_bytes(); storage=[B.S_BLOB,self.add_content(raw,p.suffix.lower())]
                else: rid=len(self.recipes); self.recipes.append(recipe); storage=[B.S_VZIP,rid]
                self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,st.st_size,B.sha(p.read_bytes()),storage])
        if self.reproducible:
            for row in self.files: row[3]=self.reproducible_epoch_ns
        self.files.sort(key=lambda x:x[0])

    def build(self,out:Path):
        s=dict(super(CZ.ContentZipBuilder,self).build(out)); s['information_yield_gate']=dict(self.information_yield_stats); return s

def _child(arm:str,source:str,work:str,q):
    source=Path(source); work=Path(work); arc=work/f'{arm}.cmpct'; out=work/f'{arm}-out'; work.mkdir(parents=True,exist_ok=True)
    original=codec.deflate_level_for; codec.deflate_level_for=_search
    try:
        cls=YIELD.InformationYieldBuilder if arm.startswith('current') else FusedInformationYieldBuilder
        c=time.process_time(); w=time.perf_counter(); stats=cls(source).build(arc); c=time.process_time()-c; w=time.perf_counter()-w
        verify=YIELD._verify(arc,source,out)
    finally: codec.deflate_level_for=original
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    q.put({'arm':arm,'archive_bytes':arc.stat().st_size,'archive_sha256':hashlib.sha256(arc.read_bytes()).hexdigest(),'create_cpu_s':c,'create_wall_s':w,'peak_rss_kib':rss,'tree_sha256':verify['tree_sha256'],'vzip_file_count':verify['vzip_file_count'],'range_checks':len(verify['range_checks']),'admitted_hidden_zip_files':stats['information_yield_gate']['admitted_hidden_zip_files']})

def run(work:Path):
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    neutral=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_fused_n'); repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,'cmpct_v030_fused_r'); repair.install_generation_hooks(neutral)
    root=work/'neutral'; neutral.build(root); repair.normalize_root(root); office=root/'02_office_workspace'; rows=[]
    ctx=mp.get_context('spawn')
    for i in range(REPS):
        for base in ('current','fused'):
            arm=f'{base}-{i}'; q=ctx.Queue(); p=ctx.Process(target=_child,args=(arm,str(office),str(work/'runs'/arm),q)); p.start(); p.join()
            if p.exitcode!=0: raise RuntimeError(f'{arm} child failed: {p.exitcode}')
            row=q.get(); rows.append(row); print(json.dumps(row),flush=True)
    cur=[r for r in rows if r['arm'].startswith('current')]; fused=[r for r in rows if r['arm'].startswith('fused')]
    def ident(rs,k):
        v={r[k] for r in rs}
        if len(v)!=1: raise RuntimeError(f'nondeterministic {k}: {v}')
        return next(iter(v))
    if len({r['tree_sha256'] for r in rows})!=1 or len({r['admitted_hidden_zip_files'] for r in rows})!=1: raise RuntimeError('semantic/admission drift')
    summary={'current_archive_bytes':ident(cur,'archive_bytes'),'fused_archive_bytes':ident(fused,'archive_bytes'),'current_archive_sha256':ident(cur,'archive_sha256'),'fused_archive_sha256':ident(fused,'archive_sha256'),'current_cpu_median_s':statistics.median(r['create_cpu_s'] for r in cur),'fused_cpu_median_s':statistics.median(r['create_cpu_s'] for r in fused),'current_wall_median_s':statistics.median(r['create_wall_s'] for r in cur),'fused_wall_median_s':statistics.median(r['create_wall_s'] for r in fused),'current_rss_median_kib':statistics.median(r['peak_rss_kib'] for r in cur),'fused_rss_median_kib':statistics.median(r['peak_rss_kib'] for r in fused)}
    summary['archive_delta_bytes']=summary['fused_archive_bytes']-summary['current_archive_bytes']; summary['cpu_ratio']=summary['fused_cpu_median_s']/summary['current_cpu_median_s']; summary['wall_ratio']=summary['fused_wall_median_s']/summary['current_wall_median_s']; summary['rss_ratio']=summary['fused_rss_median_kib']/summary['current_rss_median_kib']
    original=codec.deflate_level_for; codec.deflate_level_for=_search
    try: hostiles=YIELD._hostiles(work/'hostiles')
    finally: codec.deflate_level_for=original
    supported=summary['archive_delta_bytes']<=0 and summary['cpu_ratio']<1.0 and summary['wall_ratio']<1.0 and summary['rss_ratio']<=1.10 and all(v['passes'] for v in hostiles.values())
    return {'schema':'cmpct-v030-content-zip-fused-plan-cache-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'level_order':list(LEVEL6_FIRST),'rows':rows,'summary':summary,'hostiles':hostiles,'hypothesis':{'supported_for_full_matrix_next_rung':supported},'contract':{'diagnostic_only':True,'shipping_code_changed':False,'format_changed':False,'reader_changed':False,'admission_policy_changed':False,'one_filesystem_walk_in_fused_arm':True,'fresh_process_per_measurement':True,'full_tree_verified':True,'range_reads_verified':True},'decision':'If supported, run unchanged 15-workload generalization plus S_PACK/selective locality before any shipping patch; otherwise preserve the negative and isolate the exported cost.'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/fused-plan-cache-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/fused-plan-cache.json')); a=p.parse_args(); d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+'\n'); print(json.dumps(d['summary'],indent=2))
if __name__=='__main__': main()
