#!/usr/bin/env python3
"""J24G87 O0: charged hypothetical immutable-plane member checkpoint.

No production import. Requires original hosted evidence ZIP described in
J24G86 and its authenticated physical parser (sibling research module).
THIS IS NOT A VALID r24 FOOTER OR A COMPATIBLE PRODUCT FORMAT.
"""
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
import msgpack
import j24g86_periodic_checkpoint_oracle as r24

def evaluate(path):
    source=Path(path).read_bytes()
    assert r24.sha(source)==r24.ROOT_SHA
    result={'schema':'j24g87-factorized-immutable-plane-checkpoint-o0',
            'source_zip_sha256':r24.ROOT_SHA,'research_only':True,
            'requires_new_decoder_grammar':True,'cases':{}}
    with zipfile.ZipFile(io.BytesIO(source)) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read('j24g83_original_hosted_evidence.zip'))) as z:
            for case in ('8192-middle','32768-tail'):
                data=z.read('j24g80-'+case+'-public-valid.cmpct')
                base,chain=r24.read_wire(data)
                assert len(chain)==65 and len(base['files'])==int(case.split('-')[0])
                final=chain[-1]['object']
                # Scientific admission: immutable physical/metadata planes cannot
                # be silently borrowed when any inherited non-file field changed.
                immutable={k:v for k,v in base.items() if k!='files'}
                assert immutable=={k:v for k,v in final.items() if k!='files'}
                initial_sha=hashlib.sha256(msgpack.packb(base,use_bin_type=True)).digest()
                assert initial_sha.hex()==chain[0]['raw_sha']
                removed=set()
                costs={}
                for generation in range(1,65):
                    if generation<64:
                        op=chain[generation]['object']
                        assert op['blobs']==[] and len(op['ops'])==1
                        action,name=op['ops'][0]
                        assert action=='del' and name not in removed
                        removed.add(name)
                    else:
                        actual={x[0] for x in final['files']}
                        new={x[0] for x in base['files']}-removed-actual
                        assert len(new)==1
                        removed.update(new)
                    files=[x for x in base['files'] if x[0] not in removed]
                    if generation==64:
                        assert files==final['files']
                        continue
                    if generation not in (8,16,24,32,40,48,56):
                        continue
                    # Explicit 16B grammar/flags, 32B root digest, 8B pointer,
                    # plus full surviving file rows. All MessagePack keys charged.
                    rec={'type':b'FMP1'+bytes(12),
                         'base_index_sha256':initial_sha,
                         'base_index_offset_le64':struct.pack('<Q',0),
                         'files':files}
                    raw=msgpack.packb(rec,use_bin_type=True)
                    def resolve(x):
                        if x['base_index_sha256']!=hashlib.sha256(msgpack.packb(base,use_bin_type=True)).digest():
                            raise ValueError('untrusted source root')
                        if x['base_index_offset_le64']!=struct.pack('<Q',0):
                            raise ValueError('untrusted root offset')
                        return {**base,'files':x['files']}
                    assert resolve(rec)['files']==files
                    corrupt=dict(rec)
                    corrupt['base_index_sha256']=bytes([initial_sha[0]^1])+initial_sha[1:]
                    try:resolve(corrupt)
                    except ValueError:pass
                    else:raise AssertionError('forged immutable-plane reference accepted')
                    choices=[r24.compress(raw,l) for l in (1,3,19)]
                    best=min(choices,key=lambda c:c['bytes'])
                    assert best['bytes']>chain[generation]['body_bytes']
                    costs[str(generation)]={'decoded_record_bytes':len(raw),'body_bytes':best['bytes'],
                        'codec_trials':choices,'chosen_level':best['level'],
                        'signed_footer_bytes':r24.FOOTER.size,
                        'displaced_delta_footer_bytes':chain[generation]['body_bytes']+r24.FOOTER.size,
                        'net_extra_bytes':best['bytes']-chain[generation]['body_bytes']}
                schedules={}
                for k in (8,16,32):
                    at=list(range(k,64,k))
                    extra=sum(costs[str(g)]['net_extra_bytes'] for g in at)
                    worst=max(t%k for t in range(1,64))
                    schedules[str(k)]={'checkpoint_generations':at,'extra_bytes':extra,
                        'total_archive_bytes_estimate':len(data)+extra,
                        'overhead_percent':100*extra/len(data),
                        'max_delta_steps':worst,'worst_step_reduction':63/worst,
                        'k32_research_gate_pass':k==32 and extra/len(data)<=.05 and 63/worst>=2}
                result['cases'][case]={'source_sha256':r24.sha(data),'source_archive_bytes':len(data),
                    'nonfile_planes_exactly_unchanged':True,'source_footers':len(chain),
                    'hostile_root_digest_refused':True,'checkpoint_cost':costs,'schedules':schedules}
    result['decision']='FACTOR_MEMBER_K32_SURVIVES_O0' if all(
        x['schedules']['32']['k32_research_gate_pass'] for x in result['cases'].values()
    ) else 'FACTOR_MEMBER_K32_FAILS_O0'
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':evaluate(sys.argv[1])
