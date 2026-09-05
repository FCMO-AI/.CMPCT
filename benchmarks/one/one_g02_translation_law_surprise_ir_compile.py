"""ONE-G0.2 compile edited translation Law+Surprise into the existing generic ONE IR.

Referee freeze
==============
The Law-persistence result must not become a disguised new codec/opcode. This experiment
compiles the same edited-version family using only existing ONE-G0.1 primitives:
- one `surprise` node containing the already-stored base;
- ordinary Ref ranges back into that node for predicted spans;
- one-byte `surprise` nodes at mismatches;
- one generic `concat` node for the edited version.
No new reader operation is added.

The exact experimental wire is encoded and independently decoded, then the reference VM
must reconstruct/authenticate both roots. Incremental wire cost is measured by subtracting
an otherwise-identical base-only ONE program, so the existing base bytes are not gifted or
charged twice.

Frozen gates on all 64 edited-version rows:
- wire roundtrip canonical and VM reconstruction exact;
- node count <= 66 (base + <=64 Surprises + concat);
- dependency depth <=2;
- incremental ONE wire for the second version <1% of literal second-version bytes;
- incremental reader work is measured, not used as a density escape hatch.

This tests representation unification and current-reader debt, not discovery or product speed.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
import random

from benchmarks.one.one_g02_epoch_min_edited_version_transfer import (
    MASTER_SEED, BASE_SIZES, BASES_PER_SIZE, MUTATION_COUNTS, _edited,
)
from experiments.one.ir import Limits, Node, Program, Ref, Root
from experiments.one.vm import evaluate
from experiments.one.wire import decode_program, encode_program


def _programs(base: bytes, edited: bytes):
    limits=Limits(max_nodes=256,max_output_bytes=2*len(base)+1024,max_work_bytes=16*len(base)+65536,max_depth=8)
    base_node=Node("surprise",surprise=base,declared_length=len(base))
    base_root=Root(Ref(0),len(base),sha256(base).hexdigest())
    baseline=Program((base_node,),{"base":base_root},limits)

    mismatches=[i for i,(a,b) in enumerate(zip(base,edited)) if a!=b]
    nodes=[base_node]
    surprise_ids={}
    for pos in mismatches:
        surprise_ids[pos]=len(nodes)
        nodes.append(Node("surprise",surprise=bytes([edited[pos]]),declared_length=1))
    refs=[]; cursor=0
    for pos in mismatches:
        if pos>cursor: refs.append(Ref(0,cursor,pos-cursor))
        refs.append(Ref(surprise_ids[pos],0,1)); cursor=pos+1
    if cursor<len(base): refs.append(Ref(0,cursor,len(base)-cursor))
    edited_id=len(nodes)
    nodes.append(Node("concat",refs=tuple(refs),declared_length=len(edited)))
    full=Program(tuple(nodes),{
        "base":base_root,
        "edited":Root(Ref(edited_id),len(edited),sha256(edited).hexdigest()),
    },limits)
    return baseline,full,len(mismatches)


def run():
    master=random.Random(MASTER_SEED); rows=[]; failures=[]
    total_literal=total_incremental_wire=total_incremental_work=0
    for size in BASE_SIZES:
        for base_index in range(BASES_PER_SIZE):
            seed=master.getrandbits(64); base=random.Random(seed).randbytes(size)
            for mutations in MUTATION_COUNTS:
                edited=_edited(base,random.Random(seed^(mutations<<32)^0xA11CE5EED),mutations)
                baseline,full,mismatch_count=_programs(base,edited)
                bw,_=encode_program(baseline); fw,fstats=encode_program(full)
                decoded=decode_program(fw); outputs,stats=evaluate(decoded)
                _,bstats=evaluate(decode_program(bw))
                incremental=len(fw)-len(bw); work=stats.work_bytes-bstats.work_bytes
                reasons=[]
                if outputs["base"]!=base or outputs["edited"]!=edited: reasons.append("reconstruction")
                if encode_program(decoded)[0]!=fw: reasons.append("wire_roundtrip")
                if len(full.nodes)>66: reasons.append("nodes")
                if stats.max_depth>2: reasons.append("depth")
                if incremental>=size//100: reasons.append("incremental_wire_ge_1pct")
                if reasons: failures.append({"base_bytes":size,"base_index":base_index,"mutations":mutations,"reasons":reasons})
                rows.append({"base_bytes":size,"base_index":base_index,"mutation_count":mutations,
                             "mismatches":mismatch_count,"nodes":len(full.nodes),"max_depth":stats.max_depth,
                             "baseline_wire_bytes":len(bw),"full_wire_bytes":len(fw),
                             "incremental_second_version_wire_bytes":incremental,
                             "incremental_wire_fraction_of_literal":incremental/size,
                             "full_surprise_bytes":fstats.surprise_bytes,
                             "full_control_integrity_bytes":fstats.control_integrity_bytes,
                             "incremental_reader_work_bytes":work,
                             "incremental_reader_work_per_output_byte":work/size,
                             "failures":reasons})
                total_literal+=size;total_incremental_wire+=incremental;total_incremental_work+=work
    return {"schema":"cmpct-one-g02-law-surprise-ir-compile-v1","experimental_version":"ONE-G0.2",
            "source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rows":len(rows),"gate_failures":failures,
            "total_literal_second_version_bytes":total_literal,
            "total_incremental_one_wire_bytes":total_incremental_wire,
            "incremental_wire_fraction_of_literal":total_incremental_wire/total_literal,
            "total_incremental_reader_work_bytes":total_incremental_work,
            "incremental_reader_work_per_output_byte":total_incremental_work/total_literal,
            "decision":"generic_one_ir_subsumes_translation_law_surprise" if not failures else "generic_one_ir_compile_blocked",
            "claim_boundary":"existing generic ONE IR/wire/VM representation evidence only; no discovery/native/product/comparator/release authority",
            "results":rows}

if __name__=="__main__": print(json.dumps(run(),indent=2,sort_keys=True))
