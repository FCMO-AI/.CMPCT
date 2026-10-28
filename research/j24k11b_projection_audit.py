#!/usr/bin/env python3
"""J24K11b independent stdlib-only raw audit, cannot invoke CMPCT or native code."""
import copy, hashlib, json, math, statistics, sys
from pathlib import Path

def audit(d,source):
    assert d['schema']=='j24k11b-projection-v1'
    assert d['source_sha256']==hashlib.sha256(Path(source).read_bytes()).hexdigest()
    assert d['class']=='scientific_component_not_product'
    assert len(d['c_scanner_sha256'])==64
    assert len(d['cells'])==18 and d['observations']==648 and d['hostile_cases']==54 and d['strict_ref_hostile_cases']==108
    expected={(n,m,p) for n in (64,512,4096) for m in (0,1,2) for p in ('sequential','permuted')}
    assert {(c['n'],c['mode'],c['layout']) for c in d['cells']}==expected
    for c in d['cells']:
        assert c['descriptor_count']==c['n'] and c['payload_count']==c['n']
        assert len(c['source_sha256'])==64
        assert c['fresh_projected_python_heap_bytes']>c['n']*56
        assert c['class']=='component_projection_model_not_product'
        assert {x['name'] for x in c['hostile']}=={'signed_size_plus','signed_size_minus','physical_flags'}
        assert all(x['accepted']==[False,False,False] for x in c['hostile'])
        assert len(c['strict_ref_hostile'])==6
        assert all(x['accepted']==[False,False,False] for x in c['strict_ref_hostile'])
        expect={'boolean_owner','subclass_owner','negative_owner','outside_owner','unsupported_method', ('boolean_signed_csize' if c['mode']==0 else 'unsupported_stream_mode')}
        assert {x['name'] for x in c['strict_ref_hostile']}==expect
        assert set(c['raw'])=={'direct','projected_python','projected_native'}
        for arm,samples in c['raw'].items():
            assert len(samples)==12
            for point in samples:
                assert type(point['wall_ns']) is int and point['wall_ns']>=0
                assert type(point['cpu_ns']) is int and point['cpu_ns']>=0
            for k in ('wall_ns','cpu_ns'):
                assert c['median'][arm][k]==statistics.median(point[k] for point in samples)
        for k in ('wall_ns','cpu_ns'):
            ratio=c['median']['direct'][k]/c['median']['projected_native'][k]
            assert math.isclose(c['speedup_over_direct'][k],ratio,rel_tol=1e-12)
    minimum=min(c['speedup_over_direct'][k] for c in d['cells'] if c['n']==4096 for k in ('wall_ns','cpu_ns'))
    assert math.isclose(d['min_4096_speedup'],minimum,rel_tol=1e-12)
    assert d['decision']==('PROJECTION_BRIDGE_HEADROOM' if minimum>=1.5 else 'PROJECTION_BRIDGE_HEADROOM_NOT_PROVEN')
    assert d['native_build_ns']>0
    return {'verdict':'PASS','samples':648,'hostile_cases':54,'strict_ref_hostile_cases':108,'worst_4096_speedup':minimum,'scientific_decision':d['decision']}

def main():
    source=sys.argv[1] if len(sys.argv)>1 else 'research/j24k11b_projection_oracle.py'
    fp=sys.argv[2] if len(sys.argv)>2 else 'j24k11b_results.json'
    d=json.loads(Path(fp).read_text())
    record=audit(d,source)
    forged=[]
    def trial(label,fn):
        bad=copy.deepcopy(d)
        fn(bad)
        try:audit(bad,source)
        except (AssertionError,TypeError,ValueError,KeyError,ZeroDivisionError):forged.append(label)
        else:raise AssertionError('audit accepted forged evidence '+label)
    trial('source',lambda q:q.__setitem__('source_sha256','0'*64))
    trial('cell',lambda q:q['cells'].pop())
    trial('raw',lambda q:q['cells'][0]['raw']['direct'][0].__setitem__('wall_ns',-1))
    trial('median',lambda q:q['cells'][0]['median']['projected_native'].__setitem__('wall_ns',1))
    trial('hostile',lambda q:q['cells'][0]['hostile'][0]['accepted'].__setitem__(0,True))
    trial('speedup',lambda q:q['cells'][0]['speedup_over_direct'].__setitem__('wall_ns',1000))
    trial('bool_owner',lambda q:q['cells'][0]['strict_ref_hostile'][0]['accepted'].__setitem__(2,True))
    trial('projection_heap',lambda q:q['cells'][0].__setitem__('fresh_projected_python_heap_bytes',0))
    trial('decision',lambda q:q.__setitem__('decision','PROJECTION_BRIDGE_HEADROOM' if q['decision']!='PROJECTION_BRIDGE_HEADROOM' else 'PROJECTION_BRIDGE_HEADROOM_NOT_PROVEN'))
    record['forged_rejected']=len(forged)
    print('J24K11B_INDEPENDENT_AUDIT='+json.dumps(record,sort_keys=True))
if __name__=='__main__':main()
