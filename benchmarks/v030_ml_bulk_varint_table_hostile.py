from __future__ import annotations
import json
from pathlib import Path
from benchmarks.v030_ml_bulk_varint_table_oracle import install_bulk
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_verified_restore as VR

def run():
    C=PRODUCT._BASE_IMPL.C; O=C.SHARED.G.O; historical=VR._PRE_RELEASE_DELIMITER_INVERSE
    # Force multi-byte varints (130 and 257) so the bulk one-byte proof must decline.
    delimiter=44; raw=(b'A'*130)+bytes([delimiter])+(b'B'*3)+bytes([delimiter])+(b'C'*257)
    encoded=O.delimiter_forward(raw,delimiter)
    install_bulk(); candidate=C.SHARED.G.O.delimiter_inverse
    expected=historical(encoded,len(raw)); actual=candidate(encoded,len(raw))
    if expected!=raw or actual!=raw or actual!=expected: raise RuntimeError('multi-byte fallback identity drift')
    malformed=[]
    for cut in (1,2,5,9):
        blob=encoded[:-cut]
        old_ok=new_ok=True
        try: historical(blob,len(raw))
        except Exception: old_ok=False
        try: candidate(blob,len(raw))
        except Exception: new_ok=False
        malformed.append({'cut':cut,'historical_accepted':old_ok,'candidate_accepted':new_ok})
        if old_ok!=new_ok: raise RuntimeError(f'malformed acceptance drift at cut {cut}')
    return {'schema':'cmpct-v030-ml-bulk-varint-hostile-v1','release_credit':False,'multi_byte_lengths':[130,3,257],'exact_fallback_identity':True,'malformed_equivalence':malformed,'result':'PASS'}
if __name__=='__main__':
    result=run(); out=Path('benchmark-artifacts/v030-ml-bulk-varint-hostile.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
