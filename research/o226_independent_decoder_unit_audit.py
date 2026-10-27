#!/usr/bin/env python3
"""O226 independent receipt auditor. Does not import the experiment or Reader."""
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

raw=Path(sys.argv[1]).read_bytes()
d=json.loads(raw)
assert d["schema"]=="o226-decoder-unit-ownership-v1"
assert d["source_parent"]=="c5e13bb3fbb4cdade8b64246658ce7c7818de41f"
assert d["reader_blob"]=="dbd4ac576a05a47eae97e1e40de89cf1de440516"
assert d["prereg_commit"]=="ec882b0fc0ddf5e204d008f46ca5585be33ed6d2"
families=("zstd_entropy_once","deflate_entropy_once","zstd_entropy_twice","deflate_entropy_twice","zstd_pattern_twice","deflate_pattern_twice")
kinds=("fixed","cdc")
arms=("eager","serial","bounded64")
assert tuple(d["families"])==families
assert tuple(d["kinds"])==kinds
assert tuple(d["arms"])==arms
assert len(d["archives"])==12
manifest={(a["family"],a["kind"]):a for a in d["archives"]}
assert len(manifest)==12 and set(manifest)=={(f,k) for f in families for k in kinds}
for (f,k),m in manifest.items():
    for h in ("archive_sha256","logical_sha256"):
        assert len(m[h])==64 and all(c in "0123456789abcdef" for c in m[h])
    assert m["archive_bytes"]>0 and m["logical_bytes"]>0 and m["distinct_owners"]>0
    assert sum(m["codec_mix"].values())==m["distinct_owners"]
    assert m["distinct_owners"]==12
    assert m["refs"]==(12 if f.endswith("_once") else 24)
    assert m["logical_bytes"]==m["refs"]*3*1024*1024
    assert m["archive_bytes"]>0

sample_keys={(f,k,a,r) for f in families for k in kinds for a in arms for r in range(3)}
samples=d["samples"]
assert len(samples)==len(sample_keys)==108
seen=set();pids=set();by_key={}
for s in samples:
    key=s["family"],s["kind"],s["arm"],s["rep"]
    assert key in sample_keys and key not in seen
    seen.add(key)
    m=manifest[key[:2]]
    assert s["archive_sha256"]==m["archive_sha256"]
    assert s["archive_bytes"]==m["archive_bytes"]
    assert s["logical_sha256"]==m["logical_sha256"]
    assert s["expected_sha256"]==m["logical_sha256"]
    assert s["logical_bytes"]==m["logical_bytes"]
    assert s["python"] and isinstance(s["pid"],int) and s["pid"]>0
    pids.add(s["pid"])
    for name in ("read_wall_ms","read_cpu_ms","session_wall_ms","session_cpu_ms",
                 "open_wall_ms","open_cpu_ms","process_wall_ms","VmHWM_kib","VmRSS_kib"):
        v=s[name]
        assert type(v) in (int,float) and math.isfinite(v) and v>=0,(key,name,v)
    assert s["VmHWM_kib"]>=s["VmRSS_kib"]
    assert s["session_wall_ms"]+0.02>=s["read_wall_ms"]
    assert s["session_cpu_ms"]+0.02>=s["read_cpu_ms"]
    assert s["process_wall_ms"]+100>=s["session_wall_ms"],key
    by_key[key]=s
assert seen==sample_keys and len(pids)==108,"fresh subprocess ownership must be unique"
positive=d["heldout_controls"]
negative=d["hostile_controls"]
assert len(positive)==6 and len(negative)==6
assert {(r["kind"],r["arm"]) for r in positive}=={(k,a) for k in kinds for a in arms}
assert {(r["kind"],r["arm"]) for r in negative}=={(k,a) for k in kinds for a in arms}
assert all(r["rejected"] is True for r in negative)
for k in kinds:
    rr=[r for r in positive if r["kind"]==k]
    assert len({r["sha256"] for r in rr})==1
    assert len({r["bytes"] for r in rr})==1
summaries=d["summary"]
assert len(summaries)==12
summary_map={(g["family"],g["kind"]):g for g in summaries}
assert set(summary_map)==set(manifest)
def close(a,b):
    return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-7)
for (family,kind),g in summary_map.items():
    for arm in arms:
        rr=[by_key[(family,kind,arm,r)] for r in range(3)]
        for field in ("read_wall_ms","read_cpu_ms","session_wall_ms",
                      "session_cpu_ms","open_wall_ms","VmHWM_kib"):
            assert close(statistics.median(x[field] for x in rr),g["arms"][arm][field])
    e=g["arms"]["eager"];s=g["arms"]["serial"];b=g["arms"]["bounded64"]
    assert e["session_wall_ms"]>0 and s["session_wall_ms"]>0 and b["session_wall_ms"]>0
    assert close(g["eager_serial_speedup"],e["session_wall_ms"]/s["session_wall_ms"])
    assert close(g["serial_eager_ratio"],s["session_wall_ms"]/e["session_wall_ms"])
    assert close(g["bounded_eager_speedup"],e["session_wall_ms"]/b["session_wall_ms"])
    assert close(g["bounded_serial_speedup"],s["session_wall_ms"]/b["session_wall_ms"])
veto=any(g["serial_eager_ratio"]>1.10 or
    g["arms"]["serial"]["VmHWM_kib"]-g["arms"]["eager"]["VmHWM_kib"]>8192
    for g in summaries)
high_entropy=("zstd_entropy_once","deflate_entropy_once",
              "zstd_entropy_twice","deflate_entropy_twice")
strong=any(g["family"] in high_entropy and
    g["arms"]["serial"]["read_wall_ms"]>=1.20*g["arms"]["eager"]["read_wall_ms"] and
    g["arms"]["serial"]["session_wall_ms"]>=1.20*g["arms"]["eager"]["session_wall_ms"]
    for g in summaries)
decision=("EAGER_PARALLEL_COUNTEREXAMPLE" if strong else
          "SERIAL_TRANSFER_VETO" if veto else "BOUNDED_SERIAL_TRANSFER")
assert d["any_full_veto"] is veto
assert d["strong_parallel"] is strong
assert d["decision"]==decision
bounded=[]
for g in summaries:
    if min(g["bounded_eager_speedup"],g["bounded_serial_speedup"])>=1.20 and (
        g["arms"]["bounded64"]["VmHWM_kib"]<=min(g["arms"]["eager"]["VmHWM_kib"],
                                                    g["arms"]["serial"]["VmHWM_kib"])+8192):
        bounded.append((g["family"],g["kind"]))
assert {tuple((r["family"],r["kind"])) for r in d["bounded_subset_seed"]}==set(bounded)
assert len(d["bounded_subset_seed"])==len(bounded)
print(json.dumps({
    "audit":"PASS","evidence_sha256":hashlib.sha256(raw).hexdigest(),
    "fresh_samples":len(samples),"distinct_child_pids":len(pids),
    "profiles":len(summaries),"byte_controls":len(positive),
    "hostile_refusals":len(negative),"decision":d["decision"],
    "bounded_subset_seed":d["bounded_subset_seed"],
    "serial_full_veto":veto,"strong_parallel":strong
},sort_keys=True))
