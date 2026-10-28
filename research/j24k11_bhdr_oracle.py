#!/usr/bin/env python3
"""J24K11: preregistered, no-product native BHDR batch oracle.

COMPONENT RESEARCH ONLY: same authenticated descriptor and contiguous physical
bytes modeled from the r24 Reader. No claim of full Reader or release parity.
"""
from __future__ import annotations
import hashlib, importlib, json, os, random, statistics, struct, subprocess, sys, tempfile, time
from pathlib import Path

BHDR = struct.Struct('<4sBBHQQII32s')
RAW, DEFLATE = 0, 4
C_SOURCE = r'''
#define PY_SSIZE_T_CLEAN
#define Py_LIMITED_API 0x030B0000
#include <Python.h>
#include <stdint.h>
#include <string.h>

static uint64_t get64(const unsigned char *p) {
    uint64_t out=0; for(unsigned k=0;k<8;k++)out|=((uint64_t)p[k])<<(8*k); return out;
}
static uint32_t get32(const unsigned char *p) {
    uint32_t out=0; for(unsigned k=0;k<4;k++)out|=((uint32_t)p[k])<<(8*k); return out;
}
static uint64_t get16(const unsigned char *p) {
    return (uint64_t)p[0] | ((uint64_t)p[1]<<8);
}
static int scalar_u64(PyObject *o,uint64_t *out) {
    /* Fast path rejects bool, int subclasses and non-int. Any unsupported
       object is delegated to the unchanged Python validator in a product. */
    if (!PyLong_CheckExact(o))return 0;
    unsigned long long v=PyLong_AsUnsignedLongLong(o);
    if(PyErr_Occurred()){PyErr_Clear();return 0;}
    *out=(uint64_t)v;return 1;
}
static PyObject* scan(PyObject *self,PyObject *args) {
    PyObject *wire=NULL,*rows=NULL,*base_obj=NULL;
    Py_buffer view;
    uint64_t base=0;
    if(!PyArg_ParseTuple(args,"OOO",&wire,&rows,&base_obj))return NULL;
    if(!scalar_u64(base_obj,&base))Py_RETURN_FALSE;
    if(!PyList_CheckExact(rows))Py_RETURN_FALSE;
    if(PyObject_GetBuffer(wire,&view,PyBUF_SIMPLE)!=0)return NULL;
    int ok=1;
    const unsigned char *data=(const unsigned char*)view.buf;
    const uint64_t limit=(uint64_t)view.len;
    Py_ssize_t n=PyList_Size(rows);
    if(n<0){PyErr_Clear();ok=0;goto done;}
    for(Py_ssize_t i=0;i<n;i++){
        PyObject *r=PyList_GetItem(rows,i);
        if(!r||!PyTuple_CheckExact(r)||PyTuple_Size(r)!=7){ok=0;goto done;}
        uint64_t v[7];
        for(int k=0;k<7;k++){
            PyObject *item=PyTuple_GetItem(r,k);
            if(!item||!scalar_u64(item,&v[k])){ok=0;goto done;}
        }
        /* row: off, usize, csize, codec, metadata len, expected stream, is_deflate_mode0 */
        const uint64_t off=v[0],us=v[1],cs=v[2],codec=v[3],ml=v[4],expected=v[5],compressed=v[6];
        if(codec>255||ml>UINT32_MAX||compressed>1||off>UINT64_MAX-base){ok=0;goto done;}
        const uint64_t pos=base+off;
        if(pos>limit||limit-pos<64){ok=0;goto done;}
        const unsigned char *h=data+pos;
        if(memcmp(h,"CMA4",4)!=0||h[4]!=(unsigned char)codec||h[5]!=0||get16(h+6)!=0){ok=0;goto done;}
        uint64_t rus=get64(h+8),rcs=get64(h+16);uint32_t rml=get32(h+24);
        if(rus!=us||rcs!=cs||rml!=ml){ok=0;goto done;}
        if(ml>limit-pos-64||rcs>limit-pos-64-ml){ok=0;goto done;}
        if(compressed&&codec!=4){ok=0;goto done;}
        if(expected!=(compressed?rcs:rus)){ok=0;goto done;}
    }
done:
    PyBuffer_Release(&view);
    if(!ok)Py_RETURN_FALSE;
    Py_RETURN_TRUE;
}
static PyMethodDef methods[]={
    {"scan",scan,METH_VARARGS,"Check multiple signed physical BHDR witnesses"},
    {NULL,NULL,0,NULL}
};
static struct PyModuleDef module={PyModuleDef_HEAD_INIT,"j24k11_native",NULL,-1,methods};
PyMODINIT_FUNC PyInit_j24k11_native(void){return PyModule_Create(&module);}
'''

def install_native():
    tmp=Path(tempfile.mkdtemp(prefix='j24k11-build-'))
    (tmp/'j24k11_native.c').write_text(C_SOURCE)
    (tmp/'setup.py').write_text('from setuptools import setup,Extension\nsetup(name="j24k11_native",version="0.0",ext_modules=[Extension("j24k11_native",["j24k11_native.c"],py_limited_api=True,define_macros=[("Py_LIMITED_API","0x030B0000")])])\n')
    start=time.perf_counter_ns()
    p=subprocess.run([sys.executable,'setup.py','build_ext','--inplace'],cwd=tmp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if p.returncode:
        raise RuntimeError('native compiler failed: '+p.stdout[-5000:])
    build_ns=time.perf_counter_ns()-start
    sys.path.insert(0,str(tmp))
    return importlib.import_module('j24k11_native'),tmp,build_ns

def python_exact(wire,rows,base=0):
    """Strong simple Python loop equivalent to J24K09 signed/physical geometry checks."""
    for off,us,cs,codec,ml,expected,compressed in rows:
        if not all(type(x) is int and x>=0 for x in (off,us,cs,codec,ml,expected,compressed)):
            raise IOError('invalid signed descriptor type')
        if compressed not in (0,1):raise IOError('invalid mode')
        pos=base+off
        if pos<base or pos+BHDR.size>len(wire):raise IOError('physical header out of bounds')
        m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(wire,pos)
        if m!=b'CMA4' or c!=codec or flags or res or rus!=us or rcs!=cs or rml!=ml or pos+BHDR.size+rml+rcs>len(wire):
            raise IOError('physical owner/header mismatch')
        if compressed and codec!=DEFLATE:raise IOError('canonical Deflate codec mismatch')
        if expected!=(rcs if compressed else rus):raise IOError('VZIP stream coordinate mismatch')
    return True

def python_indirect(wire,rows,base=0):
    # Models the inherited Reader's per-stream method-call overhead with a strong
    # and fully checked validation, not an intentionally weakened baseline.
    for r in rows:
        python_exact(wire,[r],base)
    return True

def fixture(n, mode, seed=411):
    rng=random.Random(seed+n+mode)
    records=[]; rows=[];offset=0
    for i in range(n):
        # Genuine 64-byte r24 BHDR layout, synthetically modeled payload and signed row.
        us=1+(i*13)%31; ml=(i%3)
        if mode==0:codec=RAW;cs=us
        elif mode==1:codec=DEFLATE;cs=3+(i%11)
        else:codec=1;cs=3+(i%11) # opaque retained stream encoded as Zstd physical blob
        blob=bytes(rng.getrandbits(8) for _ in range(cs))
        data=bytes(rng.getrandbits(8) for _ in range(ml))
        digest=hashlib.sha256(blob).digest()
        header=BHDR.pack(b'CMA4',codec,0,0,us,cs,ml,0,digest)
        records.append(header+data+blob)
        compressed=int(mode==1)
        rows.append((offset,us,cs,codec,ml,cs if compressed else us,compressed))
        offset+=len(records[-1])
    return b''.join(records),rows

def negative_cases(wire,rows):
    """Adversarial controls: each mutates one signed or physical field."""
    out={}
    center=len(rows)//2
    def mutate(name,row=None,buf=None):
        v=list(rows);v[center]=tuple(row if row is not None else v[center]);out[name]=(bytes(buf) if buf is not None else wire,v)
    base=list(rows[center]);
    for name,k,val in [('expected_plus',5,base[5]+1),('expected_minus',5,max(0,base[5]-1)),('descriptor_usize',1,base[1]+1),('descriptor_csize',2,base[2]+1),('descriptor_codec',3,base[3]+1),('descriptor_meta',4,base[4]+1),('offset_escape',0,len(wire)+1),('negative_off',0,-1),('boolean_size',1,True),('float_csize',2,float(base[2])),('subclass_csize',2,type('FancyInt',(int,),{})(base[2])),('mode_overflow',6,2)]:
        r=list(base);r[k]=val;mutate(name,r)
    for name,start,payload in [('physical_magic',0,b'BOOM'),('physical_flags',5,b'\x01'),('physical_reserved',6,b'\x01'),('physical_usize',8,struct.pack('<Q',base[1]+1)),('physical_csize',16,struct.pack('<Q',base[2]+1)),('physical_meta',24,struct.pack('<I',base[4]+1))]:
        b=bytearray(wire);at=base[0]+start;b[at:at+len(payload)]=payload;mutate(name,buf=b)
    mutate('truncated_source',buf=wire[:base[0]+60]) # later valid rows would also be unreachable
    out['empty']=(wire,[])
    return out

def measure(fn,wire,rows,rounds=12,iterations=3):
    observations=[]
    for _ in range(rounds):
        s=time.perf_counter_ns();c=time.process_time_ns()
        for _ in range(iterations):assert fn(wire,rows,0)
        observations.append({'wall_ns':(time.perf_counter_ns()-s)//iterations,'cpu_ns':(time.process_time_ns()-c)//iterations})
    return observations

def main():
    native,tmp,build_ns=install_native()
    raw=[];checks=[]
    sha=hashlib.sha256(C_SOURCE.encode()).hexdigest()
    for n in (64,512,4096):
        for mode in (0,1,2):
            wire,rows=fixture(n,mode)
            assert python_exact(wire,rows)
            assert python_indirect(wire,rows)
            assert native.scan(wire,rows,0)
            if n in (64,4096):
                for tag,(badwire,badrows) in negative_cases(wire,rows).items():
                    py_ok=True
                    try:python_exact(badwire,badrows)
                    except (ValueError,TypeError,OSError,OverflowError,struct.error):py_ok=False
                    native_ok=bool(native.scan(badwire,badrows,0))
                    assert native_ok==py_ok,(n,mode,tag,py_ok,native_ok)
                    checks.append((n,mode,tag,py_ok))
            # ABBA balanced across 12 rounds, all marshaling is included inside fn.
            fns={'method_python':python_indirect,'loop_python':python_exact,'native_batch':native.scan}
            samples={key:[] for key in fns}
            for j in range(12):
                order=['method_python','loop_python','native_batch'] if j%2==0 else ['native_batch','loop_python','method_python']
                for label in order:samples[label]+=measure(fns[label],wire,rows,rounds=1,iterations=3)
            med={label:{k:statistics.median(s[k] for s in series) for k in ('wall_ns','cpu_ns')} for label,series in samples.items()}
            speed={label:{k:med[label][k]/med['native_batch'][k] for k in ('wall_ns','cpu_ns')} for label in ('method_python','loop_python')}
            entry={'streams':n,'mode':mode,'bytes':len(wire),'source_sha256':hashlib.sha256(wire).hexdigest(), 'native_source_sha256':sha,'build_ns':build_ns,'compiled_bytes':sum(p.stat().st_size for p in tmp.glob('j24k11_native*.so')),'raw':samples,'median':med,'speedup':speed,'class':'component_oracle_no_product_credit'}
            raw.append(entry)
            print('J24K11_CELL='+json.dumps({k:v for k,v in entry.items() if k!='raw'},sort_keys=True),flush=True)
    out={'schema':'j24k11-science-v1','kind':'component_oracle_not_product','python':sys.version,'platform':sys.platform,'native_source_sha256':sha,'sample_count':sum(len(a) for r in raw for a in r['raw'].values()),'negative_cases':checks,'native_build_ns':build_ns,'cells':raw}
    # Save original unfiltered samples and negative cases for independent referee.
    path=Path(os.environ.get('J24K11_OUT','j24k11_results.json'))
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    decisive=[r for r in raw if r['streams']==4096]
    positive=all(all(r['speedup'][ctl][k]>=1.5 for ctl in ('method_python','loop_python') for k in ('wall_ns','cpu_ns')) for r in decisive)
    print('J24K11_RESULT='+json.dumps({'decision':'NATIVE_BATCH_MECHANISM_HEADROOM' if positive else 'NATIVE_BATCH_NOT_PROVEN','samples':out['sample_count'],'negative_cells':len(checks),'valid_negative_rejections':sum(not z[-1] for z in checks),'raw_path':str(path),'compiled_bytes':raw[0]['compiled_bytes'],'native_build_ns':build_ns},sort_keys=True),flush=True)

if __name__=='__main__':main()
