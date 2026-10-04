from __future__ import annotations

"""Measure the byte/CPU break-even curve for per-container hidden-ZIP correlation.

This is a mechanism attribution experiment, not an admission rule. Two hidden ZIPs contain one exact shared member
of controlled size plus distinct high-entropy members. Central-directory metadata exposes member compressed sizes
before recipe construction. The receipt measures when existing S_VZIP economics cross ordinary storage and how
well the observable repeated compressed-size mass predicts actual complete-archive savings.
"""

import argparse
import json
import os
from pathlib import Path
import random
import shutil
import time
import zipfile

from experiments.v030_r4_content_zip_builder import ContentZipBuilder
from cmpct.builder import Builder
from cmpct.codec import S_VZIP
from cmpct.reader import CMPCT

SHARED_SIZES=(1,16,64,256,1024,4096,16384,65536,262144)
UNIQUE_SIZE=512*1024


def _bytes(seed:int,n:int)->bytes:
    return random.Random(seed).randbytes(n)


def _write(path:Path, shared:bytes, unique:bytes, label:str):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('shared.bin',shared)
        z.writestr(f'unique-{label}.bin',unique)


def _central(path:Path)->dict:
    with zipfile.ZipFile(path) as z:
        return {i.filename:{'crc':int(i.CRC),'size':int(i.file_size),'compressed_size':int(i.compress_size),'method':int(i.compress_type)} for i in z.infolist() if not i.is_dir()}


def _build(cls,root:Path,out:Path)->dict:
    c0=time.process_time();w0=time.perf_counter();stats=dict(cls(root).build(out));cpu=time.process_time()-c0;wall=time.perf_counter()-w0
    dest=out.with_suffix('.out');shutil.rmtree(dest,ignore_errors=True)
    with CMPCT(out) as ar:
        vzip=[r[0] for r in ar.files if r[1]==0 and r[6] and r[6][0]==S_VZIP]
        ar.extractall(dest,metadata=True)
    for p in root.iterdir():
        if p.is_file() and (dest/p.name).read_bytes()!=p.read_bytes():raise RuntimeError(f'exact mismatch {p.name}')
    return {'archive_bytes':out.stat().st_size,'create_cpu_s':cpu,'create_wall_s':wall,'vzip_files':vzip,'stats':stats}


def _case(work:Path,n:int)->dict:
    root=work/f'root-{n}';root.mkdir(parents=True)
    shared=_bytes(101,n);left=_bytes(201,UNIQUE_SIZE);right=_bytes(301,UNIQUE_SIZE)
    lp=root/'left.bin';rp=root/'right.bin';_write(lp,shared,left,'left');_write(rp,shared,right,'right')
    lmeta=_central(lp)['shared.bin'];rmeta=_central(rp)['shared.bin']
    baseline=_build(Builder,root,work/f'baseline-{n}.cmpct');candidate=_build(ContentZipBuilder,root,work/f'candidate-{n}.cmpct')
    # If the repeated compressed streams are byte-identical, one duplicate stream is the maximum obvious physical
    # saving available before control/recipe overhead. compressed_size is central-directory-visible.
    with zipfile.ZipFile(lp) as zl, zipfile.ZipFile(rp) as zr:
        li=zl.getinfo('shared.bin');ri=zr.getinfo('shared.bin')
        ls=zl.read('shared.bin');rs=zr.read('shared.bin')
    return {'shared_uncompressed_bytes':n,'left_shared_meta':lmeta,'right_shared_meta':rmeta,
            'observable_repeated_compressed_bytes':min(lmeta['compressed_size'],rmeta['compressed_size']),
            'shared_logical_equal':ls==rs,
            'baseline':baseline,'candidate':candidate,
            'archive_delta_candidate_minus_baseline':candidate['archive_bytes']-baseline['archive_bytes'],
            'saving_bytes':baseline['archive_bytes']-candidate['archive_bytes'],
            'cpu_delta_s':candidate['create_cpu_s']-baseline['create_cpu_s']}


def run(work:Path)->dict:
    shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
    rows=[]
    for n in SHARED_SIZES:
        row=_case(work,n);rows.append(row);print(json.dumps({'shared':n,'compressed_hint':row['observable_repeated_compressed_bytes'],'saving':row['saving_bytes'],'cpu_delta':row['cpu_delta_s']}),flush=True)
    wins=[r for r in rows if r['saving_bytes']>0];first=min((r['shared_uncompressed_bytes'] for r in wins),default=None)
    overhead_samples=[r['observable_repeated_compressed_bytes']-r['saving_bytes'] for r in rows]
    return {'schema':'cmpct-v030-r4-content-zip-shared-byte-ladder-v1','source_commit':os.environ.get('EVIDENCE_HEAD'),'unique_bytes_per_container':UNIQUE_SIZE,'rows':rows,
            'summary':{'first_tested_positive_shared_size_with_net_byte_win':first,'representation_overhead_estimates_bytes':overhead_samples,
                       'overhead_estimate_min':min(overhead_samples),'overhead_estimate_max':max(overhead_samples),
                       'monotonic_net_saving_over_tested_ladder':all(rows[i]['saving_bytes']<=rows[i+1]['saving_bytes'] for i in range(len(rows)-1))},
            'contract':{'diagnostic_only':True,'release_credit':False,'shipping_builder_changed':False,'no_threshold_selected':True,'central_directory_compressed_size_is_observation_only':True},
            'next_if_stable':'derive a conservative preregistered gate from observable expected duplicate-stream bytes minus measured representation/control cost, then falsify on Office/Analytics and nonidentical-compression controls',
            'next_if_unstable':'do not select a scalar threshold; identify which recipe/control term causes nonmonotonic economics'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-shared-ladder-work'));p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-zip-shared-ladder.json'));a=p.parse_args();r=run(a.work_root);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['summary'],indent=2))
if __name__=='__main__':main()
