#!/usr/bin/env python3
"""Replay J24I68's *derived* 96 timing pairs after hosted artifacts expire.

Secondary evidence only. Does not authenticate original ABBA ZIP bytes, source
commits, full sample variances, or any release gate. Use the original provider
referee while its immutable GitHub Actions artifacts remain available.
"""
import argparse
import json
import math
from pathlib import Path
from j24i68_zip_proxy_referee import spearman

HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--derived",type=Path,default=HERE/"j24i68_derived_original_effect_pairs.json")
    args=p.parse_args()
    data=json.loads(args.derived.read_text(encoding="utf-8"))
    if data.get("schema")!="cmpct-j24i68-derived-paired-timing-deltas-v1":
        raise ValueError("not the frozen J24I68 derived timing-pair schema")
    pairs=data.get("derived_pairs")
    if not isinstance(pairs,dict) or len(pairs)!=3 or set(pairs)!=set(data.get("original_provider_zip_sha256",{})):
        raise ValueError("missing or forged original provider keys")
    results={}
    for name,rows in pairs.items():
        if len(rows)!=32 or any(len(row)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in row) for row in rows):
            raise ValueError("expected 32 finite CMPCT/ZIP paired effects per provider")
        selected=[(c,z) for c,z in rows if abs(c)>1 and abs(z)>1]
        same=sum((c>0)==(z>0) for c,z in selected)
        rho=spearman([row[0] for row in rows],[row[1] for row in rows])
        h1=bool(selected) and same/len(selected)>=.75 and rho>=.50
        results[name]={"pairs_above_1ms":len(selected),"same_sign":same,"spearman":rho,"preregistered_H1_survives":h1}
    print(json.dumps({"evidence_class":"DERIVED_SECONDARY_NOT_PRIMARY_PROVIDER","results":results,
                      "universal_ZIP_per_cell_proxy_survives":all(v["preregistered_H1_survives"] for v in results.values())},
                      indent=2,sort_keys=True))

if __name__=="__main__":
    main()
