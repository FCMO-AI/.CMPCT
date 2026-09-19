from __future__ import annotations

"""Exact-identity/performance referee for EG10 hybrid fusion."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from experiments import entropygraph_v030_federated_hybrid_fusion_candidate_v10 as EG10

EG08_MODULE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
EG10_MODULE = "experiments.entropygraph_v030_federated_hybrid_fusion_candidate_v10"
NEUTRAL = {"02_office_workspace","04_analytics_and_database","05_logs_and_telemetry","09_ml_artifacts","10_large_mixed_binary"}
HOSTILE_NAMES = {"01_shifted_versions","02_false_neighbors","03_boundary_churn","05_incompressible"}
REL=0.05
ABS_S=0.003


def H(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def confirmed_reg(base: float, cand: float) -> bool:
    return cand > base*(1.0+REL) and cand > base+ABS_S


def tail_recovery(archive: Path, source: Path, work: Path) -> bool:
    bad=work/(archive.stem+"-primary-corrupt.cmpct"); shutil.copyfile(archive,bad)
    raw=bytearray(bad.read_bytes()); raw[EG10.V25.HDR.size] ^= 1; bad.write_bytes(raw)
    try: return bool(EG10.strong_verify(bad,expected_tree=EG10._treehash(source))["ok"])
    finally: bad.unlink(missing_ok=True)


def one(family: str, source: Path, item: dict, work: Path) -> dict:
    a8=work/"eg08.cmpct"; a10=work/"eg10.cmpct"
    b8=fresh_build(EG08_MODULE,source,a8); b10=fresh_build(EG10_MODULE,source,a10)
    l8=b8["result"]["locality"]; l10=b10["result"]["locality"]
    geometry=(l8["member_count"]==l10["member_count"] and l8["max_decode_unit_bytes"]==l10["max_decode_unit_bytes"] and l8["max_member_read_amplification"]==l10["max_member_read_amplification"])
    same_bytes=a8.read_bytes()==a10.read_bytes()
    cold=b10["result"].get("cold_stream_effort",{})
    return {
        "family":family,"name":item["name"],"tree_sha256":item["tree_sha256"],"logical_bytes":item["logical_bytes"],"files":item["files"],
        "eg08_bytes":b8["archive_bytes"],"eg10_bytes":b10["archive_bytes"],"byte_delta":int(b10["archive_bytes"])-int(b8["archive_bytes"]),
        "eg08_sha256":H(a8),"eg10_sha256":H(a10),"complete_archive_identity":same_bytes,
        "eg08_cpu_s":b8["create_cpu_s"],"eg10_cpu_s":b10["create_cpu_s"],"cpu_ratio":float(b10["create_cpu_s"])/max(float(b8["create_cpu_s"]),1e-12),
        "eg08_wall_s":b8["create_wall_s"],"eg10_wall_s":b10["create_wall_s"],"wall_ratio":float(b10["create_wall_s"])/max(float(b8["create_wall_s"]),1e-12),
        "eg08_peak_rss_kib":b8["peak_rss_kib"],"eg10_peak_rss_kib":b10["peak_rss_kib"],"rss_delta_kib":int(b10["peak_rss_kib"])-int(b8["peak_rss_kib"]),
        "eg08_strong_verify":bool((b8["result"].get("verified") or {}).get("ok")),"eg10_strong_verify":bool((b10["result"].get("verified") or {}).get("ok")),
        "geometry_same":geometry,"tail_recovery":tail_recovery(a10,source,work),
        "confirmed_cpu_regression":confirmed_reg(float(b8["create_cpu_s"]),float(b10["create_cpu_s"])),
        "confirmed_wall_regression":confirmed_reg(float(b8["create_wall_s"]),float(b10["create_wall_s"])),
        "cold_stream_pack_count":cold.get("cold_stream_pack_count"),"changed_cold_stream_pack_count":cold.get("changed_cold_stream_pack_count"),"cold_stream_saved_bytes":cold.get("cold_stream_saved_bytes"),
        "max_amp":l10["max_member_read_amplification"],"max_decode_unit_bytes":l10["max_decode_unit_bytes"],
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("eg10-hybrid-fusion.json")); args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg10-hybrid-") as td:
        work=Path(td); neutral=work/"neutral"; hostile=work/"hostile"; nm=CURRENT.build(neutral); hm=HOSTILE.build(hostile)
        surfaces=[*(('neutral',neutral,x) for x in nm['corpora'] if x['name'] in NEUTRAL),*(('hostile',hostile,x) for x in hm['workloads'] if x['name'] in HOSTILE_NAMES)]
        expected={f"neutral:{x}" for x in NEUTRAL}|{f"hostile:{x}" for x in HOSTILE_NAMES}; actual={f"{f}:{x['name']}" for f,_r,x in surfaces}
        if actual!=expected: raise RuntimeError(f"surface drift expected={sorted(expected)} actual={sorted(actual)}")
        rows=[]
        for family,root,item in surfaces:
            w=work/f"{family}-{item['name']}"; w.mkdir(); rows.append(one(family,root/item['name'],item,w))
        c8=sum(float(r['eg08_cpu_s']) for r in rows); c10=sum(float(r['eg10_cpu_s']) for r in rows); w8=sum(float(r['eg08_wall_s']) for r in rows); w10=sum(float(r['eg10_wall_s']) for r in rows)
        mismatches=[{"family":r['family'],"name":r['name'],"byte_delta":r['byte_delta'],"eg08_bytes":r['eg08_bytes'],"eg10_bytes":r['eg10_bytes']} for r in rows if not r['complete_archive_identity'] or r['byte_delta']!=0]
        conditions={
            "nine_workloads":len(rows)==9,
            "all_complete_archive_identity":all(r['complete_archive_identity'] for r in rows),
            "all_zero_byte_delta":all(r['byte_delta']==0 for r in rows),
            "all_strong_verify":all(r['eg08_strong_verify'] and r['eg10_strong_verify'] for r in rows),
            "all_locality_geometry_same":all(r['geometry_same'] for r in rows),
            "all_tail_recovery":all(r['tail_recovery'] for r in rows),
            "aggregate_cpu_strict_win":c10<c8,
            "aggregate_wall_strict_win":w10<w8,
            "zero_confirmed_cpu_regressions":not any(r['confirmed_cpu_regression'] for r in rows),
            "zero_confirmed_wall_regressions":not any(r['confirmed_wall_regression'] for r in rows),
        }
        verdict="EG10_HYBRID_FUSION_PASSES" if all(conditions.values()) else "EG10_HYBRID_FUSION_BLOCKED"
        out={"schema":"v030-eg10-hybrid-fusion-v1","verdict":verdict,"conditions":conditions,"workloads":rows,"identity_mismatches":mismatches,"aggregate_byte_delta":sum(int(r['byte_delta']) for r in rows),"aggregate_abs_byte_delta":sum(abs(int(r['byte_delta'])) for r in rows),"aggregate_eg08_cpu_s":c8,"aggregate_eg10_cpu_s":c10,"aggregate_cpu_ratio":c10/max(c8,1e-12),"aggregate_eg08_wall_s":w8,"aggregate_eg10_wall_s":w10,"aggregate_wall_ratio":w10/max(w8,1e-12),"max_positive_rss_delta_kib":max(0,max(int(r['rss_delta_kib']) for r in rows)),"aggregate_changed_cold_stream_packs":sum(int(r.get('changed_cold_stream_pack_count') or 0) for r in rows),"aggregate_cold_stream_saved_bytes":sum(int(r.get('cold_stream_saved_bytes') or 0) for r in rows)}
        args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
