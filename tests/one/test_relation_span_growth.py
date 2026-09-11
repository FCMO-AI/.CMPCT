import pytest
from experiments.one.relation_span_growth import grow_relation_spans
from benchmarks.one.one_g02_relation_span_growth import _case, _compile, decide, SIZES, OPS, FAMILIES
from experiments.one.vm import evaluate

@pytest.mark.parametrize('op',['add8','xor'])
def test_growth_reconstructs_long_relation(op):
    parent,child,value,noms=_case(64*1024,op,'long_exact')
    result=grow_relation_spans(parent,child,op=op,value=value,nominations=noms)
    assert result.runs==((0,len(parent)),)
    p=_compile(parent,child,op,value,result.runs)
    assert evaluate(p)[0]['root']==parent+child

@pytest.mark.parametrize('op',['add8','xor'])
def test_false_seed_is_bounded(op):
    parent,child,value,noms=_case(64*1024,op,'false_seed')
    r=grow_relation_spans(parent,child,op=op,value=value,nominations=noms)
    assert r.accepted_bytes==64
    assert r.compared_bytes<=64+4096


def _row(s,o,f):
    return {'size':s,'op':o,'family':f,'semantic_ok':True,'grown_node_ratio_vs_fixed':0.25,'grown_wire_ratio_vs_fixed':1.01,'verify_ratio_vs_fixed':1.10,'grown_relation_bytes':64 if f=='false_seed' else 1000,'verify_bytes':65 if f=='false_seed' else 1000}

def test_decision_law_exact_and_hostile():
    rows=[_row(s,o,f) for s in SIZES for o in OPS for f in FAMILIES]
    assert decide(rows)=='ADVANCE_RELATION_SPAN_GROWTH'
    assert decide(rows[:-1])=='INVALIDATE_RELATION_SPAN_GROWTH'
    bad=[dict(r) for r in rows]; bad[-1]['semantic_ok']=False; assert decide(bad)=='INVALIDATE_RELATION_SPAN_GROWTH'
    bad=[dict(r) for r in rows]; next(r for r in bad if r['size']==1024*1024 and r['family']=='long_exact')['grown_node_ratio_vs_fixed']=0.250001; assert decide(bad)=='HOLD_RELATION_SPAN_GROWTH'
