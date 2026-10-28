#!/usr/bin/env python3
"""Detached J24B10 revision-24 wire/output referee. Never imports cmpct.

This independent audit parses both indexes and the physical RAW blob from raw
archive bytes; recomputes expected sparse reconstruction and actual output
file size, and challenges itself with tampered receipts and physical data.
"""
from __future__ import annotations
import argparse
import binascii
import copy
import hashlib
import json
from pathlib import Path
import struct
import zstandard
import msgpack

HDR = struct.Struct('<8sHHQQQ32s')
BHDR = struct.Struct('<4sBBHQQII32s')
FTR = struct.Struct('<8sBBBBQQQ32s')
L = 16384
B = 8192

def h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def unpack_archive(raw: bytes) -> dict:
    assert len(raw) >= HDR.size + FTR.size
    magic, revision, flags, cs, us, data_span, index_sha = HDR.unpack_from(raw)
    assert magic == b'CMPCT24\0' and revision == 24 and flags == 0
    assert HDR.size + cs + data_span <= len(raw)
    encoded = raw[HDR.size:HDR.size+cs]
    decompressed = zstandard.ZstdDecompressor().decompress(encoded, max_output_size=us)
    assert len(decompressed) == us and h(decompressed) == index_sha
    index = msgpack.unpackb(decompressed, raw=False)
    fpos = len(raw) - FTR.size
    fmagic, kind, codec, ff, res, fcs, fus, prev, fdigest = FTR.unpack_from(raw, fpos)
    assert fmagic == b'CMPTF24\0' and kind == 0 and codec == 1
    assert ff == res == prev == 0 and (fcs, fus, fdigest) == (cs, us, index_sha)
    assert raw[fpos-cs:fpos] == encoded
    record = raw[HDR.size+cs:HDR.size+cs+data_span]
    assert len(record) == BHDR.size + B
    m,c,flags,r,rus,rcs,ml,crc,digest = BHDR.unpack_from(record)
    assert m == b'CMA4' and c == 0 and flags == r == ml == 0
    assert rus == rcs == B
    payload = record[BHDR.size:]
    assert len(payload) == B and h(payload) == digest
    assert binascii.crc32(payload) & 0xffffffff == crc
    assert index['v'] == 24 and len(index['files']) == 1
    assert index['blobs'] == [[0, B, B, 0, 0]]
    assert index['recipes'] == []
    row = index['files'][0]
    assert len(row) == 7 and row[:5] == ['sparse.bin',0,0o644,0,L]
    assert isinstance(row[5], bytes) and len(row[5]) == 32
    assert row[6][0] == 3 and len(row[6][1]) == 1
    return {'index':index,'physical':record,'payload':payload,'row':row}

def adjudicate(root: Path, receipt: dict | None = None) -> dict:
    good = (root/'source-original.cmpct').read_bytes()
    bad = (root/'source-mutant.cmpct').read_bytes()
    g = unpack_archive(good)
    b = unpack_archive(bad)
    assert g['physical'] == b['physical']
    assert g['row'][5] == b['row'][5]
    assert g['row'][:6] == b['row'][:6]
    assert g['row'][6][1] == [[4096,8192,[0]]]
    assert b['row'][6][1] == [[L-1,1,[0]]]
    assert {k:v for k,v in g['index'].items() if k!='files'} == {k:v for k,v in b['index'].items() if k!='files'}
    source = b'\0'*4096 + g['payload'] + b'\0'*(L-4096-B)
    published = b'\0'*(L-1) + g['payload']
    assert h(source) == g['row'][5] and len(source) == L
    assert len(published) == L+B-1 == 24575
    assert (root/'original-accepted'/'sparse.bin').read_bytes() == source
    assert (root/'mutant-accepted'/'sparse.bin').read_bytes() == published
    assert not (root/'original-too-low'/'sparse.bin').exists()
    assert not (root/'mutant-too-low'/'sparse.bin').exists()
    if receipt is None:
        receipt = json.loads((root/'court-result.json').read_text())
    assert receipt['schema'] == 'cmpct-j24b10-court-v1'
    assert receipt['decision'] == 'CONFIRMED_SPARSE_SIGNED_EXTENT_QUOTA_OVERRUN'
    for key,expected in {
        'declared_logical_size':L,
        'physical_payload_size':B,
        'original_extent':[4096,8192,[0]],
        'mutant_extent':[L-1,1,[0]],
        'limit_enforced':L,
        'original_extracted_bytes':len(source),
        'mutant_extracted_bytes':len(published),
        'excess_logical_bytes':B-1,
        'original_archive_sha256':h(good).hex(),
        'mutant_archive_sha256':h(bad).hex(),
        'physical_sha256':h(g['physical']).hex(),
        'original_logical_sha256':h(source).hex(),
        'original_extracted_sha256':h(source).hex(),
        'mutant_extracted_sha256':h(published).hex(),
    }.items():
        assert receipt[key] == expected, (key, receipt.get(key), expected)
    assert 'extent' in receipt['strict_mutant_refusal'].lower()
    assert 'above limit' in receipt['original_undercap_refusal'].lower()
    assert 'above limit' in receipt['mutant_undercap_refusal'].lower()
    assert 'file integrity failure' in receipt['mutant_full_read_refusal'].lower()
    assert 'file integrity failure' in receipt['mutant_verify_refusal'].lower()
    return {
        'decision':'INDEPENDENT_WIRE_AND_EXTRACT_PROOF_PASS',
        'original_archive_sha256':h(good).hex(),
        'mutant_archive_sha256':h(bad).hex(),
        'physical_sha256':h(g['physical']).hex(),
        'declared':L,
        'published':len(published),
        'overrun':B-1,
    }

def falsifier(root: Path) -> dict:
    receipt = json.loads((root/'court-result.json').read_text())
    tampered = copy.deepcopy(receipt)
    tampered['mutant_extracted_bytes'] += 1
    refused = 0
    for candidate in [tampered]:
        try:
            adjudicate(root, candidate)
        except AssertionError:
            refused += 1
        else:
            raise AssertionError('forged receipt accepted')
    # Input mutations are challenged in throwaway copies, never original artifacts.
    import tempfile
    import shutil
    for name, rel in [('physical','source-mutant.cmpct'),('output','mutant-accepted/sparse.bin'),('index','source-original.cmpct')]:
        with tempfile.TemporaryDirectory(prefix='j24b10-referee-') as td:
            q = Path(td)
            for item in root.iterdir():
                if item.is_file(): shutil.copyfile(item,q/item.name)
                elif item.is_dir(): shutil.copytree(item,q/item.name)
            target = q/rel
            data = bytearray(target.read_bytes())
            if name=='physical':
                _,_,_,cs,_,_,_=HDR.unpack_from(data)
                off=HDR.size+cs+BHDR.size+8
            elif name=='output': off=len(data)//2
            else: off=HDR.size+5
            data[off] ^= 0x40
            target.write_bytes(data)
            try:
                adjudicate(q)
            except (AssertionError,zstandard.ZstdError,ValueError):
                refused += 1
            else:
                raise AssertionError(f'tampered {name} accepted')
    assert refused == 4
    return {'forged_evidence_rejected':refused,'forged_evidence_cases':4}

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--in-dir',type=Path,required=True)
    args=ap.parse_args();root=args.in_dir.resolve()
    result=adjudicate(root)
    result.update(falsifier(root))
    (root/'independent-referee.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
