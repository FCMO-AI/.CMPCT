#!/usr/bin/env python3
"""Office compact-floor locality oracle.

Question: is the ~5.95 MB inherited v0.25-style Office floor cheap because it
violates the current <=8x selected-member decoded-context contract?

Research bound only. Build the accepted deterministic Office tree with the
*current checked-in* inherited EntropyGraph v0.25 engine, verify exact
reconstruction, then charge every physical pack reachable from each independent
logical-member request. Historical byte identity is reported as provenance, not
asserted: the current nested tournament and the immutable historical v0.28
receipt differ by a few hundred bytes, and conflating those engines would turn
a locality falsifier into a stale-source test.
"""
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
 mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
N=load(ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','cmpct_neutral_office_oracle')
V025=load(ROOT/'experiments'/'entropygraph_v025.py','cmpct_v025_office_oracle')
EXPECTED_TREE='aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57'
EXPECTED_LOGICAL=16_063_798; EXPECTED_FILES=20
HISTORICAL_V028_FLOOR_BYTES=5_954_026
OBSERVED_CURRENT_NESTED_FLOOR_BYTES=5_954_226
LOCALITY_LIMIT=8.0

def expand_files(meta):
 fd=dict(meta['files'])
 for pi,ents in meta.get('micro',[]):
  off=0
  for path,n in ents: fd[path]=['plain',[['slice',pi,off,n]],n]; off+=n
 return fd

def refs_packs(refs): return {int(r[1]) for r in refs}
def stream_packs_for(meta,offset,length):
 end=offset+length; touched=set()
 for stream_off,pi,stream_len in meta.get('stream_packs',[]):
  stream_end=stream_off+stream_len
  if stream_end<=offset: continue
  if stream_off>=end: break
  touched.add(int(pi))
 return touched

def physical_packs_for(path,fd,meta,active=None):
 active=set() if active is None else active
 if path in active: raise RuntimeError(f'dependency cycle at {path}')
 active.add(path); d=fd[path]; typ=d[0]; touched=set()
 if typ=='plain': touched|=refs_packs(d[1])
 elif typ=='zipstreams':
  touched|=refs_packs(d[1])
  for offset,length in d[3]: touched|=stream_packs_for(meta,int(offset),int(length))
 elif typ=='inflate_stream': touched|=stream_packs_for(meta,int(d[1]),int(d[2]))
 elif typ=='decode_file': touched|=physical_packs_for(str(d[1]),fd,meta,active)
 elif typ=='splice':
  touched|=refs_packs(d[1])
  for child in d[3]: touched|=physical_packs_for(str(child),fd,meta,active)
 else: raise RuntimeError(f'unknown recipe {typ!r} for {path}')
 active.remove(path); return touched

def logical_size(d):
 return int(d[2] if d[0]=='plain' else d[4] if d[0] in ('zipstreams','inflate_stream','splice') else d[3] if d[0]=='decode_file' else (_ for _ in ()).throw(RuntimeError(d[0])))

def main():
 with tempfile.TemporaryDirectory(prefix='cmpct-office-v025-locality-') as td:
  work=Path(td); corpus_root=work/'corpus'; N.corpus_office(corpus_root); office=corpus_root/'02_office_workspace'
  files=sorted(p for p in office.rglob('*') if p.is_file()); logical=sum(p.stat().st_size for p in files); tree=V025.treehash(office)
  if tree!=EXPECTED_TREE or logical!=EXPECTED_LOGICAL or len(files)!=EXPECTED_FILES: raise RuntimeError({'tree':tree,'logical':logical,'files':len(files)})
  V025.ROOT=office; V025.OUT=work/'office-v025.cmpct'; build=V025.build(); archive_bytes=V025.OUT.stat().st_size; verify=V025.strong_verify()
  if not verify.get('ok') or verify.get('tree_sha256')!=EXPECTED_TREE: raise RuntimeError('v0.25 exact verification failed')
  f,meta,po=V025.open_ar(); f.close(); fd=expand_files(meta); rows=[]
  for path in sorted(fd):
   packs=physical_packs_for(path,fd,meta); decoded=sum(int(po[i][2]) for i in packs); lb=logical_size(fd[path]); amp=decoded/max(1,lb)
   rows.append({'path':path,'recipe':fd[path][0],'logical_bytes':lb,'decoded_physical_bytes':decoded,'physical_packs':sorted(packs),'amplification':amp,'within_8x':amp<=LOCALITY_LIMIT})
  worst=max(rows,key=lambda r:r['amplification']); failing=[r for r in rows if not r['within_8x']]
  weighted=sum(r['decoded_physical_bytes'] for r in rows)/max(1,sum(r['logical_bytes'] for r in rows))
  result={'schema':'cmpct-v030-office-v025-locality-oracle-v1','claim_boundary':'research bound only; current checked-in v0.25-style engine, not canonical product credit','office_tree_sha256':tree,'files':len(files),'logical_bytes':logical,'archive_bytes':archive_bytes,'historical_v028_floor_bytes':HISTORICAL_V028_FLOOR_BYTES,'observed_current_nested_floor_bytes':OBSERVED_CURRENT_NESTED_FLOOR_BYTES,'delta_vs_historical_floor_bytes':archive_bytes-HISTORICAL_V028_FLOOR_BYTES,'delta_vs_observed_nested_floor_bytes':archive_bytes-OBSERVED_CURRENT_NESTED_FLOOR_BYTES,'build':build,'strong_verify':verify,'locality_limit':LOCALITY_LIMIT,'max_member_amplification':worst['amplification'],'worst_member':worst,'weighted_member_amplification':weighted,'members_over_8x':len(failing),'locality_verdict':'PASS' if not failing else 'FAIL','rows':rows,'decision':'COMPACT_FLOOR_SURVIVES_LOCALITY_FALSIFIER' if not failing else 'COMPACT_FLOOR_LOCALITY_DEBT_CONFIRMED'}
  print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
