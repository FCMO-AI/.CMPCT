#!/usr/bin/env python3
"""J24G103 preregistered final CDC root-shift O0; no CMPCT product import.

Prospective prereg commit 7a0ecce92cae0b65080f092eda3a2e21b93aa396.
Original immutable source and controls: research/j24g102_cow_root_oracle.py.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import random
import struct
import time
import zipfile
from pathlib import Path
from j24g102_cow_root_oracle import SOURCES, HEAD, H, ck, makepair, priced

GEAR = tuple(int.from_bytes(hashlib.sha256(b'J24G103-GEAR-v1'+bytes([i])).digest()[:8], 'little') for i in range(256))
U64 = (1 << 64) - 1
TARGETS = (4096, 16384)

def chunks(raw: bytes, target: int):
    assert target in TARGETS
    low, high, mask = target // 4, target * 4, target - 1
    state, left = 0, 0
    for i, byte in enumerate(raw):
        state = ((state << 1) + GEAR[byte]) & U64
        span = i + 1 - left
        if span >= low and ((state & mask) == 0 or span >= high):
            yield raw[left:i+1]
            left, state = i + 1, 0
    if left < len(raw):
        yield raw[left:]

def charge(old: bytes, new: bytes, target: int, verify=True):
    entries, manifests = {}, {}
    for name, raw in (('old', old), ('new', new)):
        keys = []
        for part in chunks(raw, target):
            digest = H(part)
            ck(digest not in entries or entries[digest] == part, 'SHA-key collision')
            entries[digest] = part
            keys.append(digest)
        head = struct.pack('<8sQQ', b'CMPCDC01', len(raw), len(keys))
        root = H(b'J24G103-ROOT-v1\0' + head + b''.join(keys))
        manifest = head + root + b'\0' * 8 + b''.join(keys)
        ck(len(manifest) == 64 + 32 * len(keys), 'manifest charge')
        manifests[name] = (keys, manifest)
        if verify:
            rebuilt = b''.join(entries[key] for key in keys)
            ck(rebuilt == raw and H(rebuilt) == H(raw), 'exact model decode')
            ck(H(b'J24G103-ROOT-v1\0'+manifest[:24]+manifest[64:]) == manifest[24:56], 'manifest digest')
    if verify:
        key = next(iter(entries))
        tampered = bytes([entries[key][0] ^ 1]) + entries[key][1:]
        ck(H(tampered) != key, 'payload mutation was accepted')
        root = bytearray(manifests['old'][1]); root[64] ^= 1
        ck(H(b'J24G103-ROOT-v1\0'+root[:24]+root[64:]) != root[24:56], 'ref mutation accepted')
        ck(b'\x00'*32 not in entries, 'bogus dangling key')
    payload = sum(len(x) for x in entries.values())
    metadata = 44*len(entries)
    references = sum(len(v[1]) for v in manifests.values())
    total = payload+metadata+references
    return {'charged_total_bytes': total, 'unique_payload_bytes': payload,
            'block_records_bytes': metadata, 'two_root_manifests_bytes': references,
            'blocks_unique':len(entries), 'blocks_old':len(manifests['old'][0]),
            'blocks_new':len(manifests['new'][0]),
            'shared_sha_keys':len(set(manifests['old'][0]) & set(manifests['new'][0])),
            'ratio_larger_image':total/max(len(old),len(new)),
            'ratio_two_copies':total/(len(old)+len(new))}

def timed(fn):
    wall0=time.perf_counter_ns(); cpu0=time.process_time_ns()
    report=fn()
    return report, {'wall_ns':time.perf_counter_ns()-wall0,'cpu_ns':time.process_time_ns()-cpu0}

def main():
    p=argparse.ArgumentParser()
    for host in SOURCES:p.add_argument('--'+host,type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    output={}
    for host, expected in SOURCES.items():
        original=getattr(a,host).read_bytes()
        ck(hashlib.sha256(original).hexdigest()==expected,'original ZIP digest mismatch')
        with zipfile.ZipFile(io.BytesIO(original)) as container:
            ck(container.read('checkout-head.txt').decode().strip()==HEAD,'original source HEAD')
            for n in (4096,8192):
                old,new,src=makepair(container.read(f'{n}-A.cmpct'), container.read(f'{n}-B.cmpct'),n)
                record={'source':src,'targets':{}}
                for target in TARGETS:
                    controls=[]; candidates=[]
                    for _ in range(3):
                        x,t=timed(lambda:priced(old,new,target));controls.append(t)
                        y,t=timed(lambda:charge(old,new,target));candidates.append(t)
                    fixed=x; cand=y
                    ck(len({v['charged_total_bytes'] for v in (cand, charge(old,new,target))})==1,'unstable result')
                    variants={
                      'early_insert':new[:512]+b'!'+new[512:],
                      'mid_insert':new[:len(new)//2]+b'!'+new[len(new)//2:],
                      'early_delete':new[:512]+new[513:],
                      'independent_random':random.Random(240103+target+len(new)).randbytes(len(new)),
                      'aligned_move_4096':new[4096:]+new[:4096]}
                    perturb={label:charge(old,x,target) for label,x in variants.items()}
                    # Python tracemalloc is not enabled in this CPU-dominant rung; peak RSS is unmeasured.
                    peak=None
                    passed=(cand['ratio_larger_image']<=1.25
                        and perturb['early_insert']['ratio_larger_image']<=1.25
                        and perturb['mid_insert']['ratio_larger_image']<=1.30
                        and perturb['early_delete']['ratio_larger_image']<=1.30
                        and cand['charged_total_bytes']<=1.15*fixed['charged_total_bytes'])
                    record['targets'][str(target)]={'fixed':fixed,'cdc':cand,
                        'variants':perturb,'raw_time_fixed':controls,'raw_time_cdc':candidates,
                        'exploratory_python_traced_peak_bytes':peak,
                        'frozen_byte_gate_pass':passed}
                output[f'{host}-{n}']=record
    ok=all(c['frozen_byte_gate_pass'] for s in output.values() for c in s['targets'].values())
    timing_debt={}
    for key,item in output.items():
        timing_debt[key]={}
        for size,c in item['targets'].items():
            f=sorted(x['wall_ns'] for x in c['raw_time_fixed'])[1]
            d=sorted(x['wall_ns'] for x in c['raw_time_cdc'])[1]
            timing_debt[key][size]=round(d/f,6) if f else None
    result={'schema':'J24G103-CONTENT-DEFINED-ROOT-O0','source_producer_sha':HEAD,
        'prereg_commit':'7a0ecce92cae0b65080f092eda3a2e21b93aa396',
        'host_platform':'linux-local-or-runner-not-original-OS',
        'originals':SOURCES,'cases':output,'cdc_to_fixed_construct_wall_median_ratios':timing_debt,
        'gate':'O0_BYTE_GATE_PASS_NO_PRODUCT_CREDIT' if ok else 'O0_BYTE_GATE_FAIL_RETIRE_CDC_ROOT_SHARING',
        'truth_limitations':['Only four exact original r24 deletion/checkpoint physical pairs','CDC examples with insertion/deletion/randomness are not valid CMPCT archives',
          'Model bytes are SHA-keyed payloads, block and two manifest charges, not disk allocated bytes',
          'No product Writer/Reader/portability/atomicity/GC/CAS and no cold process benchmarks',
          'No baseline J24G99 equivalence: no-rebase vs independently rewritten root']}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'gate':result['gate'],'cdc_vs_fixed_wall':timing_debt,
      'ratios':{k:{s:{'original':round(v['cdc']['ratio_larger_image'],4),
      'early_shift':round(v['variants']['early_insert']['ratio_larger_image'],4),
      'fixed':round(v['fixed']['ratio_larger_image'],4),
      'pass':v['frozen_byte_gate_pass']} for s,v in x['targets'].items()} for k,x in output.items()},
      'receipt_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest()},sort_keys=True))

if __name__=='__main__':main()
