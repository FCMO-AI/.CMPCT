"""Opt-in bounded RAW digest-range regression court, independent of negative PR #263."""
from __future__ import annotations

import binascii
import os
from pathlib import Path
import random
import tracemalloc

import pytest
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import BHDR, CODEC_RAW, K_HARDLINK, S_BLOB


def _raw_bytes(n=512*1024):
    return random.Random(0xC0FFEE).randbytes(n)


def _archive(tmp_path:Path, *, with_hardlink=False):
    source=tmp_path/'input';source.mkdir()
    raw=_raw_bytes()
    (source/'original.bin').write_bytes(raw)
    if with_hardlink:
        os.link(source/'original.bin',source/'alias.bin')
    dst=tmp_path/'a.cmpct'
    Builder(source,workers=1).build(dst)
    with CMPCT(dst) as r:
        row=r.by['original.bin']
        if row[1]==K_HARDLINK:
            row=r.by[row[6][0]]
        assert row[6][0]==S_BLOB
        idx=row[6][1]
        assert r.blobs[idx][3]==CODEC_RAW
        pos=r.record_base+r.blobs[idx][0]
        offset=pos+BHDR.size+r.blobs[idx][4]
    return dst,raw,pos,offset


def _tamper(dst:Path,pos:int,payload_off:int,where:int,*,repair_crc=False,crc_only=False,sha_only=False):
    data=bytearray(dst.read_bytes());hdr=list(BHDR.unpack_from(data,pos));n=hdr[4]
    if not crc_only and not sha_only:
        data[payload_off+where]^=0x15
    if repair_crc:
        hdr[7]=binascii.crc32(data[payload_off:payload_off+n])&0xffffffff
    if crc_only:
        hdr[7]^=1
    if sha_only:
        v=bytearray(hdr[8]);v[0]^=1;hdr[8]=bytes(v)
    data[pos:pos+BHDR.size]=BHDR.pack(*hdr)
    out=dst.with_name(f'tampered-{where}-{repair_crc}-{crc_only}-{sha_only}.cmpct')
    out.write_bytes(data)
    return out


@pytest.mark.parametrize('start',[0,1023,512*1024-1])
def test_pristine_selected_bytes_and_empty_range(tmp_path,start):
    path,raw,_,_=_archive(tmp_path)
    with CMPCT(path) as reader:
        n=min(33,len(raw)-start)
        assert reader.read_raw_range_verified('original.bin',start,n)==raw[start:start+n]
        assert reader.read_raw_range_verified('original.bin',start,0)==b''
        assert reader.read_range('original.bin',start,n)==raw[start:start+n]


@pytest.mark.parametrize('where',[0,512*1024//2,512*1024-1])
@pytest.mark.parametrize('repair_crc',[False,True])
def test_corruption_rejected_after_crc_stale_or_repaired(tmp_path,where,repair_crc):
    path,raw,pos,payload_off=_archive(tmp_path)
    bad=_tamper(path,pos,payload_off,where,repair_crc=repair_crc)
    with CMPCT(bad) as reader:
        assert reader.read_range('original.bin',where,1)!=raw[where:where+1]
        with pytest.raises(IOError,match='CRC32|SHA-256'):
            reader.read_raw_range_verified('original.bin',where,1)
        with pytest.raises(IOError):
            reader.verify()
        if repair_crc:
            # The cheap normal read accepts a repaired CRC; explicit digest checking does not.
            assert reader.read('original.bin')[where]!=raw[where]


@pytest.mark.parametrize('tamper_mode',['crc','sha'])
def test_physical_header_checksum_corruption_rejected(tmp_path,tamper_mode):
    path,raw,pos,payload_off=_archive(tmp_path)
    bad=_tamper(path,pos,payload_off,1,crc_only=tamper_mode=='crc',sha_only=tamper_mode=='sha')
    with CMPCT(bad) as reader:
        with pytest.raises(IOError,match='CRC32|SHA-256'):
            reader.read_raw_range_verified('original.bin',10,5)


def test_budget_bounds_and_raw_only_refusal(tmp_path):
    path,raw,_,_=_archive(tmp_path)
    with CMPCT(path) as reader:
        for budget in [0,1024,512*1024-1]:
            with pytest.raises(ValueError,match='max_scan_bytes'):
                reader.read_raw_range_verified('original.bin',0,1,max_scan_bytes=budget)
        for budget in [-1,0.5,True,None]:
            with pytest.raises(ValueError,match='max_scan_bytes'):
                reader.read_raw_range_verified('original.bin',0,1,max_scan_bytes=budget)
        for start,length in [(-1,1),(0,-1),(len(raw),1),(len(raw)+1,0)]:
            with pytest.raises(ValueError,match='range outside member'):
                reader.read_raw_range_verified('original.bin',start,length)
        assert reader.read_raw_range_verified('original.bin',len(raw),0)==b''


def test_hardlink_alias_and_no_whole_payload_allocation(tmp_path):
    path,raw,_,_=_archive(tmp_path,with_hardlink=True)
    with CMPCT(path) as reader:
        aliases=[row[0] for row in reader.files if row[1]==K_HARDLINK]
        assert aliases
        tracemalloc.start()
        try:
            assert reader.read_raw_range_verified(aliases[0],17,7)==raw[17:24]
            current,peak=tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        # A 512KiB whole-blob copy would exceed this conservative Python heap budget.
        assert peak<256*1024,peak


def test_rejects_corruption_outside_requested_one_byte(tmp_path):
    path,raw,pos,payload_off=_archive(tmp_path)
    bad=_tamper(path,pos,payload_off,0,repair_crc=True)
    with CMPCT(bad) as reader:
        assert reader.read_range('original.bin',len(raw)-1,1)==raw[-1:]
        with pytest.raises(IOError,match='SHA-256'):
            reader.read_raw_range_verified('original.bin',len(raw)-1,1)


def test_non_raw_direct_blob_is_explicitly_unsupported(tmp_path):
    source=tmp_path/'input';source.mkdir()
    (source/'repeat.bin').write_bytes(b'ABCD'*128*1024)
    archive=tmp_path/'compressed.cmpct'
    Builder(source,workers=1).build(archive)
    with CMPCT(archive) as reader:
        row=reader.by['repeat.bin']
        assert row[6][0]==S_BLOB
        assert reader.blobs[row[6][1]][3]!=CODEC_RAW
        with pytest.raises(ValueError,match='one exact RAW blob'):
            reader.read_raw_range_verified('repeat.bin',10,1)


def test_logical_member_sha_mismatch_is_refused(tmp_path):
    path,raw,_,_=_archive(tmp_path)
    with CMPCT(path) as reader:
        row=reader.by['original.bin']
        row[5]=bytes([0])*32
        with pytest.raises(IOError,match='logical SHA-256'):
            reader.read_raw_range_verified('original.bin',0,1)


def test_recomputed_crc_and_sha_is_not_origin_authentication(tmp_path):
    # Research-negative: an attacker able to rewrite both physical payload and checksum
    # can present a self-consistent archive. Digest equality is NOT a MAC/signature.
    path,raw,pos,payload_off=_archive(tmp_path)
    data=bytearray(path.read_bytes());data[payload_off+123]^=0x1a
    hdr=list(BHDR.unpack_from(data,pos));n=hdr[4]
    modified=bytes(data[payload_off:payload_off+n])
    import hashlib
    hdr[7]=binascii.crc32(modified)&0xffffffff
    hdr[8]=hashlib.sha256(modified).digest()
    data[pos:pos+BHDR.size]=BHDR.pack(*hdr)
    forged=tmp_path/'recomputed.cmpct';forged.write_bytes(data)
    with CMPCT(forged) as reader:
        assert reader.read_raw_range_verified('original.bin',123,1)==modified[123:124]
        assert modified!=raw
