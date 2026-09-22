from __future__ import annotations

"""End-to-end research wrapper for sparse tabular admission + authenticated binary owner.

Diagnostic only. Nonaccepted workloads fall through to ordinary v0.30 bytes. Accepted CSV/JSONL
relations are removed from an otherwise ordinary v0.30 archive and represented once by the already-tested
TCOL binary owner. The receipt charges discovery, exact proof, owner encoding, archive assembly, full
reconstruction, corruption rejection, 4 KiB selective reads and fresh-process RSS.
"""

import argparse, hashlib, json, os, resource, shutil, subprocess, sys, time
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_admission_oracle_v2 as ADMIT
from benchmarks import v030_r4_tabular_owner_oracle as OWNER
from benchmarks import v030_r4_tabular_binary_owner_fast_oracle as FAST
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA='cmpct-v030-r4-tabular-integrated-archive-v1'
MAGIC=b'R4TI1\0\0\0'
GROUP_ROWS=8192
REQUEST=4096
MAX_COLD_STORED_AMP=8.0
MAX_DECODED_LOGICAL=8*1024*1024


def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def _rss_bytes()->int:return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024


def _discover(root:Path)->dict:
    total=obs=0;samples=[];t0=time.process_time();w0=time.perf_counter()
    for p in sorted(q for q in root.rglob('*') if q.is_file() and not q.is_symlink()):
        size=p.stat().st_size;total+=size;sample,used=ADMIT._sample(p);obs+=used
        if sample:sample.update({'path':p.relative_to(root).as_posix()});samples.append(sample)
    obs_cpu=time.process_time()-t0;obs_wall=time.perf_counter()-w0;groups={}
    for s in samples:groups.setdefault(s['fields'],[]).append(s)
    candidates=[]
    for fields,items in groups.items():
        csvs=[x for x in items if x['kind']=='csv'];jsons=[x for x in items if x['kind']=='jsonl']
        for c in csvs:
            for j in jsons:
                n=min(len(c['rows']),len(j['rows']),ADMIT.SAMPLE_ROWS)
                if n>=3 and c['rows'][:n]==j['rows'][:n]:candidates.append((c,j,n))
    accepted=[];proof_bytes=0;proof_cpu=proof_wall=0.0
    for c,j,n in candidates:
        cp=root.joinpath(*Path(c['path']).parts);jp=root.joinpath(*Path(j['path']).parts);proof_bytes+=c['size']+j['size']
        c0=time.process_time();w1=time.perf_counter();ok,reason=ADMIT._full_proof(cp,jp);proof_cpu+=time.process_time()-c0;proof_wall+=time.perf_counter()-w1
        if ok:accepted.append({'csv_path':c['path'],'jsonl_path':j['path'],'fields':list(c['fields']),'sample_rows_matched':n,'proof_bytes':c['size']+j['size'],'result':reason})
    return {'logical_bytes':total,'observation_bytes':obs,'observation_fraction':obs/max(1,total),'observation_cpu_s':obs_cpu,'observation_wall_s':obs_wall,'sampled_tabular_files':len(samples),'sample_matched_pairs':len(candidates),'proof_bytes':proof_bytes,'proof_fraction':proof_bytes/max(1,total),'proof_cpu_s':proof_cpu,'proof_wall_s':proof_wall,'accepted':accepted}


def _stat_record(p:Path)->dict:
    st=p.stat();return {'mode':st.st_mode & 0o7777,'mtime_ns':st.st_mtime_ns}


def _copy_without(root:Path,dst:Path,remove:set[str])->None:
    shutil.copytree(root,dst,symlinks=True,copy_function=shutil.copy2)
    for rel in remove:
        p=dst.joinpath(*Path(rel).parts)
        if p.exists() or p.is_symlink():p.unlink()


def _write_bundle(out:Path,base:Path,owner:bytes,manifest:dict)->dict:
    out.mkdir(parents=True,exist_ok=False);base_dst=out/'base.cmpct';shutil.copy2(base,base_dst);(out/'owner.tcol').write_bytes(owner)
    mraw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();(out/'manifest.json').write_bytes(mraw)
    auth=MAGIC+hashlib.sha256(mraw).digest()+hashlib.sha256(base_dst.read_bytes()).digest()+hashlib.sha256(owner).digest();(out/'auth.bin').write_bytes(auth)
    sizes={p.name:p.stat().st_size for p in out.iterdir() if p.is_file()}
    return {'component_bytes':sizes,'stored_bytes':sum(sizes.values()),'wrapper_bytes':sizes['manifest.json']+sizes['auth.bin']}


def _open_bundle(bundle:Path)->tuple[dict,Path,bytes]:
    mraw=(bundle/'manifest.json').read_bytes();base=bundle/'base.cmpct';owner=(bundle/'owner.tcol').read_bytes();auth=(bundle/'auth.bin').read_bytes()
    if len(auth)!=8+32*3 or auth[:8]!=MAGIC:raise ValueError('bad integrated auth header')
    if auth[8:40]!=hashlib.sha256(mraw).digest():raise ValueError('integrated manifest authentication failed')
    if auth[40:72]!=hashlib.sha256(base.read_bytes()).digest():raise ValueError('integrated base authentication failed')
    if auth[72:104]!=hashlib.sha256(owner).digest():raise ValueError('integrated owner authentication failed')
    return json.loads(mraw),base,owner


def _owner_raw(owner:bytes)->tuple[bytes,bytes]:
    fields,rows=FAST.B._full(owner);return OWNER._csv_bytes(fields,rows),OWNER._jsonl_bytes(rows)


def _strong_verify_bundle(bundle:Path)->dict:
    manifest,base,owner=_open_bundle(bundle);sv=dict(PRODUCT.strong_verify(base));csv_raw,json_raw=_owner_raw(owner);members=manifest['members']
    if _sha(csv_raw)!=members['csv']['sha256'] or _sha(json_raw)!=members['jsonl']['sha256']:raise ValueError('integrated reconstructed member hash mismatch')
    if not FAST.B._corruption(owner):raise ValueError('integrated owner corruption control failed')
    return {'base_strong_verify':sv,'owner_csv_bytes':len(csv_raw),'owner_jsonl_bytes':len(json_raw),'corruption_rejected':True}


def _extract_bundle(bundle:Path,out:Path)->None:
    manifest,base,owner=_open_bundle(bundle);PRODUCT.extract(base,out);csv_raw,json_raw=_owner_raw(owner)
    for kind,raw in (('csv',csv_raw),('jsonl',json_raw)):
        meta=manifest['members'][kind];p=out.joinpath(*Path(meta['path']).parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);os.chmod(p,int(meta['mode']));os.utime(p,ns=(int(meta['mtime_ns']),int(meta['mtime_ns'])))
    parent=manifest['pair_parent'];pp=out.joinpath(*Path(parent['path']).parts) if parent['path']!='.' else out;os.chmod(pp,int(parent['mode']));os.utime(pp,ns=(int(parent['mtime_ns']),int(parent['mtime_ns'])))


def _selective_bundle(bundle:Path,source:Path)->list[dict]:
    manifest,_,owner=_open_bundle(bundle);rows=[]
    for kind in ('csv','jsonl'):
        meta=manifest['members'][kind];raw=source.joinpath(*Path(meta['path']).parts).read_bytes();length=min(REQUEST,len(raw))
        for start in sorted({0,max(0,len(raw)//2-length//2),max(0,len(raw)-length)}):
            got,diag=FAST.B._read_range(owner,kind,start,length)
            if got!=raw[start:start+length]:raise RuntimeError('integrated owner range mismatch')
            touched=int(diag['payload_bytes_touched'])+int(diag['metadata_bytes_touched_cold'])
            rows.append({'member':meta['path'],'start':start,'length':length,**diag,'modeled_cold_stored_amplification':touched/max(1,length)})
    return rows


def _build_candidate(root:Path,out:Path,work:Path)->dict:
    d=_discover(root)
    if len(d['accepted'])!=1:
        stats=dict(PRODUCT.build(root,out));return {'mode':'ordinary-v030-fallback','discovery':d,'stored_bytes':out.stat().st_size,'product_stats':stats}
    rel=d['accepted'][0];cp=root.joinpath(*Path(rel['csv_path']).parts);jp=root.joinpath(*Path(rel['jsonl_path']).parts);csv_source=cp.read_bytes();json_source=jp.read_bytes()
    cf,cr=OWNER._parse_csv(csv_source);jf,jr=OWNER._parse_jsonl(json_source)
    if cf!=jf or not OWNER._semantic_equal(cf,cr,jr):raise RuntimeError('accepted relation failed owner semantic gate')
    csv_lengths=FAST._line_lengths(csv_source,len(jr),GROUP_ROWS,header=True);json_lengths=FAST._line_lengths(json_source,len(jr),GROUP_ROWS,header=False);owner,owner_stats=FAST._encode(cf,jr,GROUP_ROWS,csv_lengths,json_lengths)
    csv_raw,json_raw=_owner_raw(owner)
    if csv_raw!=csv_source or json_raw!=json_source:raise RuntimeError('integrated owner exact reconstruction failed')
    stripped=work/'stripped';_copy_without(root,stripped,{rel['csv_path'],rel['jsonl_path']});base=work/'base.cmpct';base_stats=dict(PRODUCT.build(stripped,base));parent=cp.parent
    manifest={'schema':'cmpct-v030-r4-tabular-integrated-bundle-v1','group_rows':GROUP_ROWS,'members':{'csv':{'path':rel['csv_path'],'sha256':_sha(csv_raw),**_stat_record(cp)},'jsonl':{'path':rel['jsonl_path'],'sha256':_sha(json_raw),**_stat_record(jp)}},'pair_parent':{'path':parent.relative_to(root).as_posix() if parent!=root else '.',**_stat_record(parent)},'base_sha256':_sha(base.read_bytes()),'owner_sha256':_sha(owner),'discovery':{k:v for k,v in d.items() if k!='accepted'}}
    bundle_stats=_write_bundle(out,base,owner,manifest)
    return {'mode':'integrated-tabular-owner','discovery':d,'stored_bytes':bundle_stats['stored_bytes'],'bundle':bundle_stats,'owner_stats':owner_stats,'base_stats':base_stats}


def _worker(mode:str,root:Path,out:Path,work:Path,result:Path)->None:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);t0=time.process_time();w0=time.perf_counter()
    if mode=='baseline':stats=dict(PRODUCT.build(root,out));payload={'mode':'ordinary-v030','stored_bytes':out.stat().st_size,'product_stats':stats}
    else:payload=_build_candidate(root,out,work)
    payload.update({'create_cpu_s':time.process_time()-t0,'create_wall_s':time.perf_counter()-w0,'peak_rss_bytes':_rss_bytes()});result.write_text(json.dumps(payload,sort_keys=True)+'\n')


def _run_worker(script:Path,mode:str,root:Path,out:Path,work:Path,result:Path)->dict:
    subprocess.run([sys.executable,str(script),'--worker',mode,'--source',str(root),'--archive',str(out),'--work-root',str(work),'--worker-result',str(result)],check=True);return json.loads(result.read_text())


def _timed_verify_extract(verify_fn,extract_fn,out:Path)->dict:
    out.parent.mkdir(parents=True,exist_ok=True);shutil.rmtree(out,ignore_errors=True);c=time.process_time();w=time.perf_counter();sv=verify_fn();vc=time.process_time()-c;vw=time.perf_counter()-w;c=time.process_time();w=time.perf_counter();extract_fn(out);ec=time.process_time()-c;ew=time.perf_counter()-w
    return {'strong_verify':sv,'verify_cpu_s':vc,'verify_wall_s':vw,'extract_cpu_s':ec,'extract_wall_s':ew}


def _verify_baseline(archive:Path,work:Path)->dict:
    m=_timed_verify_extract(lambda:dict(PRODUCT.strong_verify(archive)),lambda out:PRODUCT.extract(archive,out),work/'extract');m['tree_sha256']=PRODUCT.treehash(work/'extract');return m


def _verify_candidate(candidate:Path,source:Path,row:dict,work:Path)->dict:
    if row['mode']=='ordinary-v030-fallback':
        m=_timed_verify_extract(lambda:dict(PRODUCT.strong_verify(candidate)),lambda out:PRODUCT.extract(candidate,out),work/'extract');m.update({'tree_sha256':PRODUCT.treehash(work/'extract'),'selective_owner_requests':[],'max_modeled_cold_stored_amplification':None,'max_decoded_logical_bytes':None});return m
    m=_timed_verify_extract(lambda:_strong_verify_bundle(candidate),lambda out:_extract_bundle(candidate,out),work/'extract');requests=_selective_bundle(candidate,source);m.update({'tree_sha256':PRODUCT.treehash(work/'extract'),'selective_owner_requests':requests,'max_modeled_cold_stored_amplification':max(r['modeled_cold_stored_amplification'] for r in requests),'max_decoded_logical_bytes':max(int(r['decoded_member_segment_bytes']) for r in requests)});return m


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);script=Path(__file__).resolve();accepted=V029._accepted_v029_rows();neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_int_neutral');hostile=V029._load(V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_int_hostile');repair=V029._load(V029.REPAIR_PATH,'cmpct_v030_int_repair');repair.install_generation_hooks(neutral);rows=[]
    for suite,builder,root in (('neutral_hostile_v1',neutral,work/'neutral'),('resemblance_hostile_v1',hostile,work/'resemblance')):
        builder.build(root)
        if suite=='neutral_hostile_v1':repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            rd=work/'rows'/suite/source.name;rd.mkdir(parents=True);base=rd/'baseline.cmpct';cand=rd/'candidate';br=_run_worker(script,'baseline',source,base,rd/'bw',rd/'baseline.json');cr=_run_worker(script,'candidate',source,cand,rd/'cw',rd/'candidate.json');expected=PRODUCT.treehash(source);bv=_verify_baseline(base,rd/'baseline-verify');cv=_verify_candidate(cand,source,cr,rd/'verify')
            if bv['tree_sha256']!=expected or cv['tree_sha256']!=expected:raise RuntimeError(f'tree mismatch {suite}/{source.name}')
            if cr['mode']=='ordinary-v030-fallback' and cr['stored_bytes']!=br['stored_bytes']:raise RuntimeError(f'fallback bytes changed {suite}/{source.name}')
            row={'suite':suite,'name':source.name,'logical_bytes':sum(p.stat().st_size for p in source.rglob('*') if p.is_file() and not p.is_symlink()),'tree_sha256':expected,'accepted_v029_bytes':int(accepted[(suite,source.name)]['accepted_v029_bytes']),'baseline':br,'baseline_verify':bv,'candidate':cr,'candidate_verify':cv,'saving_bytes':br['stored_bytes']-cr['stored_bytes'],'create_cpu_delta_s':cr['create_cpu_s']-br['create_cpu_s'],'create_wall_delta_s':cr['create_wall_s']-br['create_wall_s'],'peak_rss_delta_bytes':cr['peak_rss_bytes']-br['peak_rss_bytes']};rows.append(row);print(json.dumps({k:row[k] for k in ('suite','name','saving_bytes','create_cpu_delta_s','peak_rss_delta_bytes')},sort_keys=True),flush=True)
    base=sum(r['baseline']['stored_bytes'] for r in rows);cand=sum(r['candidate']['stored_bytes'] for r in rows);accepted_rows=[r for r in rows if r['candidate']['mode']=='integrated-tabular-owner'];reg=[r for r in rows if r['saving_bytes']<0];amps=[r['candidate_verify']['max_modeled_cold_stored_amplification'] or 0 for r in rows];decoded=[r['candidate_verify']['max_decoded_logical_bytes'] or 0 for r in rows];max_amp=max(amps);max_dec=max(decoded);analytics=next(r for r in rows if r['suite']=='neutral_hostile_v1' and r['name']=='04_analytics_and_database')
    supported=len(accepted_rows)==1 and accepted_rows[0]['name']=='04_analytics_and_database' and not reg and cand<base and analytics['candidate']['stored_bytes']<analytics['accepted_v029_bytes'] and max_amp<=MAX_COLD_STORED_AMP and max_dec<=MAX_DECODED_LOGICAL
    return {'schema':SCHEMA,'source_commit':os.environ.get('EVIDENCE_HEAD'),'group_rows':GROUP_ROWS,'rows':rows,'totals':{'baseline_bytes':base,'candidate_bytes':cand,'saving_bytes':base-cand,'baseline_create_cpu_s':sum(r['baseline']['create_cpu_s'] for r in rows),'candidate_create_cpu_s':sum(r['candidate']['create_cpu_s'] for r in rows),'create_cpu_delta_s':sum(r['create_cpu_delta_s'] for r in rows),'baseline_extract_cpu_s':sum(r['baseline_verify']['extract_cpu_s'] for r in rows),'candidate_extract_cpu_s':sum(r['candidate_verify']['extract_cpu_s'] for r in rows),'max_modeled_cold_stored_amplification':max_amp,'max_decoded_logical_bytes':max_dec},'hypothesis':{'exactly_one_accepted_relation':len(accepted_rows)==1 and accepted_rows[0]['name']=='04_analytics_and_database','zero_nonanalytics_byte_regressions':all(r['saving_bytes']==0 for r in rows if r['name']!='04_analytics_and_database'),'positive_total_authenticated_byte_saving':cand<base,'analytics_beats_accepted_v029':analytics['candidate']['stored_bytes']<analytics['accepted_v029_bytes'],'cold_owner_locality_within_8x':max_amp<=MAX_COLD_STORED_AMP,'decoded_owner_work_within_8mib':max_dec<=MAX_DECODED_LOGICAL,'supported_for_productization_design':supported},'contract':{'diagnostic_only':True,'release_credit':False,'production_format_changed':False,'production_selector_changed':False,'nonaccepted_fallback_is_ordinary_v030_bytes':True,'discovery_and_exact_proof_charged':True,'fresh_process_builds':True,'peak_rss_measured':True,'authenticated_component_wrapper':True,'full_reconstruction_verified':True,'owner_corruption_rejected':True,'selective_owner_amplification_is_modeled_from_touched_segments':True},'next_if_supported':'design the smallest shipping-compatible owner primitive and rerun full product gates before any promotion','next_if_falsified':'preserve the negative; do not tune admission thresholds on Genesis; return to a different R4 or physical-representation mechanism'}


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-integrated-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-integrated.json'));p.add_argument('--worker',choices=['baseline','candidate']);p.add_argument('--source',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--worker-result',type=Path);a=p.parse_args()
    if a.worker:_worker(a.worker,a.source,a.archive,a.work_root,a.worker_result);return
    r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');analytics=next(x for x in r['rows'] if x['name']=='04_analytics_and_database');print(json.dumps({'totals':r['totals'],'hypothesis':r['hypothesis'],'analytics':{'baseline_bytes':analytics['baseline']['stored_bytes'],'candidate_bytes':analytics['candidate']['stored_bytes'],'accepted_v029_bytes':analytics['accepted_v029_bytes'],'saving_bytes':analytics['saving_bytes'],'create_cpu_delta_s':analytics['create_cpu_delta_s'],'peak_rss_delta_bytes':analytics['peak_rss_delta_bytes'],'candidate_verify':{k:analytics['candidate_verify'][k] for k in ('verify_cpu_s','extract_cpu_s','max_modeled_cold_stored_amplification','max_decoded_logical_bytes')}}},indent=2))

if __name__=='__main__':main()
