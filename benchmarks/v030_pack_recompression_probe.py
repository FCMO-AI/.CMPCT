from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--workload",default="09_ml_artifacts");args=ap.parse_args()
    eng=load(ROOT/"experiments"/"entropygraph_v028.py","v028_probe")
    neutral=load(ROOT/"benchmarks"/"neutral_hostile_corpus_v1.py","neutral_probe")\n    hostile=load(ROOT/"benchmarks"/"resemblance_hostile_corpus_v1.py","hostile_probe")
    choose0,compress0=eng._choose_pack_plan,eng._compress_record
    selected=set();after=False;dups=[]
    def choose(nodes,sketches,roots):
        nonlocal after
        chosen,trials=choose0(nodes,sketches,roots)
        for group in chosen[3]:
            selected.add(hashlib.sha256(b"".join(nodes[i] for i in group)).digest())
        after=True
        return chosen,trials
    def compress(raw,level=19):
        t=time.perf_counter();result=compress0(raw,level);dt=time.perf_counter()-t
        if after and level==19 and hashlib.sha256(raw).digest() in selected:
            dups.append((len(raw),len(result[1]),dt))
        return result
    eng._choose_pack_plan=choose;eng._compress_record=compress
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-probe-") as td:
        root=Path(td)/"probe"\n        if args.workload=="09_ml_artifacts": neutral.corpus_ml(root)\n        elif args.workload=="01_shifted_versions": hostile.shifted_versions(root)\n        else: raise SystemExit(f"unsupported workload {args.workload}")\n        work=root/args.workload
        if not work.is_dir(): raise SystemExit(f"unknown workload {args.workload}")
        files=sorted(p for p in work.rglob("*") if p.is_file())
        logical_bytes=sum(p.stat().st_size for p in files)
        tree_sha256=(neutral.tree_hash(work) if args.workload=="09_ml_artifacts" else hostile.tree_hash(work))
        stats=eng._build_graph(work,Path(td)/"graph.cmpct")
    print(json.dumps({"schema":"cmpct-v030-pack-recompression-probe-v1","claim_boundary":"diagnostic only; no product credit","workload":args.workload,"logical_bytes":logical_bytes,"tree_sha256":tree_sha256,"graph_bytes":stats["graph_bytes"],"adaptive_pack_limit":stats["adaptive_pack_limit"],"selected_pack_groups":len(selected),"duplicate_selected_pack_calls":len(dups),"duplicate_logical_bytes":sum(x[0] for x in dups),"duplicate_payload_bytes":sum(x[1] for x in dups),"duplicate_level19_wall_s":sum(x[2] for x in dups)},indent=2,sort_keys=True))
if __name__=="__main__":main()
