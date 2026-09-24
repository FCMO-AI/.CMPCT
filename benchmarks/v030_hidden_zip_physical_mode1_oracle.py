from __future__ import annotations
"""Gifted representation oracle: validated exact Deflate streams as physical-only mode-1 blobs.

Unlike the retired mode1 oracle, decoded logical Deflate members are validated but never retained. A Deflated
payload's rawref and mode-1 streamref are both the exact-stream blob. Validation remains at least as strong as
the product path: ZipFile.read checks CRC/length once per unique exact stream, then the decoded bytes are dropped.
The A/B is forced serial so the shared validation cache is deterministic and both arms have the same worker policy.
Research only; no product/release credit.
"""
import argparse,binascii,json,os,shutil,statistics,struct,subprocess,sys,zipfile
from pathlib import Path
from benchmarks import v030_hidden_zip_resource_gate as RESOURCE
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
REPS=3;LFH=struct.Struct('<IHHHHHIIIHH')

def _stage_physical_only(original:bytes,*,max_retained_bytes=None,exact_stream_retention=True,validated_deflates=None):
    from cmpct.codec import sha
    from cmpct.vzip_transaction import StagedVzipRecipe,_BytesView
    original=bytes(original);view=_BytesView(original);payloads=[];spans=[];staged=[];validated_deflates=validated_deflates if validated_deflates is not None else {}
    def add(raw,hint=''):
        raw=bytes(raw);ref=sha(raw);staged.append((raw,hint,None,ref));return ref
    try:
        with zipfile.ZipFile(view) as z:
            infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda x:x.header_offset)
            for info in infos:
                if info.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):return None
                view.seek(info.header_offset);v=LFH.unpack(view.read(LFH.size));nl,xl=v[-2],v[-1];start=info.header_offset+LFH.size+nl+xl;end=start+int(info.compress_size)
                if end>len(original):return None
                stream=original[start:end]
                if info.compress_type==zipfile.ZIP_DEFLATED:
                    stream_hash=sha(stream);key=(int(info.compress_size),int(info.file_size),int(info.CRC),stream_hash)
                    if key not in validated_deflates:
                        z.read(info)  # authoritative CRC/length validation; output deliberately not retained
                        validated_deflates[key]=True
                    ref=add(stream,'.opaque-deflate')
                else:
                    stream_hash=b'';ref=add(stream,Path(info.filename).suffix.lower())
                spans.append((start,end));payloads.append([ref,int(info.compress_type),stream_hash,len(stream),-1])
    except (OSError,ValueError,RuntimeError,struct.error,zipfile.BadZipFile):return None
    literals=[];cursor=0
    for start,end in spans:literals.append(original[cursor:start]);cursor=end
    literals.append(original[cursor:]);skeleton=b''.join(literals);skref=add(skeleton,'.cmpct-skeleton');retained=sum(len(x[0]) for x in staged)
    if max_retained_bytes is not None and retained>int(max_retained_bytes):return None
    return StagedVzipRecipe([skref,[len(x) for x in literals],payloads,sha(original),len(original),binascii.crc32(original)&0xffffffff],tuple(staged))

def _child(source:Path,arc:Path,out:Path,result:Path):
    os.environ['CMPCT_ENCODE_WORKERS']='1'
    from cmpct import hidden_zip_stage as STAGE,builder_hidden_zip as BRIDGE
    original_stage=STAGE.stage_vzip_recipe_bytes;original_retain=BRIDGE._retain_exact_streams_for_hidden_winners
    def retain(builder,cohort):
        for staged in cohort.staged.values():
            for _rawref,method,stream_hash,_csize,_level in staged.recipe[2]:
                if int(method)==zipfile.ZIP_DEFLATED:
                    h=bytes(stream_hash)
                    if h not in builder.cands:raise RuntimeError('physical-only stream candidate missing')
                    builder.secondary_stream_hashes.add(h)
    STAGE.stage_vzip_recipe_bytes=_stage_physical_only;BRIDGE._retain_exact_streams_for_hidden_winners=retain
    try:RESOURCE._child(source,'candidate',arc,out,result)
    finally:STAGE.stage_vzip_recipe_bytes=original_stage;BRIDGE._retain_exact_streams_for_hidden_winners=original_retain
    from cmpct.reader import CMPCT
    with CMPCT(arc) as reader:modes=[int(p[2]) for recipe in reader.index.get('recipes',[]) for p in recipe[2] if int(p[1])==zipfile.ZIP_DEFLATED]
    if not modes or any(m!=1 for m in modes):raise RuntimeError(f'physical-only oracle emitted modes {sorted(set(modes))}')
    row=json.loads(result.read_text());row['physical_only_mode1_verified']=True;row['deflate_stream_modes']=modes;result.write_text(json.dumps(row,indent=2)+'\n')

def _run_child(script,source,root,tag):
    arc=root/f'{tag}.cmpct';out=root/f'{tag}-out';result=root/f'{tag}.json';env=dict(os.environ);env['PYTHONPATH']=os.getcwd();env['CMPCT_ENCODE_WORKERS']='1';subprocess.run([sys.executable,os.fspath(script),'--child','--source',os.fspath(source),'--arc',os.fspath(arc),'--extract',os.fspath(out),'--child-output',os.fspath(result)],check=True,env=env);return json.loads(result.read_text())

def run(root:Path):
    shutil.rmtree(root,ignore_errors=True);root.mkdir(parents=True);script=Path(__file__).resolve();rows=[]
    for rep in range(REPS):
        work=root/f'rep-{rep}';suite=work/'neutral';n=GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py',f'cmpct_phys_mode1_n_{rep}');repair=GENERAL.V029._load(GENERAL.V029.REPAIR_PATH,f'cmpct_phys_mode1_r_{rep}');repair.install_generation_hooks(n);n.build(suite);repair.normalize_root(suite);source=suite/'02_office_workspace';want=PRODUCT.treehash(source);runroot=work/'runs';runroot.mkdir(parents=True)
        old=os.environ.get('CMPCT_ENCODE_WORKERS');os.environ['CMPCT_ENCODE_WORKERS']='1'
        try:base=RESOURCE._run_child(Path(RESOURCE.__file__).resolve(),source,'base',runroot,'base');candidate=_run_child(script,source,runroot,'candidate')
        finally:
            if old is None:os.environ.pop('CMPCT_ENCODE_WORKERS',None)
            else:os.environ['CMPCT_ENCODE_WORKERS']=old
        if base['tree_sha256']!=want or candidate['tree_sha256']!=want:raise RuntimeError('tree identity failure')
        rows.append({'rep':rep,'saving_bytes':base['archive_bytes']-candidate['archive_bytes'],'base':base,'candidate':candidate})
    def med(arm,key):return statistics.median(float(r[arm][key]) for r in rows)
    bc=med('base','create_wall_s');cc=med('candidate','create_wall_s');be=med('base','extract_wall_s');ce=med('candidate','extract_wall_s');br=med('base','peak_rss_kib');cr=med('candidate','peak_rss_kib')
    return {'schema':'cmpct-v030-hidden-zip-physical-mode1-oracle-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'evidence_class':'research-oracle','product_release_credit':False,'summary':{'saving_bytes_by_rep':[r['saving_bytes'] for r in rows],'saving_bytes_median':statistics.median(r['saving_bytes'] for r in rows),'create_wall_ratio':cc/bc,'extract_wall_ratio':ce/be,'peak_rss_ratio':cr/br,'exact_tree':True,'all_deflate_mode1':True},'contract':{'serial_AB':True,'deflate_crc_length_validated_once_per_unique_stream':True,'decoded_deflate_members_retained':False,'exact_stream_blob_is_recipe_rawref_and_streamref':True,'existing_reader_grammar_only':True,'release_thresholds_unchanged':True},'rows':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-physical-mode1-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-physical-mode1.json'));p.add_argument('--child',action='store_true');p.add_argument('--source',type=Path);p.add_argument('--arc',type=Path);p.add_argument('--extract',type=Path);p.add_argument('--child-output',type=Path);a=p.parse_args()
    if a.child:_child(a.source,a.arc,a.extract,a.child_output);return
    result=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
