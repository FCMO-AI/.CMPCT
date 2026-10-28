from __future__ import annotations

"""Path-blind shared-dictionary referee for the v0.30 micro-pack frontier.

Mission lock
============
Stable-current15 selective evidence shows that solid S_PACK groups can preserve the
existing <=8x whole-member law while a 4 KiB range still touches far more physical
work than an independent blob.  The raw-floor admission guard was falsified: it
rejected hundreds of candidate groups, lost bytes on Developer, and still retained
selective-read debt on false-neighbors.

Falsifiable hypothesis
----------------------
Cross-file redundancy can be recovered without a solid decode unit by training the
existing r24 Zstd dictionary representation on the same path-blind small regular
blob population and keeping members independently addressable.  This must remove
confirmed selective-read debt versus same-grammar independent storage while
remaining no larger than independent storage on every first-gate source.  Dictionary
training/open cost is charged; path/suffix/corpus identity never enters the new
training or dictionary-admission policy.

This is research-only.  It changes no canonical Builder, format, locality budget,
Genesis score, version, comparator, or timing confidence envelope.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import msgpack

from cmpct.codec import CODEC_RAW, CODEC_ZSTDDICT, zcd
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_content_selective_read_referee as SEL
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder


class PathBlindDictionaryBuilder(BASE.BUILDER.Builder):
    """Keep blobs independent and use one existing-format dictionary, trained path-blind."""

    def _build_micro_packs(self):
        self._locality_derived_groups = []

    def _train_dictionary(self):
        # Restrict training to unique ordinary S_BLOB candidates already referenced by
        # logical files.  No path, extension, suffix, corpus id, or ordinal is consulted.
        refs = set()
        for row in self.files:
            if row[1] == BASE.R24.K_FILE and row[6] and row[6][0] == BASE.R24.S_BLOB:
                refs.add(bytes(row[6][1]))
        samples = []
        candidate_hashes = []
        for h in sorted(refs):
            c = self.cands.get(h)
            if c is None or c.deflates:
                continue
            if len(c.raw) < 64 or len(c.raw) > self.micro_pack_max_file:
                continue
            samples.append(c.raw)
            candidate_hashes.append(h)
        self._pathblind_dict_hashes = set(candidate_hashes)
        self._pathblind_dict_audit = {
            'sample_count': len(samples),
            'sample_bytes': sum(map(len, samples)),
            'trained': False,
            'dictionary_bytes': 0,
            'train_cpu_s': 0.0,
            'train_wall_s': 0.0,
        }
        # Reuse the mature product trainer floor and dictionary cap; these are not a
        # new corpus-tuned knob.  If the existing trainer would not engage, neither do we.
        if len(samples) < 16 or sum(map(len, samples)) < 96 * 1024:
            return
        exe = shutil.which('zstd')
        if not exe:
            return
        c0 = time.process_time(); w0 = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix='cmpct-pathblind-dict-') as td:
            d = Path(td); paths = []
            for i, b in enumerate(samples):
                q = d / f'{i:05d}.sample'; q.write_bytes(b); paths.append(str(q))
            out = d / 'dict'
            r = subprocess.run(
                [exe, '--train-fastcover=k=50,d=8,f=20,steps=4,split=75,accel=10',
                 *paths, '--maxdict=24576', '-o', str(out)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if r.returncode == 0 and out.exists():
                self.dictionary = out.read_bytes()
                self.dict_hash = self.add_content(self.dictionary, '.zdict')
        self._pathblind_dict_audit.update({
            'trained': bool(self.dictionary),
            'dictionary_bytes': len(self.dictionary),
            'train_cpu_s': time.process_time() - c0,
            'train_wall_s': time.perf_counter() - w0,
            'dictionary_sha256': hashlib.sha256(self.dictionary).hexdigest() if self.dictionary else None,
        })

    def _encode_candidate(self, h, c):
        if self.dict_hash is not None and h == self.dict_hash:
            return CODEC_RAW, c.raw, b''
        # Suppress the inherited extension-gated dictionary audition while preserving
        # every other mature codec candidate; then add the dictionary candidate solely
        # for the path-blind population frozen above.
        dictionary = self.dictionary
        self.dictionary = b''
        try:
            codec, comp, meta = super()._encode_candidate(h, c)
        finally:
            self.dictionary = dictionary
        if dictionary and h in getattr(self, '_pathblind_dict_hashes', set()):
            dc = zcd(c.raw, dictionary, 12)
            dm = msgpack.packb([12], use_bin_type=True)
            if len(dc) + len(dm) < len(comp) + len(meta):
                return CODEC_ZSTDDICT, dc, dm
        return codec, comp, meta


def _build_variant(builder_cls, source: Path, root: Path) -> dict:
    arm = SEL._build_variant(builder_cls, source, root)
    archive = arm['archive']; index = arm['index']
    dict_idx = index.get('dict_blob')
    if dict_idx is None:
        dict_charge = {'present': False, 'raw_bytes': 0, 'compressed_bytes': 0}
    else:
        off, usize, csize, codec, mlen = index['blobs'][dict_idx]
        dict_charge = {'present': True, 'raw_bytes': int(usize), 'compressed_bytes': int(csize) + int(mlen)}
    return arm | {'dictionary_charge': dict_charge}


def _clean(arm: dict) -> dict:
    return {k:v for k,v in arm.items() if k not in {'archive','index'}}


def _combined_debt(candidate: dict, base: dict) -> dict:
    c = float(candidate['median_open_wall_s']) + float(candidate['median_read_wall_s'])
    b = float(base['median_open_wall_s']) + float(base['median_read_wall_s'])
    delta = c - b
    rel = c / b - 1.0 if b > 0 else 0.0
    return {
        'candidate_wall_s': c, 'base_wall_s': b, 'delta_wall_s': delta,
        'relative': rel,
        'confirmed_regression': bool(delta > SEL.ABSOLUTE_REGRESSION_S and rel > SEL.RELATIVE_REGRESSION),
    }


def _one(source: Path, root: Path) -> dict:
    independent = _build_variant(SAME.NoMicroPackBuilder, source, root/'independent')
    extension = _build_variant(BASE.LocalityDerivedBuilder, source, root/'extension')
    current = _build_variant(ContentEconomicBuilder, source, root/'current')
    dictionary = _build_variant(PathBlindDictionaryBuilder, source, root/'dictionary')

    # Use the current solid candidate's fixed expensive-member population; an
    # alternative is not allowed to make known hard probes disappear from the test.
    probes = SEL._probes(source, current)
    timings = {}
    if probes:
        for name, arm in (('independent',independent),('current',current),('dictionary',dictionary)):
            timings[name] = SEL._time_variant(arm, probes)
    read_debt = SEL._confirmed_regression(timings['dictionary'], timings['independent']) if probes else {'confirmed_regression':False}
    op_debt = _combined_debt(timings['dictionary'], timings['independent']) if probes else {'confirmed_regression':False}
    inv = {
        'all_tree_exact': all(x['strong_tree_exact'] for x in (independent,extension,current,dictionary)),
        'dictionary_locality': dictionary['locality_pass'],
        'dictionary_amp_at_most_8x': dictionary['max_member_amplification'] <= BASE.LOCALITY_BUDGET + 1e-9,
        'dictionary_payload_exact': dictionary['physical_payload_exact'],
        'dictionary_tail_recovery': dictionary['tail_recovery'],
        'reads_exact': all(not t['correctness_failures'] for t in timings.values()) if timings else True,
    }
    return {
        'variants': {k:_clean(v) for k,v in {'independent':independent,'extension':extension,'current':current,'dictionary':dictionary}.items()},
        'probe_count': len(probes), 'timings': timings,
        'dictionary_read_debt': bool(read_debt['confirmed_regression']),
        'dictionary_operation_debt': bool(op_debt['confirmed_regression']),
        'dictionary_vs_independent_read': read_debt,
        'dictionary_vs_independent_open_plus_read': op_debt,
        'dictionary_delta_vs_independent_bytes': dictionary['final_membership_bytes']-independent['final_membership_bytes'],
        'dictionary_delta_vs_extension_bytes': dictionary['final_membership_bytes']-extension['final_membership_bytes'],
        'dictionary_delta_vs_current_bytes': dictionary['final_membership_bytes']-current['final_membership_bytes'],
        'invariants': inv, 'invariants_pass': all(inv.values()),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    paths, identities = CUR._build(work_root/'corpus')
    fingerprint = CUR._fingerprint(identities)
    targets = {
        'neutral_hostile_v1/01_developer_repository',
        'neutral_hostile_v1/08_many_tiny_files',
        'neutral_hostile_v1/07_incompressible_and_encrypted_like',
        'resemblance_hostile_v1/02_false_neighbors',
        'resemblance_hostile_v1/05_incompressible',
    }
    missing = sorted(targets-set(paths))
    if missing: raise RuntimeError(f'missing target workloads: {missing}')
    rows = {k:_one(paths[k], work_root/'work'/k.split('/')[0]/k.split('/')[1]) for k in sorted(targets)}
    invariant_failures=[k for k,r in rows.items() if not r['invariants_pass']]
    byte_losses=[k for k,r in rows.items() if r['dictionary_delta_vs_independent_bytes']>0]
    read_debts=[k for k,r in rows.items() if r['dictionary_read_debt']]
    op_debts=[k for k,r in rows.items() if r['dictionary_operation_debt']]
    strict_wins=[k for k,r in rows.items() if r['dictionary_delta_vs_independent_bytes']<0]
    if invariant_failures or byte_losses or read_debts or op_debts:
        verdict='RETIRE_PATHBLIND_DICTIONARY'
    elif strict_wins:
        verdict='PATHBLIND_DICTIONARY_EARNS_CURRENT15_TRANSFER'
    else:
        verdict='PATHBLIND_DICTIONARY_SAFE_BUT_NO_DENSITY_GAIN'
    return {
        'schema':'cmpct-v030-r24-pathblind-dictionary-v1',
        'experiment_valid':True,'release_credit':False,'canonical_builder_changed':False,'genesis_rescore':False,
        'path_signal_used':False,'corpus_fingerprint':fingerprint,'targets':sorted(targets),'rows':rows,
        'invariant_failures':invariant_failures,'byte_losses_vs_independent':byte_losses,
        'read_debts':read_debts,'open_plus_read_debts':op_debts,'strict_wins_vs_independent':strict_wins,
        'verdict':verdict,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-pathblind-dict-work')); ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-pathblind-dict.json')); args=ap.parse_args()
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
        'verdict':result['verdict'],'fingerprint':result['corpus_fingerprint'],
        'invariant_failures':result['invariant_failures'],'byte_losses':result['byte_losses_vs_independent'],
        'read_debts':result['read_debts'],'open_plus_read_debts':result['open_plus_read_debts'],
        'strict_wins':result['strict_wins_vs_independent'],
        'rows':{k:{'di':v['dictionary_delta_vs_independent_bytes'],'de':v['dictionary_delta_vs_extension_bytes'],'dc':v['dictionary_delta_vs_current_bytes'],'read_debt':v['dictionary_read_debt'],'op_debt':v['dictionary_operation_debt'],'ind_ms':v.get('timings',{}).get('independent',{}).get('median_read_wall_ms_per_probe'),'dict_ms':v.get('timings',{}).get('dictionary',{}).get('median_read_wall_ms_per_probe'),'dict_open_ms':(v.get('timings',{}).get('dictionary',{}).get('median_open_wall_s') or 0)*1000,'dict':v['variants']['dictionary'].get('dictionary_charge')} for k,v in result['rows'].items()},
    },indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
