from __future__ import annotations

"""Hostile causal tests for the first content-ZIP correlation gate.

The matrix gate intentionally used a high-recall cohort-wide rule: any repeated member (CRC32,size) across distinct
valid ZIP containers admits every hidden valid ZIP in the build scope.  This falsifier attacks two assumptions before
shipping work:

1. zero-byte/trivial repeated members must not manufacture an opportunity signal;
2. a genuinely correlated pair must not drag an unrelated hidden ZIP passenger onto the expensive recipe path.

A green CI job only means the receipt completed. Hypothesis booleans record whether the current policy survives.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

from benchmarks.v030_r4_content_zip_correlation_gate import CorrelationGateBuilder
from experiments.v030_r4_content_zip_builder import ContentZipBuilder
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT


def _write_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, raw in members:
            z.writestr(name, raw)


def _measure(root: Path, work: Path, label: str, cls) -> dict:
    archive = work / f'{label}.cmpct'
    cpu0=time.process_time(); wall0=time.perf_counter(); stats=dict(cls(root).build(archive)); cpu=time.process_time()-cpu0; wall=time.perf_counter()-wall0
    out=work/f'{label}-out'; shutil.rmtree(out,ignore_errors=True)
    with CMPCT(archive) as ar:
        vzip=[row[0] for row in ar.files if row[1]==0 and row[6] and row[6][0]==S_VZIP]
        ar.extractall(out,metadata=True)
    for p in sorted(q for q in root.rglob('*') if q.is_file()):
        q=out/p.relative_to(root)
        if not q.exists() or q.read_bytes()!=p.read_bytes(): raise RuntimeError(f'exact reconstruction mismatch: {p}')
    return {'archive_bytes':archive.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'vzip_files':vzip,'vzip_count':len(vzip),'stats':stats}


def _case_empty_signature(base: Path) -> dict:
    root=base/'empty-signature-root'; root.mkdir(parents=True)
    # Different nontrivial payloads, but both containers carry one empty member: (CRC32=0,size=0).
    _write_zip(root/'left.bin',[('empty',b''),('left.bin',bytes(range(256))*256)])
    _write_zip(root/'right.bin',[('empty',b''),('right.bin',bytes(reversed(range(256)))*256)])
    work=base/'empty-signature-work'; work.mkdir(parents=True)
    b=_measure(root,work,'baseline',Builder); a=_measure(root,work,'all-valid',ContentZipBuilder); g=_measure(root,work,'gated',CorrelationGateBuilder)
    gate=g['stats'].get('correlation_gate') or {}
    return {'baseline':b,'all_valid':a,'gated':g,'gate':gate,
            'hypothesis':{'trivial_empty_signature_does_not_trigger':not bool(gate.get('cohort_signal')),
                          'trivial_case_hidden_not_admitted':int(gate.get('admitted_hidden_zip_files',0))==0,
                          'gated_matches_baseline_bytes':g['archive_bytes']==b['archive_bytes']}}


def _case_passenger(base: Path) -> dict:
    root=base/'passenger-root'; root.mkdir(parents=True)
    shared=(b'shared-semantic-payload\n'*8192)
    _write_zip(root/'version-a.bin',[('shared.dat',shared),('unique-a.txt',b'A'*4096)])
    _write_zip(root/'version-b.bin',[('shared.dat',shared),('unique-b.txt',b'B'*4096)])
    # Valid but unrelated passenger; should not be admitted merely because another pair is correlated.
    passenger=bytes((i*131+17)&255 for i in range(512*1024))
    _write_zip(root/'passenger.bin',[('passenger.dat',passenger)])
    work=base/'passenger-work'; work.mkdir(parents=True)
    b=_measure(root,work,'baseline',Builder); a=_measure(root,work,'all-valid',ContentZipBuilder); g=_measure(root,work,'gated',CorrelationGateBuilder)
    gate=g['stats'].get('correlation_gate') or {}
    admitted=set(g['vzip_files'])
    return {'baseline':b,'all_valid':a,'gated':g,'gate':gate,
            'hypothesis':{'real_correlation_detected':bool(gate.get('cohort_signal')),
                          'correlated_pair_admitted':{'version-a.bin','version-b.bin'}.issubset(admitted),
                          'unrelated_passenger_not_admitted':'passenger.bin' not in admitted,
                          'only_correlated_pair_admitted':admitted=={'version-a.bin','version-b.bin'}}}


def run(work: Path) -> dict:
    shutil.rmtree(work,ignore_errors=True); work.mkdir(parents=True)
    empty=_case_empty_signature(work); passenger=_case_passenger(work)
    survived=all(empty['hypothesis'].values()) and all(passenger['hypothesis'].values())
    return {'schema':'cmpct-v030-r4-content-zip-correlation-hostile-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),
            'cases':{'trivial_empty_signature':empty,'correlated_pair_with_unrelated_passenger':passenger},
            'hypothesis':{'coarse_correlation_gate_survives_hostile_review':survived},
            'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'format_changed':False,'reader_changed':False,
                        'green_ci_means_receipt_integrity_not_scientific_success':True},
            'next_if_falsified':'replace cohort-wide any-signature admission with per-container positive-byte correlation accounting; ignore zero-length signatures; rerun full matrix plus these controls',
            'next_if_supported':'add bounded central-directory preflight/resource and repeated CPU/RSS/locality evidence before canonical Builder integration'}


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-correlation-hostile-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-content-zip-correlation-hostile.json')); a=p.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps({'hypothesis':r['hypothesis'],'case_hypotheses':{k:v['hypothesis'] for k,v in r['cases'].items()}},indent=2))

if __name__=='__main__': main()
