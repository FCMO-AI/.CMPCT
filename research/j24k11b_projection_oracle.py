#!/usr/bin/env python3
"""J24K11b — charge fresh Python projection from VZIP recipe to native tuples.

Pre-registered in docs/v031-research/2026-10-28-j24k11b-projection-bridge-prereg.md.
Component-tier ONLY: r24 BHDR wire grammar, modeled signed payloads, no CMPCT Reader.
"""
import hashlib, json, os, random, statistics, sys, time
from pathlib import Path
import j24k11_bhdr_oracle as base

def model(n,mode,layout):
    wire,rows=base.fixture(n,mode)
    blobs=[tuple(r[:5]) for r in rows]
    order=list(range(n))
    if layout=='permuted':random.Random(91043+n+mode).shuffle(order)
    payloads=[]
    for i in order:
        expected=rows[i][5]
        if mode==0:payloads.append((i,0,0,-1,expected,0))
        elif mode==1:payloads.append((i,8,0,i,expected,0))
        else:payloads.append((i,8,1,i,expected,0))
    return wire,blobs,payloads

def project(blobs,payloads):
    rows=[]
    for rawref,method,stream_mode,streamref,csize,level in payloads:
        if method!=0 and (method!=8 or stream_mode not in (0,1)):raise IOError('unsupported VZIP physical mode')
        idx=rawref if method==0 else streamref
        if type(idx) is not int or idx<0 or idx>=len(blobs):raise IOError('invalid physical owner index type/bounds')
        if type(csize) is not int or csize<0:raise IOError('invalid signed VZIP csize')
        off,us,cs,codec,ml=blobs[idx]
        compressed=int(method==8 and stream_mode==0)
        rows.append((off,us,cs,codec,ml,csize,compressed))
    return rows

def direct(wire,blobs,payloads):
    # Strong comparator consumes real r24-shaped signed descriptors directly.
    for rawref,method,stream_mode,streamref,csize,level in payloads:
        if method!=0 and (method!=8 or stream_mode not in (0,1)):raise IOError('unsupported VZIP physical mode')
        idx=rawref if method==0 else streamref
        if type(idx) is not int or idx<0 or idx>=len(blobs):raise IOError('bad owner index')
        off,us,cs,codec,ml=blobs[idx]
        if not all(type(v) is int and v>=0 for v in (off,us,cs,codec,ml,csize)):
            raise IOError('invalid signed fields')
        compressed=(method==8 and stream_mode==0)
        pos=off
        if pos+base.BHDR.size>len(wire):raise IOError('bad header bounds')
        m,c,flags,res,rus,rcs,rml,crc,digest=base.BHDR.unpack_from(wire,pos)
        if (m!=b'CMA4' or c!=codec or flags or res or rus!=us or rcs!=cs
                or rml!=ml or pos+base.BHDR.size+rml+rcs>len(wire)):
            raise IOError('physical owner mismatch')
        if compressed and codec!=base.DEFLATE:raise IOError('wrong canonical codec')
        if csize!=(rcs if compressed else rus):raise IOError('signed coordinate mismatch')
    return True

def run(wire,blobs,payloads,native,mode):
    if mode=='direct':return direct(wire,blobs,payloads)
    rows=project(blobs,payloads)
    if mode=='projected_python':return base.python_exact(wire,rows)
    if mode=='projected_native':return bool(native.scan(wire,rows,0))
    raise ValueError(mode)

def measurements(wire,blobs,payloads,native):
    methods=('direct','projected_python','projected_native')
    raw={label:[] for label in methods}
    for repeat in range(12):
        # Balanced reversal plus rotate to avoid fixed initial position effects.
        order=methods if repeat%2==0 else tuple(reversed(methods))
        for label in order:
            wall=time.perf_counter_ns();cpu=time.process_time_ns()
            for _ in range(3):assert run(wire,blobs,payloads,native,label)
            raw[label].append({'wall_ns':(time.perf_counter_ns()-wall)//3,
                               'cpu_ns':(time.process_time_ns()-cpu)//3})
    med={label:{k:statistics.median(x[k] for x in series) for k in ('wall_ns','cpu_ns')}
         for label,series in raw.items()}
    return raw,med

def hostile(wire,blobs,payloads,native):
    mid=len(payloads)//2
    cases=[]
    bad=list(payloads);bad[mid]=(*bad[mid][:4],bad[mid][4]+1,bad[mid][5])
    cases.append(('signed_size_plus',wire,blobs,bad))
    bad=list(payloads);bad[mid]=(*bad[mid][:4],max(0,bad[mid][4]-1),bad[mid][5])
    cases.append(('signed_size_minus',wire,blobs,bad))
    item=payloads[mid];idx=item[0] if item[1]==0 else item[3]
    buf=bytearray(wire);buf[blobs[idx][0]+5]=1
    cases.append(('physical_flags',bytes(buf),blobs,payloads))
    results=[]
    for name,w,b,p in cases:
        ok=[]
        for strategy in ('direct','projected_python','projected_native'):
            try:accepted=bool(run(w,b,p,native,strategy))
            except (TypeError,ValueError,OverflowError,OSError):accepted=False
            ok.append(accepted)
        assert ok==[False,False,False],(name,ok)
        results.append({'name':name,'accepted':ok})
    return results

def strict_ref_hostile(wire,blobs,payloads,native):
    """New post-falsification transfer, separately counted from frozen original 54."""
    mid=len(payloads)//2
    raw=list(payloads[mid])
    cases=[]
    def bad(name,field,value):
        altered=list(payloads);row=list(raw);row[field]=value;altered[mid]=tuple(row)
        cases.append((name,altered))
    indexfield=0 if raw[1]==0 else 3
    bad('boolean_owner',indexfield,True)
    bad('subclass_owner',indexfield,type('SurrogateInt',(int,),{})(1))
    bad('negative_owner',indexfield,-1)
    bad('outside_owner',indexfield,len(blobs))
    bad('unsupported_method',1,13)
    bad('unsupported_stream_mode',2,2) if raw[1]==8 else bad('boolean_signed_csize',4,True)
    results=[]
    for name,modified in cases:
        verdict=[]
        for strategy in ('direct','projected_python','projected_native'):
            try:accepted=bool(run(wire,blobs,modified,native,strategy))
            except (TypeError,ValueError,OverflowError,OSError,IndexError):accepted=False
            verdict.append(accepted)
        assert verdict==[False,False,False],(name,verdict)
        results.append({'name':name,'accepted':verdict})
    return results

def main():
    native,tmp,build_ns=base.install_native()
    cells=[]
    for n in (64,512,4096):
        for mode in (0,1,2):
            for layout in ('sequential','permuted'):
                wire,blobs,payloads=model(n,mode,layout)
                assert all(run(wire,blobs,payloads,native,s) for s in ('direct','projected_python','projected_native'))
                tests=hostile(wire,blobs,payloads,native)
                typed_tests=strict_ref_hostile(wire,blobs,payloads,native)
                raw,med=measurements(wire,blobs,payloads,native)
                projected=project(blobs,payloads)
                import sys
                projected_bytes=sys.getsizeof(projected)+sum(sys.getsizeof(row) for row in projected)
                speedup={key:med['direct'][key]/med['projected_native'][key] for key in ('wall_ns','cpu_ns')}
                row={'n':n,'mode':mode,'layout':layout,'source_sha256':hashlib.sha256(wire).hexdigest(),
                     'descriptor_count':len(blobs),'payload_count':len(payloads),
                     'raw':raw,'median':med,'speedup_over_direct':speedup,'hostile':tests,'strict_ref_hostile':typed_tests,
                     'fresh_projected_python_heap_bytes':projected_bytes,
                     'class':'component_projection_model_not_product'}
                cells.append(row)
                print('J24K11B_CELL='+json.dumps({k:v for k,v in row.items() if k!='raw'},sort_keys=True),flush=True)
    decisive=[c for c in cells if c['n']==4096]
    min_speedup=min(c['speedup_over_direct'][k] for c in decisive for k in ('wall_ns','cpu_ns'))
    result={'schema':'j24k11b-projection-v1','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'c_scanner_sha256':hashlib.sha256(base.C_SOURCE.encode()).hexdigest(),
            'native_build_ns':build_ns,'observations':sum(len(s) for c in cells for s in c['raw'].values()),
            'hostile_cases':sum(len(c['hostile']) for c in cells),'strict_ref_hostile_cases':sum(len(c['strict_ref_hostile']) for c in cells),'cells':cells,
            'min_4096_speedup':min_speedup,
            'decision':'PROJECTION_BRIDGE_HEADROOM' if min_speedup>=1.5 else 'PROJECTION_BRIDGE_HEADROOM_NOT_PROVEN',
            'class':'scientific_component_not_product'}
    out=Path(os.environ.get('J24K11B_OUT','j24k11b_results.json'))
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('J24K11B_RESULT='+json.dumps({k:v for k,v in result.items() if k!='cells'},sort_keys=True),flush=True)

if __name__=='__main__':main()
