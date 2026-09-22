from __future__ import annotations

"""Second hostile review for the per-container positive-byte hidden-ZIP admission gate.

V2 fixed zero-length false signals and unrelated-passenger admission. This receipt attacks the remaining economic
assumption: *any* positive shared member may still be far too weak to pay for recipe construction/representation.
The control creates two large hidden ZIPs with one exact one-byte member and otherwise distinct high-entropy payloads.
A scientifically successful economic gate should not make the complete archive larger than the ordinary Builder.
Green CI means only that the receipt completed.
"""

import argparse
import json
import os
from pathlib import Path
import random
import shutil
import time
import zipfile

from benchmarks.v030_r4_content_zip_correlation_gate_v2 import PositiveByteGateBuilder
from experiments.v030_r4_content_zip_builder import ContentZipBuilder
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT


def _write(path:Path, seed:int):
    rng=random.Random(seed)
    raw=rng.randbytes(512*1024)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('shared-one-byte.bin',b'X')
        z.writestr(f'unique-{seed}.bin',raw)


def _measure(cls,root:Path,out:Path):
    cpu0=time.process_time();wall0=time.perf_counter();stats=dict(cls(root).build(out));cpu=time.process_time()-cpu0;wall=time.perf_counter()-wall0
    dest=out.with_suffix('.out');shutil.rmtree(dest,ignore_errors=True)
    with CMPCT(out) as ar:
        vzip=[r[0] for r in ar.files if r[1]==0 and r[6] and r[6][0]==S_VZIP]
        ar.extractall(dest,metadata=True)
    for p in root.iterdir():
        if p.is_file() and (dest/p.name).read_bytes()!=p.read_bytes():raise RuntimeError(f'exact mismatch {p.name}')
    return {'archive_bytes':out.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'vzip_files':vzip,'stats':stats}


def run(work:Path):
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True);root=work/'root';root.mkdir()
    _write(root/'left-hidden.bin',11);_write(root/'right-hidden.bin',29)
    rows={}
    for label,cls in (('baseline',Builder),('all_valid',ContentZipBuilder),('positive_gate',PositiveByteGateBuilder)):
        rows[label]=_measure(cls,root,work/f'{label}.cmpct')
    b=rows['baseline']['archive_bytes'];g=rows['positive_gate']['archive_bytes'];a=rows['all_valid']['archive_bytes']
    gate=rows['positive_gate']['stats'].get('positive_byte_gate') or {}
    hyp={
        'positive_gate_detects_one_byte_signal':gate.get('admitted_hidden_zip_files')==2,
        'one_byte_signal_is_economically_safe':g<=b,
        'ordinary_baseline_not_regressed':g<=b,
    }
    return {'schema':'cmpct-v030-r4-content-zip-positive-gate-hostile-v2','source_commit':os.environ.get('EVIDENCE_HEAD'),'rows':rows,
            'economics':{'baseline_bytes':b,'all_valid_bytes':a,'positive_gate_bytes':g,'positive_gate_delta_vs_baseline':g-b,'positive_gate_cpu_delta_vs_baseline_s':rows['positive_gate']['create_cpu_s']-rows['baseline']['create_cpu_s']},
            'hypothesis':{**hyp,'current_zero_threshold_survives':all(hyp.values())},
            'contract':{'diagnostic_only':True,'release_credit':False,'green_ci_is_not_scientific_success':True,'shipping_builder_changed':False},
            'next_if_falsified':'derive a preregistered per-container information-yield predicate from shared-positive bytes relative to candidate size/unique bytes and measured recipe overhead; do not choose a workload-specific constant',
            'next_if_supported':'expand to logarithmic shared-byte ladder and adversarial same-size CRC hints before promotion'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-positive-gate-hostile-v2-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-positive-gate-hostile-v2.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,default=str)+'\n');print(json.dumps({'economics':r['economics'],'hypothesis':r['hypothesis']},indent=2))
if __name__=='__main__':main()
