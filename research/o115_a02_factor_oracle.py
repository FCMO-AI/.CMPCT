#!/usr/bin/env python3
"""O115 source-independent, charged A02 factor oracle. SCIENCE ONLY, never CMPCT product credit.

Frozen prereg: docs/v031-research/2026-10-25-o115-a02-factor-oracle-prereg.md.
This oracle is deliberately gifted base, slot positions and member assignments; all
facts the decoder needs are serialized/charged, and every model reconstructs bytes.
"""
import argparse
import hashlib
import json
import random
import struct
import subprocess
import time
from pathlib import Path


def zc(data):
    p = subprocess.run(['zstd', '-19', '--stdout', '--quiet'], input=data, capture_output=True, check=True)
    return p.stdout


def zd(data):
    p = subprocess.run(['zstd', '-d', '--stdout', '--quiet'], input=data, capture_output=True, check=True)
    return p.stdout


def hx(a, b):
    assert len(a) == len(b)
    return bytes(x ^ y for x, y in zip(a, b))


def rbytes(seed, label, n):
    result = bytearray()
    i = 0
    while len(result) < n:
        result.extend(hashlib.sha256(f'{seed}:{label}:{i}'.encode()).digest())
        i += 1
    return bytes(result[:n])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def family(name):
    is_held = name == 'heldout'
    seed = 191 if is_held else 115
    count = 96 if is_held else 64
    width = 8192 if is_held else 4096
    lengths = [384] * 4 if is_held else [256] * 3
    offsets = [311, 2266, 4181, 7033] if is_held else [193, 1621, 3352]
    options = 5 if is_held else 4
    base = rbytes(seed, 'base', width)
    tokens = [[rbytes(seed, f'token-{i}-{j}', length) for j in range(options)] for i, length in enumerate(lengths)]
    order = list(range(count))
    random.Random(seed + 65).shuffle(order)
    values = []
    assignments = []
    for i in order:
        if name == 'crossed':
            chosen = [(i // 16) % 4, (i // 4) % 4, i % 4]
        elif name == 'correlated':
            chosen = [i % 4] * len(offsets)
        elif name == 'heldout':
            chosen = [rbytes(seed, f'choice-{i}-{axis}', 1)[0] % options for axis in range(len(offsets))]
        else:
            chosen = [rbytes(seed, f'noise-choice-{i}-{axis}', 1)[0] % options for axis in range(len(offsets))]
        out = bytearray(base)
        for k, (start, length) in enumerate(zip(offsets, lengths)):
            out[start:start+length] = tokens[k][chosen[k]]
        if name == 'noise':
            out = bytearray(rbytes(seed, f'uncorrelated-{i}', width))
        values.append(bytes(out))
        assignments.append(chosen)
    assert all(len(f) == width for f in values)
    assert len(set(values)) > 2
    return dict(name=name, base=base, files=values, slots=list(zip(offsets, lengths)), tokens=tokens, assignments=assignments, seed=seed, n=count, width=width)


def decode_factors(dictionary):
    pos = 0
    total, = struct.unpack_from('<I', dictionary, pos)
    pos += 4
    slots = []
    tokens = []
    for _ in range(total):
        offset, width, count = struct.unpack_from('<III', dictionary, pos)
        pos += 12
        these = []
        for _ in range(count):
            these.append(dictionary[pos:pos+width])
            assert len(these[-1]) == width
            pos += width
        slots.append((offset, width))
        tokens.append(these)
    assert pos == len(dictionary)
    return slots, tokens


def run_case(name):
    f = family(name)
    base, files = f['base'], f['files']
    n, width, slots, choices = f['n'], f['width'], f['slots'], f['assignments']
    common = 64 + n * (8 + 32)  # file length + strong logical SHA per member; same for all.
    trial = {}
    root = zc(base)
    assert zd(root) == base
    def record(model, payload, extra, recovered, logical_read, component_sizes):
        assert len(recovered) == n, model
        assert all(a == b and sha(a) == sha(b) for a,b in zip(files, recovered)), model
        total = common + payload + extra
        trial[model] = dict(bytes=total, payload_bytes=payload, metadata_bytes=common+extra,
                            selected_logical_decode_bytes=logical_read, components=component_sizes,
                            exact=True)
    # Plain solid, true full stream; offset+length directory charged.
    t = time.perf_counter()
    solid = zc(b''.join(files))
    flat = zd(solid)
    record('S_solid', len(solid), n*8, [flat[i*width:(i+1)*width] for i in range(n)], n*width, {'solid':len(solid)})
    trial['S_solid']['encode_wall_seconds'] = time.perf_counter()-t
    # Independent per-file; archive framing + offset/length charged per file.
    t = time.perf_counter()
    indiv = [zc(x) for x in files]
    record('I_individual', sum(map(len,indiv)), n*8, [zd(x) for x in indiv], width, {'each':list(map(len,indiv))})
    trial['I_individual']['encode_wall_seconds'] = time.perf_counter()-t
    # Root XOR residuals, independently compressed (same gifted root as factor oracle).
    xor = [hx(base, x) for x in files]
    t = time.perf_counter()
    r_ind = [zc(x) for x in xor]
    record('R_root_individual', len(root)+sum(map(len,r_ind)), 32+n*8,
           [hx(base,zd(c)) for c in r_ind], 2*width,
           {'root':len(root),'residuals':list(map(len,r_ind))})
    trial['R_root_individual']['encode_wall_seconds'] = time.perf_counter()-t
    # Strong simpler control: one solid residual stream plus charged root.
    t = time.perf_counter()
    r_solid = zc(b''.join(xor))
    dec = zd(r_solid)
    record('G_root_solid_residual', len(root)+len(r_solid), 32+n*8,
           [hx(base,dec[i*width:(i+1)*width]) for i in range(n)], (n+1)*width,
           {'root':len(root),'residuals_solid':len(r_solid)})
    trial['G_root_solid_residual']['encode_wall_seconds'] = time.perf_counter()-t
    # Dictionary is *actually serialized* (offset, length, count, token bytes), compressed,
    # decoded and parsed in the independently checked reconstruction path.
    t = time.perf_counter()
    encoded_dictionary = bytearray(struct.pack('<I', len(slots)))
    for (offset, length), tokens in zip(slots, f['tokens']):
        encoded_dictionary += struct.pack('<III', offset, length, len(tokens))
        encoded_dictionary += b''.join(tokens)
    dict_zstd = zc(bytes(encoded_dictionary))
    decoded_slots, decoded_tokens = decode_factors(zd(dict_zstd))
    assignment_wire = bytes(j for row in choices for j in row)
    assert len(assignment_wire) == n*len(slots)
    assert max(assignment_wire) < 256
    exceptions = []
    for i in range(n):
        row = assignment_wire[i*len(slots):(i+1)*len(slots)]
        out = bytearray(base)
        for axis, (offset, length) in enumerate(decoded_slots):
            out[offset:offset+length] = decoded_tokens[axis][row[axis]]
        delta = hx(files[i], out)
        exceptions.append(b'' if not any(delta) else zc(delta))
    rec=[]
    for i in range(n):
        row = assignment_wire[i*len(slots):(i+1)*len(slots)]
        out = bytearray(zd(root))
        for axis,(offset,length) in enumerate(decoded_slots):
            out[offset:offset+length] = decoded_tokens[axis][row[axis]]
        if exceptions[i]:
            out = bytearray(hx(bytes(out), zd(exceptions[i])))
        rec.append(bytes(out))
    # Descriptor: root (32 B), dictionary (32 B), membership/assignment bytes,
    # 8-byte per-file exception (offset,size) even when absent; SHA is in common.
    extra = 64+len(assignment_wire)+n*8
    payload = len(root)+len(dict_zstd)+sum(map(len,exceptions))
    record('F_factor_oracle', payload, extra, rec, width+len(encoded_dictionary)+width*int(any(exceptions)),
           {'root':len(root),'factor_dictionary':len(dict_zstd),'assignment':len(assignment_wire),
            'exception_count':sum(bool(x) for x in exceptions),'exceptions_bytes':sum(map(len,exceptions))})
    trial['F_factor_oracle']['encode_wall_seconds'] = time.perf_counter()-t
    best_key = min((k for k in trial if k != 'F_factor_oracle'), key=lambda k:trial[k]['bytes'])
    best = trial[best_key]['bytes']
    fact = trial['F_factor_oracle']['bytes']
    return {'family':name,'seed':f['seed'],'objects':n,'object_size':width,'slots':slots,
            'token_alternatives_per_slot':len(f['tokens'][0]),'total_raw_bytes':n*width,
            'zstd_binary_version':subprocess.check_output(['zstd','--version'],text=True).strip(),
            'dataset_sha256':sha(b''.join(files)),
            'fully_charged_models':trial,
            'best_simple_control':best_key,'best_control_bytes':best,
            'factor_bytes':fact,'factor_relative_margin_pct':round(100*(best-fact)/best,4),
            'factor_beats_best_control':fact < best,
            'verification':'ALL_FIVE_RECONSTRUCT_AND_SHA256_PASS'}


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--out',default='o115-a02-result.json')
    args=a.parse_args()
    first=time.perf_counter()
    cases = [run_case(n) for n in ('crossed','correlated','heldout','noise')]
    result={'experiment':'O115_A02_CHARGED_FACTOR_ORACLE','status':'RESEARCH_ONLY',
            'prereg':'docs/v031-research/2026-10-25-o115-a02-factor-oracle-prereg.md',
            'results':cases,'total_wall_seconds':round(time.perf_counter()-first,4)}
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    for c in cases:
        print(f"{c['family']} N={c['objects']} F={c['factor_bytes']} best={c['best_control_bytes']}({c['best_simple_control']}) margin={c['factor_relative_margin_pct']:+.2f}% ({c['verification']})",flush=True)
    print('ARTIFACT_SHA256',sha(p.read_bytes()),'ELAPSED',result['total_wall_seconds'],flush=True)


if __name__=='__main__':main()
