#!/usr/bin/env python3
"""J24G96 detached O0: externally pinned footer ancestry, NOT a product format.

Uses real original r24 archives. stdlib + system libzstd only, never CMPCT.
Explicitly narrower than a trusted whole-file SHA: only chain membership and
r24 footer payload checks, not physical blobs, provenance, or immutable bytes.
"""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import io
import json
import pathlib
import struct
import zipfile

FMT = struct.Struct('<8sBBBBQQQ32s')
MAGIC = b'CMPTF24\0'
DOMAIN = b'CMPCT-J24G96-HYPOTHETICAL-PINNED-ANCESTRY-V1\0'
ZERO = bytes(32)
MAX_PAYLOAD = 32 << 20
MAX_FOOTERS = 128
ZIP_CASES = {
    'small-ubuntu': ('d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d','f29561c5e2d36a8f47aa35f61191911c0611be6b',['16-normal.cmpct','128-normal.cmpct']),
    'small-windows': ('f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e','f29561c5e2d36a8f47aa35f61191911c0611be6b',['16-normal.cmpct','128-normal.cmpct']),
    'deep-ubuntu': ('19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b','129edec976efe8bb604584517de39553487fec34',['4096-A.cmpct','8192-A.cmpct']),
    'deep-windows': ('c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab','129edec976efe8bb604584517de39553487fec34',['4096-A.cmpct','8192-A.cmpct']),
}
LIB = ctypes.CDLL('libzstd.so.1')
LIB.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
LIB.ZSTD_decompress.restype = ctypes.c_size_t
LIB.ZSTD_isError.argtypes = [ctypes.c_size_t]
LIB.ZSTD_isError.restype = ctypes.c_uint

def sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def require(condition: bool, reason: str):
    if not condition:
        raise ValueError(reason)

def parse_chain(raw: bytes):
    pos = len(raw) - FMT.size
    seen = set()
    desc = []
    while pos:
        require(pos >= 1 and pos + FMT.size <= len(raw), 'footer bounds')
        require(pos not in seen and len(desc) < MAX_FOOTERS, 'footer cycle/depth')
        seen.add(pos)
        magic, kind, codec, flags, reserved, clen, ulen, prev, payload_sha = FMT.unpack_from(raw, pos)
        require(magic == MAGIC and kind in (0, 1) and flags == reserved == 0, 'footer grammar')
        require(0 < clen <= pos and 0 < ulen <= MAX_PAYLOAD and 0 <= prev < pos, 'footer size/prev')
        comp = raw[pos-clen:pos]
        if codec == 0:
            expanded = comp
        else:
            require(codec == 1, 'codec')
            inbuf = ctypes.create_string_buffer(comp)
            outbuf = ctypes.create_string_buffer(ulen)
            result = LIB.ZSTD_decompress(outbuf, ulen, inbuf, clen)
            require(not LIB.ZSTD_isError(result) and result == ulen, 'zstd decode')
            expanded = outbuf.raw[:ulen]
        require(len(expanded) == ulen and sha(expanded) == payload_sha, 'footer payload SHA')
        desc.append({'pos':pos,'kind':kind,'codec':codec,'prev':prev,'clen':clen,'ulen':ulen,
                     'sha':payload_sha,'prefix':raw[pos:pos+36]})
        pos = prev
    require(desc[-1]['kind'] == 0 and desc[-1]['prev'] == 0, 'root mismatch')
    require(all(x['kind'] == 1 for x in desc[:-1]), 'nonroot footer')
    return list(reversed(desc))

def head(chain):
    current = ZERO
    trace = []
    for node in chain:
        message = DOMAIN + current + struct.pack('<Q', node['pos']) + node['prefix'] + node['sha']
        current = sha(message)
        trace.append(current)
    return current, trace

def mutate_parent(raw: bytes, at: int, value: int) -> bytes:
    altered = bytearray(raw)
    struct.pack_into('<Q', altered, at+28, value)
    return bytes(altered)

def check_sample(raw: bytes, name: str):
    original = parse_chain(raw)
    require(len(original) in (4,64), 'unexpected chain length')
    pinned, historical = head(original)
    latest, previous, grandparent = original[-1], original[-2], original[-3]
    require(latest['prev'] == previous['pos'], 'nonadjacent original')
    alternate = mutate_parent(raw, latest['pos'], grandparent['pos'])
    alt_chain = parse_chain(alternate)
    alt_head, _ = head(alt_chain)
    require(alt_head != pinned and len(alt_chain) == len(original)-1, 'single rewire not detected')
    require(sha(alternate) != sha(raw), 'full SHA must change')
    spoofed_external_head_admits = (alt_head == alt_head)
    require(spoofed_external_head_admits, 'negative control missing')
    double = mutate_parent(alternate, previous['pos'], 0)
    double_chain = parse_chain(double)
    double_head, _ = head(double_chain)
    require(double_head != pinned and double_head == alt_head, 'two-rewire camouflage')
    broken = bytearray(raw)
    broken[latest['pos']+36] ^= 1
    try:
        parse_chain(bytes(broken))
    except ValueError as e:
        require(str(e) == 'footer payload SHA', 'unexpected negative reason')
    else:
        raise ValueError('payload corruption accepted')
    fictitious_payload_sha = sha(b'J24G96-authorized-append-model')
    seq_pos = len(raw)
    future_prefix = struct.pack('<8sBBBBQQQ', MAGIC, 1, 0, 0, 0, 1, 1, latest['pos'])
    extension = sha(DOMAIN + pinned + struct.pack('<Q',seq_pos) + future_prefix + fictitious_payload_sha)
    require(extension != pinned, 'authorized append did not rotate anchor')
    # Negative physical-coverage control. CMA4's fixed 64-byte header (r24)
    # precedes member payload; ancestry commits only to footer metadata.
    blob = raw.index(b'CMA4')
    bm, bc, bf, br, usize, csize, meta_len, crc, blob_sha = struct.unpack_from('<4sBBHQQII32s',raw,blob)
    physical_payload = blob + 64 + meta_len
    require(bm == b'CMA4' and csize and physical_payload + csize <= len(raw), 'CMA4 bounds')
    changed_blob = bytearray(raw)
    changed_blob[physical_payload] ^= 1
    require(head(parse_chain(bytes(changed_blob)))[0] == pinned,
            'physical mutation unexpectedly changes metadata-only head')
    require(sha(bytes(changed_blob)) != sha(raw),'whole file SHA must detect mutated blob')
    extra_archive = len(original) * 32
    extra_external_latest = 32
    extra_external_all_epochs = len(original) * 32
    full_sha_read_proxy = sum(x['pos'] + FMT.size for x in original)
    commitment_message_bytes = len(original) * (len(DOMAIN) + 32 + 8 + 36 + 32)
    require(extra_archive/len(raw) <= (0.05 if '16-' in name else 0.01), 'charged archive byte ceiling')
    return {'file':name, 'physical_archive_bytes':len(raw),'archive_SHA256':sha(raw).hex(),
            'footers':len(original),'last_footer_offset':latest['pos'],
            'trusted_head_SHA256':pinned.hex(), 'parent_rewire_new_head':alt_head.hex(),
            'single_rewire_rejected_by_pinned_head':True,
            'double_rewire_rejected_by_pinned_head':True,
            'local_rehash_with_replaced_untrusted_head_admitted':spoofed_external_head_admits,
            'payload_corruption_refused':True,
            'physical_blob_payload_mutation_invisible_to_ancestry_head':True,
            'whole_file_sha_detects_blob_mutation':True,
            'authorized_model_append_requires_new_head':extension != pinned,
            'authorized_model_append_head_SHA256':extension.hex(),
            'candidate_archive_extra_bytes_lower_bound':extra_archive,
            'candidate_external_latest_anchor_bytes':extra_external_latest,
            'candidate_external_all_historical_anchor_bytes':extra_external_all_epochs,
            'candidate_archive_extra_percent_lower_bound':100*extra_archive/len(raw),
            'full_SHA_historical_cumulative_input_byte_proxy':full_sha_read_proxy,
            'chain_metadata_cumulative_hash_input_byte_proxy':commitment_message_bytes,
            'hashed_payload_compressed_bytes_for_offline_r24_authentication':sum(x['clen'] for x in original),
            'full_SHA_vs_chain_metadata_byte_proxy_ratio':full_sha_read_proxy/commitment_message_bytes,
            'bounded_commitment_stage':'O0, not physical on-disk integration or same-semantics product comparison'}

def main():
    ap = argparse.ArgumentParser()
    for case in ZIP_CASES:
        ap.add_argument('--'+case,required=True,type=pathlib.Path)
    ap.add_argument('--output',required=True,type=pathlib.Path)
    args = ap.parse_args()
    cases = {}
    zip_provenance={}
    for key,(expected_sha,source_head,filenames) in ZIP_CASES.items():
        raw_zip = getattr(args,key.replace('-','_')).read_bytes()
        require(sha(raw_zip).hex()==expected_sha, 'source provider ZIP SHA:'+key)
        with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
            members=z.namelist()
            require(len(members)==len(set(members)) and len(members)<50, 'ZIP member set')
            require(z.read('checkout-head.txt').decode().strip()==source_head,'source head:'+key)
            for filename in filenames:
                raw=z.read(filename)
                require(len(raw)<2_000_000,'archive size')
                cases[key+'/'+filename] = check_sample(raw,key+'/'+filename)
        zip_provenance[key]={'provider_zip_SHA256':expected_sha,'original_source_HEAD':source_head}
    require(len(cases)==8,'case cardinality')
    result={'schema':'cmpct-j24g96-externally-pinned-ancestry-O0-v1','source':'original GitHub-hosted J24G92 (#856) and J24G91 (#853) physical binary artifacts',
            'evidence_class':'RESEARCH ONLY / detached hypothetical model / NOT installed product',
            'model_limitations':['No external trust issuance or atomic trusted-head update implemented',
                'Only signed footer ancestry: not complete archive or blob-byte attestation',
                'No native Reader, Windows execution, crash recovery or actual future format',
                'No product CPU/wall/RSS or filesystem I/O measurements; byte counts are proxies'],
            'provenance':zip_provenance,'cases':cases}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps({'cases':len(cases),'archive_overhead_percent':{k:round(v['candidate_archive_extra_percent_lower_bound'],3) for k,v in cases.items()},
                      'full_SHA_to_chain_metadata_work_proxy':{k:round(v['full_SHA_vs_chain_metadata_byte_proxy_ratio'],1) for k,v in cases.items()},
                      'result_SHA256':sha(args.output.read_bytes()).hex()},indent=2,sort_keys=True))

if __name__=='__main__':main()
