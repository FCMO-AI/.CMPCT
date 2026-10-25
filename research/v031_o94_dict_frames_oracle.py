#!/usr/bin/env python3
"""O94 charged research oracle. NOT CMPCT product/format/equivalent integrity."""
import argparse,ctypes as C,ctypes.util,hashlib,json,platform,random,statistics,time
from pathlib import Path

class Zstd:
    def __init__(self):
        name=ctypes.util.find_library('zstd')
        if not name:raise RuntimeError('system libzstd unavailable')
        self.name=name;z=C.CDLL(name);sz=C.c_size_t;vp=C.c_void_p
        def f(n,ret,args):
            g=getattr(z,n);g.restype=ret;g.argtypes=args;return g
        self.version=f('ZSTD_versionString',C.c_char_p,[])
        self.bound=f('ZSTD_compressBound',sz,[sz]);self.iserr=f('ZSTD_isError',C.c_uint,[sz])
        self.errname=f('ZSTD_getErrorName',C.c_char_p,[sz])
        self.cctx=f('ZSTD_createCCtx',vp,[]);self.cf=f('ZSTD_freeCCtx',sz,[vp])
        self.dctx=f('ZSTD_createDCtx',vp,[]);self.df=f('ZSTD_freeDCtx',sz,[vp])
        self.compress=f('ZSTD_compressCCtx',sz,[vp,vp,sz,vp,sz,C.c_int])
        self.compress_dict=f('ZSTD_compress_usingDict',sz,[vp,vp,sz,vp,sz,vp,sz,C.c_int])
        self.decompress=f('ZSTD_decompressDCtx',sz,[vp,vp,sz,vp,sz])
        self.decompress_dict=f('ZSTD_decompress_usingDict',sz,[vp,vp,sz,vp,sz,vp,sz])
        self.train=f('ZDICT_trainFromBuffer',sz,[vp,sz,vp,C.POINTER(sz),C.c_uint])
        self.train_err=f('ZDICT_isError',C.c_uint,[sz])
    def chk(self,n):
        if self.iserr(n):raise RuntimeError(self.errname(n).decode())
        return n
    def encode(self,data,dictionary=b'',level=5):
        ctx=self.cctx()
        try:
            dst=C.create_string_buffer(self.bound(len(data)));src=C.create_string_buffer(data)
            if dictionary:
                d=C.create_string_buffer(dictionary)
                n=self.compress_dict(ctx,dst,len(dst),src,len(data),d,len(dictionary),level)
            else:n=self.compress(ctx,dst,len(dst),src,len(data),level)
            return dst.raw[:self.chk(n)]
        finally:self.cf(ctx)
    def decode(self,encoded,size,dictionary=b''):
        ctx=self.dctx()
        try:
            dst=C.create_string_buffer(size);src=C.create_string_buffer(encoded)
            if dictionary:
                d=C.create_string_buffer(dictionary)
                n=self.decompress_dict(ctx,dst,size,src,len(encoded),d,len(dictionary))
            else:n=self.decompress(ctx,dst,size,src,len(encoded))
            self.chk(n)
            if n!=size:raise AssertionError(f'wrong decoded size {n} != {size}')
            return dst.raw[:size]
        finally:self.df(ctx)
    def train_dictionary(self,files,max_bytes=8192):
        samples=b''.join(files);sizes=(C.c_size_t*len(files))(*map(len,files))
        dest=C.create_string_buffer(max_bytes);src=C.create_string_buffer(samples)
        t0=time.perf_counter_ns()
        n=self.train(dest,max_bytes,src,sizes,len(files));elapsed=time.perf_counter_ns()-t0
        if self.train_err(n):return b'',elapsed,self.errname(n).decode()
        return dest.raw[:n],elapsed,None

def corpus(which,seed=89741):
    rng=random.Random(seed);r=rng.randbytes
    if which=='template':
        prefixes=[r(448) for _ in range(8)]
        return [prefixes[i%8]+r(320) for i in range(256)]
    if which=='entropy':return [r(768) for _ in range(256)]
    if which=='holdout':
        prefixes=[r(1200) for _ in range(11)];arr=[]
        for i in range(256):
            size=rng.randrange(256,2300);pre=prefixes[(i*7)%11][:min(size//2,950)]
            arr.append(pre+r(size-len(pre)))
        rng.shuffle(arr);return arr
    raise ValueError(which)

def physical_size(frames,logical_n,dict_bytes=b''):
    # Charge every physical payload, 48-byte proof/index/offset/length per physical
    # owner, common 24-byte logical file table, plus one charged dictionary owner.
    return sum(map(len,frames))+48*len(frames)+24*logical_n+(48+len(dict_bytes) if dict_bytes else 0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='o94-local.json')
    ap.add_argument('--reps',type=int,default=7);args=ap.parse_args()
    z=Zstd();all_results=[]
    for regime in ['template','entropy','holdout']:
        files=corpus(regime);common=b''.join(files);offsets=[];cur=0
        for b in files:offsets.append(cur);cur+=len(b)
        hashes=[hashlib.sha256(b).hexdigest() for b in files]
        whole_sha=hashlib.sha256(common).hexdigest()
        dictionary,train_ns,train_error=z.train_dictionary(files)
        arms={
            'monolithic':{'dictionary':b'','owner_groups':[files]},
            'individual':{'dictionary':b'','owner_groups':[[f] for f in files]},
            'dictionary':{'dictionary':dictionary,'owner_groups':[[f] for f in files]},
            'groups16':{'dictionary':b'','owner_groups':[files[i:i+16] for i in range(0,len(files),16)]},
            'groups16_dict':{'dictionary':dictionary,'owner_groups':[files[i:i+16] for i in range(0,len(files),16)]}
        }
        if not dictionary:arms.pop('dictionary');arms.pop('groups16_dict')
        raw={k:[] for k in arms};order=list(arms)
        for iteration in range(args.reps+1):
            order=order[1:]+order[:1]
            for key in order:
                entry=arms[key];d=entry['dictionary'];srcs=[b''.join(g) for g in entry['owner_groups']]
                w0=time.perf_counter_ns();c0=time.process_time_ns()
                comp=[z.encode(s,d,level=5) for s in srcs]
                cpu=time.process_time_ns()-c0;wall=time.perf_counter_ns()-w0
                if iteration==0:continue
                decoded=[z.decode(comp[i],len(srcs[i]),d) for i in range(len(comp))]
                assert b''.join(decoded)==common
                assert hashlib.sha256(b''.join(decoded)).hexdigest()==whole_sha
                index=127;owner=0 if key=='monolithic' else (
                    index//16 if key.startswith('groups16') else index)
                cbytes=comp[owner];decoded_size=len(srcs[owner]);selection=[]
                for _ in range(7):
                    st=time.perf_counter_ns();ct=time.process_time_ns()
                    opened=z.decode(cbytes,decoded_size,d)
                    if key=='monolithic':
                        selected=opened[offsets[index]:offsets[index]+len(files[index])]
                    elif key.startswith('groups16'):
                        j=index%16
                        local_offset=sum(map(len,files[owner*16:owner*16+j]))
                        selected=opened[local_offset:local_offset+len(files[index])]
                    else:selected=opened
                    assert hashlib.sha256(selected).hexdigest()==hashes[index]
                    # This hashes the selected owner, NOT all unselected owners.
                    hashlib.sha256(opened).digest()
                    selection.append({'wall_ns':time.perf_counter_ns()-st,
                                      'cpu_ns':time.process_time_ns()-ct})
                raw[key].append({'iteration':iteration,'create_wall_ns':wall,
                    'create_cpu_ns':cpu,'full_bytes':physical_size(comp,len(files),d),
                    'compressed_payload_bytes':sum(map(len,comp)),
                    'physical_owners':len(comp),'dictionary_bytes':len(d),
                    'selected_member_bytes':len(files[index]),
                    'selected_decoded_owner_bytes':decoded_size,
                    'selected_compressed_owner_bytes':len(cbytes),'reads':selection})
        summary={}
        for key,obs in raw.items():
            o=obs[0]
            summary[key]={'full_bytes':o['full_bytes'],'physical_owners':o['physical_owners'],
                'dictionary_bytes':o['dictionary_bytes'],
                'create_wall_median_ns':statistics.median(y['create_wall_ns'] for y in obs),
                'create_cpu_median_ns':statistics.median(y['create_cpu_ns'] for y in obs),
                'selected_decode_unit':o['selected_decoded_owner_bytes'],
                'selected_wall_median_ns':statistics.median(r['wall_ns'] for y in obs for r in y['reads']),
                'selected_cpu_median_ns':statistics.median(r['cpu_ns'] for y in obs for r in y['reads'])}
        baseline=summary['monolithic']['full_bytes'];decision={}
        for k,v in summary.items():
            decision[k]={'charged_bytes_over_monolithic_pct':round(100*(v['full_bytes']/baseline-1),2),
                'selected_decoded_work_ratio':round(summary['monolithic']['selected_decode_unit']/v['selected_decode_unit'],2)}
        verdict='H1_FALSIFIED_OR_NARROWED'
        if ('dictionary' in summary and
            decision['dictionary']['charged_bytes_over_monolithic_pct']<=5 and
            decision['dictionary']['selected_decoded_work_ratio']>=10):
            verdict='H1_SURVIVES_RESEARCH_TRIAGE'
        all_results.append({'regime':regime,'source_sha256':whole_sha,'logical_files':len(files),
            'logical_bytes':len(common),'train_wall_ns':train_ns,'train_error':train_error,
            'index_metadata_charge_per_file':24,'physical_owner_charge_bytes':48,
            'raw':raw,'summary':summary,'decision':decision,'verdict':verdict})
        print(regime,json.dumps({'summary':summary,'decision':decision,'verdict':verdict}),flush=True)
    out={'schema':'cmpct-o94-dict-framed-oracle-v1','platform':platform.platform(),
        'python':platform.python_version(),'libzstd':z.name,
        'libzstd_version':z.version().decode(),'level':5,'repetitions':args.reps,
        'source':'O94 prereg a265272c4ac4d9a9f4dcc1c80607e7dd7f1ac470',
        'semantics':'research only; selected-owner SHA does NOT authenticate unselected physical owners',
        'corpora':all_results}
    Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
    return out
if __name__=='__main__':main()
