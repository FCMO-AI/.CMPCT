from __future__ import annotations

from hashlib import sha256
import pytest

from benchmarks.one.one_g02_prepared_terminal_plan import adjudicate, SIZES
from experiments.one.ir import Limits, Node, OneError, Program, Ref, Root
from experiments.one.prepared_terminal_plan import compile_terminal_plan, execute_prepared_terminal_plan
from experiments.one.vm import evaluate


def _program() -> Program:
    nodes=(Node("surprise",surprise=b"ab"),Node("fill",count=4,value=120),Node("concat",refs=(Ref(0),Ref(1)),declared_length=6))
    data=b"abxxxx"
    return Program(nodes,{"root":Root(Ref(2),len(data),sha256(data).hexdigest())},Limits(max_nodes=16,max_output_bytes=1024,max_work_bytes=4096,max_depth=8))


def test_prepared_plan_matches_reference():
    p=_program(); plan=compile_terminal_plan(p)
    assert execute_prepared_terminal_plan(plan)[0]==evaluate(p)[0]=={"root":b"abxxxx"}


def test_prepared_plan_fails_closed_on_nonterminal_child():
    data=b"abab"
    p=Program((Node("surprise",surprise=b"ab"),Node("repeat",refs=(Ref(0),),count=2),Node("concat",refs=(Ref(1),),declared_length=4)),{"root":Root(Ref(2),4,sha256(data).hexdigest())})
    with pytest.raises(OneError): compile_terminal_plan(p)


def _row(size,family):
    return {"bytes":size,"family":family,"semantic_ok":True,"candidate_over_control_wire":0.9,"hot_over_control_traffic":1.0,"hot_over_control_wall":1.0,"hot_over_control_cpu":1.0,"hot_over_bulk_wall":0.8,"hot_over_bulk_cpu":0.8,"break_even_replays_wall":2.0,"break_even_replays_cpu":2.0}


def _matrix():
    from benchmarks.one.one_g02_prepared_terminal_plan import FAMILIES
    rows=[_row(s,f) for s in SIZES for f in FAMILIES]
    for r in rows:
        if r["bytes"]==(1<<20) and r["family"]=="long_runs": r["candidate_over_control_wire"]=0.50
        if r["bytes"]==(1<<20) and r["family"]=="structured": r["candidate_over_control_wire"]=0.87
    return rows


def test_adjudicator_advances_complete_green_matrix():
    assert adjudicate(_matrix())=="ADVANCE_REUSABLE_PREPARED_TERMINAL_PLAN"


def test_adjudicator_blocks_slow_hot_row():
    rows=_matrix(); rows[0]["hot_over_control_cpu"]=1.051
    assert adjudicate(rows)=="HOLD_PREPARED_TERMINAL_PLAN"


def test_adjudicator_blocks_long_break_even_above_four():
    rows=_matrix(); next(r for r in rows if r["family"]=="long_runs")["break_even_replays_wall"]=4.01
    assert adjudicate(rows)=="HOLD_PREPARED_TERMINAL_PLAN"


def test_adjudicator_rejects_missing_row():
    assert adjudicate(_matrix()[:-1])=="INVALIDATE_PREPARED_TERMINAL_PLAN"


def test_adjudicator_rejects_duplicate_replacing_missing():
    rows=_matrix(); rows[-1]=dict(rows[0])
    assert adjudicate(rows)=="INVALIDATE_PREPARED_TERMINAL_PLAN"
