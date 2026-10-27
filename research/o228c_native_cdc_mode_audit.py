#!/usr/bin/env python3
"""Independent O228c receipt evaluator: recompute both-mode gates from raw trials."""
import hashlib, json, math, statistics, sys
from pathlib import Path
import msgpack

EXPECTED=("zero","one-period","two-period","shifted","structured","independent")
SZ=16*1024*1024

def check(path):
    p=Path(path); r=json.loads(p.read_text())
    assert r["schema"]=="cmpct-o228c-native-cdc-transfer-v1"
    assert r["status"]=="RESEARCH_ONLY_NO_PRODUCT_CREDIT"
    assert r["source_sha256"]==hashlib.sha256(Path("research/o228c_native_cdc_mode_court.py").read_bytes()).hexdigest()
    assert r["native_source_sha256"]==hashlib.sha256(Path("native/cmpct_cdc.c").read_bytes()).hexdigest()
    assert len(r["native_helper_so_sha256"])==64
    assert r["input_bytes_per_profile"]==SZ
    cases=r["profiles"]
    assert [c["name"] for c in cases]==list(EXPECTED)
    fixed_hash=hashlib.sha256(msgpack.packb([256*1024]*64,use_bin_type=True)).hexdigest()
    changed=[]; qualifies=[]; material=[]; obs=0
    for c in cases:
        assert set(c)=={"name","fallback","native"}
        f,n=c["fallback"],c["native"]
        assert f["logical_sha256"]==n["logical_sha256"]
        assert f["builder_sha"]==n["builder_sha"] and f["reader_sha"]==n["reader_sha"]
        assert f["mode"]=="fallback" and n["mode"]=="native"
        assert f["native_helper_present_during_build"] is False
        assert n["native_helper_present_during_build"] is True
        assert f["chunk_lengths_sha256"]==fixed_hash
        assert f["cdc_ref_count"]==64 and f["chunk_min"]==f["chunk_max"]==256*1024
        for row in (f,n):
            assert row["file_integrity_pass"] is True
            assert row["logical_bytes"]==SZ and row["builder_stats"]["logical_files"]==1
            assert row["builder_stats"]["bytes"]==row["archive_bytes"]
            assert row["builder_stats"]["index_comp"]==row["index_bytes"]
            assert row["builder_stats"]["unique_blobs"]>=row["distinct_owners"]
            assert row["full_archive_byte_delta"]==2*(row["oracle_index_bytes"]-row["index_bytes"])
            assert math.isclose(row["full_archive_pct_delta"],
                                100*row["full_archive_byte_delta"]/row["archive_bytes"], rel_tol=1e-12,abs_tol=1e-12)
            assert 0<row["run_count"]<=row["cdc_ref_count"]
            assert 1<=row["max_run"]<=row["cdc_ref_count"]
            assert 0<row["distinct_owners"]<=row["cdc_ref_count"]
            assert 0<row["chunk_min"]<=row["chunk_max"]<=SZ
            assert row["native_source_sha256"]==r["native_source_sha256"]
            assert row["native_helper_so_sha256"]==r["native_helper_so_sha256"]
            assert len(row["chunk_lengths_sha256"])==64
            for k, count in (("literal",row["cdc_ref_count"]),("runs",row["run_count"])):
                ts=row["decode_trials"][k]; assert len(ts)==3
                for t in ts:
                    assert t["entries"]==count and t["heap_peak"]>0 and t["wall_ns"]>=0 and t["cpu_ns"]>=0
                obs+=len(ts)
            med=lambda k:statistics.median(t["heap_peak"] for t in row["decode_trials"][k])
            assert math.isclose(row["unpack_heap_ratio"],med("literal")/max(1,med("runs")),rel_tol=1e-12)
        if c["name"]!="zero" and f["chunk_lengths_sha256"]!=n["chunk_lengths_sha256"]:
            changed.append(c["name"])
        if c["name"] not in ("zero","independent") and n["max_run"]>=8 and n["unpack_heap_ratio"]>=2 and n["full_archive_byte_delta"]<=0:
            qualifies.append(c["name"])
        if n["full_archive_pct_delta"]<=-1:material.append(c["name"])
    valid=len(changed)>=2
    result=("INSTRUMENT_INVALID" if not valid else "NATIVE_TRANSFER_SEED"
            if len(qualifies)>=2 and material else "NO_NATIVE_BUILDER_TRANSFER_AT_16MIB")
    assert r["decision"]==result
    assert r["mode_difference_profiles"]==changed
    assert r["eligible_nontrivial"]==qualifies
    assert r["material_whole_archive_profiles"]==material
    assert obs==72
    return {"audit":"PASS","decision":result,"profile_pairs":len(cases),"fresh_subprocess_trials":obs,
            "native_boundary_difference_profiles":changed,"qualifying":qualifies,"material":material,
            "raw_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "native_case_results":[{"name":c["name"],"refs":c["native"]["cdc_ref_count"],
                                    "runs":c["native"]["run_count"],"size_delta":c["native"]["full_archive_byte_delta"],
                                    "heap_ratio":c["native"]["unpack_heap_ratio"]} for c in cases]}

if __name__=="__main__":
    print(json.dumps(check(sys.argv[1]),sort_keys=True,indent=2))
