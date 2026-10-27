#!/usr/bin/env python3
"""Independent receipt verifier for O223; never imports the instrument itself."""
import collections, hashlib, json, math, statistics, sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text())
assert d["schema"]=="o223-r24-futures-rss-v1"
assert d["source_parent"]=="c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
assert d["reader_blob"]=="dbd4ac576a05a47eae97e1e40de89cf1de440516"
assert d["prereg_commit"]=="fc1b0347f06ef746d253614b516ead241e29ebed"
kinds=("fixed","cdc");layouts=("repeat","eight");ns=(4096,65536,262144)
arms=("eager","bounded512","bounded64","serial","open_only")
samples=d["samples"];expected_keys=set((k,l,n,a,r)
    for k in kinds for l in layouts for n in ns for a in arms for r in range(3))
assert len(samples)==len(expected_keys)==180
actual_keys=[(s["kind"],s["layout"],s["n"],s["arm"],s["rep"]) for s in samples]
assert len(actual_keys)==len(set(actual_keys)) and set(actual_keys)==expected_keys
archive_keys={(a["kind"],a["layout"],a["n"]):(a["archive_sha256"],a["logical_sha256"]) for a in d["archives"]}
assert len(archive_keys)==12
for s in samples:
    expected_archive,expected_logical=archive_keys[(s["kind"],s["layout"],s["n"])]
    assert s["archive_sha256"]==expected_archive and s["expected_sha256"]==expected_logical
    assert s["actual_sha256"]==(None if s["arm"]=="open_only" else expected_logical)
    assert s["py"] and s["pid"]>0
    for key in ("read_wall_ms","read_cpu_ms","session_wall_ms","session_cpu_ms","open_wall_ms","process_wall_ms","peak_rss_kib"):
        assert isinstance(s[key],(int,float)) and math.isfinite(s[key]) and s[key]>=0
    assert s["session_wall_ms"]+0.01>=s["read_wall_ms"]
assert len(d["variable_payload_control"])==6
assert {(r["kind"],r["arm"]) for r in d["variable_payload_control"]}==set((k,a)
    for k in kinds for a in ("serial","bounded64","bounded512"))
summaries=d["summary"];assert len(summaries)==12
decision_rows=[]
for k in kinds:
    for l in layouts:
        for n in ns:
            row=next(x for x in summaries if (x["kind"],x["layout"],x["n"])==(k,l,n))
            comp={}
            for arm in arms:
                rr=[s for s in samples if (s["kind"],s["layout"],s["n"],s["arm"])==(k,l,n,arm)]
                assert len(rr)==3
                comp[arm]={field:statistics.median(s[field] for s in rr) for field in
                  ("read_wall_ms","read_cpu_ms","session_wall_ms","session_cpu_ms","peak_rss_kib")}
            for arm in arms:
                for field,val in comp[arm].items():
                    assert math.isclose(row["arms"][arm][field],val,rel_tol=1e-12,abs_tol=1e-9)
            delta=(comp["eager"]["peak_rss_kib"]-comp["bounded512"]["peak_rss_kib"])/1024
            ratio=comp["bounded512"]["session_wall_ms"]/comp["eager"]["session_wall_ms"]
            serial=comp["serial"]["session_wall_ms"]/comp["eager"]["session_wall_ms"]
            assert math.isclose(row["bounded_rss_save_mib"],delta,rel_tol=1e-12,abs_tol=1e-9)
            assert math.isclose(row["bounded_session_wall_ratio"],ratio,rel_tol=1e-12,abs_tol=1e-9)
            assert math.isclose(row["serial_session_wall_ratio"],serial,rel_tol=1e-12,abs_tol=1e-9)
            if n==262144:decision_rows.append((k,l,delta,ratio,serial))
passed=all(delta>=128 and ratio<=1.10 for _,_,delta,ratio,_ in decision_rows)
assert d["decision"]==("BOUND_FUTURE_HWM_MATERIAL" if passed else
                      "BOUND_FUTURE_PRODUCT_HEADROOM_NOT_PROVEN")
print(json.dumps({"audit":"PASS","raw_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
    "samples":len(samples),"matched_groups":len(summaries),"decisive":decision_rows,
    "decision":d["decision"]},sort_keys=True))
