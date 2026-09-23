from __future__ import annotations
"""Mechanism-bearing direct-base-vs-actual-Builder productization falsifier for #205.

The historical #201 research subclass is not a candidate engine here.  Each fresh generated tree is
built first with the exact authority Builder.scan captured from source, then with the installed #205
Builder.scan.  The pair therefore differs only in hidden-ZIP discovery/selection on the same Builder
implementation and the same exact generated source tree.
"""
import argparse, json, os, resource, shutil, statistics, time
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from cmpct.builder import Builder
from cmpct.codec import S_PACK, S_VZIP
from cmpct.reader import CMPCT
from cmpct import v030_hidden_zip_builder as HIDDEN_SCAN

REPS = 3
RANGE = 4096
AUTHORITY_SCAN = HIDDEN_SCAN._scan_with_hidden_zip.__globals__["Builder"].__dict__.get("_cmpct_v030_authority_scan")
if AUTHORITY_SCAN is None:
    # The draft seam replaces Builder.scan at import time.  Recover the exact authority method from
    # the class source by loading the authority module under a private name is deliberately avoided:
    # duplicate module globals can change codec/worker state.  The installer records the original
    # method in current heads; fail closed on older heads rather than benchmark a guessed control.
    raise RuntimeError("#205 must record Builder._cmpct_v030_authority_scan before product matrix execution")
CANDIDATE_SCAN = HIDDEN_SCAN._scan_with_hidden_zip


def _treehash(root: Path) -> str:
    return PRODUCT.treehash(root)


def _measure_scan(scan, source: Path, arc: Path, out: Path):
    old = Builder.scan
    Builder.scan = scan
    try:
        cpu0 = time.process_time(); wall0 = time.perf_counter()
        stats = dict(Builder(source).build(arc))
        create_cpu = time.process_time() - cpu0; create_wall = time.perf_counter() - wall0
    finally:
        Builder.scan = old
    want = _treehash(source); shutil.rmtree(out, ignore_errors=True)
    cpu0 = time.process_time(); wall0 = time.perf_counter(); range_checks = []; pack_checks = []
    with CMPCT(arc) as reader:
        for row in reader.files:
            if row[1] != 0 or not row[6]: continue
            if row[6][0] not in (S_VZIP, S_PACK): continue
            raw = (source / row[0]).read_bytes(); ln = min(RANGE, len(raw))
            for start in sorted({0, max(0, len(raw)//2-ln//2), max(0, len(raw)-ln)}):
                got = reader.read_range(row[0], start, ln)
                if got != raw[start:start+ln]: raise RuntimeError(f"range mismatch {row[0]}")
                target = pack_checks if row[6][0] == S_PACK else range_checks
                target.append([row[0], start, ln])
        reader.extractall(out, metadata=True)
    extract_cpu = time.process_time() - cpu0; extract_wall = time.perf_counter() - wall0
    got = _treehash(out)
    if got != want: raise RuntimeError(f"tree mismatch {got} != {want}")
    return {
        "archive_bytes": arc.stat().st_size, "create_cpu_s": create_cpu, "create_wall_s": create_wall,
        "extract_cpu_s": extract_cpu, "extract_wall_s": extract_wall, "tree_sha256": got,
        "vzip_range_checks": range_checks, "pack_range_checks": pack_checks, "stats": stats,
    }


def _rep(i: int, root: Path):
    work = root / f"rep-{i}"; work.mkdir(parents=True)
    n = GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py', f'cmpct_hidden_product_n_{i}')
    h = GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py', f'cmpct_hidden_product_h_{i}')
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, f'cmpct_hidden_product_r_{i}'); repair.install_generation_hooks(n)
    rows = []
    for suite, generator, suite_root in (("neutral_hostile_v1", n, work/'neutral'), ("resemblance_hostile_v1", h, work/'resemblance')):
        generator.build(suite_root)
        if suite == "neutral_hostile_v1": repair.normalize_root(suite_root)
        for source in sorted(p for p in suite_root.iterdir() if p.is_dir()):
            wd = work/'rows'/suite/source.name; wd.mkdir(parents=True)
            base = _measure_scan(AUTHORITY_SCAN, source, wd/'base.cmpct', wd/'base-out')
            candidate = _measure_scan(CANDIDATE_SCAN, source, wd/'candidate.cmpct', wd/'candidate-out')
            saving = base['archive_bytes'] - candidate['archive_bytes']
            rows.append({"suite":suite,"name":source.name,"base":base,"candidate":candidate,"saving_bytes":saving})
            print(json.dumps({"rep":i,"suite":suite,"name":source.name,"base":base['archive_bytes'],"candidate":candidate['archive_bytes'],"saving":saving}), flush=True)
    return {"rep":i,"rows":rows,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def run(root: Path):
    shutil.rmtree(root, ignore_errors=True); root.mkdir(parents=True)
    reps = [_rep(i, root) for i in range(REPS)]
    keys = [(r['suite'],r['name']) for r in reps[0]['rows']]
    if any([(r['suite'],r['name']) for r in rep['rows']] != keys for rep in reps): raise RuntimeError("row identity drift")
    rows=[]; regressed=[]
    for j,key in enumerate(keys):
        rr=[rep['rows'][j] for rep in reps]; savings=[r['saving_bytes'] for r in rr]
        if any(x < 0 for x in savings): regressed.append('/'.join(key))
        rows.append({"suite":key[0],"name":key[1],"saving_bytes_by_rep":savings,"saving_bytes_median":statistics.median(savings),
            "base_bytes_by_rep":[r['base']['archive_bytes'] for r in rr],"candidate_bytes_by_rep":[r['candidate']['archive_bytes'] for r in rr],
            "base_create_wall_median_s":statistics.median(r['base']['create_wall_s'] for r in rr),"candidate_create_wall_median_s":statistics.median(r['candidate']['create_wall_s'] for r in rr),
            "base_extract_wall_median_s":statistics.median(r['base']['extract_wall_s'] for r in rr),"candidate_extract_wall_median_s":statistics.median(r['candidate']['extract_wall_s'] for r in rr),
            "candidate_vzip_range_checks":sum(len(r['candidate']['vzip_range_checks']) for r in rr),"candidate_pack_range_checks":sum(len(r['candidate']['pack_range_checks']) for r in rr)})
    office=next(r for r in rows if r['name']=='02_office_workspace')
    totals={"saving_bytes_median_sum":sum(r['saving_bytes_median'] for r in rows),"regressed_rows":regressed,
        "office_saving_bytes_by_rep":office['saving_bytes_by_rep'],"office_saving_bytes_median":office['saving_bytes_median'],
        "peak_rss_kib_by_rep":[r['peak_rss_kib'] for r in reps]}
    supported=not regressed and min(office['saving_bytes_by_rep'])>=9_000_000
    return {"schema":"cmpct-v030-hidden-zip-product-gain-retention-v1","source_commit":os.environ.get('EVIDENCE_HEAD'),"repetitions":REPS,"rows":rows,"totals":totals,
        "hypothesis":{"zero_byte_regressions":not regressed,"office_retains_at_least_9MB_each_rep":min(office['saving_bytes_by_rep'])>=9_000_000,"supported_for_resource_gate":supported},
        "contract":{"actual_builder_candidate":True,"historical_research_subclass_candidate":False,"same_tree_per_arm":True,"fresh_tree_each_rep":True,"exact_tree_verified":True,"vzip_and_pack_ranges_verified":True,"thresholds_unchanged":True},
        "next_if_supported":"measure isolated per-arm peak RSS plus explicit hidden staging temp/source I/O and selective decoded work before promotion",
        "next_if_falsified":"preserve failing row; localize gain loss or regression without retuning admission threshold"}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/hidden-zip-product-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/hidden-zip-product.json')); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result['totals'],indent=2)); assert result['hypothesis']['supported_for_resource_gate']
if __name__=='__main__': main()
