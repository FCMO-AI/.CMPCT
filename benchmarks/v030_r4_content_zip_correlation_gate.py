from __future__ import annotations

"""Causal/economic falsifier for content-ZIP admission.

The all-valid ContentZipBuilder proved correctness/generalization but spent ~0.49 CPU s to save only 909 B on a
single hidden NPZ.  This oracle asks whether a cheap *content-derived* cohort signal can preserve the Office
breakthrough while avoiding that low-yield proof path.

Predictor, fixed before this result-bearing run:
- inspect plausible ZIP central directories only after the normal 4-byte PK gate;
- record (CRC32, uncompressed-size) for supported non-directory members;
- a hidden content-valid ZIP is admitted only when the archive-build scope contains at least one member signature
  present in two or more distinct valid ZIP containers;
- when that cohort signal exists, admit all hidden valid ZIPs in the build scope; explicit .zip/.whl paths retain
  the existing ContentZipBuilder behavior regardless of the signal.

CRC/size is an opportunity hint, never a correctness proof. Exact recipe construction and normal reader hashes remain
the proof. The cohort-wide policy is intentionally simple/high-recall for this first causal test; hostile review may
require a per-container score if the matrix exposes unrelated passengers.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import v030_r4_content_zip_builder as CZ
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT

RANGE = 4096
EXPLICIT = {'.zip', '.whl'}
MAX_OBSERVED_ENTRIES = 8192  # research safety cap; a shipping policy must make this a documented resource limit.


def _observe(root: Path) -> tuple[dict[Path, bool], set[Path], dict]:
    valid: dict[Path, bool] = {}
    signatures_by_path: dict[Path, set[tuple[int, int]]] = {}
    observed = plausible = rejected_by_cap = 0
    sniffed = 0
    cpu0 = time.process_time()
    for p in sorted(q for q in root.rglob('*') if q.is_file() and not q.is_symlink()):
        rp = p.resolve()
        observed += 1
        try:
            size = p.stat().st_size
            sniffed += min(4, size)
            if size < 64:
                valid[rp] = False
                continue
            with p.open('rb') as fh:
                magic = fh.read(4)
            if magic != b'PK\x03\x04':
                valid[rp] = False
                continue
            plausible += 1
            with zipfile.ZipFile(p) as z:
                infos = [i for i in z.infolist() if not i.is_dir()]
                if not infos or len(infos) > MAX_OBSERVED_ENTRIES:
                    if len(infos) > MAX_OBSERVED_ENTRIES:
                        rejected_by_cap += 1
                    valid[rp] = False
                    continue
                if any(i.compress_type not in CZ.SUPPORTED for i in infos):
                    valid[rp] = False
                    continue
                # One bounded member read preserves the same early structural/CRC check as the all-valid detector.
                first = infos[0]
                with z.open(first) as r:
                    r.read(min(first.file_size, 4096))
                signatures_by_path[rp] = {(int(i.CRC), int(i.file_size)) for i in infos}
                valid[rp] = True
        except Exception:
            valid[rp] = False

    owners: dict[tuple[int, int], set[Path]] = defaultdict(set)
    for p, sigs in signatures_by_path.items():
        for sig in sigs:
            owners[sig].add(p)
    repeated = {sig: paths for sig, paths in owners.items() if len(paths) >= 2}
    correlated_paths = set().union(*(paths for paths in repeated.values())) if repeated else set()
    cohort_signal = bool(repeated)
    hidden_valid = {p for p, ok in valid.items() if ok and p.suffix.lower() not in EXPLICIT}
    admitted_hidden = hidden_valid if cohort_signal else set()
    return valid, admitted_hidden, {
        'files_observed': observed,
        'plausible_pk_files': plausible,
        'valid_zip_files': sum(valid.values()),
        'hidden_valid_zip_files': len(hidden_valid),
        'repeated_member_signatures': len(repeated),
        'correlated_container_count': len(correlated_paths),
        'cohort_signal': cohort_signal,
        'admitted_hidden_zip_files': len(admitted_hidden),
        'entry_cap_rejections': rejected_by_cap,
        'sniffed_magic_bytes': sniffed,
        'observation_cpu_s': time.process_time() - cpu0,
    }


class CorrelationGateBuilder(CZ.ContentZipBuilder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correlation_gate_stats: dict = {}

    def scan(self):
        valid, admitted_hidden, gate = _observe(self.root)
        self.correlation_gate_stats = gate
        original = CZ._valid_zip_content

        def cached_gate(path: Path) -> bool:
            rp = Path(path).resolve()
            ok = bool(valid.get(rp, False))
            if not ok:
                return False
            if rp.suffix.lower() in EXPLICIT:
                return True
            return rp in admitted_hidden

        CZ._valid_zip_content = cached_gate
        try:
            return super().scan()
        finally:
            CZ._valid_zip_content = original

    def build(self, out: Path):
        stats = dict(super().build(out))
        stats['correlation_gate'] = dict(self.correlation_gate_stats)
        return stats


def _build(cls, root: Path, archive: Path) -> tuple[dict, float, float]:
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    stats = dict(cls(root).build(archive))
    return stats, time.process_time() - cpu0, time.perf_counter() - wall0


def _verify(archive: Path, source: Path, out: Path) -> dict:
    want = PRODUCT.treehash(source)
    checks = []
    shutil.rmtree(out, ignore_errors=True)
    with CMPCT(archive) as ar:
        virtual = [row[0] for row in ar.files if row[1] == 0 and row[6] and row[6][0] == S_VZIP]
        for name in virtual:
            raw = (source / name).read_bytes(); ln = min(RANGE, len(raw))
            starts = sorted({0, max(0, len(raw)//2 - ln//2), max(0, len(raw)-ln)})
            for start in starts:
                got = ar.read_range(name, start, ln)
                if got != raw[start:start+ln]:
                    raise RuntimeError(f'exact VZIP range mismatch: {name} {start}+{ln}')
                checks.append([name, start, ln])
        ar.extractall(out, metadata=True)
    got = PRODUCT.treehash(out)
    if got != want:
        raise RuntimeError(f'tree mismatch {got} != {want}')
    return {'tree_sha256': got, 'vzip_files': virtual, 'vzip_file_count': len(virtual), 'range_checks': checks}


def _measure(suite: str, source: Path, wd: Path, accepted: dict) -> dict:
    wd.mkdir(parents=True, exist_ok=True)
    variants = {}
    for label, cls in (
        ('baseline', Builder),
        ('all_valid', CZ.ContentZipBuilder),
        ('correlation_gated', CorrelationGateBuilder),
    ):
        arc = wd / f'{label}.cmpct'
        stats, cpu, wall = _build(cls, source, arc)
        verified = _verify(arc, source, wd / f'{label}-out')
        variants[label] = {'archive_bytes': arc.stat().st_size, 'create_cpu_s': cpu, 'create_wall_s': wall,
                           'builder_stats': stats, **verified}
    base = variants['baseline']; allv = variants['all_valid']; gated = variants['correlation_gated']
    return {
        'suite': suite, 'name': source.name,
        'accepted_v029_bytes': int(accepted[(suite, source.name)]['accepted_v029_bytes']),
        **variants,
        'all_valid_saving_vs_baseline_bytes': base['archive_bytes'] - allv['archive_bytes'],
        'gated_saving_vs_baseline_bytes': base['archive_bytes'] - gated['archive_bytes'],
        'gated_byte_delta_vs_all_valid': gated['archive_bytes'] - allv['archive_bytes'],
        'gated_cpu_delta_vs_all_valid_s': gated['create_cpu_s'] - allv['create_cpu_s'],
        'gated_cpu_delta_vs_baseline_s': gated['create_cpu_s'] - base['create_cpu_s'],
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'neutral_hostile_corpus_v1.py', 'cmpct_v030_zipcorr_neutral')
    hostile = GENERAL.V029._load(GENERAL.V029.ROOT/'benchmarks'/'resemblance_hostile_corpus_v1.py', 'cmpct_v030_zipcorr_hostile')
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, 'cmpct_v030_zipcorr_repair'); repair.install_generation_hooks(neutral)
    rows = []
    for suite, generator, root in (
        ('neutral_hostile_v1', neutral, work/'neutral'),
        ('resemblance_hostile_v1', hostile, work/'resemblance'),
    ):
        generator.build(root)
        if suite == 'neutral_hostile_v1': repair.normalize_root(root)
        for source in sorted(p for p in root.iterdir() if p.is_dir()):
            row = _measure(suite, source, work/'rows'/suite/source.name, accepted); rows.append(row)
            gs = row['correlation_gated']['builder_stats'].get('correlation_gate') or {}
            print(json.dumps({'suite':suite,'name':source.name,'base':row['baseline']['archive_bytes'],
                              'all_valid':row['all_valid']['archive_bytes'],'gated':row['correlation_gated']['archive_bytes'],
                              'gate_signal':gs.get('cohort_signal'),'repeated':gs.get('repeated_member_signatures'),
                              'hidden':gs.get('hidden_valid_zip_files'),'admitted_hidden':gs.get('admitted_hidden_zip_files'),
                              'cpu_delta_vs_all':row['gated_cpu_delta_vs_all_valid_s']}), flush=True)
    if len(rows) != 15: raise RuntimeError(f'expected 15 rows, got {len(rows)}')
    office = next(r for r in rows if r['suite']=='neutral_hostile_v1' and r['name']=='02_office_workspace')
    analytics = next(r for r in rows if r['suite']=='neutral_hostile_v1' and r['name']=='04_analytics_and_database')
    base_total = sum(r['baseline']['archive_bytes'] for r in rows)
    all_total = sum(r['all_valid']['archive_bytes'] for r in rows)
    gate_total = sum(r['correlation_gated']['archive_bytes'] for r in rows)
    gate_regressions = [f"{r['suite']}/{r['name']}" for r in rows if r['correlation_gated']['archive_bytes'] > r['baseline']['archive_bytes']]
    all_saving = base_total - all_total; gate_saving = base_total - gate_total
    retain = gate_saving / max(1, all_saving)
    cpu_all = sum(r['all_valid']['create_cpu_s'] for r in rows); cpu_gate = sum(r['correlation_gated']['create_cpu_s'] for r in rows)
    exact = all(PRODUCT.treehash(Path(work/('neutral' if r['suite']=='neutral_hostile_v1' else 'resemblance')/r['name'])) == r['correlation_gated']['tree_sha256'] for r in rows)
    return {
        'schema':'cmpct-v030-r4-content-zip-correlation-gate-v1', 'source_commit':os.environ.get('EVIDENCE_HEAD'), 'rows':rows,
        'totals':{
            'workloads':len(rows),'baseline_bytes':base_total,'all_valid_bytes':all_total,'correlation_gated_bytes':gate_total,
            'all_valid_saving_bytes':all_saving,'correlation_gated_saving_bytes':gate_saving,
            'saving_retention_fraction':retain,'all_valid_create_cpu_s':cpu_all,'correlation_gated_create_cpu_s':cpu_gate,
            'cpu_delta_gate_vs_all_valid_s':cpu_gate-cpu_all,'gated_regressed_rows':gate_regressions,
        },
        'hypothesis':{
            'all_gated_trees_exact':exact,
            'zero_gated_byte_regressions_vs_baseline':not gate_regressions,
            'office_cohort_signal_true':bool(office['correlation_gated']['builder_stats']['correlation_gate']['cohort_signal']),
            'office_retains_all_valid_bytes':office['correlation_gated']['archive_bytes']==office['all_valid']['archive_bytes'],
            'analytics_cohort_signal_false':not bool(analytics['correlation_gated']['builder_stats']['correlation_gate']['cohort_signal']),
            'analytics_hidden_recipe_avoided':analytics['correlation_gated']['vzip_file_count']==analytics['baseline']['vzip_file_count'],
            'retains_at_least_99_9pct_aggregate_saving':retain>=0.999,
            'supported_for_bounded_hardening':(
                exact and not gate_regressions and office['correlation_gated']['archive_bytes']==office['all_valid']['archive_bytes']
                and analytics['correlation_gated']['vzip_file_count']==analytics['baseline']['vzip_file_count'] and retain>=0.999
            ),
        },
        'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'format_changed':False,
                    'reader_changed':False,'crc_size_is_hint_not_proof':True,'exact_recipe_and_tree_proof_retained':True,
                    'workload_identity_available_to_policy':False},
        'next_if_supported':'add adversarial correlated/unrelated passenger cohorts plus bounded central-directory resource tests; then measure repeated fresh-process CPU/RSS/selective amplification before canonical Builder integration',
        'next_if_falsified':'preserve the negative and replace cohort correlation with a better preregistered content-derived economic predictor; do not tune by workload name or extension',
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-correlation-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-correlation.json')); a=p.parse_args()
    result=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'totals':result['totals'],'hypothesis':result['hypothesis']},indent=2))

if __name__=='__main__': main()
