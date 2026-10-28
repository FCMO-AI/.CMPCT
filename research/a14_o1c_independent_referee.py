#!/usr/bin/env python3
"""Independent numerical, source-provenance and tamper referee for A14-O1c.
No imports from the O1b/O1c instruments; builds on separately audited O1b SHA receipt.
"""
from __future__ import annotations
import argparse,hashlib,json,copy
from pathlib import Path

MODES=('zstd19','xz9','brotli11')
def sha(b):return hashlib.sha256(b).hexdigest()

def judge(old,new):
    if new['schema']!='cmpct-a14-o1c-symmetric-codec-v1' or old['schema']!='cmpct-a14-o1b-natural-crc-v1':raise AssertionError('schema')
    if new['header_bytes']!=58 or new['codec_choices']!=list(MODES):raise AssertionError('decoder facts')
    if len(new['rows'])!=len(old['results']) or len(new['rows'])!=128:raise AssertionError('population')
    for a,b in zip(old['results'],new['rows']):
        if a['status']!='admitted':raise AssertionError('unexpected refusal')
        if a['id']!=b['id'] or a['family']!=b['family'] or a['raw_sha256']!=b['raw_sha256'] or a['raw_bytes']!=b['raw_bytes']:raise AssertionError('source ref')
        if len(b['modes'])!=3 or any(m not in b['modes'] for m in MODES):raise AssertionError('candidate codec set')
        for m,row in b['modes'].items():
            if row['bytes']<58 or len(row['sha256'])!=64 or row['encode_ms']<0 or row['decode_ms']<0:raise AssertionError('candidate receipt')
        best_bytes=min(v['bytes'] for v in b['modes'].values())
        if b['best_derived_codec'] not in MODES or b['modes'][b['best_derived_codec']]['bytes']!=best_bytes or b['candidate_bytes']!=best_bytes:raise AssertionError('candidate minimum')
        if b['source_best_bytes']!=a['best_control_bytes'] or b['gain_bytes']!=a['best_control_bytes']-best_bytes:raise AssertionError('source control')
        if abs(b['gain_pct']-100*b['gain_bytes']/a['best_control_bytes'])>1e-9:raise AssertionError('ratio')
        if abs(b['no_header_gain_pct']-100*(a['best_control_bytes']-best_bytes+58)/a['best_control_bytes'])>1e-9:raise AssertionError('header charged')
    for fam in ('png','gzip'):
        rr=[x for x in new['rows'] if x['family']==fam];s=new['summary'][fam]
        control=sum(x['source_best_bytes'] for x in rr);cand=sum(x['candidate_bytes'] for x in rr)
        if len(rr)!=s['files'] or s['files']!=64:raise AssertionError('family population')
        if control!=s['best_source_bytes'] or cand!=s['best_derived_bytes']:raise AssertionError('totals')
        if abs(s['aggregate_gain_pct']-100*(control-cand)/control)>1e-9:raise AssertionError('aggregate ratio')
        if s['material_positive5']!=sum(x['gain_pct']>=5 for x in rr):raise AssertionError('positive count')
        for m in MODES:
            if s['best_codec_distribution'][m]!=sum(x['best_derived_codec']==m for x in rr):raise AssertionError('distribution')
    decision='ADVANCE_FORMAT_FAMILY' if all(x['material_positive5']>=2 and x['aggregate_gain_pct']>=1 for x in new['summary'].values()) else 'PARK_FORMAT_CHECKSUM_FAMILY'
    if new['decision']!=decision:raise AssertionError('decision')
    return {'decision':decision,'rows':len(new['rows']), 'png_gain_percent':new['summary']['png']['aggregate_gain_pct'],
            'gzip_gain_percent':new['summary']['gzip']['aggregate_gain_pct']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',required=True);p.add_argument('--new',required=True);a=p.parse_args()
    oldraw=Path(a.old).read_bytes();newraw=Path(a.new).read_bytes()
    old=json.loads(oldraw);new=json.loads(newraw)
    if new['original_receipt_sha256']!=sha(oldraw):raise AssertionError('wrong source receipt')
    result=judge(old,new)
    attacks=[('derived_bytes',lambda d:d['rows'][0].__setitem__('candidate_bytes',d['rows'][0]['candidate_bytes']+1)),
             ('control_bytes',lambda d:d['rows'][0].__setitem__('source_best_bytes',d['rows'][0]['source_best_bytes']+1)),
             ('source_hash',lambda d:d['rows'][0].__setitem__('raw_sha256','0'*64)),
             ('family_gain',lambda d:d['summary']['png'].__setitem__('aggregate_gain_pct',99)),
             ('mode_set',lambda d:d['rows'][0]['modes'].pop('zstd19')),
             ('decision',lambda d:d.__setitem__('decision','ADVANCE_FORMAT_FAMILY'))]
    for label,mut in attacks:
        d=copy.deepcopy(new);mut(d)
        try:judge(old,d)
        except AssertionError:pass
        else:raise AssertionError('forged receipt accepted '+label)
    receipt={'schema':'cmpct-a14-o1c-third-root-v1','result_sha256':sha(newraw),'referee_sha256':sha(Path(__file__).read_bytes()),
             'original_o1b_sha256':sha(oldraw),'verdict':'PASS','forgeries_rejected':len(attacks),**result}
    Path(a.new).with_suffix('.referee.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
