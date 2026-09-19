from __future__ import annotations

"""Cheap fresh-process discriminator for the v0.30 pack-RSS failure."""
import argparse, json, resource, subprocess, sys


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
    p=subprocess.run([sys.executable,__file__,'--child',engine],check=False,capture_output=True,text=True)
    if p.returncode != 0:
        raise RuntimeError(f'import child {engine} failed rc={p.returncode}: {p.stderr[-4000:]}')
    lines=[x for x in p.stdout.splitlines() if x.strip()]
    if not lines:
        raise RuntimeError(f'import child {engine} emitted no JSON; stderr={p.stderr[-4000:]}')
    return json.loads(lines[-1])


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--child',choices=('v029','v030')); a=p.parse_args()
    if a.child:
        _child(a.child); return
    rows=[]
    for order in (('v029','v030'),('v030','v029')):
        rows.append({e:_run(e) for e in order})
    ratios=[r['v030']['import_peak_rss_kib']/max(1,r['v029']['import_peak_rss_kib']) for r in rows]
    print(json.dumps({'schema':'cmpct-v030-import-rss-diagnostic-v1','release_credit':False,'rows':rows,
                      'ratios':ratios,'max_ratio':max(ratios),'gate_reference':1.25,
                      'decision':'import-footprint-first-order' if min(ratios)>1.25 else 'build-working-set-first-order-or-mixed'},indent=2))

if __name__=='__main__': main()
