#!/usr/bin/env python3
"""Deterministic negative controls for the independent J24G31 ZIP-wire parser.

Requires original J24G30 Actions artifacts downloaded beside this file
as j30-linux-original.zip and j30-physical-original.zip (or --artifacts DIR).
No product import and no mutation to real archive inputs.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import zipfile

p=argparse.ArgumentParser()
p.add_argument('--artifacts',type=Path,required=True)
args=p.parse_args()
root=args.artifacts
spec=importlib.util.spec_from_file_location('j24g31_independent_zip_wire_audit',Path(__file__).with_name('j24g31_independent_zip_wire_audit.py'))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
with zipfile.ZipFile(root/'j30-linux-original.zip') as z:
    original=z.read('j30-new-out/ordinary_2020.zip')
with zipfile.ZipFile(root/'j30-physical-original.zip') as z:
    manifest=json.loads(z.read('manifest.json'))
payload_sha=manifest['cases']['ordinary_2020']['payload_sha256']
lo=m.LFH.unpack_from(original,0)
cd_off=m.EOCD.unpack_from(original,len(original)-m.EOCD.size)[6]
compressed_off=m.LFH.size+lo[9]

def flip(offset):
    a=bytearray(original);a[offset]^=1;return bytes(a)
def replace(offset,bytes_):
    a=bytearray(original);a[offset:offset+len(bytes_)]=bytes_;return bytes(a)
def paired_dates():
    # Invalid 2107-02-29 in both local and central records, not a simple mismatch.
    a=bytearray(original)
    word=(2107-1980)<<9|(2<<5)|29
    struct.pack_into('<H',a,12,word)
    struct.pack_into('<H',a,cd_off+14,word)
    return bytes(a)

cases={
    'local_signature':flip(0),
    'local_version':replace(4,b'\x00\x00'),
    'local_flags':flip(6),
    'local_method':flip(8),
    'local_time':flip(10),
    'local_date':flip(12),
    'local_crc':flip(14),
    'local_compressed_size':flip(18),
    'local_uncompressed_size':flip(22),
    'local_name_length':flip(26),
    'local_filename':flip(m.LFH.size),
    'payload_byte':flip(compressed_off),
    'central_signature':flip(cd_off),
    'central_method':flip(cd_off+10),
    'central_date':flip(cd_off+14),
    'central_crc':flip(cd_off+16),
    'central_entry_count':replace(len(original)-m.EOCD.size+10,b'\x02\x00'),
    'central_offset':flip(len(original)-m.EOCD.size+16),
    'central_filename':flip(cd_off+m.CDH.size),
    'eocd_signature':flip(len(original)-m.EOCD.size),
    'eocd_comment':flip(len(original)-2),
    'truncated_zip':original[:-1],
    'trailing_byte':original+b'\x00',
    'paired_invalid_date':paired_dates(),
}
accepted=[]
for name,b in cases.items():
    try:m.Audit().read_inner(b,payload_sha,name,False)
    except (AssertionError,ValueError,struct.error,IndexError,UnicodeDecodeError,OverflowError,RuntimeError,EOFError):pass
    except Exception as e:
        if type(e).__module__!='zlib':raise
    else:accepted.append(name)
if accepted:raise AssertionError('independent auditor accepted corrupt controls: '+repr(accepted))
assert m.Audit().read_inner(original,payload_sha,'clean-control',False)['valid_date']
print(json.dumps({'schema':'j24g31-independent-zip-negative-controls-v1',
                  'total_corruptions_rejected':len(cases),'mutations':list(cases),
                  'baseline_valid':True,'no_cmpct_import':True},indent=2))
