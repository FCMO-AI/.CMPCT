from __future__ import annotations
"""Research-only O0 oracle: can exact hidden-ZIP Deflate payloads share a bounded physical basis?

This deliberately receives no product credit. Admission only gifts the same hidden winners as #205.
The timed/charged representation never inflates a ZIP member: it reads each admitted source once,
extracts exact RFC-1951 payload slices, exact-deduplicates them, then auditions bounded depth-1 rsync-style
residuals between similarity-discovered streams. Every retained base and residual byte is charged.
The question is whether physical-stream structure can recover the ~3.68 MB lost by physical-only mode1.
"""
import argparse, hashlib, io, json, os, shutil, statistics, struct, time, zipfile
from pathlib import Path
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.hidden_zip import observe_hidden_zip_admission
from cmpct.resemblance import similarity_sketch, lsh_candidates, delta_encode, delta_decode

REPS=3
LOCAL_HEADER_BYTES=30
LOCAL_SIG=b'PK\x03\x04'
EDGE_META_BYTES=48  # conservative charged base-id/target-id/length/hash framing allowance
TARGET_RECOVERY_BYTES=3_680_000


def _payload(raw: bytes, info: zipfile.ZipInfo) -> bytes:
    off=int(info.header_offset)
    if off<0 or off+LOCAL_HEADER_BYTES>len(raw) or raw[off:off+4]!=LOCAL_SIG:
        raise RuntimeError('local header bounds/signature')
    name_len,extra_len=struct.unpack_from('<HH',raw,off+26)
    start=off+LOCAL_HEADER_BYTES+name_len+extra_len; end=start+int(info.compress_size)
    if end>len(raw): raise RuntimeError('compressed payload bounds')
    return raw[start:end]


def _collect(source: Path, admitted: list[str]):
    streams=[]; source_bytes=0; members=0
    for rel in admitted:
        raw=(source/rel).read_bytes(); source_bytes+=len(raw)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                if info.is_dir() or info.compress_type!=zipfile.ZIP_DEFLATED: continue
                streams.append(_payload(raw,info)); members+=1
    return streams,source_bytes,members


def _represent(streams: list[bytes]) -> dict:
    # Exact aliases are free references after one physical owner; hashes/refs are metadata charged below.
    unique=[]; by_hash={}; aliases=0
    for stream in streams:
        h=hashlib.sha256(stream).digest(); idx=by_hash.get(h)
        if idx is not None and unique[idx]==stream: aliases+=1; continue
        by_hash[h]=len(unique); unique.append(stream)
    direct=sum(len(x) for x in unique)
    sketches=[similarity_sketch(x) for x in unique]
    edges=lsh_candidates(sketches,max_bucket=48,max_candidates=8)
    best={i:(len(unique[i]),None,None) for i in range(len(unique))}
    auditions=0
    for edge in edges:
        # Depth-1 only, earlier physical owner only. This keeps reconstruction bounded and acyclic.
        if edge.base>=edge.target: continue
        base,target=unique[edge.base],unique[edge.target]
        if len(base)>8*1024*1024: continue
        auditions+=1
        delta=delta_encode(base,target,max_base_index=8*1024*1024)
        if delta_decode(base,delta.payload)!=target: raise RuntimeError('delta oracle lost exactness')
        charged=len(delta.payload)+EDGE_META_BYTES
        if charged<best[edge.target][0]: best[edge.target]=(charged,edge.base,delta.payload)
    represented=sum(v[0] for v in best.values())
    # Charge one 32-byte identity per unique stream and one 8-byte owner reference per exact alias.
    identity_meta=32*len(unique)+8*aliases
    represented_charged=represented+identity_meta
    return {'stream_count':len(streams),'unique_streams':len(unique),'exact_aliases':aliases,
            'direct_unique_payload_bytes':direct,'candidate_edges':len(edges),'delta_auditions':auditions,
            'represented_payload_bytes':represented,'identity_metadata_bytes':identity_meta,
            'represented_charged_bytes':represented_charged,
            'recovered_vs_direct_bytes':direct-represented_charged,
            'target_recovery_bytes':TARGET_RECOVERY_BYTES,
            'target_recovery_met':direct-represented_charged>=TARGET_RECOVERY_BYTES}


def run(root: Path) -> dict:
    shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True); rows=[]
    for rep in range(REPS):
        suite=root/f'rep-{rep}'/'neutral'
        n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_stream_resid_n_{rep}')
        repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_stream_resid_r_{rep}')
        repair.install_generation_hooks(n); n.build(suite); repair.normalize_root(suite)
        source=suite/'02_office_workspace'; before=PRODUCT.treehash(source)
        admitted=[a.rel for a in observe_hidden_zip_admission(source).admitted]
        t0=time.perf_counter(); streams,source_bytes,members=_collect(source,admitted); repn=_represent(streams); wall=time.perf_counter()-t0
        if PRODUCT.treehash(source)!=before: raise RuntimeError('oracle mutated source')
        rows.append({'rep':rep,'tree_sha256':before,'admitted':admitted,'wall_s':wall,'source_bytes_read':source_bytes,'members':members,**repn})
    med=lambda k: statistics.median(r[k] for r in rows)
    return {'schema':'cmpct-v030-hidden-zip-stream-residual-oracle-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),
            'evidence_class':'research-oracle','product_release_credit':False,
            'summary':{'direct_unique_payload_bytes_median':med('direct_unique_payload_bytes'),
                       'represented_charged_bytes_median':med('represented_charged_bytes'),
                       'recovered_vs_direct_bytes_median':med('recovered_vs_direct_bytes'),
                       'target_recovery_bytes':TARGET_RECOVERY_BYTES,
                       'target_recovery_met_all':all(r['target_recovery_met'] for r in rows),
                       'wall_s_median':med('wall_s'),'stream_count_median':med('stream_count'),
                       'unique_streams_median':med('unique_streams'),'exact_aliases_median':med('exact_aliases')},
            'contract':{'no_member_inflation':True,'depth_one_only':True,'exact_delta_roundtrip':True,
                        'all_bases_and_residuals_charged':True,'identity_metadata_charged':True,
                        'admission_is_gifted_selector_only':True,'release_thresholds_unchanged':True},'rows':rows}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-stream-residual-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-stream-residual.json')); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['summary'],indent=2))
if __name__=='__main__': main()
