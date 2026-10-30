#!/usr/bin/env python3
"""Independently audit J24I47's hosted ZIP, nested source archive, and raw data.

Not imported by the producer or its workflow. No CMPCT source or decoding used.
"""
import argparse
import hashlib
import io
import json
import math
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

def digest(b): return hashlib.sha256(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('zip', type=Path)
    ap.add_argument('--head', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    archive = a.zip.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert z.testzip() is None
        names = set(z.namelist())
        needed = {'result.json','result.sha256','source-head.txt','source-files-sha256.txt','source-exact-receipt.tar.gz','receipt.sha256'}
        assert needed == names, (needed ^ names)
        payload = {n: z.read(n) for n in needed}
    assert payload['source-head.txt'].decode().strip() == a.head
    assert payload['result.sha256'].decode().split()[0] == digest(payload['result.json'])
    assert payload['receipt.sha256'].decode().split()[0] == digest(payload['source-exact-receipt.tar.gz'])
    parsed_checks = dict(reversed(line.split(maxsplit=1)) for line in payload['source-files-sha256.txt'].decode().splitlines())
    with tarfile.open(fileobj=io.BytesIO(payload['source-exact-receipt.tar.gz']),mode='r:gz') as t:
        members = {x.name:x for x in t.getmembers() if x.isfile()}
        assert set(members) == {'research/j24i47/j24i47_integrity_bound.py',
            'research/j24i47/source_j24i46_generation.json',
            'j24i47-evidence/result.json', 'j24i47-evidence/source-head.txt',
            'j24i47-evidence/source-files-sha256.txt'}
        contents = {k:t.extractfile(v).read() for k,v in members.items()}
    assert contents['j24i47-evidence/result.json'] == payload['result.json']
    assert contents['j24i47-evidence/source-head.txt'] == payload['source-head.txt']
    assert contents['j24i47-evidence/source-files-sha256.txt'] == payload['source-files-sha256.txt']
    for path, expected in parsed_checks.items():
        assert digest(contents[path]) == expected, path
    assert digest(contents['research/j24i47/source_j24i46_generation.json']) == '72af642c6193587ca226e2be40e9fc05d7e042fbe125069cad1261b6972d9111'
    original = json.loads(contents['research/j24i47/source_j24i46_generation.json'])
    result = json.loads(payload['result.json'])
    assert result['product_evidence'] is False
    assert result['source']['j24i46_generation_manifest_sha256'] == digest(contents['research/j24i47/source_j24i46_generation.json'])
    observed = result['local_integrity_not_global_integrity']
    cost = result['cost_lower_bounds']
    assert len(observed) == len(cost) == 6
    assert {w['pattern'] for w in observed} == {'periodic','prng'}
    assert {w['chunk_logical_bytes'] for w in observed} == {4096,65536,1048576}
    for w in observed:
        lo,hi = w['observed_region']
        assert 0 <= lo < hi <= original['pcm_bytes_each']
        assert w['member_bytes_not_observed_by_local_check'] == original['pcm_bytes_each']-(hi-lo)
        assert not lo <= w['mutant_unobserved_byte_offset'] < hi
        assert w['clean']['local_digest'] and w['clean']['whole_member_sha256']
        assert w['late_mutant']['local_digest'] and not w['late_mutant']['whole_member_sha256']
        assert not w['selected_mutant']['local_digest'] and not w['selected_mutant']['whole_member_sha256']
    for c in cost:
        n = math.ceil(original['pcm_bytes_each']/c['region_bytes'])
        assert c['region_count'] == n
        assert c['charged_digest_bytes'] == 32*n
        assert c['charged_offset_and_length_bytes'] == 16*n
        assert c['optimistic_total_stored_overhead_bytes'] == 48*n+32
        assert abs(c['optimistic_overhead_percent_of_existing_flac']-100*(48*n+32)/c['source_flac_bytes'])<1e-6
    # Run exact submitted producer source in a fresh temp directory and compare result bytes.
    with tempfile.TemporaryDirectory() as folder:
        d=Path(folder)
        source=d/'source.py';source.write_bytes(contents['research/j24i47/j24i47_integrity_bound.py'])
        manifest=d/'manifest.json';manifest.write_bytes(contents['research/j24i47/source_j24i46_generation.json'])
        output=d/'result.json'
        p=subprocess.run([sys.executable,str(source),'--manifest',str(manifest),'--out',str(output)],capture_output=True,text=True,check=True)
        assert output.read_bytes() == payload['result.json'], p.stdout
    audit={'schema':'cmpct-j24i47-independent-artifact-audit-v1','status':'PASS',
           'head':a.head,'zip_sha256':digest(archive),
           'nested_tar_sha256':digest(payload['source-exact-receipt.tar.gz']),
           'result_sha256':digest(payload['result.json']),
           'producer_source_sha256':digest(contents['research/j24i47/j24i47_integrity_bound.py']),
           'j24i46_manifest_sha256':digest(contents['research/j24i47/source_j24i46_generation.json']),
           'witnesses':len(observed),'independent_cost_rows':len(cost),
           'exact_source_reexecution':'byte-identical',
           'limit':'toy byte-array/derivation; no installed CMPCT runtime or FLAC product test'}
    a.out.write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps(audit,sort_keys=True))

if __name__=='__main__': main()
