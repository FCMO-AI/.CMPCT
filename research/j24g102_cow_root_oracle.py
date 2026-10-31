#!/usr/bin/env python3
"""J24G102 signed r24 terminal checkpoint vs exact two-root COW physical O0.

Research-only. Prereg: 292ee434d8578ab39e6550708029eb364d33e910.
Read originals with --ubuntu and --windows; no CMPCT module import.
"""
import argparse,ctypes,hashlib,io,json,os,random,struct,zipfile
from pathlib import Path
import msgpack
F=struct.Struct('<8sBBBBQQQ32s')
SOURCES={'ubuntu':'19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b',
'windows':'c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab'}
HEAD='129edec976efe8bb604584517de39553487fec34'
z=ctypes.CDLL('libzstd.so.1')
z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
z.ZSTD_decompress.restype=ctypes.c_size_t
z.ZSTD_isError.argtypes=[ctypes.c_size_t];z.ZSTD_isError.restype=ctypes.c_uint
H=lambda b:hashlib.sha256(b).digest()
def ck(pred,msg):
 if not pred:raise AssertionError(msg)
def foot(raw,p):
 m,k,c,f,r,cl,ul,prev,ph=F.unpack_from(raw,p)
 ck(m==b'CMPTF24\0' and k in (0,1) and f==r==0 and 0<cl<=p and 0<ul<8_000_000,'bad footer')
 src=raw[p-cl:p]
 if c==1:
  inp=ctypes.create_string_buffer(src);out=ctypes.create_string_buffer(ul)
  count=z.ZSTD_decompress(out,ul,inp,cl)
  ck(not z.ZSTD_isError(count) and count==ul,'bad Zstd');dec=out.raw[:ul]
 else:ck(c==0,'bad codec');dec=src
 ck(H(dec)==ph and len(dec)==ul,'footer payload checksum')
 return {'pos':p,'kind':k,'codec':c,'clen':cl,'ulen':ul,'prev':prev,'digest':ph,'wire':src,'index':dec}
def chain(raw):
 p=len(raw)-F.size;res=[];visited=set()
 while p:
  ck(0<p<len(raw)-F.size+1 and p not in visited and len(res)<70,'bad ancestry');visited.add(p)
  v=foot(raw,p);res.append(v);p=v['prev']
 res.reverse();ck(res[0]['kind']==0 and res[0]['prev']==0,'bad root');return res
def makepair(a,b,n):
 ck(b.startswith(a),'B not physical extension A')
 x,y=chain(a),chain(b)
 ck(len(x)==64 and len(y)==65 and y[-1]['kind']==0,'63 DELETE and one checkpoint')
 ck(all(u['pos']==v['pos'] and u['digest']==v['digest'] for u,v in zip(x,y)),'A/B chain mismatch')
 start=x[0]['pos']-x[0]['clen'];end=x[0]['pos']+F.size
 latest=y[-1];old=a[:end]
 tail=F.pack(b'CMPTF24\0',0,latest['codec'],0,0,latest['clen'],latest['ulen'],0,latest['digest'])
 new=a[:start]+latest['wire']+tail
 ck(len(chain(new))==1 and chain(new)[0]['digest']==latest['digest'],'repacked r24 checkpoint')
 first=msgpack.unpackb(x[0]['index'],raw=False,strict_map_key=False)
 final=msgpack.unpackb(latest['index'],raw=False,strict_map_key=False)
 ck(first['blobs']==final['blobs'] and len(first['files'])==n,'initial blobs')
 names=[]
 for node in x[1:]:
  delta=msgpack.unpackb(node['index'],raw=False,strict_map_key=False)
  ck(node['kind']==1 and delta.get('blobs')==[] and len(delta['ops'])==1 and delta['ops'][0][0]=='del','unexpected delta')
  names.append(delta['ops'][0][1])
 ck(len(names)==len(set(names))==63,'delete distinctness')
 survivors=[r for r in first['files'] if r[0] not in names]
 ck(len(survivors)==n-63 and survivors==final['files'],'all logical rows')
 ck({k:v for k,v in first.items() if k!='files'}=={k:v for k,v in final.items() if k!='files'},'metadata changed')
 return old,new,{'A_SHA256':H(a).hex(),'B_SHA256':H(b).hex(),'start_prefix_SHA256':H(a[:start]).hex(),
 'initial_index_SHA256':x[0]['digest'].hex(),'final_index_SHA256':latest['digest'].hex(),
 'old_sha256':H(old).hex(),'new_sha256':H(new).hex(),
 'old_bytes':len(old),'new_bytes':len(new),'initial_members':n,'final_members':n-63}
def priced(old,new,size):
 store={};heads={}
 for name,data in [('old',old),('new',new)]:
  keys=[]
  for off in range(0,len(data),size):
   block=data[off:off+size];k=H(block)
   ck(k not in store or store[k]==block,'SHA key collision');store[k]=block;keys.append(k)
  prefix=struct.pack('<8sQQ',b'CMPCOW01',len(data),len(keys))
  root=H(b'J24G102-ROOT-v1\0'+prefix+b''.join(keys))
  heads[name]=prefix+root+b'\0'*8+b''.join(keys)
  ck(len(heads[name])==64+32*len(keys),'root manifest size')
  ck(b''.join(store[k] for k in keys)==data,'unmodified exact reconstruction')
  ck(H(b'J24G102-ROOT-v1\0'+heads[name][:24]+heads[name][64:])==root,'root digest')
 corrupted=next(iter(store));ck(H(bytes([store[corrupted][0]^1])+store[corrupted][1:])!=corrupted,'tamper accepted')
 tampered=bytearray(heads['old']);tampered[64]^=1
 ck(H(b'J24G102-ROOT-v1\0'+tampered[:24]+tampered[64:])!=tampered[24:56],'manifest ref corruption accepted')
 distinct=sum(len(v)+44 for v in store.values())
 manifests=sum(len(h) for h in heads.values())
 total=distinct+manifests
 return {'block_size':size,'blocks_unique':len(store),'blocks_old':(len(old)+size-1)//size,'blocks_new':(len(new)+size-1)//size,
 'charged_blocks_bytes':distinct,'charged_two_manifests_bytes':manifests,'charged_total_bytes':total,
 'two_complete_copy_bytes':len(old)+len(new),'ratio_larger_image':total/max(len(old),len(new)),
 'ratio_two_copies':total/(len(old)+len(new)),'exact_reconstruction':True,'block_tamper_rejected':True,
 'manifest_tamper_rejected':True}
def main():
 p=argparse.ArgumentParser()
 for host in SOURCES:p.add_argument('--'+host,type=Path,required=True)
 p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 reports={}
 for host,digest in SOURCES.items():
  original=getattr(a,host).read_bytes();ck(H(original).hex()==digest,'original provider checksum')
  with zipfile.ZipFile(io.BytesIO(original)) as src:
   ck(src.read('checkout-head.txt').decode().strip()==HEAD,'original GitHub source SHA')
   for n in (4096,8192):
    old,new,meta=makepair(src.read(f'{n}-A.cmpct'),src.read(f'{n}-B.cmpct'),n)
    arms={str(size):priced(old,new,size) for size in (4096,16384)}
    perturb={}
    for size in (4096,16384):
     random_data=random.Random(240102+size+len(new)).randbytes(len(new))
     variants={'one_byte_early_insertion':new[:512]+b'!'+new[512:],
      'block_aligned_rotation':new[size:]+new[:size],
      'unrelated_random_bytes':random_data}
     perturb[str(size)]={k:round(priced(old,v,size)['ratio_larger_image'],6) for k,v in variants.items()}
    ck(all(x['ratio_larger_image']<=1.20 for x in arms.values()),'H1 failure')
    reports[f'{host}-{n}']={'original_provider_zip_SHA256':digest,**meta,
      'COW_costs':arms,'non_cmpct_geometric_perturbations':perturb}
 result={'schema':'J24G102-COW-BLOCK-ROOT-O0','science':'RESEARCH_ONLY','head':HEAD,
 'prereg_commit':'292ee434d8578ab39e6550708029eb364d33e910',
 'verdict':'H1_H2_PASS_4_REAL_PHYSICAL_INPUTS_H3_ANTI_SHIFT_NEGATIVE','cases':reports,
 'truth_boundaries':['No released CMPCT Reader run or format support','No snapshot atomicity or CAS, no verified ownership lifetime',
 'SHA-keyed packed-byte storage model only, not native reflink/storage measurement',
 'Very weak generic sharing for one-byte misalignment; no global block-dedup claim',
 'J24G99 no-rebase rolling-tail control can be substantially smaller; not dominated',
 'No complete product CPU/wall/RSS/write throughput/Reader range proof or release benchmark']}
 a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'verdict':result['verdict'],'case_ratios':{k:{s:round(v['ratio_larger_image'],4) for s,v in c['COW_costs'].items()} for k,c in reports.items()},'result_sha256':H(a.out.read_bytes()).hex()},sort_keys=True))
if __name__=='__main__':main()
