"""O55 detached one-buffer VZIP oracle: coherent source bytes, unchanged stable r24 output.

Uses the *actual* O50 Builder, Reader and codecs; only the source recipe
function is overridden during an isolated research test. No src/ mutation.
"""
from __future__ import annotations

import binascii
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import pytest

import cmpct.builder as builder_mod
import cmpct.codec as codec
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def snapshot_vzip_recipe(original: bytes, add_content):
    """Research reference for make_vzip_recipe, consuming ONE already captured byte buffer."""
    with zipfile.ZipFile(io.BytesIO(original)) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()), key=lambda x:x.header_offset)
        payloads=[];spans=[]
        for zi in infos:
            header=original[zi.header_offset:zi.header_offset+codec.LFH.size]
            v=codec.LFH.unpack(header); nl,xl=v[-2],v[-1]
            start=zi.header_offset+codec.LFH.size+nl+xl
            end=start+zi.compress_size
            raw=z.read(zi);stream=original[start:end]
            if zi.compress_type==zipfile.ZIP_STORED:
                cref=add_content(raw,Path(zi.filename).suffix.lower())
                stream_hash=b'';level=-1
            elif zi.compress_type==zipfile.ZIP_DEFLATED:
                level=codec.deflate_level_for(raw,stream)
                if level is None:return None
                cref=add_content(raw,Path(zi.filename).suffix.lower(),stream)
                stream_hash=codec.sha(stream)
            else:return None
            spans.append((start,end))
            payloads.append([cref,zi.compress_type,stream_hash,len(stream),level])
    literals=[];cursor=0
    for start,end in spans:
        literals.append(original[cursor:start])
        cursor=end
    literals.append(original[cursor:])
    skeleton=b''.join(literals)
    lens=[len(x) for x in literals]
    skref=add_content(skeleton,'.cmpct-skeleton')
    return [skref,lens,payloads,codec.sha(original),len(original),binascii.crc32(original)&0xffffffff]


def _make_zip(kind: str, symbol: bytes):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for i in range(3):
            compression=zipfile.ZIP_STORED if kind=='stored' or (kind=='mixed' and i==0) else zipfile.ZIP_DEFLATED
            z.writestr(f'payload_{i:02d}.txt',symbol*4096+bytes([65+i])*273,compress_type=compression,compresslevel=9)
    out=b.getvalue()
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        assert len(z.infolist())==3
        for i in range(3):assert z.read(f'payload_{i:02d}.txt').startswith(symbol)
    return out


def _build(root: Path,archive: Path):
    b=Builder(root,workers=1,reproducible=True)
    b.build(archive)
    kinds=[row[6][0] for row in b.files if row[0]=='nested.zip' and row[6]]
    assert kinds==[builder_mod.S_VZIP],('not-vzip',kinds)
    with CMPCT(archive) as reader:
        raw=reader.read('nested.zip')
        assert reader.verify()>=1
    return raw


@pytest.mark.parametrize('kind',['stored','deflated','mixed'])
def test_stable_single_buffer_exact_complete_archive_bytes(tmp_path,monkeypatch,kind):
    original=_make_zip(kind,b'A')
    root=tmp_path/'src';root.mkdir();source=root/'nested.zip';source.write_bytes(original)
    actual=tmp_path/'original.cmpct';oracle=tmp_path/'single-buffer.cmpct'
    got_original=_build(root,actual)
    with monkeypatch.context() as mp:
        mp.setattr(builder_mod,'make_vzip_recipe',lambda p,add: snapshot_vzip_recipe(p.read_bytes(),add))
        got_oracle=_build(root,oracle)
    assert got_original==original and got_oracle==original
    expected=actual.read_bytes();new=oracle.read_bytes()
    summary={'kind':kind,'original_source_sha':hashlib.sha256(original).hexdigest(),
             'canonical_archive_sha':hashlib.sha256(expected).hexdigest(),
             'snapshot_archive_sha':hashlib.sha256(new).hexdigest(),
             'archive_bytes':len(expected),'full_archive_identical':expected==new}
    print('O55_PARITY='+json.dumps(summary,sort_keys=True))
    assert expected==new, summary


def test_single_buffer_remains_coherent_when_source_inode_mutates_after_capture(tmp_path,monkeypatch):
    original=_make_zip('stored',b'A')
    substitute=_make_zip('stored',b'B')
    assert len(original)==len(substitute) and original!=substitute
    root=tmp_path/'source';root.mkdir()
    source=root/'nested.zip';source.write_bytes(original)
    st0=os.stat(source); pivot={'n':0}
    archive=tmp_path/'snapshot.cmpct'

    def captured_then_changed(p,add):
        captured=p.read_bytes()
        assert captured==original
        source.write_bytes(substitute)
        pivot['n']+=1
        st1=os.stat(source)
        pivot['same_inode']=(st0.st_dev,st0.st_ino)==(st1.st_dev,st1.st_ino)
        pivot['same_size']=st0.st_size==st1.st_size
        return snapshot_vzip_recipe(captured,add)

    with monkeypatch.context() as mp:
        mp.setattr(builder_mod,'make_vzip_recipe',captured_then_changed)
        extracted=_build(root,archive)
    outcome={'count':pivot['n'],'same_inode':pivot.get('same_inode'),
             'same_size':pivot.get('same_size'),'archive_sha':hashlib.sha256(archive.read_bytes()).hexdigest(),
             'captured_sha':hashlib.sha256(original).hexdigest(),
             'current_source_sha':hashlib.sha256(source.read_bytes()).hexdigest(),
             'output_sha':hashlib.sha256(extracted).hexdigest(),
             'exact_original_output':extracted==original,
             'original_byte_length':len(original)}
    Path('o55-result.json').write_text(json.dumps(outcome,sort_keys=True,indent=2),encoding='utf-8')
    print('O55_RESULT='+json.dumps(outcome,sort_keys=True))
    assert pivot['n']==1 and pivot['same_inode'] and pivot['same_size'],outcome
    assert extracted==original and source.read_bytes()==substitute,outcome
