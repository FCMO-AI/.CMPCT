from __future__ import annotations

"""Cheap fresh-process discriminator for the v0.30 pack-RSS failure.

This is diagnostic evidence only. It asks whether the release-product RSS debt already exists immediately after
import, before any corpus/build working set exists. If import-only v0.30 is already above 1.25x v0.29, module/profile
footprint is a first-order owner; otherwise the build working set owns the debt and import refactors are a dead end.
"""
import argparse
import json
import resource
import subprocess
import sys


def _child(engine: str) -> None:
    if engine == 'v029':
        from experiments import entropygraph_v029_release as mod
    elif engine == 'v030':
        from experiments import entropygraph_v030_release_product as mod
    else:
        raise ValueError(engine)
    print(json.dumps({'engine':engine,'module':mod.__name__,
                      'import_peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)},separators=(',',':')))


def _run(engine: str) -> dict:
    p=subprocess.run([sys.executable,__file__,'--child',engine],check=True,capture_output=True,text=True)
    return json.loads(p.stdout.strip().splitlines()[-1])


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--child',choices=('v029','v030')); a=p.parse_args()
    if a.child:
        _child(a.child); return
    # Alternate order twice to expose host/order drift without conflating process allocator state.
    rows=[]
    for order in (('v029','v030'),('v030','v029')):
        rows.append({e:_run(e) for e in order})
    ratios=[r['v030']['import_peak_rss_kib']/max(1,r['v029']['import_peak_rss_kib']) for r in rows]
    print(json.dumps({'schema':'cmpct-v030-import-rss-diagnostic-v1','release_credit':False,'rows':rows,
                      'ratios':ratios,'max_ratio':max(ratios),'gate_reference':1.25,
                      'decision':'import-footprint-first-order' if min(ratios)>1.25 else 'build-working-set-first-order-or-mixed'},indent=2))

if __name__=='__main__': main()
