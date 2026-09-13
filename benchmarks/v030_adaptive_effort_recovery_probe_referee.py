from __future__ import annotations

"""H-EFFORT-3: preregistered one-probe repair of C25EG08's false monotonic stop law.

Scientific question: after the first strictly-worse policy rung, can exactly one
fixed level-9 recovery probe recover useful later compression without paying the
full level-19 oracle everywhere?

The rule is deliberately threshold-free and workload/path blind:
* preserve the current payload and hot-root exclusion from C25EG08;
* replay policy levels 3, 6, 12, 19;
* on the first strictly-worse rung, evaluate level 9 exactly once if level 9 has
  not already been passed;
* if level 9 beats the incumbent, retain it and continue with later original
  policy rungs; otherwise stop;
* if the first worse rung occurs after level 9, stop normally.

This is a research counterfactual only. It cannot receive product/R4 credit.
The held-out transfer set is frozen before results: Developer, Tiny Files,
Logs/Telemetry, Media, and Scientific/HPC from current15. No threshold learned
from Office/Analytics is permitted.
"""

import argparse
import json
from pathlib import Path
import statistics
import tempfile
import time

from benchmarks import v030_adaptive_effort_residual_referee as H2
from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks import v030_office_physical_economics_referee as OFFICE
from benchmarks import v030_physical_effort_attribution as H1
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

TARGETS = (
    "02_office_workspace",
    "04_analytics_and_database",
    "03_developer_workspace",
    "06_tiny_files",
    "08_logs_and_telemetry",
    "01_media_library",
    "13_scientific_hpc",
)
PRIMARY = {"02_office_workspace", "04_analytics_and_database"}
HELD_OUT = set(TARGETS) - PRIMARY
REPS = 3
EXPECTED_POLICY_GIT_BLOB = H2.EXPECTED_POLICY_GIT_BLOB


def _probe_once(units: list[dict], hot_indices: set[int]) -> tuple[list[tuple[int, bytes]], dict]:
    selected: list[tuple[int, bytes]] = []
    attempts = probes = probe_wins = early_stops = 0
    for row in units:
        pi = int(row["index"])
        best_codec = int(row["codec"]); best_payload = row["payload"]; best_size = len(best_payload)
        if pi not in hot_indices:
            for level in H2.POLICY_LEVELS:
                attempts += 1
                codec, payload = H1._encode(row["raw"], level)
                size = len(payload)
                if size <= best_size:
                    if size < best_size:
                        best_codec, best_payload, best_size = codec, payload, size
                    continue
                # Exactly one fixed recovery observation. Level 9 is observation-only
                # in H2 and therefore was not selected from target residual thresholds.
                if level < 9:
                    probes += 1; attempts += 1
                    pcodec, ppayload = H1._encode(row["raw"], 9)
                    psize = len(ppayload)
                    if psize < best_size:
                        probe_wins += 1
                        best_codec, best_payload, best_size = pcodec, ppayload, psize
                        continue
                early_stops += 1
                break
        selected.append((best_codec, best_payload))
    return selected, {"attempts": attempts, "recovery_probes": probes, "recovery_probe_wins": probe_wins, "early_stops": early_stops}


def _timed_probe(units: list[dict], hot: set[int]):
    first = stats0 = None; cpus=[]; walls=[]
    for _ in range(REPS):
        c0=time.process_time(); w0=time.perf_counter(); out, stats=_probe_once(units, hot)
        cpus.append(time.process_time()-c0); walls.append(time.perf_counter()-w0)
        if first is None: first, stats0 = out, stats
        elif any(a[0] != b[0] or a[1] != b[1] for a,b in zip(first,out)): raise RuntimeError("recovery-probe policy nondeterministic")
    return first, stats0, statistics.median(cpus), statistics.median(walls)


def _one(source: Path, item: dict, work: Path) -> dict:
    profile=work/"profile"; v1_raw, implicit_raw, _=OFFICE.profile_controls(source, profile)
    base=work/"base.cmpct"; OFFICE.physical_base(profile, base)
    current=work/"current.cmpct"; OFFICE.embedded_copy(base,current,implicit_raw)
    verify=OFFICE.verify_controlled("h-effort-3",current,source,v1_raw,implicit=True)
    units,_=H1._physical_units(base); meta,_=H2.EG05._parse_physical_region(base.read_bytes())
    _,hot=EG08._stream_roles(meta,len(units))
    l1,c1,w1=H2._run_level(units,1); l19,c19,w19=H2._run_level(units,19)
    if any(int(r["codec"])!=int(e[0]) or r["payload"]!=e[1] for r,e in zip(units,l1)): raise RuntimeError("level1 identity failure")
    old,_,oldcpu,oldwall=H2._run_policy(units,hot)
    new,stats,cpu,wall=_timed_probe(units,hot)
    phys=lambda x: H2._physical_bytes(x)
    p1,p19,pold,pnew=map(phys,(l1,l19,old,new)); oracle=p1-p19
    return {"name":item["name"],"tree_sha256":item["tree_sha256"],"verify":verify,"pack_count":len(units),"hot_pack_count":len(hot),
            "level1_physical_bytes":p1,"level19_physical_bytes":p19,"historical_physical_bytes":pold,"probe_physical_bytes":pnew,
            "oracle_saving_bytes":oracle,"historical_recovered_bytes":p1-pold,"probe_recovered_bytes":p1-pnew,
            "probe_share_of_oracle":((p1-pnew)/oracle if oracle>0 else 1.0),"probe_residual_bytes":pnew-p19,
            "historical_cpu_s":oldcpu,"historical_wall_s":oldwall,"probe_cpu_s":cpu,"probe_wall_s":wall,"level19_cpu_s":c19,"level19_wall_s":w19,
            "probe_vs_l19_cpu_ratio":cpu/max(c19,1e-12),"stats":stats}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("adaptive-effort-recovery-probe.json")); args=ap.parse_args()
    blob=H2._policy_blob()
    if blob != EXPECTED_POLICY_GIT_BLOB: raise RuntimeError(f"policy source drift {blob}")
    with tempfile.TemporaryDirectory(prefix="cmpct-h-effort-3-") as td:
        root=Path(td); corpus=root/"corpus"; manifest=CORPUS.build(corpus); by={x["name"]:x for x in manifest["corpora"]}
        rows=[]
        for name in TARGETS:
            if name not in by: raise RuntimeError(f"missing frozen target {name}")
            rows.append(_one(corpus/name,by[name],root/name))
    primary=[r for r in rows if r["name"] in PRIMARY]; held=[r for r in rows if r["name"] in HELD_OUT]
    # Promotion is intentionally strict: target repair must be large, no held-out
    # surface may enlarge relative to historical policy, and compute must remain
    # below the full L19 oracle on every measured surface.
    primary_ok=all(r["probe_share_of_oracle"]>=0.90 for r in primary)
    held_no_regress=all(r["probe_physical_bytes"]<=r["historical_physical_bytes"] for r in held)
    compute_ok=all(r["probe_vs_l19_cpu_ratio"]<0.90 for r in rows)
    verdict="RECOVERY_PROBE_TRANSFERS" if primary_ok and held_no_regress and compute_ok else "RECOVERY_PROBE_NOT_READY"
    out={"schema":"cmpct-v030-adaptive-effort-recovery-probe-v1","status":"research evidence; no release or R4 credit","historical_policy_blob":blob,
         "targets":list(TARGETS),"primary":sorted(PRIMARY),"held_out":sorted(HELD_OUT),"rows":rows,"verdict":verdict,
         "gates":{"primary_ge_90pct_oracle":primary_ok,"heldout_no_density_regression":held_no_regress,"all_cpu_lt_90pct_l19":compute_ok},
         "note":"threshold-free one-probe falsifier; no workload/path identity enters decisions"}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__": main()
