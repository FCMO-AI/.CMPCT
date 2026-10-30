#!/usr/bin/env python3
"""J24G89 source-pinned physical r24 O0 replay-only ceiling. NO CMPCT imports.
Not a source-exact #823 Reader benchmark, product win, or real checkpoint.
"""
import ctypes, ctypes.util, hashlib, json, os, platform, statistics, struct, sys, time
import msgpack

H=struct.Struct('<8sHHQQQ32s')
F=struct.Struct('<8sBBBBQQQ32s')
CASES={'8192-middle':('j24g83-8192-middle-fresh-valid.cmpct',
 '5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a'),
 '32768-tail':('j24g83-32768-tail-fresh-valid.cmpct',
 '8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81')}
lib=ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')
lib.ZSTD_decompress.argtypes=(ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t)
lib.ZSTD_decompress.restype=ctypes.c_size_t
lib.ZSTD_isError.argtypes=(ctypes.c_size_t,)
lib.ZSTD_isError.restype=ctypes.c_uint

def sha(b): return hashlib.sha256(b).digest()
def deco(b,n,c):
 assert 0<n<50000000
 if c==0:
  assert len(b)==n
  return b
 assert c==1
 out=ctypes.create_string_buffer(n)
 inp=ctypes.create_string_buffer(b)
 k=lib.ZSTD_decompress(out,n,inp,len(b))
 assert not lib.ZSTD_isError(k) and k==n
 return out.raw[:n]

def layout(data):
 m,rev,fl,cs,us,span,digest=H.unpack_from(data)
 assert (m,rev,fl)==(b'CMPCT24\0',24,0)
 base=H.size+cs
 assert base+span<=len(data)-F.size
 source=data[H.size:base]
 a=deco(source,us,1)
 assert sha(a)==digest
 original=msgpack.unpackb(a,raw=False)
 chain=[];seen=set();off=len(data)-F.size
 while True:
  assert off not in seen and base+span<=off<=len(data)-F.size
  seen.add(off)
  m,kind,c,flags,res,compressed,uncompressed,prev,signed=F.unpack_from(data,off)
  assert m==b'CMPTF24\0' and kind in (0,1) and flags==res==0 and compressed>0 and prev<off
  start=off-compressed
  assert start>=base+span
  blob=data[start:off]
  raw=deco(blob,uncompressed,c)
  assert sha(raw)==signed
  chain.append((off,kind,prev,c,uncompressed,signed,blob,msgpack.unpackb(raw,raw=False)))
  if prev==0: break
  off=prev
 chain.reverse()
 assert len(chain)==65 and chain[0][1]==0 and chain[-1][1]==0
 assert all(x[1]==1 for x in chain[1:-1])
 assert all(chain[i][2]==chain[i-1][0] for i in range(1,65))
 assert chain[0][-1]==original
 deleted=[]
 for entry in chain[1:64]:
  a=entry[-1]
  assert a['blobs']==[] and len(a['ops'])==1 and a['ops'][0][0]=='del'
  deleted.append(a['ops'][0][1])
 assert len(set(deleted))==63 and len(original['files'])>=8192
 s=[r for r in original['files'] if r[0] not in set(deleted)]
 last=chain[-1][-1]['files'];names={r[0] for r in last}
 assert len(s)==len(original['files'])-63 and len(last)==len(s)-1
 assert [r for r in s if r[0] in names]==last
 return source,us,digest,chain,len(original['files'])

def onepass(source,us,digest,chain):
 w=time.perf_counter_ns;p=time.process_time_ns
 ts=[w()];ps=[p()]
 first=chain[0]
 root=deco(first[6],first[4],first[3])
 assert sha(root)==first[5]
 base=msgpack.unpackb(root,raw=False)
 ts.append(w());ps.append(p())
 names=[]
 for off,kind,prev,codec,n,signed,compressed,expected in chain[1:64]:
  raw=deco(compressed,n,codec)
  assert sha(raw)==signed
  rec=msgpack.unpackb(raw,raw=False)
  if kind==1:
   assert rec['blobs']==[] and len(rec['ops'])==1 and rec['ops'][0][0]=='del'
   names.append(rec['ops'][0][1])
 ts.append(w());ps.append(p())
 deleted=set(names)
 survivors=[r for r in base['files'] if r[0] not in deleted]
 ts.append(w());ps.append(p())
 by={r[0]:r for r in survivors}
 ts.append(w());ps.append(p())
 assert len(by)==len(base['files'])-63 and len(names)==63
 return {'wall_ns':[ts[i+1]-ts[i] for i in range(4)],
         'cpu_ns':[ps[i+1]-ps[i] for i in range(4)]}

def main(folder,out,n=151):
 assert 50<=n<=500
 report={'schema':'cmpct-j24g89-physical-replay-only-o0-v1','host':platform.platform(),
         'product_credit':0,'samples_per_case':n,'cases':{},'status':'RUNNING',
         'source_head':os.popen('git rev-parse HEAD').read().strip()}
 for k,(name,expected) in CASES.items():
  data=open(os.path.join(folder,name),'rb').read()
  assert hashlib.sha256(data).hexdigest()==expected
  source,us,digest,chain,initial=layout(data)
  bad=bytearray(data);bad[chain[63][0]+F.size-1]^=0x55
  rejected=False
  try:layout(bytes(bad))
  except (AssertionError,ValueError,IndexError,struct.error):rejected=True
  assert rejected
  samples=[]
  for _ in range(12):onepass(source,us,digest,chain)
  for _ in range(n):samples.append(onepass(source,us,digest,chain))
  phase=['checkpoint0_decode','63_delta_auth_decode','63_delete_onepass','by_lookup']
  med={clk:{phase[i]:statistics.median(row[clk][i] for row in samples)
            for i in range(4)} for clk in ('wall_ns','cpu_ns')}
  shares=[r['wall_ns'][2]/sum(r['wall_ns']) for r in samples]
  sup=[sum(r['wall_ns'])/(sum(r['wall_ns'])-r['wall_ns'][2]) for r in samples]
  wide=[(r['wall_ns'][1]+r['wall_ns'][2])/sum(r['wall_ns']) for r in samples]
  report['cases'][k]={'physical_sha256':expected,'physical_bytes':len(data),
    'signed_footers':65,'original_members':initial,'real_deltas':63,
    'checkpoint64_index_parity':True,'tamper_rejected':True,
    'median_total_wall_ns':statistics.median(sum(r['wall_ns']) for r in samples),
    'median_phase_ns':med,'median_replay_share':statistics.median(shares),
    'median_free_replay_only_speedup_ceiling':statistics.median(sup),
    'median_footer_plus_replay_fraction_not_a_valid_free_oracle':statistics.median(wide),
    'raw_samples':samples}
 shares=[d['median_replay_share'] for d in report['cases'].values()]
 report['decision']=('REPLAY_WORK_LOW_FRACTION_O0' if all(x<0.10 for x in shares)
                    else 'REPLAY_WORK_MATERIAL_O0' if any(x>=0.20 for x in shares)
                    else 'AMBIGUOUS_10_TO_20_PERCENT')
 report['status']='PASS'
 with open(out,'w') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:{v:w for v,w in a.items() if v in ('median_replay_share',
     'median_total_wall_ns','median_free_replay_only_speedup_ceiling')}
     for k,a in report['cases'].items()},indent=2))
 print('J24G89_DECISION',report['decision'])

if __name__=='__main__':
 assert len(sys.argv) in (3,4)
 main(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)==4 else 151)
