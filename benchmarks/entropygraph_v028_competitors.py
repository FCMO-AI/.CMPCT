from __future__ import annotations

"""Aggregate structural-competitor sweep for EntropyGraph II.

Expensive archival tools are run once on the complete neutral suite and once on the complete
resemblance-hostile suite. Per-workload causal evidence remains the separate v0.25→v0.28 harness.
This prevents 7z/ZPAQ/DwarFS/Borg startup and high-ratio work from being repeated fifteen times while
still giving every competitor the exact same full trees as CMPCT.
"""

import argparse
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def _load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise RuntimeError(f'cannot load {path}')
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def _tree_stats(root:Path):
    files=[p for p in root.rglob('*') if p.is_file()]
    return len(files),sum(p.stat().st_size for p in files)


def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    engine=_load(ROOT/'experiments'/'entropygraph_v028.py','eg2_competitor_engine')
    harness=_load(ROOT/'benchmarks'/'entropygraph_v028_bench.py','eg2_competitor_helpers')
    neutral=_load(ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py','eg2_neutral_generator')
    hostile=_load(ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py','eg2_hostile_generator')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='cmpct-eg2-competitors-') as td:
        temp=Path(td)
        suites=[]
        nr=temp/'neutral';neutral.build(nr);suites.append(('neutral_hostile_v1_aggregate',nr))
        hr=temp/'hostile';hostile.build(hr);suites.append(('resemblance_hostile_v1_aggregate',hr))
        for name,root in suites:
            archive=temp/(name+'.cmpct')
            stats=engine.bench(root,archive);files,logical=_tree_stats(root)
            competitor_dir=temp/(name+'-competitors');competitor_dir.mkdir()
            competitors=harness._competitors(root,competitor_dir)
            rows.append({
                'suite':name,'files':files,'logical_bytes':logical,
                'cmpct_bytes':stats['archive_bytes'],'cmpct_selected':stats['selected'],
                'cmpct_legacy_v025_bytes':stats['legacy_bytes'],'cmpct_graph_bytes':stats['graph_bytes'],
                'cmpct_portfolio_create_s':stats['portfolio_create_s'],
                'cmpct_strong_verify_median_s':stats['strong_verify_median_s'],
                'competitors':competitors,
            })
            print(json.dumps({'suite':name,'cmpct_bytes':stats['archive_bytes'],
                              'competitors':{k:(v.get('bytes') if v.get('available') else None) for k,v in competitors.items()}}),flush=True)
    record={
        'schema':'cmpct-entropygraph-v028-structural-competitors-v1',
        'generated_utc':datetime.now(timezone.utc).isoformat(),
        'rows':rows,
        'method':{
            'aggregation':'each public deterministic suite is archived as one complete recursive tree',
            'reason':'avoid repeating high-ratio structural-tool startup/work for every constituent workload',
            'semantic_mismatches_recorded':True,
            'ranking_policy':'no single scalar winner; archive size and creation time retain each tool’s documented semantics',
        },
    }
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
