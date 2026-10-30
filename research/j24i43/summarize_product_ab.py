#!/usr/bin/env python3
"""J24I43 exact complete-product median accounting; no floating benchmark score."""
import argparse, json, re, statistics
from collections import defaultdict
from pathlib import Path

RE = re.compile(r"^(A|B) J24I43 iter=(\d+) size=(\d+) ns=(\d+) rchar=(\d+) vmhwm_kib=(\d+)$")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    x=ap.parse_args()
    groups=defaultdict(list)
    for line in x.raw.read_text().splitlines():
        m=RE.fullmatch(line.strip())
        if not m: raise ValueError(f"unrecognized product observation: {line!r}")
        lane,it,size,ns,rc,rss=m.groups()
        assert lane in ("A","B") and int(it) in (0,1,2,3) and int(size) in (8,32)
        groups[(lane,int(size))].append({"iteration":int(it),"ns":int(ns),"rchar":int(rc),"vmhwm_kib":int(rss)})
    result={"schema":"j24i43-source-exact-product-ab-v1","unit":"verified complete archive, same physical input",
            "comparison":"A=unmodified #784 native; B=streamed direct-WAV native",
            "warmup":"iteration 0 discarded for wall/rchar median, never for raw count","rows":{}}
    for size in (8,32):
        a=groups[("A",size)]; b=groups[("B",size)]
        assert len(a)==len(b)==16, (size,len(a),len(b))
        assert all(sum(item["iteration"]==k for item in rows)==4 for rows in (a,b) for k in range(4))
        def stats(rows):
            selected=[t for t in rows if t["iteration"]>0]
            return {"raw_count":len(rows),"measured_count":len(selected),
                    "median_wall_ms":statistics.median(t["ns"] for t in selected)/1e6,
                    "median_rchar":statistics.median(t["rchar"] for t in selected),
                    "peak_process_vmhwm_kib":max(t["vmhwm_kib"] for t in rows),
                    "raw_observations":rows}
        sa,sb=stats(a),stats(b)
        result["rows"][str(size)]={
            "old":sa,"new":sb,
            "wall_candidate_to_old":sb["median_wall_ms"]/sa["median_wall_ms"],
            "rchar_candidate_to_old":sb["median_rchar"]/sa["median_rchar"] if sa["median_rchar"] else None,
            "rss_peak_delta_kib":sb["peak_process_vmhwm_kib"]-sa["peak_process_vmhwm_kib"]}
    x.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":"MEASURED_NOT_RELEASE_CREDIT","by_size":{
        k:{"wall_candidate_to_old":v["wall_candidate_to_old"],
           "rchar_candidate_to_old":v["rchar_candidate_to_old"],
           "rss_peak_delta_kib":v["rss_peak_delta_kib"]} for k,v in result["rows"].items()}},sort_keys=True))

if __name__=="__main__": main()
