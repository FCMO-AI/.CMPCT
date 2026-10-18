"""Builder-independent v24 strong verification of chunk/CDC logical maps.

These tests intentionally use a separately framed archive rather than the CMPCT
Builder, and demand incremental hashing instead of invoking read() to attest itself.
"""
from pathlib import Path
import pytest

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from make_map_archive import make,make_cdc_cross_boundary,make_alternating,PAYLOAD

@pytest.mark.parametrize('kind',['chunks','cdc'])
def test_map_verify_without_materializing_full_member(tmp_path,kind):
    path=tmp_path/f'{kind}.cmpct'
    make(path,kind,32)
    assert preflight_archive(path)['files']==1
    with CMPCT(path) as c:
        c.read=lambda _name: (_ for _ in ()).throw(
            AssertionError('streamable map must not use whole-member read()'))
        assert c.verify()==1

@pytest.mark.parametrize('kind',['chunks','cdc'])
def test_hardlink_map_verifies_without_whole_member_read(tmp_path,kind):
    path=tmp_path/'hardlink.cmpct'
    make(path,kind,32,hardlink=True)
    with CMPCT(path) as c:
        c.read=lambda _name: (_ for _ in ()).throw(AssertionError('hardlink copied'))
        assert c.verify()==2

@pytest.mark.parametrize('kind',['chunks','cdc'])
@pytest.mark.parametrize('mutation',['physical','logical','no_commit'])
def test_maps_reject_cryptographic_contradiction(tmp_path,kind,mutation):
    path=tmp_path/'mutated.cmpct'
    make(path,kind,8,mutation=mutation)
    with CMPCT(path) as c:
        with pytest.raises((OSError,IOError),match='SHA-256'):
            c.verify()

def test_cdc_metadata_alias_false_green_is_refused(tmp_path):
    path=tmp_path/'cdc_bad.cmpct'
    want=make_cdc_cross_boundary(path)
    with CMPCT(path) as c:
        assert c.read('pair.bin')==want
        assert c.read_range('pair.bin',262140,8)!=want[262140:262148]
        with pytest.raises(IOError,match='CDC declared chunk length mismatch'):
            c.verify()
    with pytest.raises(Exception,match='length disagrees with blob'):
        preflight_archive(path)

@pytest.mark.parametrize('kind',['chunks','cdc'])
def test_heldout_alternating_physical_owner(tmp_path,kind):
    path=tmp_path/'alternating.cmpct'
    make_alternating(path,kind,count=16)
    with CMPCT(path) as c:
        assert c.verify()==1
        assert c.read_range('heldout.bin',(1<<20)-4,8)==PAYLOAD[-4:]+PAYLOAD[::-1][:4]

@pytest.mark.parametrize('kind',['length','reference'])
def test_bool_wire_values_do_not_alias_integer_chunk_identity(tmp_path,kind):
    # MessagePack booleans are not legitimate length/ref integers. Python's
    # bool==1 and bool==0 aliases must not launder them through verify().
    import hashlib,binascii,msgpack
    from cmpct.codec import HDR,BHDR,MAGIC,BMAGIC,CODEC_RAW,K_FILE,S_CDC,S_CHUNKS,zc
    raw=b'A'
    storage=[S_CDC,[[True,0]]] if kind=='length' else [S_CHUNKS,[False]]
    index={'v':24,'blobs':[[0,1,1,CODEC_RAW,0]],
           'files':[['bool.bin',K_FILE,0o644,0,1,hashlib.sha256(raw).digest(),storage]],
           'recipes':[],'dict_blob':None,'fsmeta':{},'features':[]}
    b=msgpack.packb(index,use_bin_type=True);c=zc(b,3)
    record=BHDR.pack(BMAGIC,CODEC_RAW,0,0,1,1,0,
                     binascii.crc32(raw)&0xffffffff,hashlib.sha256(raw).digest())+raw
    path=tmp_path/'boolean.cmpct'
    path.write_bytes(HDR.pack(MAGIC,24,0,len(c),len(b),len(record),
                              hashlib.sha256(b).digest())+c+record)
    with CMPCT(path) as a:
        with pytest.raises(IOError,match='invalid'):
            a.verify()
    with pytest.raises(Exception):preflight_archive(path)
