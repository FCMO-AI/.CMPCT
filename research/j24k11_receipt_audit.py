#!/usr/bin/env python3
"""Independent J24K11 raw receipt auditor: no CMPCT/native import or execution."""
import ast, copy, hashlib, json, math, statistics, sys
from pathlib import Path

EXPECTED_NS={64,512,4096}
EXPECTED_MODES={0,1,2}
EXPECTED_CASES={'expected_plus','expected_minus','descriptor_usize','descriptor_csize','descriptor_codec','descriptor_meta','offset_escape','negative_off','boolean_size','float_csize','subclass_csize','mode_overflow','physical_magic','physical_flags','physical_reserved','physical_usize','physical_csize','physical_meta','truncated_source','empty'}

def code_hash(source):
    tree=ast.parse(Path(source).read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='C_SOURCE':
            return hashlib.sha256(ast.literal_eval(node.value).encode()).hexdigest()
    raise AssertionError('No C_SOURCE in instrument')

def check(d,sha):
    assert d['schema']=='j24k11-science-v1'
    assert d['kind']=='component_oracle_not_product'
    assert d['native_source_sha256']==sha
    assert len(d['cells'])==9
    assert d['sample_count']==324
    assert {(c['streams'],c['mode']) for c in d['cells']}=={(n,m) for n in EXPECTED_NS for m in EXPECTED_MODES}
    assert len(d['negative_cases'])==120
    assert {(n,m,tag) for n,m,tag,_ in d['negative_cases']}=={(n,m,tag) for n in (64,4096) for m in EXPECTED_MODES for tag in EXPECTED_CASES}
    for n,m,tag,accepted in d['negative_cases']:
        assert type(accepted) is bool
        assert accepted==(tag=='empty'), (n,m,tag,accepted)
    for c in d['cells']:
        assert c['class']=='component_oracle_no_product_credit'
        assert c['native_source_sha256']==sha
        assert len(c['source_sha256'])==64 and all(x in '0123456789abcdef' for x in c['source_sha256'])
        assert c['compiled_bytes']>0 and c['bytes']>=64*c['streams']
        assert c['build_ns']>0 and c['build_ns']==d['native_build_ns']
        assert set(c['raw'])=={'method_python','loop_python','native_batch'}
        for label,series in c['raw'].items():
            assert len(series)==12
            for sample in series:
                assert type(sample['wall_ns']) is int and type(sample['cpu_ns']) is int
                assert sample['wall_ns']>=0 and sample['cpu_ns']>=0
            for k in ('wall_ns','cpu_ns'):
                med=statistics.median(z[k] for z in series)
                assert c['median'][label][k]==med,(label,k,med)
        for label in ('method_python','loop_python'):
            for k in ('wall_ns','cpu_ns'):
                value=c['median'][label][k]/c['median']['native_batch'][k]
                assert math.isclose(c['speedup'][label][k],value,rel_tol=1e-12)
    return {
        'status':'PASS',
        'source_hash':sha,
        'samples':324,
        'mutants':120,
        'falsifiers_rejected':114,
        'decisive_min_speedup':min(c['speedup'][ctl][k] for c in d['cells'] if c['streams']==4096 for ctl in ('method_python','loop_python') for k in ('wall_ns','cpu_ns'))
    }

def main():
    source=sys.argv[1] if len(sys.argv)>1 else 'research/j24k11_bhdr_oracle.py'
    file=sys.argv[2] if len(sys.argv)>2 else 'j24k11_results.json'
    d=json.loads(Path(file).read_text())
    sha=code_hash(source)
    summary=check(d,sha)
    mutations=[]
    def trial(label,fn):
        bad=copy.deepcopy(d);fn(bad)
        try:check(bad,sha)
        except (AssertionError,KeyError,ZeroDivisionError,TypeError,ValueError):mutations.append(label)
        else:raise AssertionError('auditor accepted forged receipt '+label)
    trial('median',lambda x:x['cells'][0]['median']['native_batch'].__setitem__('wall_ns',1))
    trial('raw',lambda x:x['cells'][0]['raw']['native_batch'][0].__setitem__('cpu_ns',-1))
    trial('source',lambda x:x.__setitem__('native_source_sha256','0'*64))
    trial('cell',lambda x:x['cells'].pop())
    trial('negative',lambda x:x['negative_cases'][0].__setitem__(3,True))
    trial('duplicate',lambda x:x['cells'][1].__setitem__('mode',0))
    trial('ratio',lambda x:x['cells'][0]['speedup']['loop_python'].__setitem__('wall_ns',1000000))
    trial('sample',lambda x:x['cells'][0]['raw']['native_batch'].pop())
    summary['forged_receipts_rejected']=len(mutations)
    print('J24K11_INDEPENDENT_AUDIT='+json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
