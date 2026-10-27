#!/usr/bin/env python3
"""Detached J24B02 wire/receipt referee: deliberately no cmpct imports."""
from __future__ import annotations
import argparse
import binascii
import copy
import hashlib
import json
import struct
import msgpack
import zstandard as zstd

HDR = struct.Struct('<8sHHQQQ32s')
BHDR = struct.Struct('<4sBBHQQII32s')
FTR = struct.Struct('<8sBBBBQQQ32s')

def H(data):
    return hashlib.sha256(data).hexdigest()

def audit(report):
    checks = 0
    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(label)

    check(report['question'] == 'J24B02' and report['revision'] == 24, 'experiment identity')
    controls = []
    for name, size in (('valid', 128), ('oversized', 136)):
        c = report['cases'][name]
        blob = bytes.fromhex(c['archive_hex'])
        check(H(blob) == c['archive_sha256'], 'archive identity')
        m, ver, flag, cs, us, ds, sha = HDR.unpack_from(blob)
        check((m, ver, flag) == (b'CMPCT24\x00', 24, 0), 'header')
        check(0 < cs < 1_000_000 and 0 < us < 1_000_000, 'bounded index size')
        compressed = blob[HDR.size:HDR.size + cs]
        wire = zstd.ZstdDecompressor().decompress(compressed, max_output_size=1_000_000)
        check(len(wire) == us and hashlib.sha256(wire).digest() == sha, 'authenticated primary index')
        idx = msgpack.unpackb(wire, raw=False, strict_map_key=False)
        check(idx['v'] == 24 and len(idx['files']) == len(idx['blobs']) == 1, 'index shape')
        row = idx['files'][0]
        check(row[0] == 'link' and row[1] == 2 and row[4] == size
              and row[6] == [0, 0], 'symlink direct owner and stated logical size')
        check(idx['blobs'][0] == [0, 128, 128, 0, 0], 'physical index')
        first_blob = HDR.size + cs
        bm, codec, flags, reserved, usize, csize, meta, crc, ph = BHDR.unpack_from(blob, first_blob)
        check((bm, codec, flags, reserved, usize, csize, meta) ==
              (b'CMA4', 0, 0, 0, 128, 128, 0), 'RAW owner header')
        data_start = first_blob + BHDR.size
        data_end = data_start + 128
        data = blob[data_start:data_end]
        check(len(data) == 128 and H(data) == report['payload_sha256'], 'payload bytes')
        check(binascii.crc32(data) & 0xffffffff == crc, 'physical CRC32')
        check(hashlib.sha256(data).digest() == ph, 'physical SHA256')
        check(H(blob[first_blob:data_end]) == c['physical_frame_sha256'], 'physical frame identity')
        check(ds == data_end - first_blob and c['owner_size'] == 128 and c['declared'] == size,
              'physical/index length consistency of receipt')
        tail = blob[data_end:data_end + cs]
        check(tail == compressed and c['tail_prefix_hex'] == tail[:8].hex(), 'tail index redundancy')
        foot = FTR.unpack_from(blob, data_end + cs)
        check(foot == (b'CMPTF24\x00', 0, 1, 0, 0, cs, us, 0, sha)
              and data_end + cs + FTR.size == len(blob), 'footer identity')
        check(c['preflight']['status'] == 'ACCEPT' and c['read']['status'] == 'ACCEPT'
              and c['verify']['status'] == 'ACCEPT', 'all full/public interfaces accept')
        check(c['read']['hex'] == data.hex() and c['read']['length'] == 128,
              'full read content, notwithstanding false declared size')
        check(c['inside']['status'] == 'ACCEPT' and c['inside']['hex'] == data[20:28].hex(),
              'in-owner range exactness')
        if name == 'valid':
            check(c['after_owner']['status'] == 'REJECT', 'valid end bound')
        else:
            check(c['after_owner']['status'] == 'ACCEPT' and c['after_owner']['length'] == 8
                  and c['after_owner']['hex'] == tail[:8].hex(), 'cross-owner tail provenance')
        controls.append((data, blob[first_blob:data_end], idx))
    check(controls[0][0] == controls[1][0] and
          controls[0][1] == controls[1][1], 'exact unchanged physical frame')
    alt = copy.deepcopy(controls[1][2])
    alt['files'][0][4] = 128
    check(alt == controls[0][2], 'only symlink size changed between indexes')
    return checks

def run(path):
    with open(path, encoding='utf-8') as f:
        report = json.load(f)
    checks = audit(report)
    tamper = [
        (('cases', 'valid', 'archive_sha256'), '0' * 64),
        (('cases', 'oversized', 'tail_prefix_hex'), 'bad0'),
        (('cases', 'oversized', 'after_owner', 'hex'), '00' * 8),
        (('cases', 'oversized', 'verify', 'status'), 'REJECT'),
        (('cases', 'valid', 'physical_frame_sha256'), 'f' * 64),
        (('cases', 'oversized', 'declared'), 128),
        (('payload_sha256',), '0' * 64),
        (('cases', 'valid', 'read', 'hex'), 'cc' * 128),
    ]
    rejected = 0
    for keys, value in tamper:
        forged = copy.deepcopy(report)
        obj = forged
        for key in keys[:-1]:
            obj = obj[key]
        obj[keys[-1]] = value
        try:
            audit(forged)
        except (AssertionError, ValueError, struct.error):
            rejected += 1
        else:
            raise AssertionError(f'forged receipt accepted: {keys}')
    return {'status': 'PASS', 'independent_checks': checks,
            'forged_receipts_rejected': rejected,
            'result': 'SYMLINK_DECLARED_SIZE_IGNORED_BY_FULL_READ_AND_VERIFY'}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('receipt')
    print(json.dumps(run(p.parse_args().receipt), sort_keys=True))
