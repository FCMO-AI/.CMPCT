#!/usr/bin/env python3
"""A14-O1c: symmetric fully charged codec oracle over frozen O1b source identities.
Scientific only. Must run beside a14_o1b_natural_crc_oracle.py, never product.
"""
from __future__ import annotations
import argparse,hashlib,json,lzma,struct,subprocess,time
from pathlib import Path
import brotli
import a14_o1b_natural_crc_oracle as b

HDR=struct.Struct('<8sBBQQ32s')
MODES=('zstd19','xz9','brotli11')

def enc(x,mode):
    if mode=='zstd19':return b.zstd(x)
    if mode=='xz9':return lzma.compress(x,preset=9)
    if mode=='brotli11':return brotli.compress(x,quality=11)
    raise ValueError('codec')

def dec(x,mode):
    if mode=='zstd19':return b.zstd(x,decode=True)
    if mode=='xz9':return lzma.decompress(x)
    if mode=='brotli11':return brotli.decompress(x)
    raise ValueError('codec')

def evaluate(source_receipt):
    data={'schema':'cmpct-a14-o1c-symmetric-codec-v1','question':'are O1b losses solely from asymmetric candidate codec?',
          'original_receipt_sha256':b.sha(Path(source_receipt).read_bytes()),'base_source_sha256':b.sha(Path(b.__file__).read_bytes()),
          'header_bytes':HDR.size,'rows':[],'summary':{},'codec_choices':list(MODES)}
    previous=json.loads(Path(source_receipt).read_text())
    for fid,suffix in ((1,'.png'),(2,'.gz')):
        pathlist=b.selected_paths(suffix)
        rows=[x for x in previous['results'] if x['family']==('png' if fid==1 else 'gzip')]
        assert len(pathlist)==len(rows)==64
        for i,(path,old) in enumerate(zip(pathlist,rows)):
            raw=path.read_bytes();assert b.sha(raw)==old['raw_sha256']
            if fid==1:clean,count=b.png_parse(raw,strip=True)
            else:clean,count=b.gzip_strip(raw)
            measurements={}
            for mode in MODES:
                t=time.perf_counter_ns();compress=enc(clean,mode);encode_ms=(time.perf_counter_ns()-t)/1e6
                t=time.perf_counter_ns();decoded=dec(compress,mode)
                restored=b.png_restore(decoded) if fid==1 else b.gzip_restore(decoded)
                decode_ms=(time.perf_counter_ns()-t)/1e6
                if restored!=raw or decoded!=clean:raise AssertionError('roundtrip '+mode)
                header=HDR.pack(b'A14CRCS1',fid,MODES.index(mode),len(raw),len(compress),hashlib.sha256(raw).digest())
                blob=header+compress
                measurements[mode]={'bytes':len(blob),'encode_ms':encode_ms,'decode_ms':decode_ms,'sha256':b.sha(blob)}
            best=min(measurements,key=lambda name:measurements[name]['bytes'])
            ctrl=old['best_control_bytes'];size=measurements[best]['bytes']
            data['rows'].append({'id':old['id'],'family':old['family'],'raw_sha256':old['raw_sha256'],
                 'raw_bytes':len(raw),'field_count':count,'source_best_bytes':ctrl,'best_derived_codec':best,
                 'candidate_bytes':size,'gain_bytes':ctrl-size,'gain_pct':100*(ctrl-size)/ctrl,
                 'no_header_gain_pct':100*(ctrl-(size-HDR.size))/ctrl,'modes':measurements})
    for fam in ('png','gzip'):
        rr=[x for x in data['rows'] if x['family']==fam];best=sum(x['source_best_bytes'] for x in rr);candidate=sum(x['candidate_bytes'] for x in rr)
        data['summary'][fam]={'files':len(rr),'material_positive5':sum(x['gain_pct']>=5 for x in rr),
             'best_source_bytes':best,'best_derived_bytes':candidate,'aggregate_gain_pct':100*(best-candidate)/best,
             'best_codec_distribution':{m:sum(x['best_derived_codec']==m for x in rr) for m in MODES},
             'total_search_ms':sum(sum(v['encode_ms'] for v in x['modes'].values()) for x in rr),
             'total_selected_decode_ms':sum(x['modes'][x['best_derived_codec']]['decode_ms'] for x in rr)}
    data['decision']='INSUFFICIENT' if any(s['files']<16 for s in data['summary'].values()) else ('ADVANCE_FORMAT_FAMILY' if all(s['material_positive5']>=2 and s['aggregate_gain_pct']>=1 for s in data['summary'].values()) else 'PARK_FORMAT_CHECKSUM_FAMILY')
    data['instrument_sha256']=b.sha(Path(__file__).read_bytes())
    return data

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default='a14_o1c_symmetric_result.json');a=p.parse_args()
    result=evaluate(a.source);Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'decision':result['decision'],'summary':result['summary']},indent=2))
if __name__=='__main__':main()
