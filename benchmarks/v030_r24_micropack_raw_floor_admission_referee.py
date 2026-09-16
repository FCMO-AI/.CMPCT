from __future__ import annotations

"""Raw-floor admission referee for path-blind content-economic micro-packs.

Mission lock
============
Stable-current15 evidence shows three selective-read debts, two explicitly
incompressible.  The existing admission probe compares joint Zstd-1 bytes only
against the sum of per-member Zstd-1 bytes.  The real r24 encoder, however, can
and does fall back to RAW when compression does not beat raw bytes by its frozen
product rule.  On incompressible members the current probe can therefore call a
pack economical merely because one Zstd frame has less framing overhead than
many Zstd frames the independent product would never publish.

Falsifiable hypothesis
----------------------
Require a locality-legal group to prove *content* compression before spending
selective-read locality: joint Zstd-1 payload must be strictly smaller than both
(a) the sum of member Zstd-1 payloads and (b) the aggregate raw member bytes.
No tunable threshold is introduced.

First gate (this file): on the three stable-current15 timing-debt workloads plus
Developer and Tiny Files, the raw-floor rule must preserve all product invariants,
remove every confirmed debt vs same-grammar independent, and be no larger than
the earned extension-bucket control on every source.  Failure retires this rule;
success only earns a full current15 transfer.

Research-only: no canonical Builder, version, frozen Genesis score, locality
budget, probe policy, or timing confidence envelope is changed.
"""

import argparse
import json
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_content_selective_read_referee as SEL
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks import v030_r24_micropack_current15_transfer as CUR
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder


class RawFloorBuilder(BASE.BUILDER.Builder):
    """ContentEconomicBuilder with one exact lower-bound guard: joint < raw sum."""

    def _build_micro_packs(self):
        refs = {}
        for row in self.files:
            if row[1] != BASE.R24.K_FILE or not row[6] or row[6][0] != BASE.R24.S_BLOB:
                continue
            h = bytes(row[6][1])
            refs.setdefault(h, []).append(row)

        eligible = []
        for h in refs:
            c = self.cands.get(h)
            if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
                continue
            eligible.append((h, c))
        eligible.sort(key=lambda hc: (len(hc[1].raw), hc[0]))

        compressor = zstd.ZstdCompressor(level=1)
        emitted_groups = []
        audit_cpu = audit_wall = 0.0
        auditions = rejected_groups = rejected_members = 0
        raw_floor_rejections = zstd_separate_rejections = 0

        def flush(group):
            nonlocal audit_cpu, audit_wall, auditions, rejected_groups, rejected_members
            nonlocal raw_floor_rejections, zstd_separate_rejections
            if len(group) < 2:
                return
            buf = b"".join(c.raw for _, c in group)
            smallest = len(group[0][1].raw)
            if len(buf) > int(BASE.LOCALITY_BUDGET * max(1, smallest)):
                raise RuntimeError("raw-floor group exceeds 8x smallest-member law")

            c0 = time.process_time(); w0 = time.perf_counter()
            joint = len(compressor.compress(buf))
            separate = sum(len(compressor.compress(c.raw)) for _, c in group)
            raw_sum = len(buf)
            audit_cpu += time.process_time() - c0
            audit_wall += time.perf_counter() - w0
            auditions += 1

            zstd_fail = joint >= separate
            raw_fail = joint >= raw_sum
            if zstd_fail or raw_fail:
                rejected_groups += 1
                rejected_members += len(group)
                zstd_separate_rejections += int(zstd_fail)
                raw_floor_rejections += int(raw_fail)
                return

            ph = self.add_content(buf, ".cmpct-pack")
            slots = {}; off = 0
            for h, c in group:
                slots[h] = (off, len(c.raw)); off += len(c.raw)
            for h, (start, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [BASE.R24.S_PACK, ph, start, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)
            emitted_groups.append({
                "members": len(group), "raw_bytes": raw_sum,
                "smallest_member_bytes": smallest,
                "max_raw_amplification": raw_sum / max(1, smallest),
                "audit_joint_zstd1_bytes": joint,
                "audit_separate_zstd1_bytes": separate,
                "audit_raw_sum_bytes": raw_sum,
                "audit_saved_vs_separate_zstd1": separate - joint,
                "audit_saved_vs_raw": raw_sum - joint,
            })

        group = []; used = cap = 0
        for h, c in eligible:
            size = len(c.raw)
            if not group:
                group=[(h,c)]; used=size; cap=int(BASE.LOCALITY_BUDGET*max(1,size)); continue
            if used + size > cap:
                flush(group); group=[(h,c)]; used=size; cap=int(BASE.LOCALITY_BUDGET*max(1,size))
            else:
                group.append((h,c)); used += size
        flush(group)

        self._locality_derived_groups = emitted_groups
        self._content_economic_audit = {
            "eligible_members": len(eligible), "auditions": auditions,
            "rejected_groups": rejected_groups, "rejected_members": rejected_members,
            "accepted_groups": len(emitted_groups),
            "accepted_members": sum(int(g["members"]) for g in emitted_groups),
            "raw_floor_rejections": raw_floor_rejections,
            "zstd_separate_rejections": zstd_separate_rejections,
            "audition_cpu_s": audit_cpu, "audition_wall_s": audit_wall,
        }


def _clean(arm: dict) -> dict:
    return {k:v for k,v in arm.items() if k not in {"archive","index"}}


def _one(source: Path, root: Path) -> dict:
    independent = SEL._build_variant(SAME.NoMicroPackBuilder, source, root/'independent')
    extension = SEL._build_variant(BASE.LocalityDerivedBuilder, source, root/'extension')
    current = SEL._build_variant(ContentEconomicBuilder, source, root/'current')
    raw_floor = SEL._build_variant(RawFloorBuilder, source, root/'raw_floor')

    # Keep the old candidate's expensive members as the fixed probe population so a
    # new rule cannot evade a known debt by making those files disappear from sampling.
    probes = SEL._probes(source, current)
    timings = {}
    if probes:
        for name, arm in (("independent",independent),("current",current),("raw_floor",raw_floor)):
            timings[name] = SEL._time_variant(arm, probes)

    raw_debt = SEL._confirmed_regression(timings['raw_floor'], timings['independent']) if probes else {
        'confirmed_regression': False, 'candidate_wall_s':0.0, 'base_wall_s':0.0, 'delta_wall_s':0.0, 'relative':0.0}
    current_debt = SEL._confirmed_regression(timings['current'], timings['independent']) if probes else dict(raw_debt)
    variants = {"independent":_clean(independent),"extension":_clean(extension),"current":_clean(current),"raw_floor":_clean(raw_floor)}
    inv = {
        "all_tree_exact": all(x['strong_tree_exact'] for x in (independent,extension,current,raw_floor)),
        "raw_floor_locality": raw_floor['locality_pass'],
        "raw_floor_amp_at_most_8x": raw_floor['max_member_amplification'] <= BASE.LOCALITY_BUDGET + 1e-9,
        "raw_floor_payload_exact": raw_floor['physical_payload_exact'],
        "raw_floor_tail_recovery": raw_floor['tail_recovery'],
        "reads_exact": all(not t['correctness_failures'] for t in timings.values()) if timings else True,
    }
    return {
        "variants": variants,
        "probe_count": len(probes),
        "timings": timings,
        "current_timing_debt": bool(current_debt['confirmed_regression']),
        "raw_floor_timing_debt": bool(raw_debt['confirmed_regression']),
        "current_vs_independent": current_debt,
        "raw_floor_vs_independent": raw_debt,
        "raw_floor_delta_vs_extension_bytes": raw_floor['final_membership_bytes'] - extension['final_membership_bytes'],
        "raw_floor_delta_vs_current_bytes": raw_floor['final_membership_bytes'] - current['final_membership_bytes'],
        "raw_floor_delta_vs_independent_bytes": raw_floor['final_membership_bytes'] - independent['final_membership_bytes'],
        "invariants": inv,
        "invariants_pass": all(inv.values()),
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
    missing = sorted(targets - set(paths))
    if missing:
        raise RuntimeError(f'missing target workloads: {missing}')
    rows = {key:_one(paths[key], work_root/'work'/key.split('/')[0]/key.split('/')[1]) for key in sorted(targets)}
    invariant_failures=[k for k,r in rows.items() if not r['invariants_pass']]
    debt_failures=[k for k,r in rows.items() if r['raw_floor_timing_debt']]
    extension_losses=[k for k,r in rows.items() if r['raw_floor_delta_vs_extension_bytes'] > 0]
    known_debt={
        'neutral_hostile_v1/07_incompressible_and_encrypted_like',
        'resemblance_hostile_v1/02_false_neighbors',
        'resemblance_hostile_v1/05_incompressible',
    }
    current_debt_reproduced=sorted(k for k in known_debt if rows[k]['current_timing_debt'])
    if invariant_failures or debt_failures or extension_losses:
        verdict='RETIRE_RAW_FLOOR_ADMISSION'
    else:
        verdict='RAW_FLOOR_ADMISSION_EARNS_CURRENT15_TRANSFER'
    return {
        'schema':'cmpct-v030-r24-raw-floor-admission-v1',
        'experiment_valid':True,'release_credit':False,'canonical_builder_changed':False,
        'genesis_rescore':False,'path_signal_used':False,
        'corpus_fingerprint':fingerprint,
        'rule':'joint_zstd1 < separate_zstd1 AND joint_zstd1 < aggregate_raw_bytes',
        'targets':sorted(targets),'rows':rows,
        'current_known_debt_reproduced':current_debt_reproduced,
        'invariant_failures':invariant_failures,'raw_floor_timing_debt':debt_failures,
        'losses_vs_extension':extension_losses,'verdict':verdict,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-raw-floor-work')); ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-raw-floor.json')); args=ap.parse_args()
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
        'verdict':result['verdict'],'fingerprint':result['corpus_fingerprint'],
        'current_known_debt_reproduced':result['current_known_debt_reproduced'],
        'raw_floor_timing_debt':result['raw_floor_timing_debt'],
        'losses_vs_extension':result['losses_vs_extension'],
        'invariant_failures':result['invariant_failures'],
        'rows':{k:{'di':v['raw_floor_delta_vs_independent_bytes'],'de':v['raw_floor_delta_vs_extension_bytes'],'dc':v['raw_floor_delta_vs_current_bytes'],'current_debt':v['current_timing_debt'],'raw_debt':v['raw_floor_timing_debt'],'current_ms':v.get('timings',{}).get('current',{}).get('median_read_wall_ms_per_probe'),'raw_ms':v.get('timings',{}).get('raw_floor',{}).get('median_read_wall_ms_per_probe'),'ind_ms':v.get('timings',{}).get('independent',{}).get('median_read_wall_ms_per_probe'),'audit':v['variants']['raw_floor']['audit']} for k,v in result['rows'].items()},
    },indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
