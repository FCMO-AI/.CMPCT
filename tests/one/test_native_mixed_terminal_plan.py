from copy import deepcopy
import pytest
from benchmarks.one.one_g02_compact_observer_handoff_writer import _case
from benchmarks.one.one_g02_native_terminal_fill_batch import _programs
from benchmarks.one.one_g02_native_mixed_terminal_plan import SIZES,adjudicate
from experiments.one.ir import OneError
from experiments.one.prepared_terminal_plan import compile_terminal_plan
from experiments.one.native_mixed_terminal_plan import compile_native_mixed_terminal_plan,execute_native_mixed_terminal_plan
from experiments.one.vm import evaluate

@pytest.mark.parametrize("family",["structured","compressed_like","long_runs","random","near_repeats"])
def test_native_mixed_matches_generic(family):
    source,target=_case(family,64<<10);_,candidate,_,_,_=_programs(source,target)
    expected,_=evaluate(candidate);plan=compile_native_mixed_terminal_plan(compile_terminal_plan(candidate));actual,_=execute_native_mixed_terminal_plan(plan)
    assert actual==expected=={"previous":source,"current":target}

def _rows():
    rows=[]
    for s in SIZES:
        for f in ["structured","compressed_like","long_runs","random","near_repeats"]:
            law=f in {"structured","long_runs"}; rows.append({"bytes":s,"family":f,"semantic_ok":True,"candidate_over_control_wire":0.5 if f=="long_runs" else (0.875 if f=="structured" else 1.0),"mixed_over_literal_traffic":0.9 if law else 1.0,"mixed_over_literal_wall":1.0,"mixed_over_literal_cpu":1.0,"mixed_over_prepared_wall":0.89 if f=="long_runs" else (0.94 if f=="structured" else 1.0),"mixed_over_prepared_cpu":0.89 if f=="long_runs" else (0.94 if f=="structured" else 1.0),"incremental_break_even_wall":1.0,"incremental_break_even_cpu":1.0})
    return rows

def test_adjudicator_advances_only_complete_green_matrix(): assert adjudicate(_rows())=="ADVANCE_NATIVE_MIXED_TERMINAL_PLAN"
def test_missing_row_invalidates(): assert adjudicate(_rows()[:-1])=="INVALIDATE_NATIVE_MIXED_TERMINAL_PLAN"
def test_semantic_failure_invalidates():
    r=_rows();r[0]["semantic_ok"]=False;assert adjudicate(r)=="INVALIDATE_NATIVE_MIXED_TERMINAL_PLAN"
def test_1051_literal_regression_holds():
    r=_rows();r[0]["mixed_over_literal_wall"]=1.051;assert adjudicate(r)=="HOLD_NATIVE_MIXED_TERMINAL_PLAN"
def test_long_run_causal_gate_holds_at_0901():
    r=_rows();x=next(x for x in r if x["bytes"]==(1<<20) and x["family"]=="long_runs");x["mixed_over_prepared_cpu"]=0.901;assert adjudicate(r)=="HOLD_NATIVE_MIXED_TERMINAL_PLAN"
def test_break_even_over_four_holds():
    r=_rows();x=next(x for x in r if x["bytes"]==(1<<20) and x["family"]=="structured");x["incremental_break_even_wall"]=4.01;assert adjudicate(r)=="HOLD_NATIVE_MIXED_TERMINAL_PLAN"
