#!/usr/bin/env python3
"""O228 independent receipt auditor. No import of the producer or CMPCT product code."""
from __future__ import annotations
import hashlib, json, math, statistics, sys
from pathlib import Path
EXPECTED_CASES={"same","run128","run8","run2","alternating","random32","unique32k"}
EXPECTED_KINDS={"fixed","cdc"}
EXPECTED_N=262144

def main(path):
    raw=Path(path).read_bytes()
    obj=json.loads(raw)
    assert obj["schema"]=="cmpct-o228-oracle-v1"
    assert obj["source_kind"]=="synthetic-r24-index-shape-not-CMPCT-archive"
    rows=obj["rows"]
    assert len(rows)==14
    assert {(r["kind"],r["case"]) for r in rows}=={(k,c) for k in EXPECTED_KINDS for c in EXPECTED_CASES}
    out=[]
    for row in rows:
        n=32768 if row["case"]=="unique32k" else EXPECTED_N
        assert row["logical_refs"]==n and row["logical_size"]>0
        if row["case"]=="same":assert row["run_count"]==1
        if row["case"] in ("run2","run8","run128"):
            stride=int(row["case"][3:])
            assert row["run_count"]==n//stride
        if row["case"] in ("alternating","unique32k"):assert row["run_count"]==n
        if row["case"]=="random32":assert 0<row["run_count"]<=n
        assert row["semantic_sha_equal"] is True and row["selective_byte_equal"] is True
        assert row["hostile_rejects"]==11
        arms=row["arms"]
        assert set(arms)=={"literal","runs"}
        for label, arm in arms.items():
            assert len(arm["trials"])==3
            assert arm["dual_index_zstd"]==2*arm["index_zstd"]
            assert arm["index_raw"]>0 and arm["index_zstd"]>0
            assert len(arm["raw_index_sha256"])==64
            for observation in arm["trials"]:
                assert observation["materialized_storage_entries"]==(n if label=="literal" else row["run_count"])
                for field in ("unpack_wall_ns","unpack_cpu_ns","unpack_heap_peak","unpack_heap_current",
                              "decompress_wall_ns","decompress_cpu_ns","resident_peak_kib"):
                    assert type(observation[field]) is int and observation[field]>=0
        best=min(arms,key=lambda a:arms[a]["dual_index_zstd"])
        assert best==row["best_full_index_oracle"]
        lit,runs=arms["literal"],arms["runs"]
        peak=lambda arm:statistics.median(x["unpack_heap_peak"] for x in arm["trials"])
        unpack=lambda arm:statistics.median(x["unpack_wall_ns"] for x in arm["trials"])
        heap_ratio=peak(lit)/max(1,peak(runs))
        raw_ratio=unpack(lit)/max(1,unpack(runs))
        out.append({"kind":row["kind"],"case":row["case"],"n":n,"run_count":row["run_count"],
                    "literal_zstd":lit["index_zstd"],"runs_zstd":runs["index_zstd"],
                    "bytes_change":runs["index_zstd"]-lit["index_zstd"],
                    "heap_ratio":round(heap_ratio,3),"unpack_time_ratio":round(raw_ratio,3),
                    "oracle_choice":best})
    decisive=[r for r in out if r["n"]==EXPECTED_N and r["case"] in ("same","run128")]
    prospectively_positive=any(r["heap_ratio"]>=4 and r["bytes_change"]<=0 for r in decisive)
    heldout=[r for r in out if r["case"] in ("run8","run128")]
    scoped_heldout=any(r["heap_ratio"]>=2 and r["bytes_change"]<=0 for r in heldout)
    result={"independent_audit":"PASS","raw_sha256":hashlib.sha256(raw).hexdigest(),
            "rows":len(out),"fresh_process_trials":sum(len(v["trials"]) for r in rows for v in r["arms"].values()),
            "promotional_status":"RESEARCH_ONLY_NO_PRODUCT_CREDIT",
            "large_repeat_heap_hypothesis":prospectively_positive,
            "intermediate_repeat_hypothesis":scoped_heldout,
            "observations":out}
    assert result["fresh_process_trials"]==84
    print(json.dumps(result,sort_keys=True,indent=2))
    return result

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: o228_independent_audit.py <raw.json>")
    main(sys.argv[1])
