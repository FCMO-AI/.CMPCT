#!/usr/bin/env python3
"""Posthoc independent RAW physical-boundary referee, separate from frozen J24B01 court.

Consumes the observed receipt emitted even when the prospective court fails.
Does not import CMPCT or modify the failed preregistered prediction.
"""
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

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def audit(report: dict) -> dict:
    checks = 0
    def must(ok: bool, why: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(why)

    must(report['experiment'] == 'J24B01', 'experiment identity')
    must(report['revision'] == 24, 'revision')
    must(report['payload_length'] == 128, 'payload length')
    archive_facts = {}
    for label, declared in (('valid', 128), ('oversized', 136)):
        c = report['cases'][label]
        image = bytes.fromhex(c['archive_hex'])
        must(digest(image) == c['archive_sha256'], f'{label}: image digest')
        must(len(image) >= HDR.size + BHDR.size + FTR.size, f'{label}: minimum image length')
        magic, version, flags, cs, us, ds, ih = HDR.unpack_from(image)
        must((magic, version, flags) == (b'CMPCT24\x00', 24, 0), f'{label}: header')
        must(0 < cs < 1_000_000 and 0 < us < 1_000_000 and 0 < ds < 1_000_000, f'{label}: bounded fields')
        compressed_primary = image[HDR.size:HDR.size + cs]
        must(len(compressed_primary) == cs, f'{label}: primary length')
        raw_idx = zstd.ZstdDecompressor().decompress(compressed_primary, max_output_size=1_000_000)
        must(len(raw_idx) == us and hashlib.sha256(raw_idx).digest() == ih, f'{label}: primary authenticated index')
        idx = msgpack.unpackb(raw_idx, raw=False, strict_map_key=False)
        must(isinstance(idx, dict) and idx['v'] == 24, f'{label}: revision index')
        must(len(idx['files']) == 1 and len(idx['blobs']) == 1, f'{label}: one logical/physical owner')
        row, owner = idx['files'][0], idx['blobs'][0]
        must(len(row) == 7 and row[0] == 'direct.bin' and row[4] == declared, f'{label}: logical row size')
        must(len(row[6]) == 2 and row[6][1] == 0, f'{label}: direct ref owner')
        must(len(owner) >= 5 and owner[0] == 0 and owner[1] == owner[2] == 128, f'{label}: physical index length')
        must(owner[3] == 0 and owner[4] == 0, f'{label}: RAW codec and metadata length')
        blob_offset = HDR.size + cs
        must(blob_offset + BHDR.size <= len(image), f'{label}: blob header within image')
        bm, codec, blob_flags, reserved, bu, bc, bmeta, crc, sh = BHDR.unpack_from(image, blob_offset)
        must((bm, codec, blob_flags, reserved, bu, bc, bmeta) ==
             (b'CMA4', 0, 0, 0, 128, 128, 0), f'{label}: physical RAW frame')
        physical_start = blob_offset + BHDR.size
        physical_end = physical_start + bu
        data = image[physical_start:physical_end]
        must(len(data) == 128 and digest(data) == report['payload_sha256'], f'{label}: raw payload identity')
        must((binascii.crc32(data) & 0xffffffff) == crc, f'{label}: CRC32')
        must(hashlib.sha256(data).digest() == sh, f'{label}: physical SHA256')
        must(c['physical_owner_length'] == bu, f'{label}: owner receipt')
        must(c['declared_logical_size'] == declared, f'{label}: declared receipt')
        physical_frame = image[blob_offset:physical_end]
        must(digest(physical_frame) == c['physical_sha256'], f'{label}: frame receipt')
        must(ds == len(physical_frame), f'{label}: header physical region')
        tail_start = blob_offset + ds
        tail = image[tail_start:tail_start + cs]
        must(tail_start == physical_end and tail == compressed_primary, f'{label}: tail redundancy')
        must(digest(tail) == c['tail_index_sha256'], f'{label}: encoded tail digest')
        must(c['tail_prefix_hex'] == tail[:8].hex(), f'{label}: tail prefix receipt')
        footer_start = tail_start + cs
        must(footer_start + FTR.size == len(image), f'{label}: complete footer')
        fm, fk, fc, ff, fr, fcs, fus, fp, fh = FTR.unpack_from(image, footer_start)
        must((fm, fk, fc, ff, fr, fcs, fus, fp, fh) ==
             (b'CMPTF24\x00', 0, 1, 0, 0, cs, us, 0, ih), f'{label}: footer identity')
        must(c['in_frame_range']['status'] == 'ACCEPT' and
             c['in_frame_range']['hex'] == data[20:28].hex() and
             c['in_frame_range']['length'] == 8, f'{label}: selective in-owner result')
        must(c['preflight']['status'] == 'ACCEPT', f'{label}: actual preflight observation')
        must(c['read']['status'] == ('ACCEPT' if label == 'valid' else 'REJECT'),
             f'{label}: complete read observation')
        must(c['verify']['status'] == ('ACCEPT' if label == 'valid' else 'REJECT'),
             f'{label}: verify observation')
        if label == 'valid':
            must(c['after_owner_range']['status'] == 'REJECT', 'valid requested range rejection')
            must(c['read']['hex'] == data.hex(), 'valid full read exact bytes')
        else:
            cross = c['after_owner_range']
            must(cross['status'] == 'ACCEPT' and cross['length'] == 8,
                 'oversized outside-owner acceptance')
            must(cross['hex'] == image[physical_end:physical_end + 8].hex() == tail[:8].hex(),
                 'cross-owner bytes provably tail-index bytes')
        archive_facts[label] = (data, physical_frame, copy.deepcopy(idx))
    vdata, vframe, vi = archive_facts['valid']
    bdata, bframe, bi = archive_facts['oversized']
    must(vdata == bdata and vframe == bframe, 'identical physical owner and frame')
    bi['files'][0][4] = 128
    must(bi == vi, 'index semantic delta solely logical declared size')
    return {'status': 'PASS', 'independent_checks': checks,
            'decision': 'OBSERVED_PREFLIGHT_ACCEPTS_AND_RAW_RANGE_CROSSES_PHYSICAL_OWNER',
            'original_preregistered_preflight_prediction': 'FALSIFIED'}

def run(filename: str, adversarial: bool) -> dict:
    with open(filename, encoding='utf-8') as file:
        report = json.load(file)
    verdict = audit(report)
    refused = 0
    if adversarial:
        corruptions = (
            (('cases', 'valid', 'archive_sha256'), '0' * 64),
            (('cases', 'oversized', 'tail_prefix_hex'), 'deadbeef'),
            (('cases', 'oversized', 'after_owner_range', 'hex'), '00' * 8),
            (('cases', 'oversized', 'declared_logical_size'), 128),
            (('cases', 'valid', 'physical_sha256'), 'f' * 64),
            (('cases', 'valid', 'in_frame_range', 'hex'), 'bb' * 8),
            (('cases', 'oversized', 'preflight', 'status'), 'REJECT'),
            (('cases', 'oversized', 'read', 'status'), 'ACCEPT'),
            (('cases', 'valid', 'verify', 'status'), 'REJECT'),
            (('payload_sha256',), '0' * 64),
            (('cases', 'valid', 'archive_hex'), '00'),
            (('cases', 'oversized', 'after_owner_range', 'length'), 7),
        )
        for path, new in corruptions:
            forged = copy.deepcopy(report)
            target = forged
            for field in path[:-1]:
                target = target[field]
            target[path[-1]] = new
            try:
                audit(forged)
            except (AssertionError, ValueError, struct.error):
                refused += 1
            else:
                raise AssertionError(f'forged receipt accepted: {path}')
        if refused != len(corruptions):
            raise AssertionError('adversarial rejection count')
    verdict['forged_receipts_rejected'] = refused
    return verdict

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('receipt')
    parser.add_argument('--adversarial', action='store_true')
    options = parser.parse_args()
    print(json.dumps(run(options.receipt, options.adversarial), sort_keys=True))
