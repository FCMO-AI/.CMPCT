from __future__ import annotations

"""Exact portfolio rehabilitation for the path-blind dictionary counter-invention.

Mission lock
============
The first path-blind dictionary referee removed every confirmed read and open+read
debt on five hard targets with zero invariant failures, but its single global
candidate was larger than same-grammar independent storage on three targets and
smaller on two.  That is precisely the portfolio case described by the repository's
breakthrough-rehabilitation policy.

Falsifiable hypothesis
----------------------
Build the ordinary independent r24 candidate and the existing-format path-blind
Zstd-dictionary candidate from the exact same source tree, then publish the smaller
complete artifact (ties publish independent).  This exact selector must preserve
all size/read/integrity/recovery floors while retaining at least one strict dictionary
win.  Its exported creation cost is measured as a debt; no timing threshold, corpus
identity, path signal, locality law, or Genesis score is changed.

The first gate deliberately uses separate complete builds, so it upper-bounds rather
than hides portfolio creation cost.  A successful seed earns shared-scan/shared-work
rehabilitation; it does not earn canonical Builder or release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

from benchmarks import v030_r24_micropack_content_selective_read_referee as SEL
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder
from benchmarks.v030_r24_pathblind_dictionary_referee import PathBlindDictionaryBuilder, _clean


def _timed_build(builder_cls, source: Path, root: Path) -> tuple[dict, dict]:
    c0=time.process_time(); w0=time.perf_counter()
    arm=SEL._build_variant(builder_cls, source, root)
    timing={'cpu_s':time.process_time()-c0,'wall_s':time.perf_counter()-w0}
    return arm,timing


def _confirmed_slow(candidate_s: float, base_s: float) -> dict:
    delta=float(candidate_s)-float(base_s)
    rel=(float(candidate_s)/float(base_s)-1.0) if float(base_s)>0 else 0.0
    return {'candidate_s':float(candidate_s),'base_s':float(base_s),'delta_s':delta,'relative':rel,
            'confirmed_regression':bool(delta>SEL.ABSOLUTE_REGRESSION_S and rel>SEL.RELATIVE_REGRESSION)}


def _one(source: Path, root: Path) -> dict:
    independent,it=_timed_build(SAME.NoMicroPackBuilder,source,root/'independent')
    dictionary,dt=_timed_build(PathBlindDictionaryBuilder,source,root/'dictionary')
    content,ct=_timed_build(ContentEconomicBuilder,source,root/'content')
    if dictionary['final_membership_bytes'] < independent['final_membership_bytes']:
        selected_name='dictionary'; selected=dictionary
    else:
        selected_name='independent'; selected=independent

    probes=SEL._probes(source,content)
    timings={}
    if probes:
        timings['independent']=SEL._time_variant(independent,probes)
        timings['selected']=SEL._time_variant(selected,probes)
        read_debt=SEL._confirmed_regression(timings['selected'],timings['independent'])
    else:
        read_debt={'confirmed_regression':False,'candidate_wall_s':0.0,'base_wall_s':0.0,'delta_wall_s':0.0,'relative':0.0}

    portfolio_cpu=it['cpu_s']+dt['cpu_s']
    portfolio_wall=it['wall_s']+dt['wall_s']
    inv={
        'all_tree_exact':all(x['strong_tree_exact'] for x in (independent,dictionary,content)),
        'selected_locality':selected['locality_pass'],
        'selected_amp_at_most_8x':selected['max_member_amplification']<=SEL.BASE.LOCALITY_BUDGET+1e-9,
        'selected_payload_exact':selected['physical_payload_exact'],
        'selected_tail_recovery':selected['tail_recovery'],
        'selected_no_size_regression':selected['final_membership_bytes']<=independent['final_membership_bytes'],
        'reads_exact':all(not t['correctness_failures'] for t in timings.values()) if timings else True,
    }
    return {
        'selected':selected_name,
        'variants':{'independent':_clean(independent),'dictionary':_clean(dictionary),'content_economic':_clean(content)},
        'build_timings':{'independent':it,'dictionary':dt,'content_economic':ct,
                         'sequential_portfolio':{'cpu_s':portfolio_cpu,'wall_s':portfolio_wall}},
        'creation_cpu_debt':_confirmed_slow(portfolio_cpu,it['cpu_s']),
        'creation_wall_debt':_confirmed_slow(portfolio_wall,it['wall_s']),
        'selected_delta_vs_independent_bytes':selected['final_membership_bytes']-independent['final_membership_bytes'],
        'selected_delta_vs_content_bytes':selected['final_membership_bytes']-content['final_membership_bytes'],
        'dictionary_delta_vs_independent_bytes':dictionary['final_membership_bytes']-independent['final_membership_bytes'],
        'probe_count':len(probes),'timings':timings,'selected_read_debt':bool(read_debt['confirmed_regression']),
        'selected_vs_independent_read':read_debt,'invariants':inv,'invariants_pass':all(inv.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root,ignore_errors=True)
    paths,identities=CUR._build(work_root/'corpus'); fingerprint=CUR._fingerprint(identities)
    targets={
        'neutral_hostile_v1/01_developer_repository',
        'neutral_hostile_v1/08_many_tiny_files',
        'neutral_hostile_v1/07_incompressible_and_encrypted_like',
        'resemblance_hostile_v1/02_false_neighbors',
        'resemblance_hostile_v1/05_incompressible',
    }
    rows={k:_one(paths[k],work_root/'work'/k.split('/')[0]/k.split('/')[1]) for k in sorted(targets)}
    inv=[k for k,r in rows.items() if not r['invariants_pass']]
    losses=[k for k,r in rows.items() if r['selected_delta_vs_independent_bytes']>0]
    read=[k for k,r in rows.items() if r['selected_read_debt']]
    wins=[k for k,r in rows.items() if r['selected_delta_vs_independent_bytes']<0]
    cpu_debt=[k for k,r in rows.items() if r['creation_cpu_debt']['confirmed_regression']]
    wall_debt=[k for k,r in rows.items() if r['creation_wall_debt']['confirmed_regression']]
    aggregate={
        'independent_bytes':sum(r['variants']['independent']['final_membership_bytes'] for r in rows.values()),
        'selected_bytes':sum(r['variants'][r['selected']]['final_membership_bytes'] for r in rows.values()),
        'content_economic_bytes':sum(r['variants']['content_economic']['final_membership_bytes'] for r in rows.values()),
        'independent_build_cpu_s':sum(r['build_timings']['independent']['cpu_s'] for r in rows.values()),
        'portfolio_build_cpu_s':sum(r['build_timings']['sequential_portfolio']['cpu_s'] for r in rows.values()),
        'independent_build_wall_s':sum(r['build_timings']['independent']['wall_s'] for r in rows.values()),
        'portfolio_build_wall_s':sum(r['build_timings']['sequential_portfolio']['wall_s'] for r in rows.values()),
    }
    aggregate['selected_delta_vs_independent_bytes']=aggregate['selected_bytes']-aggregate['independent_bytes']
    aggregate['selected_regret_vs_content_bytes']=aggregate['selected_bytes']-aggregate['content_economic_bytes']
    if inv or losses or read or not wins:
        verdict='RETIRE_PATHDICT_PORTFOLIO'
    elif cpu_debt or wall_debt:
        verdict='PATHDICT_PORTFOLIO_EARNS_SHARED_BUILD_REHAB'
    else:
        verdict='PATHDICT_PORTFOLIO_EARNS_CURRENT15_TRANSFER'
    return {
        'schema':'cmpct-v030-r24-pathdict-portfolio-v1','experiment_valid':True,'release_credit':False,
        'canonical_builder_changed':False,'genesis_rescore':False,'path_signal_used':False,
        'corpus_fingerprint':fingerprint,'targets':sorted(targets),'rows':rows,'aggregate':aggregate,
        'invariant_failures':inv,'byte_losses_vs_independent':losses,'read_debts':read,
        'strict_wins_vs_independent':wins,'creation_cpu_debts':cpu_debt,'creation_wall_debts':wall_debt,
        'verdict':verdict,
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-pathdict-portfolio-work'));ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-pathdict-portfolio.json'));args=ap.parse_args()
    d=run(args.work_root);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':d['verdict'],'fingerprint':d['corpus_fingerprint'],'aggregate':d['aggregate'],'wins':d['strict_wins_vs_independent'],'losses':d['byte_losses_vs_independent'],'read_debts':d['read_debts'],'cpu_debts':d['creation_cpu_debts'],'wall_debts':d['creation_wall_debts'],'rows':{k:{'selected':v['selected'],'di':v['selected_delta_vs_independent_bytes'],'dc':v['selected_delta_vs_content_bytes'],'dict_di':v['dictionary_delta_vs_independent_bytes'],'ind_cpu':v['build_timings']['independent']['cpu_s'],'portfolio_cpu':v['build_timings']['sequential_portfolio']['cpu_s'],'ind_wall':v['build_timings']['independent']['wall_s'],'portfolio_wall':v['build_timings']['sequential_portfolio']['wall_s']} for k,v in d['rows'].items()}},indent=2,sort_keys=True),flush=True)

if __name__=='__main__':main()
