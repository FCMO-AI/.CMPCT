from __future__ import annotations

"""Content-driven opportunity gate for reversible tabular co-lifting.

No filename extension or workload identity is used for discovery.  Each regular file contributes at most 64 KiB to
a cheap sniff.  CSV-like and object-JSONL-like samples are grouped by ordered schema; only complementary candidates
whose first rows agree advance to full semantic + exact-lexical proof.  The oracle runs on all frozen 15 workloads
and reports observation bytes, full-proof bytes, CPU/wall time, rejected candidates and accepted exact relations.
"""

import argparse, csv, io, json, os, shutil, time
from pathlib import Path

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_tabular_owner_oracle as OWNER

SNIFF=64*1024
SAMPLE_ROWS=16


def _sample(path:Path)->dict|None:
    size=path.stat().st_size
    with path.open('rb') as f: raw=f.read(SNIFF)
    try:text=raw.decode('utf-8')
    except UnicodeDecodeError:return None
    if not text:return None
    complete=text if raw.endswith(b'\n') or size<=len(raw) else text[:text.rfind('\n')+1] if '\n' in text else ''
    if not complete:return None
    lines=complete.splitlines()
    # JSONL object table.
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
                    return {'kind':'jsonl','fields':fields,'rows':rows,'size':size,'sniff_bytes':len(raw)}
        except Exception:pass
    # CSV-like table. Require >=3 columns and stable width to suppress ordinary text.
    try:
        parsed=list(csv.reader(io.StringIO(complete,newline='')))
        if len(parsed)>=4 and len(parsed[0])>=3:
            fields=tuple(parsed[0]); body=parsed[1:1+SAMPLE_ROWS]
            if body and all(len(r)==len(fields) for r in body):
                return {'kind':'csv','fields':fields,'rows':[tuple(r) for r in body],'size':size,'sniff_bytes':len(raw)}
    except Exception:pass
    return None


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
    total=0;obs=0;samples=[];t0=time.process_time();w0=time.perf_counter()
    for workload in sorted(p for p in root.iterdir() if p.is_dir()):
        for p in sorted(q for q in workload.rglob('*') if q.is_file()):
            size=p.stat().st_size;total+=size
            s=_sample(p);obs+=min(size,SNIFF)
            if s:
                s.update({'suite':label,'workload':workload.name,'path':p.relative_to(workload).as_posix()});samples.append(s)
    return samples,{'logical_bytes':total,'observation_bytes':obs,'observation_cpu_s':time.process_time()-t0,'observation_wall_s':time.perf_counter()-w0}


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    neutral=V029._load(V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_v030_admission_neutral');hostile=V029._load(V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','cmpct_v030_admission_hostile');repair=V029._load(V029.REPAIR_PATH,'cmpct_v030_admission_repair');repair.install_generation_hooks(neutral)
    roots=[]
    for label,builder,root in (('neutral_hostile_v1',neutral,work/'neutral'),('resemblance_hostile_v1',hostile,work/'resemblance')):
        builder.build(root)
        if label=='neutral_hostile_v1':repair.normalize_root(root)
        roots.append((label,root))
    samples=[];suite_metrics={}
    for label,root in roots:
        got,metrics=_scan_suite(label,root);samples.extend(got);suite_metrics[label]=metrics

    groups={}
    for s in samples:groups.setdefault((s['suite'],s['workload'],s['fields']),[]).append(s)
    candidate_pairs=[]
    for (suite,workload,fields),items in groups.items():
        csvs=[x for x in items if x['kind']=='csv'];jsons=[x for x in items if x['kind']=='jsonl']
        for c in csvs:
            for j in jsons:
                n=min(len(c['rows']),len(j['rows']),SAMPLE_ROWS)
                if n>=3 and c['rows'][:n]==j['rows'][:n]:candidate_pairs.append((c,j,n))

    accepted=[];rejected=[];proof_bytes=0;proof_cpu=0.0;proof_wall=0.0
    for c,j,n in candidate_pairs:
        # Resolve the workload root without trusting the names for admission; labels are evidence only.
        root=dict(roots)[c['suite']]/c['workload'];cp=root.joinpath(*Path(c['path']).parts);jp=root.joinpath(*Path(j['path']).parts)
        proof_bytes+=c['size']+j['size'];p0=time.process_time();w0=time.perf_counter();ok,reason=_full_proof(cp,jp);proof_cpu+=time.process_time()-p0;proof_wall+=time.perf_counter()-w0
        row={'suite':c['suite'],'workload':c['workload'],'csv_path':c['path'],'jsonl_path':j['path'],'fields':list(c['fields']),'sample_rows_matched':n,'proof_bytes':c['size']+j['size'],'result':reason}
        (accepted if ok else rejected).append(row)

    total=sum(m['logical_bytes'] for m in suite_metrics.values());obs=sum(m['observation_bytes'] for m in suite_metrics.values())
    outside=[x for x in accepted if not (x['suite']=='neutral_hostile_v1' and x['workload']=='04_analytics_and_database')]
    analytics=[x for x in accepted if x['suite']=='neutral_hostile_v1' and x['workload']=='04_analytics_and_database' and {x['csv_path'],x['jsonl_path']}=={'events.csv','events.jsonl'}]
    return {'schema':'cmpct-v030-r4-tabular-admission-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'sniff_bytes_per_file_cap':SNIFF,'sample_rows':SAMPLE_ROWS,'suite_metrics':suite_metrics,'logical_bytes_total':total,'observation_bytes_total':obs,'observation_fraction':obs/max(1,total),'sampled_tabular_files':len(samples),'sample_matched_candidate_pairs':len(candidate_pairs),'full_proof_bytes':proof_bytes,'full_proof_fraction':proof_bytes/max(1,total),'full_proof_cpu_s':proof_cpu,'full_proof_wall_s':proof_wall,'accepted_relations':accepted,'rejected_after_sample':rejected,'hypothesis':{'analytics_relation_discovered_without_path_or_extension_dispatch':bool(analytics),'zero_other_accepted_relations_on_frozen_15':not outside,'observation_under_20pct_of_logical_bytes':obs/max(1,total)<0.20,'full_proof_under_15pct_of_logical_bytes':proof_bytes/max(1,total)<0.15,'supported_as_sparse_opportunity_gate':bool(analytics) and not outside and obs/max(1,total)<0.20 and proof_bytes/max(1,total)<0.15},'contract':{'diagnostic_only':True,'release_credit':False,'filename_extension_used_for_admission':False,'workload_identity_used_for_admission':False,'full_proof_only_after_schema_and_sample_match':True,'exact_lexical_reconstruction_required':True},'next_if_supported':'reuse the sparse schema/sample gate ahead of the research integrated binary owner; measure changed-cone cacheability and hostile parser limits before any production selector','next_if_falsified':'do not integrate broad tabular discovery; tighten the observation signature or keep the owner research-only'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-admission-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-tabular-admission.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('logical_bytes_total','observation_bytes_total','observation_fraction','sampled_tabular_files','sample_matched_candidate_pairs','full_proof_bytes','full_proof_fraction','accepted_relations','rejected_after_sample','hypothesis')},indent=2))

if __name__=='__main__':main()
