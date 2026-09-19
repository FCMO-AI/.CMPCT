from __future__ import annotations
import binascii, json, shutil, time
from pathlib import Path
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

def run(root:Path)->dict:
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
    src=PERF._build_corpora(root/'corpora')[("neutral_hostile_v1","09_ml_artifacts")]
    C=PRODUCT._BASE_IMPL.C; G=C.SHARED.build.__globals__["G"]; O=G.O
    graph=root/'attempt5.cmpct'; G.A5.build_graph(src,graph); _fmt,_source,meta,records=G.strict._read_source_records(graph); users=O._record_member_lengths(meta,len(records)); original=O._audition_record
    def selected_only(record_id,record,member_lengths):
        raw=O.A5._decode_record(record); amp=max((len(raw)/n for n in member_lengths),default=float('inf')); baseline=record[2]
        stats={'record_id':record_id,'raw_bytes':len(raw),'baseline_payload_bytes':len(baseline),'max_member_read_amplification':amp,'selected':'none','payload_saving_bytes':0}
        if not (O.MIN_RECORD_BYTES<=len(raw)<=O.MAX_OVERLAY_RECORD) or amp>O.MAX_MEMBER_READ_AMP: return record,None,stats
        best_payload=baseline; best=None
        for width in O.LANE_WIDTHS:
            transformed=O.lane_forward(raw,width); codec,payload=O._compress_transformed(transformed)
            if len(baseline)-len(payload)>=O.MIN_PAYLOAD_SAVING and len(payload)<len(best_payload): best_payload=payload; best=('lane',width,transformed,codec,payload)
        for delimiter in O._delimiter_rank(raw):
            transformed=O.delimiter_forward(raw,delimiter); codec,payload=O._compress_transformed(transformed)
            if len(baseline)-len(payload)>=O.MIN_PAYLOAD_SAVING and len(payload)<len(best_payload): best_payload=payload; best=('delimiter',delimiter,transformed,codec,payload)
        if best is None: return record,None,stats
        kind,param,physical,codec,payload=best
        restored=O.lane_inverse(physical,param,len(raw)) if kind=='lane' else O.delimiter_inverse(physical,len(raw))
        if restored!=raw: raise RuntimeError('selected Geometry inverse failed')
        transformed_record=(codec,len(physical),payload,binascii.crc32(raw)&0xFFFFFFFF,O.H(raw)); descriptor=[kind,int(param),len(raw)]
        stats.update({'selected':kind,'param':int(param),'payload_saving_bytes':len(baseline)-len(payload),'candidate_payload_bytes':len(payload),'physical_transform_bytes':len(physical)})
        return transformed_record,descriptor,stats
    def measure(fn):
        O._audition_record=fn; started_cpu=time.process_time(); started=time.perf_counter(); rows=[G._audition_record(i,r,users[i]) for i,r in enumerate(records)]; return rows,time.perf_counter()-started,time.process_time()-started_cpu
    pairs=[]
    try:
        for rep,order in enumerate((('control','fast'),('fast','control'))*2):
            got={}
            for arm in order: got[arm]=measure(original if arm=='control' else selected_only)
            c,cw,cc=got['control']; f,fw,fc=got['fast']
            if c!=f: raise RuntimeError('audition result/stats identity drift')
            pairs.append({'rep':rep,'order':list(order),'control_wall_s':cw,'fast_wall_s':fw,'control_cpu_s':cc,'fast_cpu_s':fc,'wall_improvement_pct':(cw-fw)/cw*100,'cpu_improvement_pct':(cc-fc)/cc*100})
    finally: O._audition_record=original
    vals=sorted(p['wall_improvement_pct'] for p in pairs); med=(vals[1]+vals[2])/2
    return {'schema':'cmpct-v030-ml-selected-only-inverse-proof-v1','release_credit':False,'record_count':len(records),'pairs':pairs,'median_overlay_audition_wall_improvement_pct':med,'exact_audition_identity':True,'claim_boundary':'flat G1/G2 audition only; hierarchical owner unchanged; whole-product transfer unpaid'}
if __name__=='__main__':
    result=run(Path('benchmark-artifacts/v030-ml-selected-only-inverse-work')); out=Path('benchmark-artifacts/v030-ml-selected-only-inverse.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
