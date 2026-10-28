from __future__ import annotations

"""Streaming-length audition referee for content-economic micro-packs.

Mission lock
============
The retained-state referee showed that Developer's apparent post-build RSS debt
mostly disappears under allocator trim, while peak RSS remains a real transient
cost.  The content-economic admission probe currently materializes complete
Zstd-1 outputs merely to compare their lengths, then discards them; accepted
packs are later encoded independently by the real r24 codec competition.

Falsifiable hypothesis
----------------------
A known-size, chunk-fed Zstd compression object can count the exact same Zstd-1
frame length without retaining the compressed payload. Replacing only the
*measurement* primitive must preserve every accept/reject decision and produce
byte-identical final archives on origin + hostile controls while reducing peak
RSS on at least one origin workload without a material CPU regression.

Disproof: any one-shot vs streaming length mismatch, decision mismatch, archive
byte mismatch, invariant failure, or a >=5% and >=10 ms median CPU regression on
an origin workload retires this mechanism.

Research-only. No canonical Builder, format, locality, codec levels, thresholds,
or Genesis score are changed here.
"""

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

import zstandard as zstd

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_locality_derived_micropack_hostile_transfer as HOST
from benchmarks import v030_r24_locality_derived_micropack_referee as BASE
from benchmarks.v030_r24_micropack_content_economic_admission import ContentEconomicBuilder

CHUNK = 64 * 1024
ROUNDS = 3


def _stream_zstd1_len(data: bytes, compressor: zstd.ZstdCompressor) -> int:
    obj = compressor.compressobj(size=len(data))
    total = 0
    view = memoryview(data)
    for off in range(0, len(data), CHUNK):
        total += len(obj.compress(view[off:off + CHUNK]))
    total += len(obj.flush(zstd.COMPRESSOBJ_FLUSH_FINISH))
    return total


class StreamingAuditionBuilder(BASE.BUILDER.Builder):
    """ContentEconomicBuilder semantics with only output-length materialization removed."""

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
        audit_cpu = 0.0
        audit_wall = 0.0
        auditions = 0
        rejected_groups = 0
        rejected_members = 0
        length_checks = 0
        length_mismatches = []

        def checked_len(data: bytes, label: str) -> int:
            nonlocal length_checks
            streaming = _stream_zstd1_len(data, compressor)
            # The one-shot value is retained only by this referee as a falsifier.
            # A promoted Builder would remove this control path entirely.
            one_shot = len(compressor.compress(data))
            length_checks += 1
            if streaming != one_shot:
                length_mismatches.append({"label": label, "raw_bytes": len(data), "streaming": streaming, "one_shot": one_shot})
            return streaming

        def flush(group):
            nonlocal audit_cpu, audit_wall, auditions, rejected_groups, rejected_members
            if len(group) < 2:
                return
            buf = b"".join(c.raw for _, c in group)
            smallest = len(group[0][1].raw)
            if len(buf) > int(BASE.LOCALITY_BUDGET * max(1, smallest)):
                raise RuntimeError("streaming-audition group exceeds 8x smallest-member law")

            c0 = time.process_time(); w0 = time.perf_counter()
            joint = checked_len(buf, "joint")
            separate = sum(checked_len(c.raw, "member") for _, c in group)
            audit_cpu += time.process_time() - c0
            audit_wall += time.perf_counter() - w0
            auditions += 1
            if joint >= separate:
                rejected_groups += 1
                rejected_members += len(group)
                return

            ph = self.add_content(buf, ".cmpct-pack")
            slots = {}
            off = 0
            for h, c in group:
                slots[h] = (off, len(c.raw)); off += len(c.raw)
            for h, (start, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [BASE.R24.S_PACK, ph, start, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)
            emitted_groups.append({
                "members": len(group), "raw_bytes": len(buf),
                "smallest_member_bytes": smallest,
                "max_raw_amplification": len(buf) / max(1, smallest),
                "audit_joint_zstd1_bytes": joint,
                "audit_separate_zstd1_bytes": separate,
                "audit_saved_bytes": separate - joint,
            })

        group = []; used = 0; cap = 0
        for h, c in eligible:
            size = len(c.raw)
            if not group:
                group = [(h, c)]; used = size; cap = int(BASE.LOCALITY_BUDGET * max(1, size)); continue
            if used + size > cap:
                flush(group); group = [(h, c)]; used = size; cap = int(BASE.LOCALITY_BUDGET * max(1, size))
            else:
                group.append((h, c)); used += size
        flush(group)

        self._locality_derived_groups = emitted_groups
        self._content_economic_audit = {
            "eligible_members": len(eligible), "auditions": auditions,
            "rejected_groups": rejected_groups, "rejected_members": rejected_members,
            "accepted_groups": len(emitted_groups),
            "accepted_members": sum(int(g["members"]) for g in emitted_groups),
            "audition_cpu_s": audit_cpu, "audition_wall_s": audit_wall,
            "accepted_audit_saved_bytes": sum(int(g["audit_saved_bytes"]) for g in emitted_groups),
            "streaming_length_checks": length_checks,
            "streaming_length_mismatches": length_mismatches,
        }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _build_one(builder_cls, source: Path, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    b = builder_cls(source, deflate_reuse_min=0, workers=1)
    b.micro_pack_max_file = int(BASE.PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)
    out = root / 'base.cmpct'
    c0 = time.process_time(); w0 = time.perf_counter()
    stats = dict(b.build(out))
    cpu = time.process_time() - c0; wall = time.perf_counter() - w0
    verify = BASE.PRODUCT.strong_verify(out)
    index, _ = BASE._parse_r24(out)
    locality = BASE._pack_locality(index)
    audit = dict(getattr(b, '_content_economic_audit', {}))
    groups = list(getattr(b, '_locality_derived_groups', []))
    return {
        'archive_bytes': out.stat().st_size,
        'archive_sha256': _sha256(out),
        'cpu_s': cpu, 'wall_s': wall,
        'peak_rss_kib': int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        'strong_verify': bool(verify.get('ok')),
        'locality_pass': bool(locality['locality_pass']),
        'max_decode_unit_bytes': int(locality['max_decode_unit_bytes']),
        'groups': len(groups), 'group_members': sum(int(g['members']) for g in groups),
        'audit': audit,
        'stats': stats,
    }


def _worker(source: Path, root: Path, variant: str) -> dict:
    cls = ContentEconomicBuilder if variant == 'oneshot' else StreamingAuditionBuilder
    return _build_one(cls, source, root)


def _child(source: Path, root: Path, variant: str) -> dict:
    cp = subprocess.run([
        sys.executable, '-m', 'benchmarks.v030_r24_micropack_streaming_audition_referee',
        '--worker', '--source', str(source), '--work-root', str(root), '--variant', variant,
    ], check=True, capture_output=True, text=True, env={**os.environ, 'PYTHONHASHSEED': '0'})
    lines = [x for x in cp.stdout.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError(cp.stderr[-2000:])
    return json.loads(lines[-1])


def _median(rows, key):
    return float(statistics.median(float(r[key]) for r in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    origin = work_root / 'origin'; ATTR._build_sources(origin)
    hostile = HOST._build_corpora(work_root / 'hostile')
    sources = {
        'origin_developer': origin / '01_developer_repository',
        'origin_tiny_files': origin / '08_many_tiny_files',
        **{f'hostile_{name}': p for name, p in hostile.items()},
    }

    rows = {}
    for name, source in sources.items():
        rounds = ROUNDS if name.startswith('origin_') else 1
        arms = {'oneshot': [], 'streaming': []}
        for i in range(rounds):
            order = ('oneshot', 'streaming') if i % 2 == 0 else ('streaming', 'oneshot')
            for variant in order:
                arms[variant].append(_child(source, work_root / 'workers' / name / f'r{i}-{variant}', variant))
        o, s = arms['oneshot'][0], arms['streaming'][0]
        identity = {
            'archive_bytes_equal': o['archive_bytes'] == s['archive_bytes'],
            'archive_sha256_equal': o['archive_sha256'] == s['archive_sha256'],
            'groups_equal': o['groups'] == s['groups'],
            'group_members_equal': o['group_members'] == s['group_members'],
            'stream_lengths_exact': not s['audit'].get('streaming_length_mismatches', []),
            'strong_verify_both': o['strong_verify'] and s['strong_verify'],
            'locality_both': o['locality_pass'] and s['locality_pass'],
        }
        med = {
            'oneshot_cpu_s': _median(arms['oneshot'], 'cpu_s'),
            'streaming_cpu_s': _median(arms['streaming'], 'cpu_s'),
            'oneshot_wall_s': _median(arms['oneshot'], 'wall_s'),
            'streaming_wall_s': _median(arms['streaming'], 'wall_s'),
            'oneshot_peak_rss_kib': int(statistics.median(int(r['peak_rss_kib']) for r in arms['oneshot'])),
            'streaming_peak_rss_kib': int(statistics.median(int(r['peak_rss_kib']) for r in arms['streaming'])),
        }
        med['cpu_delta_s'] = med['streaming_cpu_s'] - med['oneshot_cpu_s']
        med['cpu_delta_ratio'] = med['cpu_delta_s'] / max(1e-9, med['oneshot_cpu_s'])
        med['peak_rss_delta_kib'] = med['streaming_peak_rss_kib'] - med['oneshot_peak_rss_kib']
        material_cpu_regression = med['cpu_delta_ratio'] >= 0.05 and med['cpu_delta_s'] >= 0.010
        rows[name] = {
            'identity': identity,
            'identity_pass': all(identity.values()),
            'medians': med,
            'material_cpu_regression': material_cpu_regression,
            'oneshot_audit': o['audit'],
            'streaming_audit': s['audit'],
            'rounds': arms,
        }

    identity_failures = [k for k,v in rows.items() if not v['identity_pass']]
    cpu_regressions = [k for k,v in rows.items() if k.startswith('origin_') and v['material_cpu_regression']]
    rss_improvements = [k for k,v in rows.items() if k.startswith('origin_') and v['medians']['peak_rss_delta_kib'] < 0]
    verdict = 'STREAMING_AUDITION_EARNED' if not identity_failures and not cpu_regressions and rss_improvements else 'RETIRE_STREAMING_AUDITION'
    return {
        'schema': 'cmpct-v030-r24-streaming-audition-v1',
        'experiment_valid': True, 'release_credit': False,
        'canonical_builder_changed': False, 'genesis_rescore': False,
        'chunk_bytes': CHUNK, 'origin_rounds': ROUNDS,
        'sources': rows,
        'identity_failures': identity_failures,
        'material_cpu_regressions': cpu_regressions,
        'origin_rss_improvements': rss_improvements,
        'verdict': verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--worker', action='store_true')
    ap.add_argument('--source', type=Path)
    ap.add_argument('--variant', choices=('oneshot','streaming'))
    ap.add_argument('--work-root', type=Path, default=Path('benchmark-artifacts/v030-streaming-audition-work'))
    ap.add_argument('--output', type=Path, default=Path('benchmark-artifacts/v030-streaming-audition.json'))
    args = ap.parse_args()
    if args.worker:
        if args.source is None or args.variant is None:
            raise SystemExit('--worker requires --source and --variant')
        print(json.dumps(_worker(args.source,args.work_root,args.variant),sort_keys=True),flush=True); return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
        'verdict':result['verdict'],
        'identity_failures':result['identity_failures'],
        'material_cpu_regressions':result['material_cpu_regressions'],
        'origin_rss_improvements':result['origin_rss_improvements'],
        'origins':{k:v['medians'] for k,v in result['sources'].items() if k.startswith('origin_')},
    },indent=2,sort_keys=True),flush=True)

if __name__ == '__main__':
    main()
