#!/usr/bin/env python3
"""Exploratory held-out O1a: system binaries/text windows, exact frozen O0 detector.

Preregistered before inspection in docs/v031-research/2026-10-28-a14-heldout-os-prereg.md.
Does not publish source bytes, names, paths, or individual file hashes.
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, pathlib, platform, time, sys

ROOT=pathlib.Path(__file__).resolve().parent
p=ROOT/'a14_derived_crc_o0.py'
spec=importlib.util.spec_from_file_location('a14_frozen',p)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
CATEGORIES=[('ELF',pathlib.Path('/usr/bin'),'*',64),
            ('Python',pathlib.Path('/usr/lib/python3.13'),'*.py',64),
            ('Shared',pathlib.Path('/usr/lib/x86_64-linux-gnu'),'*.so*',64),
            ('JSON',pathlib.Path('/usr/share'),'*.json',32)]

def eligible(path,kind):
    if path.is_symlink() or not path.is_file():return False
    try:size=path.stat().st_size
    except OSError:return False
    if not 8192<=size<=2*1024*1024:return False
    if kind=='ELF':
        try:
            with path.open('rb') as f:return f.read(4)==b'\x7fELF'
        except OSError:return False
    return True

def select(root,pattern,kind,n):
    return [x for x in sorted(root.rglob(pattern),key=lambda p:p.as_posix()) if eligible(x,kind)][:n]

def windows(data):
    end=len(data)-4096
    mid=max(0,min(end,((len(data)//2-2048)//4096)*4096))
    return [('start',data[:4096]),('mid',data[mid:mid+4096]),('end',data[end:])]

def main():
    t=time.perf_counter_ns();manifest=hashlib.sha256();out=[];totals={'files':0,'windows':0,'crc_checks':0,'candidate_geometries':0,'admissions':0};found=[]
    for kind,root,pattern,limit in CATEGORIES:
        row={'category':kind,'files':0,'windows':0,'candidates_considered':0,'crc_checks':0,'admissions':0}
        for path in select(root,pattern,kind,limit):
            data=path.read_bytes()
            manifest.update(path.as_posix().encode('utf8')+b'\0'+len(data).to_bytes(8,'little')+hashlib.sha256(data).digest())
            row['files']+=1;totals['files']+=1
            for where,win in windows(data):
                assert len(win)==4096
                hit,stats=engine.discover(win)
                row['windows']+=1;totals['windows']+=1
                row['candidates_considered']+=stats['candidates_considered'];totals['candidate_geometries']+=stats['candidates_considered']
                row['crc_checks']+=stats['crc_checks'];totals['crc_checks']+=stats['crc_checks']
                if hit:
                    art=engine.pack(win,hit)
                    if engine.unpack(art)!=win:raise AssertionError('detector false admission / roundtrip '+kind)
                    row['admissions']+=1;totals['admissions']+=1
                    found.append({'category':kind,'position':where,'width':hit[0],'offset':hit[1],'endian':hit[2],
                                  'original_sha256':hashlib.sha256(win).hexdigest()})
        out.append(row)
    receipt={'schema':'cmpct-a14-heldout-os-o1a-v1','status':'EXPLORATORY_NOT_PRODUCT','os':platform.platform(),
             'python':sys.version.split()[0], 'instrument_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
             'manifest_sha256':manifest.hexdigest(),'total':totals,'by_category':out,'true_positive_if_any':found,
             'elapsed_ms':(time.perf_counter_ns()-t)/1e6,
             'limitations':'Nonrepresentative host binaries/text; 4KiB windows may break record alignment; zero positives cannot prove universality; no original names/bytes exported'}
    target=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'a14_heldout_os_court_result.json'
    target.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'total':totals,'by_category':out,'manifest_sha256':manifest.hexdigest()},indent=2))

if __name__=='__main__':main()
