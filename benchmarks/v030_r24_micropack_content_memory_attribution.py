from __future__ import annotations

"""Phase-level memory attribution for path-blind content-economic micro-packs.

Fresh-process economics exposed +3.5 MiB (Developer) and +8.3 MiB (Tiny) peak RSS
versus same-grammar independent.  This diagnostic does not optimize or gate the
mechanism.  It separates current resident state after major Builder phases from
process high-water RSS so the next intervention targets retained product state
or transient discovery traffic for causal reasons.

Linux hosted runner only; research evidence, no release credit.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks import v030_r24_micropack_same_grammar_attribution as SAME
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder, _arm

ROUNDS = 3


def _current_rss_kib() -> int:
    with open('/proc/self/status', 'r', encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    raise RuntimeError('VmRSS unavailable')


class _RSSMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rss_phases = {'post_init': _current_rss_kib()}

    def scan(self):
        result = super().scan()
        self._rss_phases['post_scan'] = _current_rss_kib()
        return result

    def _build_micro_packs(self):
        result = super()._build_micro_packs()
        self._rss_phases['post_micropack'] = _current_rss_kib()
        return result

    def _prepare_deflate_reuse(self):
        result = super()._prepare_deflate_reuse()
        self._rss_phases['post_deflate_reuse'] = _current_rss_kib()
        return result

    def _train_dictionary(self):
        result = super()._train_dictionary()
        self._rss_phases['post_dictionary'] = _current_rss_kib()
        return result


class InstrumentedIndependent(_RSSMixin, SAME.NoMicroPackBuilder):
    pass


class InstrumentedContent(_RSSMixin, ContentEconomicBuilder):
    pass


BUILDERS = {
    'independent': InstrumentedIndependent,
    'content_economic': InstrumentedContent,
}


def _worker(source: Path, work: Path, variant: str) -> dict:
    builder_cls = BUILDERS[variant]
    # Reproduce _arm but retain access to the builder's phase snapshots.
    work.mkdir(parents=True, exist_ok=True)
    b = builder_cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    archive = work / 'base.cmpct'
    build = BASE._build_with(b, archive)
    post_build_rss = _current_rss_kib()
    index, data = BASE._parse_r24(archive)
    locality = BASE._pack_locality(index)
    verify = BASE.PRODUCT.strong_verify(archive)
    if not verify.get('ok'):
        raise RuntimeError('base strong verify failed')
    membership = work / 'membership.cmpct'
    if getattr(b, '_locality_derived_groups', []):
        wrapped = SAME._candidate(archive, membership, work)
    else:
        wrapped = SAME._noop_candidate(archive, len(data), verify)
    post_membership_rss = _current_rss_kib()
    return {
        'variant': variant,
        'archive_bytes': int(wrapped['archive_bytes']),
        'groups': len(getattr(b, '_locality_derived_groups', [])),
        'phase_rss_kib': dict(b._rss_phases),
        'post_build_rss_kib': post_build_rss,
        'post_membership_rss_kib': post_membership_rss,
        'peak_rss_kib': int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'max_decode_unit_bytes': int(locality['max_decode_unit_bytes']),
        'locality_pass': bool(locality['locality_pass']),
        'strong_tree_exact': bool(verify.get('ok')),
        'tail_recovery': bool(wrapped['primary_corruption_tail_recovery']),
        'audit': dict(getattr(b, '_content_economic_audit', {})),
        'build_cpu_s': float(build['build_cpu_s']),
        'build_wall_s': float(build['build_wall_s']),
    }


def _child(source: Path, work: Path, variant: str) -> dict:
    cp = subprocess.run([
        sys.executable, '-m', 'benchmarks.v030_r24_micropack_content_memory_attribution',
        '--worker', '--source', str(source), '--work-root', str(work), '--variant', variant,
    ], check=True, capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED':'0'})
    lines=[x for x in cp.stdout.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError(cp.stderr[-2000:])
    return json.loads(lines[-1])


def _median(rows: list[dict], getter) -> int:
    return int(statistics.median(getter(r) for r in rows))


def _summary(rows: list[dict]) -> dict:
    phases = sorted(rows[0]['phase_rss_kib'])
    return {
        'archive_bytes': int(rows[0]['archive_bytes']),
        'groups': int(rows[0]['groups']),
        'median_phase_rss_kib': {p: _median(rows, lambda r, p=p: int(r['phase_rss_kib'][p])) for p in phases},
        'median_post_build_rss_kib': _median(rows, lambda r: int(r['post_build_rss_kib'])),
        'median_post_membership_rss_kib': _median(rows, lambda r: int(r['post_membership_rss_kib'])),
        'median_peak_rss_kib': _median(rows, lambda r: int(r['peak_rss_kib'])),
        'max_decode_unit_bytes': max(int(r['max_decode_unit_bytes']) for r in rows),
        'audition_cpu_s_median': float(statistics.median(float(r['audit'].get('audition_cpu_s',0.0)) for r in rows)),
        'auditions': int(rows[0]['audit'].get('auditions',0)),
        'accepted_groups': int(rows[0]['audit'].get('accepted_groups',0)),
        'rejected_groups': int(rows[0]['audit'].get('rejected_groups',0)),
        'raw_rounds': rows,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus=work_root/'corpus'; ATTR._build_sources(corpus)
    sources={
        'origin_developer': corpus/'01_developer_repository',
        'origin_tiny_files': corpus/'08_many_tiny_files',
    }
    out={}
    for name, source in sources.items():
        raw={v:[] for v in BUILDERS}
        for round_idx in range(ROUNDS):
            order=('independent','content_economic') if round_idx%2==0 else ('content_economic','independent')
            for variant in order:
                raw[variant].append(_child(source, work_root/'workers'/name/f'r{round_idx}-{variant}', variant))
        arms={v:_summary(rows) for v,rows in raw.items()}
        i=arms['independent']; c=arms['content_economic']
        phase_delta={p:int(c['median_phase_rss_kib'][p])-int(i['median_phase_rss_kib'][p]) for p in c['median_phase_rss_kib']}
        out[name]={
            'arms':arms,
            'phase_delta_kib_content_minus_independent':phase_delta,
            'post_build_delta_kib':c['median_post_build_rss_kib']-i['median_post_build_rss_kib'],
            'post_membership_delta_kib':c['median_post_membership_rss_kib']-i['median_post_membership_rss_kib'],
            'peak_delta_kib':c['median_peak_rss_kib']-i['median_peak_rss_kib'],
        }
    return {
        'schema':'cmpct-v030-r24-content-memory-attribution-v1',
        'experiment_valid':True,
        'release_credit':False,
        'canonical_builder_changed':False,
        'source_commit':os.environ.get('GITHUB_SHA'),
        'rss_credit':False,
        'sources':out,
        'verdict':'CONTENT_MEMORY_ATTRIBUTION_COMPLETE',
    }


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--worker',action='store_true'); ap.add_argument('--source',type=Path); ap.add_argument('--variant',choices=tuple(BUILDERS)); ap.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-content-memory-work')); ap.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-content-memory.json')); args=ap.parse_args()
    if args.worker:
        if args.source is None or args.variant is None: raise SystemExit('--worker requires source/variant')
        print(json.dumps(_worker(args.source,args.work_root,args.variant),sort_keys=True),flush=True); return
    result=run(args.work_root); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':result['verdict'],'sources':{n:{'phase_delta':r['phase_delta_kib_content_minus_independent'],'post_build_delta':r['post_build_delta_kib'],'post_membership_delta':r['post_membership_delta_kib'],'peak_delta':r['peak_delta_kib'],'auditions':r['arms']['content_economic']['auditions'],'accepted':r['arms']['content_economic']['accepted_groups'],'rejected':r['arms']['content_economic']['rejected_groups']} for n,r in result['sources'].items()}},indent=2,sort_keys=True),flush=True)

if __name__=='__main__': main()
