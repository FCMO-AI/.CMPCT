#!/usr/bin/env python3
"""O228b independent receipt arithmetic and exact-source audit; no shared result helper."""
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

def audit(path):
    p=Path(path)
    r=json.loads(p.read_text())
    expected=("zero","one-period","two-period","shifted","structured","independent")
    assert r["schema"]=="cmpct-o228b-builder-transfer-v1"
    assert r["status"]=="RESEARCH_ONLY_NO_PRODUCT_CREDIT"
    assert r["released_reference"]=="main@80c358f8824ec1b20d349c92ed94c898090969b0"
    src=Path("research/o228b_builder_transfer_court.py")
    assert r["source_sha256"]==hashlib.sha256(src.read_bytes()).hexdigest()
    rows=r["rows"]
    assert [x["name"] for x in rows]==list(expected)
    qualifies=[]; material=[]; observations=0
    for x in rows:
        assert x["file_integrity_pass"] is True
        assert len(x["logical_sha256"])==len(x["archive_sha256"])==len(x["ref_semantic_sha256"])==64
        assert x["logical_bytes"]==16*1024*1024
        assert 0 < x["run_count"] <= x["cdc_ref_count"]
        assert 1 <= x["max_run"] <= x["cdc_ref_count"]
        assert 0 < x["distinct_owners"] <= x["cdc_ref_count"]
        assert len(x["builder_sha"])==len(x["reader_sha"])==64
        assert x["builder_stats"]["bytes"]==x["archive_bytes"]
        assert x["builder_stats"]["index_comp"]==x["index_bytes"]
        assert x["builder_stats"]["unique_blobs"]>=x["distinct_owners"]
        assert x["builder_stats"]["logical_files"]==1
        assert x["full_archive_byte_delta"]==2*(x["oracle_index_bytes"]-x["index_bytes"])
        assert math.isclose(x["full_archive_pct_delta"],100*x["full_archive_byte_delta"]/x["archive_bytes"],rel_tol=1e-12,abs_tol=1e-12)
        trials=x["decode_trials"]
        assert set(trials)=={"literal","runs"}
        assert len(trials["literal"])==len(trials["runs"])==3
        observations+=6
        med=lambda k:statistics.median(y["heap_peak"] for y in trials[k])
        ratio=med("literal")/max(1,med("runs"))
        assert math.isclose(ratio,x["unpack_heap_ratio"],rel_tol=1e-12)
        for k in ("literal","runs"):
            for sample in trials[k]:
                assert sample["wall_ns"]>=0 and sample["cpu_ns"]>=0 and sample["heap_peak"]>0
                assert sample["entries"]==(x["cdc_ref_count"] if k=="literal" else x["run_count"])
        if x["name"] not in ("zero","independent") and x["max_run"]>=8 and ratio>=2 and x["full_archive_byte_delta"]<=0:
            qualifies.append(x["name"])
        if x["full_archive_pct_delta"]<=-1:material.append(x["name"])
    decision="BOUNDED_BUILDER_TRANSFER_SEED" if len(qualifies)>=2 and material else "NO_BUILDER_TRANSFER_AT_THIS_SCALE"
    assert r["decision"]==decision
    assert r["qualifying_nontrivial"]==qualifies
    assert r["material_savings_profiles"]==material
    assert observations==36
    return {"independent_audit":"PASS","decision":decision,
            "profiles":len(rows),"fresh_decoder_processes":observations,
            "qualifying":qualifies,"material":material,
            "source_sha256":r["source_sha256"],
            "raw_result_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
            "negative_or_ambiguous":[{"profile":x["name"],"delta_bytes":x["full_archive_byte_delta"],
                                    "heap_ratio":round(x["unpack_heap_ratio"],3),"refs":x["cdc_ref_count"],
                                    "runs":x["run_count"]} for x in rows]}

if __name__=="__main__":
    print(json.dumps(audit(sys.argv[1]),indent=2,sort_keys=True))
