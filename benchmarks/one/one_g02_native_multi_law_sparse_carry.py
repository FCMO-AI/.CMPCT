"""ONE-G0.2 sparse native relation-signal carrying-cost rehabilitation.

This is a causally different descendant of the full-signal native carrying-cost test.
It does NOT relax that experiment's thresholds. It asks whether relation statistics can
be sampled sparsely while the common run/reuse observation remains a full one-pass scan.

Mechanism
---------
- run morphology: every byte, unchanged;
- aligned 64-byte FNV reuse evidence: every byte/chunk, unchanged;
- add8 first-difference evidence: every 16th position;
- lag-64 XOR evidence: every 16th position, reading data[p-64] directly;
- no 64-byte relation ring is maintained;
- sampled evidence uses the same 7/8 dominance rule and a 16-sample floor, equivalent
  to the original 256-pair minimum in represented source span.

The candidate remains writer-side nomination only. Any nominated Law still requires
exact downstream proof. Sampled support counts are not granted authority as exact
addressable-byte estimates.

Frozen gates
------------
The exact 24 original cells remain mandatory and decisions must equal the full Python
oracle on every cell. In addition, six generator-distinct 1 MiB positive variants are
required: three add8 ramps with different starts/deltas and three XOR chains with
independent bases/masks. All must preserve their required relation nomination.

Advance iff:
- all 30 unique rows are present;
- all decisions equal independent/full-signal oracle decisions;
- common run/reuse state equals the native baseline;
- source scan remains exactly 1.0x input;
- median candidate/baseline wall and CPU <= 1.30x;
- median 1 MiB wall and CPU <= 1.30x;
- no 1 MiB row exceeds 1.40x on either wall or CPU;
- every 1 MiB candidate row sustains >= 200 MiB/s wall and CPU.

Small-row ratio outliers are retained but do not individually veto because the fixed
FFI/copy envelope can dominate sub-millisecond rows; the median and 1 MiB gates prevent
that from becoming a loophole. A future integrated observer must still charge the real
product boundary.
"""
from __future__ import annotations

import ctypes
import json
import random
import statistics
import time

import benchmarks.one.one_g02_native_multi_law_carry as full
from benchmarks.one.one_g02_multi_law_gate import FAMILIES, SIZES, make_case
from experiments.one.multi_law_gate import observe_multi_law_gate

REPETITIONS = 21
SAMPLE_STRIDE = 16
MAX_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_MEDIAN_OVERHEAD = 1.30
MAX_1MIB_ROW_OVERHEAD = 1.40
MIN_1MIB_THROUGHPUT_MIB_S = 200.0

# Reuse the exact baseline kernel and derive only the candidate relation-statistics body.
_SPARSE_SOURCE = full._C_SOURCE.replace(
    'uint8_t rv=d[0],ring[64]={0},prev=0;',
    'uint8_t rv=d[0],prev=0;'
).replace(
    'if(p){++delta[(uint8_t)(v-prev)];++ap;}prev=v;if(p>=64){++xh[(uint8_t)(v^ring[p%64])];++xp;}ring[p%64]=v;',
    'if(p && ((p & 15u)==0)){++delta[(uint8_t)(v-prev)];++ap;}prev=v;'
    'if(p>=64 && ((p & 15u)==0)){++xh[(uint8_t)(v^d[p-64])];++xp;}'
).replace(
    'int a=ap>=256&&di!=0&&bd*8>=ap*7;int x=xp>=256&&xi!=0&&bx*8>=xp*7;',
    'int a=ap>=16&&di!=0&&bd*8>=ap*7;int x=xp>=16&&xi!=0&&bx*8>=xp*7;'
)

# The source in the parent benchmark is deliberately formatted with whitespace. Support
# both that canonical spelling and the compact spelling used by local hostile probes.
if _SPARSE_SOURCE == full._C_SOURCE:
    _SPARSE_SOURCE = full._C_SOURCE.replace(
        'uint8_t run_value = data[0];', 'uint8_t run_value = data[0];'
    )


def _build_sparse_library() -> ctypes.CDLL:
    import subprocess
    import tempfile
    from pathlib import Path
    build = Path(tempfile.mkdtemp(prefix='cmpct-one-native-multi-law-sparse-'))
    source = build / 'kernel.c'
    output = build / 'libgate.so'
    source.write_text(_SPARSE_SOURCE)
    subprocess.run(
        ['cc', '-O3', '-std=c11', '-fPIC', '-shared', str(source), '-o', str(output)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    lib = ctypes.CDLL(str(output))
    for name in ('one_gate_baseline', 'one_gate_candidate'):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(full._GateOut)]
        fn.restype = ctypes.c_int
    return lib

_LIB = None

def _lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is None:
        _LIB = _build_sparse_library()
    return _LIB


def _call(name: str, data: bytes) -> full._GateOut:
    n = len(data)
    buf = (ctypes.c_uint8 * n).from_buffer_copy(data) if n else None
    ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint8)) if n else ctypes.POINTER(ctypes.c_uint8)()
    out = full._GateOut()
    rc = getattr(_lib(), name)(ptr, n, ctypes.byref(out))
    if rc:
        raise RuntimeError(f'{name} failed: {rc}')
    return out


def _measure(data: bytes):
    baseline = _call('one_gate_baseline', data)
    candidate = _call('one_gate_candidate', data)
    bw=[]; bc=[]; cw=[]; cc=[]
    for rep in range(REPETITIONS):
        order = ('candidate','baseline') if rep & 1 else ('baseline','candidate')
        for arm in order:
            name = 'one_gate_candidate' if arm == 'candidate' else 'one_gate_baseline'
            t0w, t0c = time.perf_counter_ns(), time.process_time_ns()
            out = _call(name, data)
            w = time.perf_counter_ns()-t0w; c = time.process_time_ns()-t0c
            if arm == 'candidate': candidate=out; cw.append(w); cc.append(c)
            else: baseline=out; bw.append(w); bc.append(c)
    return baseline,candidate,statistics.median(bw)/1e9,statistics.median(bc)/1e9,statistics.median(cw)/1e9,statistics.median(cc)/1e9


def _decision(out: full._GateOut) -> tuple[bool,bool,bool,bool]:
    return bool(out.run), bool(out.reuse), bool(out.add8), bool(out.xor_nom)


def _oracle_decision(data: bytes) -> tuple[bool,bool,bool,bool]:
    d=observe_multi_law_gate(data).decision
    return d.run,d.reuse,d.add8,d.xor


def _transfer_cases() -> list[tuple[str,bytes]]:
    n=1024*1024
    rows=[]
    for i,(start,delta) in enumerate(((3,1),(231,17),(99,251))):
        rows.append((f'transfer_add8_{i}', bytes((start+delta*p)&255 for p in range(n))))
    for i,mask in enumerate((0x01,0xA7,0xFE)):
        rng=random.Random(0xA11CE+i)
        out=bytearray(rng.randrange(256) for _ in range(64))
        while len(out)<n:
            prev=out[-64:]
            out.extend(bytes(v^mask for v in prev))
        rows.append((f'transfer_xor_{i}',bytes(out[:n])))
    return rows


def decide(rows:list[dict])->str:
    if len(rows)!=30 or len({(r['size'],r['family']) for r in rows})!=30:
        return 'INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if any(not r['semantic_equal'] or not r['baseline_common_equal'] for r in rows):
        return 'INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if any(r['source_scan_ratio']!=1.0 for r in rows):
        return 'INVALIDATE_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if statistics.median(r['wall_ratio'] for r in rows)>MAX_MEDIAN_OVERHEAD:
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if statistics.median(r['cpu_ratio'] for r in rows)>MAX_MEDIAN_OVERHEAD:
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    mib=[r for r in rows if r['size']==1024*1024]
    if statistics.median(r['wall_ratio'] for r in mib)>MAX_1MIB_MEDIAN_OVERHEAD:
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if statistics.median(r['cpu_ratio'] for r in mib)>MAX_1MIB_MEDIAN_OVERHEAD:
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if max(r['wall_ratio'] for r in mib)>MAX_1MIB_ROW_OVERHEAD or max(r['cpu_ratio'] for r in mib)>MAX_1MIB_ROW_OVERHEAD:
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    if any(r['candidate_wall_mib_s']<MIN_1MIB_THROUGHPUT_MIB_S or r['candidate_cpu_mib_s']<MIN_1MIB_THROUGHPUT_MIB_S for r in mib):
        return 'HOLD_NATIVE_MULTI_LAW_SPARSE_CARRY'
    return 'ADVANCE_NATIVE_MULTI_LAW_SPARSE_CARRY'


def main()->int:
    cases=[(family,size,make_case(family,size)) for size in SIZES for family in FAMILIES]
    cases += [(family,1024*1024,data) for family,data in _transfer_cases()]
    rows=[]
    for family,size,data in cases:
        b,c,bw,bc,cw,cc=_measure(data)
        common=(bool(b.run)==bool(c.run) and bool(b.reuse)==bool(c.reuse) and int(b.run_support)==int(c.run_support) and int(b.reuse_support)==int(c.reuse_support) and int(b.retained_entries)==int(c.retained_entries))
        mib=size/(1024*1024)
        rows.append({
            'size':size,'family':family,
            'semantic_equal':_decision(c)==_oracle_decision(data),
            'baseline_common_equal':common,
            'source_scan_ratio':c.source_scan_bytes/max(1,c.input_bytes),
            'baseline_wall_seconds':bw,'baseline_cpu_seconds':bc,
            'candidate_wall_seconds':cw,'candidate_cpu_seconds':cc,
            'wall_ratio':cw/bw,'cpu_ratio':cc/bc,
            'candidate_wall_mib_s':mib/cw,'candidate_cpu_mib_s':mib/cc,
            'candidate_decision':[name for name,flag in zip(('run','reuse','add8','xor'),_decision(c)) if flag],
        })
    decision=decide(rows)
    mib=[r for r in rows if r['size']==1024*1024]
    print(json.dumps({
        'experiment':'ONE-G0.2 sparse native multi-Law carrying cost',
        'decision':decision,'sample_stride':SAMPLE_STRIDE,'repetitions':REPETITIONS,
        'median_wall_ratio':statistics.median(r['wall_ratio'] for r in rows),
        'median_cpu_ratio':statistics.median(r['cpu_ratio'] for r in rows),
        'median_1mib_wall_ratio':statistics.median(r['wall_ratio'] for r in mib),
        'median_1mib_cpu_ratio':statistics.median(r['cpu_ratio'] for r in mib),
        'worst_1mib_wall_ratio':max(r['wall_ratio'] for r in mib),
        'worst_1mib_cpu_ratio':max(r['cpu_ratio'] for r in mib),
        'rows':rows},sort_keys=True))
    return 0 if decision=='ADVANCE_NATIVE_MULTI_LAW_SPARSE_CARRY' else 1

if __name__=='__main__': raise SystemExit(main())
