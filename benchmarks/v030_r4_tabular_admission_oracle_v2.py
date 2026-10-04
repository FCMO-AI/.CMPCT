from __future__ import annotations

"""Adaptive sparse opportunity gate for reversible tabular co-lifting.

V1 found exactly the Analytics CSV<->JSONL relation and zero false positives across the frozen 15-workload
matrix, but its fixed 64 KiB read per file consumed 23.2% of corpus bytes.  This v2 keeps the same semantic gate
and thresholds while making observation incremental: read 4 KiB at a time, stop once 16 complete sample rows can
be classified, and never exceed 16 KiB for a non-candidate.  Full proof still occurs only after schema + sample-row
agreement.  No extension, path or workload identity participates in admission.
"""

import argparse, csv, io, json, os, shutil, time
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_owner_oracle as OWNER

CHUNK=4096
MAX_SNIFF=16384
SAMPLE_ROWS=16


def _classify(raw:bytes, size:int)->dict|None:
    try:text=raw.decode('utf-8')
    except UnicodeDecodeError:return None
    if not text:return None
    complete=text if len(raw)>=size or raw.endswith(b'\n') else text[:text.rfind('\n')+1] if '\n' in text else ''
    if not complete:return None
    lines=complete.splitlines()
    if len(lines)>=3:
        objs=[]
        try:
            for line in lines[:SAMPLE_ROWS]:
                if not line:continue
                obj=json.loads(line)
                if not isinstance(obj,dict):raise ValueError
                objs.append(obj)
            if len(objs)>=3:
                fields=tuple(objs[0].keys())
                if len(fields)>=3 and all(tuple(o.keys())==fields for o in objs):
                    rows=[tuple(str(o[f]) if not isinstance(o[f],bool) else ('True' if o[f] else 'False') for f in fields) for o in objs]
                    return {'kind':'jsonl','fields':fields,'rows':rows,'size':size}
        except Exception:pass
    try:
        parsed=list(csv.reader(io.StringIO(complete,newline='')))
        if len(parsed)>=4 and len(parsed[0])>=3:
            fields=tuple(parsed[0]);body=parsed[1:1+SAMPLE_ROWS]
            if body and all(len(r)==len(fields) for r in body):
                return {'kind':'csv','fields':fields,'rows':[tuple(r) for r in body],'size':size}
    except Exception:pass
    return None


def _sample(path:Path)->tuple[dict|None,int]:
    size=path.stat().st_size;limit=min(size,MAX_SNIFF);raw=bytearray();consumed=0
    with path.open('rb') as f:
        while consumed<limit:
            part=f.read(min(CHUNK,limit-consumed))
            if not part:break
            raw.extend(part);consumed+=len(part)
            got=_classify(bytes(raw),size)
            if got is not None:
                # Require enough complete rows for the promised sample when the file is large enough.
                if len(got['rows'])>=min(SAMPLE_ROWS,3 if size<=consumed else SAMPLE_ROWS):
                    got['sniff_bytes']=consumed
                    return got,consumed
    got=_classify(bytes(raw),size)
    if got is not None:
        got['sniff_bytes']=consumed
    return got,consumed


def _full_proof(csv_path:Path,json_path:Path)->tuple[bool,str]:
    try:
        raw_csv=csv_path.read_bytes();raw_json=json_path.read_bytes()
        cf,cr=OWNER._parse_csv(raw_csv);jf,jr=OWNER._parse_jsonl(raw_json)
        if cf!=jf:return False,'schema_drift'
        if not OWNER._semantic_equal(cf,cr,jr):return False,'semantic_rows_differ'
        if OWNER._csv_bytes(cf,jr)!=raw_csv:return False,'csv_not_exactly_reconstructable'
        if OWNER._jsonl_bytes(jr)!=raw_json:return False,'jsonl_not_exactly_reconstructable'
        return True,'exact'
    except Exception as exc:return False,f'{type(exc).__name__}:{exc}'


def _scan_suite(label:str,root:Path)->tuple[list[dict],dict]:
    total=obs=0;samples=[];t0=time.process_time();w0=time.perf_counter()
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        for p in sorted(q for q in workload.rglob('*') if q.is_file()):
            size=p.stat().st_size;total+=size;sample,used=_sample(p);obs+=used
            if sample:
                sample.update({'suite':label,'workload':workload.name,'path':p.relative_to(workload).as_posix()});samples.append(sample)
    return samples,{'logical_bytes':total,'observation_bytes':obs,'observation_cpu_s':time.process_time()-t0,'observation_wall_s':time.perf_counter()-w0}


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_admission_v2_neutral');hostile=V029._load(V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_admission_v2_hostile');repair=V029._load(V029.REPAIR_PATH,'cmpct_v030_admission_v2_repair');repair.install_generation_hooks(neutral)
    roots=[]
    for label,builder,root in (('neutral_hostile_v1',neutral,work/'neutral'),('resemblance_hostile_v1',hostile,work/'resemblance')):
        builder.build(root)
        if label=='neutral_hostile_v1':repair.normalize_root(root)
        roots.append((label,root))
    samples=[];metrics={}
    for label,root in roots:
        got,m=_scan_suite(label,root);samples.extend(got);metrics[label]=m
    groups={}
    for s in samples:groups.setdefault((s['suite'],s['workload'],s['fields']),[]).append(s)
    pairs=[]
    for (suite,workload,fields),items in groups.items():
        csvs=[x for x in items if x['kind']=='csv'];jsons=[x for x in items if x['kind']=='jsonl']
        for c in csvs:
            for j in jsons:
                n=min(len(c['rows']),len(j['rows']),SAMPLE_ROWS)
                if n>=3 and c['rows'][:n]==j['rows'][:n]:pairs.append((c,j,n))
    accepted=[];rejected=[];proof_bytes=0;proof_cpu=proof_wall=0.0
    rootmap=dict(roots)
    for c,j,n in pairs:
        root=rootmap[c['suite']]/c['workload'];cp=root.joinpath(*Path(c['path']).parts);jp=root.joinpath(*Path(j['path']).parts);proof_bytes+=c['size']+j['size']
        p0=time.process_time();w0=time.perf_counter();ok,reason=_full_proof(cp,jp);proof_cpu+=time.process_time()-p0;proof_wall+=time.perf_counter()-w0
        row={'suite':c['suite'],'workload':c['workload'],'csv_path':c['path'],'jsonl_path':j['path'],'fields':list(c['fields']),'sample_rows_matched':n,'csv_sniff_bytes':c['sniff_bytes'],'jsonl_sniff_bytes':j['sniff_bytes'],'proof_bytes':c['size']+j['size'],'result':reason}
        (accepted if ok else rejected).append(row)
    total=sum(m['logical_bytes'] for m in metrics.values());obs=sum(m['observation_bytes'] for m in metrics.values());outside=[x for x in accepted if not(x['suite']=='neutral_hostile_v1' and x['workload']=='04_analytics_and_database')];analytics=[x for x in accepted if x['suite']=='neutral_hostile_v1' and x['workload']=='04_analytics_and_database' and {x['csv_path'],x['jsonl_path']}=={'events.csv','events.jsonl'}]
    return {'schema':'cmpct-v030-r4-tabular-admission-oracle-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'chunk_bytes':CHUNK,'max_sniff_bytes_per_file':MAX_SNIFF,'sample_rows':SAMPLE_ROWS,'suite_metrics':metrics,'logical_bytes_total':total,'observation_bytes_total':obs,'observation_fraction':obs/max(1,total),'observation_cpu_s_total':sum(m['observation_cpu_s'] for m in metrics.values()),'sampled_tabular_files':len(samples),'sample_matched_candidate_pairs':len(pairs),'full_proof_bytes':proof_bytes,'full_proof_fraction':proof_bytes/max(1,total),'full_proof_cpu_s':proof_cpu,'full_proof_wall_s':proof_wall,'accepted_relations':accepted,'rejected_after_sample':rejected,'hypothesis':{'analytics_relation_discovered_without_path_or_extension_dispatch':bool(analytics),'zero_other_accepted_relations_on_frozen_15':not outside,'observation_under_20pct_of_logical_bytes':obs/max(1,total)<0.20,'full_proof_under_15pct_of_logical_bytes':proof_bytes/max(1,total)<0.15,'supported_as_sparse_opportunity_gate':bool(analytics) and not outside and obs/max(1,total)<0.20 and proof_bytes/max(1,total)<0.15},'contract':{'diagnostic_only':True,'release_credit':False,'filename_extension_used_for_admission':False,'workload_identity_used_for_admission':False,'incremental_observation':True,'full_proof_only_after_schema_and_sample_match':True,'exact_lexical_reconstruction_required':True,'thresholds_unchanged_from_v1':True},'next_if_supported':'combine this sparse gate with the fast binary owner in one integrated research archive wrapper; charge actual complete create/read/RSS/recovery and hostile parser limits','next_if_falsified':'do not relax the observation threshold; further reduce observation work or keep tabular co-lift research-only'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-admission-v2-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-admission-v2.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('logical_bytes_total','observation_bytes_total','observation_fraction','observation_cpu_s_total','sampled_tabular_files','sample_matched_candidate_pairs','full_proof_bytes','full_proof_fraction','accepted_relations','rejected_after_sample','hypothesis')},indent=2))

if __name__=='__main__':main()
