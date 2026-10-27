#!/usr/bin/env python3
"""Independent O229 result referee; never imports the tested scientific instrument."""
import hashlib, json, math, statistics, sys
from collections import defaultdict
from pathlib import Path

FIXED=("zero","one-period","two-period","shifted","structured","independent")
TEST=("periodic-altseed","two-period-altseed","shifted-altseed","boundary-insertion",
      "mixed-blocks","random-altseed","late-shift")
ALL=FIXED+TEST
MODES=("fixed","native","admitted")
def med(xs):return statistics.median(xs)
def audit(filename):
    raw=json.loads(Path(filename).read_text())
    assert raw["schema"]=="cmpct-o229-prefix-admission-v1"
    assert raw["status"]=="RESEARCH_ONLY_NO_PRODUCT_CREDIT"
    assert raw["sample_bytes"]==4<<20 and raw["full_bytes"]==16<<20
    path=Path(__file__).with_name("o229_prefix_chunker_court.py")
    assert hashlib.sha256(path.read_bytes()).hexdigest()==raw["source_sha256"]
    assert len(raw["rows"])==117
    groups=defaultdict(list)
    for row in raw["rows"]:
        assert row["name"] in ALL and row["mode"] in MODES
        assert row["rep"] in range(3) and row["verified"]
        assert row["full"]["verified"] and row["sha"]==row["full"]["source_sha"]
        assert row["full"]["chunk_count"]>0  # exact 16-MiB source size is fixed by audited generator and SHA
        assert row["full"]["mode"]==row["selected"]
        assert row["peak_vmhwm_kib"]>0 and row["total_wall_ns"]>0 and row["total_cpu_ns"]>0
        if row["mode"]=="admitted":
            f=row["sample_fixed"];n=row["sample_native"]
            assert f["chunk_count"]>0 and n["chunk_count"]>0  # bounded 4-MiB prefix from source-exact generator
            assert f["source_sha"]==n["source_sha"]
            assert f["mode"]=="fixed" and n["mode"]=="native"
            assert row["selected"]==("native" if n["bytes"]*5<=f["bytes"]*4 else "fixed")
            assert row["total_wall_ns"]==f["wall_ns"]+n["wall_ns"]+row["full"]["wall_ns"]
            assert row["total_cpu_ns"]==f["cpu_ns"]+n["cpu_ns"]+row["full"]["cpu_ns"]
        else:
            assert row["selected"]==row["mode"]
            assert row["sample_fixed"] is None and row["sample_native"] is None
            assert row["total_wall_ns"]==row["full"]["wall_ns"]
            assert row["total_cpu_ns"]==row["full"]["cpu_ns"]
        groups[(row["name"],row["mode"])].append(row)
    assert len(groups)==39
    records=[]
    for name in ALL:
        by={}
        for mode in MODES:
            rows=groups[(name,mode)]
            assert sorted(x["rep"] for x in rows)==[0,1,2]
            for field in ("sha","selected"):
                assert len({x[field] for x in rows})==1
            assert len({x["full"]["archive_sha"] for x in rows})==1
            by[mode]=dict(
                bytes=rows[0]["full"]["bytes"],sha=rows[0]["full"]["archive_sha"],
                selected=rows[0]["selected"],
                wall=med(x["total_wall_ns"] for x in rows),
                cpu=med(x["total_cpu_ns"] for x in rows),
                rss=med(x["peak_vmhwm_kib"] for x in rows))
        assert by["fixed"]["bytes"]>0 and by["native"]["bytes"]>0
        assert by["admitted"]["sha"]==by[by["admitted"]["selected"]]["sha"]
        records.append(dict(name=name,by=by,gifted=min(by["fixed"]["bytes"],by["native"]["bytes"])))
    heldout=[r for r in records if r["name"] in TEST]
    tot=lambda m,f:sum(r["by"][m][f] for r in heldout)
    fixed=tot("fixed","bytes");chosen=tot("admitted","bytes")
    oracle=sum(r["gifted"] for r in heldout);gap=fixed-oracle
    capture=(fixed-chosen)/gap if gap>0 else None
    regret=max(r["by"]["admitted"]["bytes"]/r["gifted"]-1 for r in heldout)
    wall=tot("admitted","wall")/tot("fixed","wall")
    cpu=tot("admitted","cpu")/tot("fixed","cpu")
    rss=max(r["by"]["admitted"]["rss"]-r["by"]["fixed"]["rss"] for r in heldout)
    bp=gap>0 and capture>=.75 and regret<=.25
    cp=wall<=1.5 and cpu<=1.5 and rss<=10240
    verdict="PREFIX_PREDICTOR_FALSIFIED" if not bp else (
        "BYTE_HEADROOM_EXECUTION_DEBT" if not cp else "BOUNDED_CHUNKER_ADMISSION_SEED")
    result=raw["summary"]
    assert result["decision"]==verdict
    checks={
        "gifted_gap_capture":capture,"max_byte_regret":regret,"charged_wall_ratio":wall,
        "charged_cpu_ratio":cpu,"max_rss_extra_kib":rss,
        "heldout_fixed_bytes":fixed,"heldout_selected_bytes":chosen,
        "heldout_gifted_bytes":oracle,"gifted_gap_bytes":gap}
    for k,v in checks.items():
        got=result[k]
        if isinstance(v,float):assert math.isclose(v,got,rel_tol=1e-10,abs_tol=1e-10),k
        else:assert v==got,k
    assert result["byte_gate_pass"]==bp and result["cost_gate_pass"]==cp
    assert result["independent_process_observations"]==117
    print(json.dumps({"audit":"PASS","decision":verdict,"observations":117,
          "heldout_profiles":len(TEST),**checks},sort_keys=True))
if __name__=="__main__":
    assert len(sys.argv)==2
    audit(sys.argv[1])
