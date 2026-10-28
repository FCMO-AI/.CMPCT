#!/usr/bin/env python3
"""J24G17 independent post-result differential stress (research only).

This test cannot turn a structural C scanner into a semantic MessagePack
acceptance oracle; direct msgpack.unpackb remains final semantic authority.
"""
from __future__ import annotations
import ctypes, hashlib, json, random, sys
from pathlib import Path
import msgpack

BASE=Path(__file__).resolve().parent
SRC=BASE/"j24g17_msgpack_token_counter.c"
SO=BASE/"j24g17_token_counter.so"
LIMIT=65536
lib=ctypes.CDLL(str(SO))
scan=lib.mp_count_tokens
scan.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.c_uint64,ctypes.POINTER(ctypes.c_uint64)]
scan.restype=ctypes.c_int

def decoded_nodes(v):
    if isinstance(v,dict):
        return 1+sum(decoded_nodes(k)+decoded_nodes(x) for k,x in v.items())
    if isinstance(v,(list,tuple)) and not isinstance(v,msgpack.ExtType):
        return 1+sum(decoded_nodes(x) for x in v)
    return 1

def native(b):
    n=ctypes.c_uint64()
    return scan(b,len(b),LIMIT,ctypes.byref(n)),n.value

def run():
    rng=random.Random(7321052)
    sizes=(0,1,2,15,16,30,31,32,63,127,128,255,256,1000,65534,65535)
    values=[b'a'*n for n in sizes]
    values+=['é'*n for n in (0,1,30,31,32,100,1000,65535)]
    values += [msgpack.ExtType(1,b'Z'*n) for n in (0,1,2,4,8,16,31,32,255,256,1000)]
    values += [None,True,False,0,127,128,-32,-33,2**64-1,-2**63,1.0]
    for n in (0,1,2,15,16,31,32,127,128,255,256,1000,20000,65534,65535):
        values.append([None]*n)
    for n in (0,1,2,15,16,31,32,100,1000,32000):
        values.append({f'x{i}':None for i in range(n)})
    small=values[:50]
    def random_value(depth=0):
        if depth>=3 or rng.random()<.4: return rng.choice(small)
        if rng.randrange(4)==0:
            return [random_value(depth+1) for _ in range(rng.randrange(8))]
        if rng.randrange(4)==1:
            return {f'k{i}':random_value(depth+1) for i in range(rng.randrange(7))}
        return rng.choice(small)
    values += [random_value() for _ in range(2500)]
    under=over=mutations=semantically_invalid_structurally_counted=0
    failures=[]
    for value in values:
        packed=msgpack.packb(value,use_bin_type=True)
        result,count=native(packed)
        exact=decoded_nodes(value)
        if exact<=LIMIT:
            under+=1
            if result!=1 or count!=exact: failures.append(("valid_under_cap",len(packed),exact,result,count))
        else:
            over+=1
            if result!=0: failures.append(("valid_over_cap",len(packed),exact,result,count))
        for j in range(1 if len(packed)>10000 else 3):
            b=bytearray(packed)
            mode=rng.randrange(4)
            if mode==0:b[rng.randrange(len(b))]=rng.randrange(256)
            elif mode==1:b=b[:rng.randrange(len(b))]
            elif mode==2:b.append(rng.randrange(256))
            else:b[0]=0xc1
            modified=bytes(b)
            status,_=native(modified)
            try: obj=msgpack.unpackb(modified,raw=False)
            except Exception:
                if status==1:semantically_invalid_structurally_counted+=1
            else:
                nodes=decoded_nodes(obj)
                expected=1 if nodes<=LIMIT else 0
                if status!=expected:failures.append(("false_refusal_mutation",len(modified),nodes,status))
            mutations+=1
        if len(failures)>=10:break
    result={"schema":"cmpct-j24g17-independent-wire-stress-v1",
            "stage":"post-result differential stress, not prospectively preregistered",
            "seed":7321052,
            "msgpack":msgpack.__version__,
            "c_source_sha256":hashlib.sha256(SRC.read_bytes()).hexdigest(),
            "under_cap_valid":under,"over_cap_valid":over,
            "mutated_wire_cases":mutations,
            "syntactically_counted_but_semantically_invalid":semantically_invalid_structurally_counted,
            "failures":failures,
            "no_product_acceptance_credit":True}
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
    if failures:raise SystemExit(1)
if __name__=="__main__":run()
