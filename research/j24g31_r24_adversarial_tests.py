#!/usr/bin/env python3
"""Read-only independent negative controls for the original J24G30 r24 archive.

These controls prove the detached *strict physical oracle* rejects mutations;
they do NOT assert that the CMPCT product must reject recoverable archives.
"""
import argparse,binascii,hashlib,importlib.util,json,struct,subprocess,zipfile
from pathlib import Path
import msgpack
ap=argparse.ArgumentParser();ap.add_argument('--physical-artifact',type=Path,required=True);args=ap.parse_args()
spec=importlib.util.spec_from_file_location('r24',Path(__file__).with_name('j24g31_cmpct_physical_oracle.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with zipfile.ZipFile(args.physical_artifact) as z:
    manifest=json.loads(z.read('manifest.json'))
    case=manifest['cases']['ordinary_2020']
    original=z.read(case['archive'])
header=m.HDR.unpack_from(original);cs=header[3]
index_bytes=m.decode_zstd(original[m.HDR.size:m.HDR.size+cs]);idx=msgpack.unpackb(index_bytes,raw=False)
blob=idx['blobs'][idx['files'][0][6][1]];off,blob_us,blob_cs,codec,ml=blob
record_start=m.HDR.size+cs+off; payload_start=record_start+m.BHDR.size+ml
footer_start=len(original)-m.FTR.size; tail_start=footer_start-m.FTR.unpack_from(original,footer_start)[5]

def flip(loc):
    b=bytearray(original);b[loc]^=1;return bytes(b)
cases={
 'head_magic':flip(0),
 'head_revision':flip(8),
 'head_index_csize':flip(12),
 'head_index_uncompressed_size':flip(20),
 'head_index_sha':flip(36),
 'head_zstd_payload':flip(m.HDR.size+cs//2),
 'record_magic':flip(record_start),
 'record_codec':flip(record_start+4),
 'record_size':flip(record_start+8),
 'record_crc':flip(record_start+24),
 'record_sha':flip(record_start+28),
 'physical_zstd_payload':flip(payload_start+blob_cs//2),
 'tail_zstd_payload':flip(tail_start+(footer_start-tail_start)//2),
 'footer_magic':flip(footer_start),
 'footer_commit_kind':flip(footer_start+8),
 'footer_index_compressed_size':flip(footer_start+12),
 'footer_index_sha':flip(footer_start+28),
 'truncated_footer':original[:-1],
 'trailing_byte':original+b'\0',
}
negative=[]
expected=(AssertionError,ValueError,IndexError,TypeError,struct.error,subprocess.CalledProcessError,msgpack.exceptions.ExtraData,msgpack.exceptions.FormatError,msgpack.exceptions.StackError,EOFError)
for name,raw in cases.items():
 try:
    m.audit(name,raw,case)
    # strict source length equality is fixture custody, not the reader's recovery law
    assert len(raw)==case['size'] and hashlib.sha256(raw).hexdigest()==case['sha256'],'original physical archive fingerprint must match'
 except expected:negative.append(name)
 else:raise AssertionError('invalid r24 physical mutation accepted: '+name)
assert len(negative)==len(cases),(len(negative),len(cases))
m.audit('unaltered-control',original,case)
assert hashlib.sha256(original).hexdigest()==case['sha256']
print(json.dumps({'schema':'j24g31-strict-wire-oracle-negative-controls-v1','corruptions_rejected':len(negative),'names':negative,'clean_control':True,'scope':'Strict independent physical envelope oracle, not a product-reader recovery oracle'},indent=2))
