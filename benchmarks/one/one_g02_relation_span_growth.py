"""ONE-G0.2 writer falsifier: bounded maximal relation-span growth."""
from __future__ import annotations

from hashlib import sha256
import json
import random
import statistics
import time

from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.relation_span_growth import grow_relation_spans
from experiments.one.vm import evaluate
from experiments.one.wire import encode_program

SIZES = (64 * 1024, 256 * 1024, 1024 * 1024)
OPS = ("add8", "xor")
FAMILIES = ("long_exact", "sparse_cracks", "false_seed")
SEED_BYTES = 64
EXTENSION_BYTES = 4096
FIXED_WINDOW = 4096
REPETITIONS = 11
MAX_NODE_RATIO = 0.25
MAX_WIRE_RATIO = 1.01
MAX_VERIFY_RATIO = 1.10


def _limits() -> Limits:
    return Limits(max_nodes=4096, max_output_bytes=2*1024*1024, max_work_bytes=128*1024*1024, max_depth=8)


def _root(node: int, data: bytes) -> dict[str, Root]:
    return {"root": Root(Ref(node), len(data), sha256(data).hexdigest())}


def _case(size: int, op: str, family: str) -> tuple[bytes, bytes, int, tuple[int, ...]]:
    half = size // 2
    rng = random.Random(0x51A90000 ^ size ^ (0xA8 if op == "add8" else 0x58) ^ len(family))
    parent = bytes(rng.randrange(256) for _ in range(half))
    value = 37 if op == "add8" else 0xA7
    child = bytearray(((b + value) & 0xFF) if op == "add8" else (b ^ value) for b in parent)
    if family == "long_exact":
        nominations = (0,)
    elif family == "sparse_cracks":
        nominations_list = [0]
        step = 64 * 1024
        for crack in range(step - 1, half, step):
            child[crack] ^= 1
            resume = crack + 1
            if resume + SEED_BYTES <= half:
                nominations_list.append(resume)
        nominations = tuple(nominations_list)
    elif family == "false_seed":
        # Preserve one real seed then destroy the relation immediately after it. A correct
        # exact grower may spend bounded work proving the nomination false beyond the seed.
        for i in range(SEED_BYTES, half):
            child[i] = rng.randrange(256)
        nominations = (0,)
    else:
        raise ValueError(family)
    return parent, bytes(child), value, nominations


def _compile(parent: bytes, child: bytes, op: str, value: int, runs: tuple[tuple[int,int], ...]) -> Program:
    nodes: list[Node] = [Node("surprise", surprise=parent, declared_length=len(parent)), Node("fill", count=len(parent), value=value, declared_length=len(parent))]
    root_refs = [Ref(0)]
    cursor = 0
    for start, length in runs:
        if start > cursor:
            lit = child[cursor:start]
            lid = len(nodes); nodes.append(Node("surprise", surprise=lit, declared_length=len(lit))); root_refs.append(Ref(lid))
        rid = len(nodes)
        nodes.append(Node(op, refs=(Ref(0, start, length), Ref(1, start, length)), declared_length=length))
        root_refs.append(Ref(rid)); cursor = start + length
    if cursor < len(child):
        lit = child[cursor:]
        lid = len(nodes); nodes.append(Node("surprise", surprise=lit, declared_length=len(lit))); root_refs.append(Ref(lid))
    root_id = len(nodes); data = parent + child
    nodes.append(Node("concat", refs=tuple(root_refs), declared_length=len(data)))
    return Program(tuple(nodes), _root(root_id, data), _limits())


def _fixed_runs(parent: bytes, child: bytes, op: str, value: int) -> tuple[tuple[tuple[int,int], ...], int]:
    runs=[]; checked=0
    for start in range(0, len(parent), FIXED_WINDOW):
        width=min(FIXED_WINDOW,len(parent)-start); ok=True
        for i in range(start,start+width):
            checked += 1
            exp=((parent[i]+value)&255) if op=="add8" else (parent[i]^value)
            if child[i] != exp: ok=False; break
        if ok: runs.append((start,width))
    return tuple(runs), checked


def _median(fn) -> tuple[int,int]:
    ws=[]; cs=[]; fn()
    for _ in range(REPETITIONS):
        w0,c0=time.perf_counter_ns(),time.process_time_ns(); fn(); ws.append(time.perf_counter_ns()-w0); cs.append(time.process_time_ns()-c0)
    return int(statistics.median(ws)), int(statistics.median(cs))


def decide(rows: list[dict]) -> str:
    expected={(s,o,f) for s in SIZES for o in OPS for f in FAMILIES}; observed={(r['size'],r['op'],r['family']) for r in rows}
    if len(rows)!=len(expected) or observed!=expected or any(not r['semantic_ok'] for r in rows): return "INVALIDATE_RELATION_SPAN_GROWTH"
    decisive=[r for r in rows if r['size']==1024*1024 and r['family'] in {'long_exact','sparse_cracks'}]
    if any(r['grown_node_ratio_vs_fixed']>MAX_NODE_RATIO or r['grown_wire_ratio_vs_fixed']>MAX_WIRE_RATIO or r['verify_ratio_vs_fixed']>MAX_VERIFY_RATIO for r in decisive): return "HOLD_RELATION_SPAN_GROWTH"
    negatives=[r for r in rows if r['family']=='false_seed']
    if any(r['grown_relation_bytes']>SEED_BYTES or r['verify_bytes']>SEED_BYTES+EXTENSION_BYTES for r in negatives): return "HOLD_RELATION_SPAN_GROWTH"
    return "ADVANCE_RELATION_SPAN_GROWTH"


def main() -> int:
    rows=[]
    for size in SIZES:
      for op in OPS:
       for family in FAMILIES:
        parent,child,value,nominations=_case(size,op,family)
        fixed_runs,fixed_checks=_fixed_runs(parent,child,op,value); fixed=_compile(parent,child,op,value,fixed_runs)
        result=grow_relation_spans(parent,child,op=op,value=value,nominations=nominations,seed_bytes=SEED_BYTES,extension_bytes=EXTENSION_BYTES)
        grown=_compile(parent,child,op,value,result.runs)
        data=parent+child; fixed_out,_=evaluate(fixed); grown_out,_=evaluate(grown)
        fw,_=encode_program(fixed); gw,_=encode_program(grown)
        ww,wc=_median(lambda: grow_relation_spans(parent,child,op=op,value=value,nominations=nominations,seed_bytes=SEED_BYTES,extension_bytes=EXTENSION_BYTES))
        rows.append({"size":size,"op":op,"family":family,"semantic_ok":fixed_out['root']==grown_out['root']==data,"fixed_nodes":len(fixed.nodes),"grown_nodes":len(grown.nodes),"grown_node_ratio_vs_fixed":len(grown.nodes)/len(fixed.nodes),"fixed_wire_bytes":len(fw),"grown_wire_bytes":len(gw),"grown_wire_ratio_vs_fixed":len(gw)/len(fw),"fixed_verify_bytes":fixed_checks,"verify_bytes":result.compared_bytes,"verify_ratio_vs_fixed":result.compared_bytes/max(1,fixed_checks),"grown_relation_bytes":result.accepted_bytes,"grown_runs":len(result.runs),"writer_wall_ns":ww,"writer_cpu_ns":wc})
    decision=decide(rows); print(json.dumps({"experiment":"ONE-G0.2 relation span growth","decision":decision,"seed_bytes":SEED_BYTES,"extension_bytes":EXTENSION_BYTES,"fixed_window":FIXED_WINDOW,"repetitions":REPETITIONS,"rows":rows},sort_keys=True)); return 0 if decision=="ADVANCE_RELATION_SPAN_GROWTH" else 1

if __name__=='__main__': raise SystemExit(main())
