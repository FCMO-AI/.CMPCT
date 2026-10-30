#!/usr/bin/env python3
"""J24G62b: follow-up physical comparator with no per-op deepcopy (Reader geometry).
The first hosted J24G62 result remains immutable and separately cited.
"""
from __future__ import annotations

import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import tempfile
import time
import tracemalloc

import msgpack
from cmpct.builder import Builder
from cmpct.journal_replay import _apply_journal_ops
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import make_case, sha256_file, verify_source
from j24g62_crossgen_rename_oracle import (
    differential_cases, factored_replay, read_wire, original_replay,
)

N=2048
D=63
PREREG="dd401637a9b53638f1c700651074828a5aaa2141"
PREVIOUS_HEAD="e3948f6dee571b7b682f72ae5016caf4b6e95d83"


def original_no_op_copy(base, deltas):
    idx=copy.deepcopy(base)
    for delta in deltas:
        # Authentic Writer one-op renames contain only strings; no aliased rows
        # from put are possible in this strictly source-verified stratum.
        assert len(delta["ops"])==1 and delta["ops"][0][0]=="ren"
        idx["blobs"].extend(copy.deepcopy(delta.get("blobs",[])))
        _apply_journal_ops(idx, delta["ops"])
    return idx


def bench(base,deltas,kind):
    gc.collect()
    w=time.perf_counter_ns()
    cpu=time.process_time_ns()
    if kind=="baseline_no_op_copy":
        out=original_no_op_copy(base,deltas)
    else:
        out,route=factored_replay(base,deltas)
        assert route=="factored"
    return out, {"wall_ns":time.perf_counter_ns()-w,
                 "cpu_ns":time.process_time_ns()-cpu,"variant":kind}


def main():
    source=verify_source()
    differential=differential_cases()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g62b-") as td:
        root=Path(td)
        tree=root/"tree";tree.mkdir()
        for i in range(N):
            (tree/f"f{i:04d}.dat").write_bytes(hashlib.sha256(f"generic-record-{i}".encode()).digest()*2)
        snaps=make_case(tree,root,N)
        phys=snaps[str(D)]
        path=Path(phys["paths"]["chain"])
        original_sha=sha256_file(path)
        base,deltas=read_wire(path)
        assert len(deltas)==D
        deltas_frozen=copy.deepcopy(deltas)
        old=original_replay(base,deltas)
        control=original_no_op_copy(base,deltas)
        new,route=factored_replay(base,deltas)
        assert route=="factored" and new==control==old
        assert msgpack.packb(control,use_bin_type=True)==msgpack.packb(new,use_bin_type=True)
        assert deltas==deltas_frozen,"Reader-like reference mutated its signed op input"
        with CMPCT(path) as ar:
            assert ar.index==control and ar.verify()==N
        assert preflight_archive(path)["files"]==N
        assert sha256_file(path)==original_sha
        samples=[]
        for block in range(8):
            seq=("baseline_no_op_copy","factored","factored","baseline_no_op_copy") if block%2==0 else (
                "factored","baseline_no_op_copy","baseline_no_op_copy","factored")
            for phase,kind in enumerate(seq):
                out,row=bench(base,deltas,kind)
                assert out==old
                samples.append({"block":block,"phase":phase,**row})
        assert deltas==deltas_frozen,"measurement mutated signed deltas"
        peaks={}
        for kind in ("baseline_no_op_copy","factored"):
            gc.collect()
            tracemalloc.start()
            out=original_no_op_copy(base,deltas) if kind=="baseline_no_op_copy" else factored_replay(base,deltas)[0]
            cur,peak=tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert out==old
            peaks[kind]={"peak_traced_bytes":peak,"retained_traced_bytes":cur}
        bas=[s for s in samples if s["variant"]=="baseline_no_op_copy"]
        opt=[s for s in samples if s["variant"]=="factored"]
        a=statistics.median(s["wall_ns"] for s in bas)
        b=statistics.median(s["wall_ns"] for s in opt)
        extra=peaks["factored"]["peak_traced_bytes"]-peaks["baseline_no_op_copy"]["peak_traced_bytes"]
        dec="NO_OP_COPY_CONTROL_SURVIVES" if a/b>=3 and extra<=2097152 else "NO_OP_COPY_CONTROL_KILLS_OR_NARROWS"
        result={
          "schema":"cmpct-j24g62b-no-op-copy-control-v1","status":dec,
          "source":source,"prereg_commit":PREREG,
          "prior_result_source":PREVIOUS_HEAD,"members":N,"depth":D,
          "archive_sha256":original_sha,
          "archive_bytes":phys["archive_bytes"],"differential":differential,
          "samples":samples,
          "wall_medians_ns":{"baseline_no_op_copy":a,"factored":b},
          "cpu_medians_ns":{"baseline_no_op_copy":statistics.median(s["cpu_ns"] for s in bas),
                             "factored":statistics.median(s["cpu_ns"] for s in opt)},
          "wall_speedup":a/b,"peaks":peaks,"extra_traced_peak_bytes":extra,
          "platform":platform.platform(),
          "limitations":["replay-only, no Reader-open product claim","no physical peak RSS",
                         "no extra archive bytes emitted","all deltas one-op rename without sparse xattrs",
                         "no full release or hostile recovery/economics"]
        }
    dst=Path(os.getenv("J24G62B_RESULT","evidence/j24g62b-result.json"))
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24G62B_HEAD",source["head"])
    print("J24G62B_DECISION",dec)
    print("J24G62B_SPEEDUP",a/b)
    print("J24G62B_EXTRA_PEAK",extra)
    print("J24G62B_SHA256",sha256_file(dst))


if __name__=="__main__":
    main()
