from __future__ import annotations
import binascii,zlib,zipfile
import pytest
import cmpct.vzip_transaction as tx


def test_in_memory_peak_bound_and_recipe_share_one_zip_parse(monkeypatch,tmp_path):
    path=tmp_path/'candidate.zip';payload=b'parse-fusion-'*8192
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('payload.bin',payload)
    raw=path.read_bytes();bound=len(raw)*4+len(payload);real=tx.zipfile.ZipFile;calls=0
    def counted(*args,**kwargs):
        nonlocal calls;calls+=1;return real(*args,**kwargs)
    monkeypatch.setattr(tx.zipfile,'ZipFile',counted)
    staged=tx.stage_vzip_recipe_bytes(raw,max_retained_bytes=bound,exact_stream_retention=True)
    assert staged is not None
    assert calls==1


def test_in_memory_fused_peak_bound_still_refuses_before_member_decode(monkeypatch,tmp_path):
    path=tmp_path/'candidate.zip';payload=b'bounded-'*(256*1024)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('payload.bin',payload)
    raw=path.read_bytes();bound=len(raw)*4+len(payload);reads=0;real_read=zipfile.ZipFile.read
    def counted_read(self,*args,**kwargs):
        nonlocal reads;reads+=1;return real_read(self,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,'read',counted_read)
    assert tx.stage_vzip_recipe_bytes(raw,max_retained_bytes=bound-1,exact_stream_retention=True) is None
    assert reads==0


def test_in_memory_fused_parse_preserves_malformed_preflight_refusal():
    assert tx.stage_vzip_recipe_bytes(b'not-a-zip',max_retained_bytes=1024,exact_stream_retention=True) is None


def test_direct_raw_deflate_validation_enforces_length_and_crc():
    raw=b'direct-validation-'*4096;co=zlib.compressobj(6,zlib.DEFLATED,-15);stream=co.compress(raw)+co.flush();info=zipfile.ZipInfo('payload.bin');info.file_size=len(raw);info.CRC=binascii.crc32(raw)&0xffffffff
    assert tx._validated_raw_deflate(stream,info)==raw
    info.CRC^=1
    with pytest.raises(zipfile.BadZipFile,match='CRC'):tx._validated_raw_deflate(stream,info)
    info.CRC=binascii.crc32(raw)&0xffffffff;info.file_size+=1
    with pytest.raises(zipfile.BadZipFile,match='size'):tx._validated_raw_deflate(stream,info)
    with pytest.raises(zipfile.BadZipFile,match='deflate'):tx._validated_raw_deflate(stream[:-1],zipfile.ZipInfo('broken.bin'))
