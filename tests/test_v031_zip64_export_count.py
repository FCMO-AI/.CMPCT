"""ZIP64 entry-count falsifier: valid revision-24 source, independent stdlib/Info-ZIP readers.

The original ZIP32-only exporter emitted ~6.4 MiB then raised OverflowError at 65,536
directories, leaving an unreadable partial file. No special file names or 4GiB fixture needed.
"""
import binascii
import zipfile
import zlib
import msgpack
import pytest
from cmpct.codec import (
    HDR,FTR,BHDR,MAGIC,FMAGIC,BMAGIC,VERSION,sha,zc,
    K_FILE,K_DIR,CODEC_DEFLATE,S_BLOB,LFH,
)
from cmpct.reader import CMPCT


def make_r24(path, directory_count, *, with_deflate=False):
    files=[[f'dir_{i:06d}',K_DIR,0o755,0,0,None,None] for i in range(directory_count)]
    blobs=[];data=b'';control=None
    if with_deflate:
        control=b'The quick brown fox jumps over the lazy dog.\n'*72
        co=zlib.compressobj(9,zlib.DEFLATED,-15)
        packed=co.compress(control)+co.flush()
        data=BHDR.pack(
            BMAGIC,CODEC_DEFLATE,0,0,len(control),len(packed),0,
            binascii.crc32(control)&0xffffffff,sha(control),
        )+packed
        blobs=[[0,len(control),len(packed),CODEC_DEFLATE,0]]
        files.append(['real.txt',K_FILE,0o644,0,len(control),None,[S_BLOB,0]])
    index={'v':VERSION,'files':files,'blobs':blobs,'recipes':[],'dict_blob':None,
           'fsmeta':{'owner':[0,0],'owner_overrides':[],'xattrs':[]},'features':[]}
    uncompressed=msgpack.packb(index,use_bin_type=True)
    compressed=zc(uncompressed,12)
    head=HDR.pack(MAGIC,VERSION,0,len(compressed),len(uncompressed),len(data),sha(uncompressed))
    tail=FTR.pack(FMAGIC,0,1,0,0,len(compressed),len(uncompressed),0,sha(uncompressed))
    path.write_bytes(head+compressed+data+compressed+tail)
    return control


@pytest.mark.parametrize('directory_count', [65534,65535,65536,70000])
def test_zip_count_transition_with_real_cmpct_and_zip_reader(tmp_path,directory_count):
    original=tmp_path/'original.cmpct'; exported=tmp_path/'legacy.zip'
    make_r24(original,directory_count)
    with CMPCT(original) as reader:
        assert reader.verify()==0
        assert len(reader.files)==directory_count
        reader.export_zip(exported)
    data=exported.read_bytes()
    assert (b'PK\x06\x06' in data[-120:])==(directory_count>65535)
    assert (b'PK\x06\x07' in data[-120:])==(directory_count>65535)
    with zipfile.ZipFile(exported) as z:
        assert len(z.infolist())==directory_count
        assert z.namelist()[0]=='dir_000000/'
        assert z.namelist()[-1]==f'dir_{directory_count-1:06d}/'
        assert z.testzip() is None


def test_zip64_preserves_copied_exact_deflate_payload(tmp_path):
    original=tmp_path/'original.cmpct'; exported=tmp_path/'legacy.zip'
    source=make_r24(original,65536,with_deflate=True)
    with CMPCT(original) as reader:
        assert reader.verify()==1
        assert reader.read('real.txt')==source
        reader.export_zip(exported)
    with zipfile.ZipFile(exported) as z:
        assert len(z.infolist())==65537
        assert z.read('real.txt')==source
        info=z.getinfo('real.txt')
        assert info.compress_type==zipfile.ZIP_DEFLATED
        stream=exported.read_bytes()
        local=LFH.unpack_from(stream,info.header_offset)
        name_length,extra_length=local[-2:]
        data_start=info.header_offset+LFH.size+name_length+extra_length
        retained=stream[data_start:data_start+info.compress_size]
        co=zlib.compressobj(9,zlib.DEFLATED,-15)
        assert retained==co.compress(source)+co.flush()


def test_zip32_offsets_bound_without_allocating_four_gib():
    obj=object.__new__(CMPCT)
    obj.blobs=[]
    obj.files=[['one',K_FILE,0o644,0,0x7fffffd0,None,None],
               ['two',K_FILE,0o644,0,0x7fffffd0,None,None]]
    assert obj._zip64_offset_fallback_required()
    obj.files=[['small',K_FILE,0o644,0,100,None,None]]
    assert not obj._zip64_offset_fallback_required()
    # Imported exact Deflate payload may be larger than its raw member: charge the
    # actual physical length when assessing ZIP32 representability.
    obj.blobs=[[0,16,0xffffffd0,CODEC_DEFLATE,0]]
    obj.files=[['copied',K_FILE,0o644,0,16,None,[S_BLOB,0]]]
    assert obj._zip64_offset_fallback_required()
