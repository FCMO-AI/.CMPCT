"""ONE-G0.2 end-to-end writer falsifier: block witness -> exact Law -> Program.

The test asks whether a single block observation record can hand exact verification
an actionable (op, value, parent offset, child offset) witness without a second
source-discovery scan, and whether that handoff removes bytes on non-periodic
versioned data rather than merely rediscovering exact reuse.
"""
from __future__ import annotations

from hashlib import sha256
import json
import random
import statistics
import time
import zlib

from experiments.one.block_relation_witness import BLOCK, PROBES, observe_relation_witnesses
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.relation_span_growth import grow_relation_spans
from experiments.one.vm import evaluate
from experiments.one.wire import encode_program

SIZES=(64*1024,256*1024,1024*1024)
FAMILIES=("add8_versioned","xor_versioned","add8_sparse_cracks","xor_sparse_cracks","exact_repeat","random","probe_false_positive")
REPETITIONS=7
SEED_BYTES=64
EXTENSION_BYTES=4096
MAX_POSITIVE_WIRE_RATIO=0.60
MAX_PROBE_RATIO=0.05
MAX_STATE_RATIO=0.60
MAX_FALSE_PROOF_BYTES=8192


def _limits(): return Limits(max_nodes=4096,max_output_bytes=2*1024*1024,max_work_bytes=128*1024*1024,max_depth=8)
def _root(node,data): return {"root":Root(Ref(node),len(data),sha256(data).hexdigest())}
def _literal(data): return Program((Node("surprise",surprise=data,declared_length=len(data)),),_root(0,data),_limits())
def _rel(b,op,value): return ((b+value)&255) if op=="add8" else b^value


def _case(size,family):
    half=size//2; rng=random.Random(0x77110000 ^ size ^ sum(map(ord,family)))
    parent=bytes(rng.randrange(256) for _ in range(half)); value=37
    if family.startswith("xor"): value=0xA7
    if family.startswith("add8") or family.startswith("xor"):
        op="add8" if family.startswith("add8") else "xor"
        child=bytearray(_rel(b,op,value) for b in parent)
        if family.endswith("sparse_cracks"):
            for p in range(64*1024-1,half,64*1024): child[p]^=1
        return parent+bytes(child),op,value,True
    if family=="exact_repeat": return parent+parent,None,None,False
    if family=="random": return parent+bytes(rng.randrange(256) for _ in range(half)),None,None,False
    if family=="probe_false_positive":
        child=bytearray(rng.randrange(256) for _ in range(half))
        # Force only the three observed lanes to imitate add8.  Exact seed proof must
        # reject this structure; the false nomination cost remains charged.
        for off in range(0,half-(half%BLOCK),BLOCK):
            for p in PROBES: child[off+p]=(parent[off+p]+37)&255
        return parent+bytes(child),None,None,False
    raise ValueError(family)


def _compile(parent,child,op,value,runs):
    nodes=[Node("surprise",surprise=parent,declared_length=len(parent)),Node("fill",count=len(parent),value=value,declared_length=len(parent))]
    refs=[Ref(0)]; cursor=0
    for start,length in runs:
        if start>cursor:
            lit=child[cursor:start]; lid=len(nodes);nodes.append(Node("surprise",surprise=lit,declared_length=len(lit)));refs.append(Ref(lid))
        rid=len(nodes);nodes.append(Node(op,refs=(Ref(0,start,length),Ref(1,start,length)),declared_length=length));refs.append(Ref(rid));cursor=start+length
    if cursor<len(child):
        lit=child[cursor:];lid=len(nodes);nodes.append(Node("surprise",surprise=lit,declared_length=len(lit)));refs.append(Ref(lid))
    data=parent+child; root=len(nodes);nodes.append(Node("concat",refs=tuple(refs),declared_length=len(data)))
    return Program(tuple(nodes),_root(root,data),_limits())


def _group_witnesses(obs,half):
    groups={}
    for w in obs.witnesses:
        # Geometry comes from the observation record.  This filter asks whether a
        # nomination links corresponding offsets across the two contiguous versions;
        # it performs no source-byte discovery.
        if w.parent_offset<half<=w.child_offset and w.child_offset-w.parent_offset==half:
            groups.setdefault((w.op,w.value),[]).append(w.child_offset-half)
    return sorted(groups.items(),key=lambda kv:(-len(kv[1]),kv[0]))


def _writer(data):
    half=len(data)//2; parent,child=data[:half],data[half:]
    obs=observe_relation_witnesses(data); total_proof=0; best=None; best_wire=None; accepted=0; chosen=None
    for (op,value),noms in _group_witnesses(obs,half):
        result=grow_relation_spans(parent,child,op=op,value=value,nominations=tuple(noms),seed_bytes=SEED_BYTES,extension_bytes=EXTENSION_BYTES)
        total_proof+=result.compared_bytes
        if not result.runs: continue
        program=_compile(parent,child,op,value,result.runs); wire,_=encode_program(program)
        if best_wire is None or len(wire)<best_wire:
            best,best_wire,accepted,chosen=program,len(wire),result.accepted_bytes,(op,value)
    if best is None:
        best=_literal(data);best_wire=len(encode_program(best)[0])
    return obs,best,best_wire,total_proof,accepted,chosen


def _median_writer(data):
    wall=[];cpu=[];latest=None
    for _ in range(REPETITIONS):
        w0=time.perf_counter_ns();c0=time.process_time_ns();latest=_writer(data);cpu.append(time.process_time_ns()-c0);wall.append(time.perf_counter_ns()-w0)
    return latest,int(statistics.median(wall)),int(statistics.median(cpu))


def decide(rows):
    expected=len(SIZES)*len(FAMILIES)
    if len(rows)!=expected or len({(r['size'],r['family']) for r in rows})!=expected or any(not r['semantic_ok'] for r in rows): return "INVALIDATE_RELATION_WITNESS_TRANSFER"
    positives=[r for r in rows if r['positive']]
    negatives=[r for r in rows if not r['positive']]
    if any(not r['correct_relation'] or r['wire_ratio_vs_literal']>MAX_POSITIVE_WIRE_RATIO or r['accepted_relation_bytes']<=0 for r in positives): return "HOLD_RELATION_WITNESS_TRANSFER"
    if any(r['accepted_relation_bytes']>0 for r in negatives): return "INVALIDATE_RELATION_WITNESS_TRANSFER"
    if any(r['family']=='probe_false_positive' and r['proof_bytes']>MAX_FALSE_PROOF_BYTES for r in negatives): return "HOLD_RELATION_WITNESS_TRANSFER"
    if any(r['probe_ratio']>MAX_PROBE_RATIO or r['state_ratio']>MAX_STATE_RATIO for r in rows): return "HOLD_RELATION_WITNESS_TRANSFER"
    return "ADVANCE_RELATION_WITNESS_TRANSFER"


def main():
    rows=[]
    for size in SIZES:
      for family in FAMILIES:
        data,expected_op,expected_value,positive=_case(size,family); literal=_literal(data); literal_wire=len(encode_program(literal)[0])
        (obs,program,wire,proof,accepted,chosen),wall,cpu=_median_writer(data);out,_=evaluate(program)
        # Exact 64-byte reuse across parent->child would make relation savings
        # ambiguous.  Positive versioned cases must be non-reuse at block granularity.
        half=size//2;pblocks={data[i:i+BLOCK] for i in range(0,half,BLOCK)};cross_reuse=sum(data[i:i+BLOCK] in pblocks for i in range(half,size,BLOCK))
        saved=max(0,literal_wire-wire);extra_s=max(cpu/1e9,1e-12)
        rows.append({"size":size,"family":family,"positive":positive,"semantic_ok":out['root']==data,"chosen":chosen,"correct_relation":((chosen is not None and chosen[0]==expected_op and chosen[1]==expected_value) if positive else chosen is None),"wire_bytes":wire,"literal_wire_bytes":literal_wire,"wire_ratio_vs_literal":wire/literal_wire,"bytes_saved":saved,"proof_bytes":proof,"accepted_relation_bytes":accepted,"source_scan_ratio":obs.source_scan_bytes/len(data),"probe_ratio":obs.probe_bytes/len(data),"state_ratio":obs.modeled_state_bytes/len(data),"retained_records":obs.retained_records,"witnesses":len(obs.witnesses),"cross_version_exact_reuse_blocks":cross_reuse,"writer_wall_ns":wall,"writer_cpu_ns":cpu,"bits_saved_per_cpu_second":saved*8/extra_s})
    decision=decide(rows);print(json.dumps({"experiment":"ONE-G0.2 relation witness transfer","decision":decision,"repetitions":REPETITIONS,"rows":rows},sort_keys=True));return 0 if decision=="ADVANCE_RELATION_WITNESS_TRANSFER" else 1

if __name__=='__main__': raise SystemExit(main())
