#!/usr/bin/env python3
"""Prospectively frozen J24G103c CPU-cause micro. Research only, no product code."""
import argparse,ctypes,hashlib,io,json,random,statistics,struct,time,zipfile
from pathlib import Path
from j24g102_cow_root_oracle import SOURCES,HEAD,H,makepair,priced
from j24g103_cdc_shift import GEAR,chunks,charge

def load(path):
 lib=ctypes.CDLL(str(path.resolve()))
 f=lib.j24g103_scan_cuts
 f.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t),ctypes.c_size_t]
 f.restype=ctypes.c_size_t
 return f
GT=(ctypes.c_uint64*256)(*GEAR)

def cuts(fn,raw,target):
 buf=(ctypes.c_size_t*(len(raw)//(target//4)+2))()
 n=fn(ctypes.c_char_p(raw),len(raw),GT,target,buf,len(buf))
 assert n<len(buf), 'native cut buffer error'
 start=0
 for i in range(n):
  end=buf[i]
  assert start<end<=len(raw),'invalid native cut'
  yield raw[start:end]
  start=end
 assert start==len(raw)

def native_price(fn,old,new,target):
 seen={};roots=[];counts=[]
 for raw in (old,new):
  keys=[]
  for part in cuts(fn,raw,target):
   key=H(part)
   assert key not in seen or seen[key]==part,'SHA keyed physical byte collision'
   seen[key]=part
   keys.append(key)
  header=struct.pack('<8sQQ',b'CMPCDC01',len(raw),len(keys))
  root=H(b'J24G103-ROOT-v1\0'+header+b''.join(keys))
  manifest=header+root+b'\0'*8+b''.join(keys)
  assert len(manifest)==64+32*len(keys)
  assert H(b'J24G103-ROOT-v1\0'+manifest[:24]+manifest[64:])==root
  roots.append((raw,keys,manifest));counts.append(len(keys))
 for raw,keys,_ in roots:
  assert b''.join(seen[k] for k in keys)==raw,'native physical reconstruction mismatch'
 total=sum(len(v)+44 for v in seen.values())+sum(len(x[2]) for x in roots)
 return total,counts

def clock(fn):
 t0=time.perf_counter_ns();c0=time.process_time_ns()
 fn()
 return {'wall_ns':time.perf_counter_ns()-t0,'cpu_ns':time.process_time_ns()-c0}

def main():
 ap=argparse.ArgumentParser()
 for host in SOURCES:ap.add_argument('--'+host,type=Path,required=True)
 ap.add_argument('--lib',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args()
 fn=load(a.lib);cases={}
 for host,expected in SOURCES.items():
  orig=getattr(a,host).read_bytes()
  assert hashlib.sha256(orig).hexdigest()==expected,'original provider ZIP mismatch'
  with zipfile.ZipFile(io.BytesIO(orig)) as z:
   assert z.read('checkout-head.txt').decode().strip()==HEAD,'original producer HEAD'
   for n in (4096,8192):
    old,new,_=makepair(z.read(f'{n}-A.cmpct'),z.read(f'{n}-B.cmpct'),n)
    for target in (4096,16384):
     variants={
      'root':old,'new':new,
      'early_insert':new[:512]+b'!'+new[512:],
      'mid_insert':new[:len(new)//2]+b'!'+new[len(new)//2:],
      'early_delete':new[:512]+new[513:],
      'unrelated_random':random.Random(240103+len(new)).randbytes(len(new))
     }
     for label,raw in variants.items():
      original=[H(p) for p in chunks(raw,target)]
      optimized=[H(p) for p in cuts(fn,raw,target)]
      assert original==optimized, f'parity failed {host}/{n}/{target}/{label}'
     reference=charge(old,new,target,verify=False)
     encoded,counts=native_price(fn,old,new,target)
     assert encoded==reference['charged_total_bytes'],'fully charged byte mismatch'
     assert counts==[reference['blocks_old'],reference['blocks_new']]
     methods={'python_gear':lambda:charge(old,new,target,verify=False),
        'native_cuts_sha':lambda:native_price(fn,old,new,target),
        'fixed_block_model':lambda:priced(old,new,target)}
     raw={k:[] for k in methods}
     order=list(methods)
     for rep in range(7):
      for key in (order if rep%2==0 else order[::-1]):
       raw[key].append(clock(methods[key]))
     med={k:statistics.median(q['wall_ns'] for q in obs) for k,obs in raw.items()}
     key=f'{host}-{n}-{target}'
     cases[key]={'boundary_parity_variants':list(variants),'fully_charged_bytes':encoded,
       'raw_seven_balanced':raw,'median_wall_ms':{k:v/1e6 for k,v in med.items()},
       'python_to_native_speedup':med['python_gear']/med['native_cuts_sha'],
       'native_over_fixed_ratio':med['native_cuts_sha']/med['fixed_block_model']}
     print(key,'py/native',round(cases[key]['python_to_native_speedup'],3),
       'native/fixed',round(cases[key]['native_over_fixed_ratio'],3),flush=True)
 four=[v for k,v in cases.items() if k.endswith('4096')]
 cpu_h1=all(v['python_to_native_speedup']>=5 for v in four)
 fixed_h2=sum(v['native_over_fixed_ratio']<=4 for v in four)>=3
 output={'schema':'J24G103C-NATIVE-BOUNDARY-CAUSAL-MICRO',
   'prereg_commit':'1048423bb571b55201d044f9f3801bafd019c524',
   'source_producer_HEAD':HEAD,'source_provider_SHA256':SOURCES,
   'source_C_SHA256':hashlib.sha256(Path('research/j24g103c_native_cuts.c').read_bytes()).hexdigest(),
   'compiler':'cc -O3 -shared -fPIC -std=c11 -Wall -Wextra -Werror',
   'scope':'Linux only; full in-process model construct CPU/wall, not Reader, Writer, cold process or release',
   'cases':cases,'fivefold_python_speedup_four_of_four':cpu_h1,
   'within_fourfold_fixed_three_of_four':fixed_h2,
   'verdict':'MICRO_CPU_OWNER_IS_PYTHON_DISPATCH' if cpu_h1 and fixed_h2 else 'MICRO_CPU_DEBT_UNRESOLVED',
   'truth_limitations':['no native CMPCT integration or ABI','no peak RSS or disk allocation',
    'fixed control inherits original J24G102 validation overhead',
    'J24G103 posthoc one-third shift failure and J24G99 stronger simple control remain']}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'verdict':output['verdict'],'result_SHA256':hashlib.sha256(a.out.read_bytes()).hexdigest(),
    'native_over_fixed_fourK':[round(q['native_over_fixed_ratio'],3) for q in four]},sort_keys=True))
if __name__=='__main__':main()
