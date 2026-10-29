#!/usr/bin/env python3
"""Read-only ABBA/BAAB referee; a scientific status is not a product PASS."""
import argparse,json,re,statistics
from pathlib import Path
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--manifest",type=Path,required=True);ap.add_argument("--raw",type=Path,required=True)
 ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
 manifest=json.loads(a.manifest.read_text());assert manifest["schema"]=="j24i38-builder-wav-flac-v1"
 pattern=re.compile(r"([AB]) J24I38 size=(8|32) iter=(\d+) wall_ns=(\d+) rchar=(\d+) vmhwm_kib=(\d+)")
 data={str(m):{"A":[],"B":[]} for m in (8,32)}
 for line in a.raw.read_text().splitlines():
  match=pattern.fullmatch(line);assert match,line
  lane,size,iteration,wall,rchar,peak=match.groups()
  if int(iteration)>0:data[size][lane].append(
      {"wall_ns":int(wall),"rchar":int(rchar),"vmhwm_kib":int(peak)})
 out={"schema":"j24i38-builder-wav-source-exact-amplification-v1",
      "classification":"research-only; one-shot control has different RSS",
      "base_product_head":manifest["base_sha"],"results":{}}
 for size,group in data.items():
  assert len(group["A"])==len(group["B"])==12,(size,group)
  def median(k,field):return statistics.median(x[field] for x in group[k])
  aw,bw=median("A","wall_ns"),median("B","wall_ns")
  ar,br=median("A","rchar"),median("B","rchar")
  out["results"][size]={"actual_verify_wall_ns":aw,"optimistic_whole_wall_ns":bw,
    "wall_ratio":aw/bw,"actual_verify_rchar":ar,"optimistic_whole_rchar":br,
    "rchar_ratio":ar/br if br else None,
    "actual_vmhwm_kib":median("A","vmhwm_kib"),
    "optimistic_vmhwm_kib":median("B","vmhwm_kib"),
    "samples_each":12,"raw_samples":group}
 ratio=out["results"]["32"]["rchar_ratio"]
 out["decision"]="BUILDER_WAV_MECHANISM_SUPPORTED" if ratio is not None and ratio>1.5 else "BUILDER_WAV_MECHANISM_NOT_SUPPORTED"
 out["no_product_credit"]=True
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"decision":out["decision"],"summaries":{
   k:{a:b for a,b in v.items() if a!="raw_samples"} for k,v in out["results"].items()
 }},sort_keys=True))
if __name__=="__main__":main()
