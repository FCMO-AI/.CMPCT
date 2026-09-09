from experiments.one.block_relation_witness import observe_relation_witnesses
from benchmarks.one.one_g02_relation_witness_transfer import _case, _writer


def test_versioned_add8_yields_actionable_witness_and_exact_program():
    data,op,value,positive=_case(64*1024,"add8_versioned")
    obs,program,wire,proof,accepted,chosen=_writer(data)
    assert positive and chosen==(op,value)
    assert accepted>0 and proof>0
    assert obs.source_scan_bytes==len(data)


def test_versioned_xor_yields_actionable_witness():
    data,op,value,_=_case(64*1024,"xor_versioned")
    obs=observe_relation_witnesses(data)
    half=len(data)//2
    assert any(w.op==op and w.value==value and w.child_offset-w.parent_offset==half for w in obs.witnesses)


def test_probe_only_false_positive_never_authorizes_law():
    data,_,_,_=_case(64*1024,"probe_false_positive")
    obs,program,wire,proof,accepted,chosen=_writer(data)
    assert obs.witnesses
    assert proof>0
    assert accepted==0
    assert chosen is None


def test_exact_repeat_does_not_become_nonzero_relation():
    data,_,_,_=_case(64*1024,"exact_repeat")
    _,_,_,_,accepted,chosen=_writer(data)
    assert accepted==0 and chosen is None
