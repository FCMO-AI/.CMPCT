from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as V030
from experiments import entropygraph_v030_release as HISTORICAL_TREE


def tree(root: Path) -> str:
    return HISTORICAL_TREE.treehash(root)


def current_once(stage: Path, work: Path) -> dict:
    archive = work / "v030.cmpct"
    extracted = work / "v030-out"
    archive.unlink(missing_ok=True)
    shutil.rmtree(extracted, ignore_errors=True)
    started = time.perf_counter()
    stats = V030.build(stage, archive)
    create_s = time.perf_counter() - started
    verified = V030.strong_verify(archive)
    if not verified.get("ok"):
        raise RuntimeError(f"v0.30 strong verification failed: {verified!r}")
    started = time.perf_counter()
    V030.extract(archive, extracted)
    extract_s = time.perf_counter() - started
    if tree(extracted) != tree(stage):
        raise RuntimeError("v0.30 extracted tree mismatch")
    return {
        "archive_bytes": archive.stat().st_size,
        "create_s": create_s,
        "extract_s": extract_s,
        "selected": stats.get("selected"),
        "tree_verified": True,
    }


V029_CODE = r'''
import json
from pathlib import Path
import shutil
import sys
import time
from experiments import entropygraph_v029_release as E
stage=Path(sys.argv[1]); archive=Path(sys.argv[2]); extracted=Path(sys.argv[3])
archive.unlink(missing_ok=True); shutil.rmtree(extracted, ignore_errors=True)
started=time.perf_counter(); stats=E.build(stage, archive); create_s=time.perf_counter()-started
verified=E.strong_verify(archive)
if not verified.get("ok"):
    raise RuntimeError(f"v0.29 strong verification failed: {verified!r}")
started=time.perf_counter(); E.extract(archive, extracted); extract_s=time.perf_counter()-started
print(json.dumps({"archive_bytes":archive.stat().st_size,"create_s":create_s,"extract_s":extract_s,"selected":stats.get("selected"),"tree_verified":True}))
'''


def v029_once(stage: Path, work: Path, v029_src: Path) -> dict:
    archive = work / "v029.cmpct"
    extracted = work / "v029-out"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(v029_src.resolve())
    cp = subprocess.run(
        [sys.executable, "-c", V029_CODE, str(stage.resolve()), str(archive.resolve()), str(extracted.resolve())],
        cwd=v029_src,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = json.loads(cp.stdout.strip().splitlines()[-1])
    if tree(extracted) != tree(stage):
        raise RuntimeError("v0.29 extracted tree mismatch")
    return result


def run(work_root: Path, v029_src: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_now_v29_neutral")
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py", "cmpct_now_v29_hostile")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_now_v29_repair")
    repair.install_generation_hooks(neutral)
    roots = (("neutral_hostile_v1", neutral, work_root / "neutral"), ("resemblance_hostile_v1", hostile, work_root / "resemblance"))
    rows=[]
    for suite,builder,root in roots:
        builder.build(root)
        if suite == "neutral_hostile_v1":
            repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            key=(suite,source.name)
            if tree(source) != accepted[key]["tree_sha256"]:
                raise RuntimeError(f"source drift: {suite}/{source.name}")
            with tempfile.TemporaryDirectory(prefix="cmpct-now-v29-", dir=work_root) as td:
                td=Path(td)
                stage=EXT._normalized_stage(source,td)
                # Alternate order by row parity to reduce monotonic runner bias.
                if len(rows)%2:
                    v29=v029_once(stage,td,v029_src); v30=current_once(stage,td)
                else:
                    v30=current_once(stage,td); v29=v029_once(stage,td,v029_src)
                row={"label":f"{suite}/{source.name}","suite":suite,"name":source.name,"tree_sha256":tree(stage),"v030":v30,"v029":v29}
                rows.append(row)
                print(json.dumps(row,separators=(",",":")),flush=True)
    def aggregate(engine: str) -> dict:
        vals=[r[engine] for r in rows]
        return {
            "archive_bytes":sum(int(x["archive_bytes"]) for x in vals),
            "create_s":sum(float(x["create_s"]) for x in vals),
            "extract_s":sum(float(x["extract_s"]) for x in vals),
        }
    a30=aggregate("v030"); a29=aggregate("v029")
    return {
        "schema":"cmpct-current-v030-vs-release-v029-v1",
        "v030_product_source":"experiments/entropygraph_v030_release_product.py",
        "v029_release_commit":"291423c604642b21a4b84d2500a12eeaac7bd9e0",
        "v029_product_source":"experiments/entropygraph_v029_release.py",
        "workload_count":len(rows),
        "rows":rows,
        "aggregates":{"v030":a30,"v029":a29},
        "ratios_v030_over_v029":{
            "archive_bytes":a30["archive_bytes"]/a29["archive_bytes"],
            "create_s":a30["create_s"]/a29["create_s"],
            "extract_s":a30["extract_s"]/a29["extract_s"],
        },
        "wins_v030":{
            "size":sum(r["v030"]["archive_bytes"] < r["v029"]["archive_bytes"] for r in rows),
            "create":sum(r["v030"]["create_s"] < r["v029"]["create_s"] for r in rows),
            "extract":sum(r["v030"]["extract_s"] < r["v029"]["extract_s"] for r in rows),
        },
        "exact_all":all(r["v030"]["tree_verified"] and r["v029"]["tree_verified"] for r in rows),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work-root",type=Path,required=True); ap.add_argument("--v029-src",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    out=run(a.work_root,a.v029_src); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k not in {"rows"}},indent=2),flush=True)

if __name__=="__main__":
    import sys
    main()
