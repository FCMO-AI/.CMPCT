#!/usr/bin/env python3
"""O228d: reverse native-first / fallback-second, exact genuine archive hashes."""
import argparse,hashlib,json,tempfile,sys
from pathlib import Path
import cmpct.codec as codec
from o228b_builder_transfer_court import profile

EXPECTED={
 "one-period":{"native":"318c46031e40e15efdf7d1e6d2dadfb6adb114d8f33a4a867ebad3ff39c32176","fallback":"b012bbd91aac855220de3f660c2e8db1f5c84a0d86d138d4eb122baf906c2ff0"},
 "shifted":{"native":"31d9fe554419ac69e544448fabd597f4e4faf61efeac4358bea8434c6f5bf03a","fallback":"3b0199feee2e84f7298a45ddb9d6873fc1fde680645d063b08085117b0cf01aa"},
}
def run(output):
 helper=codec._cdc
 if helper is None:raise RuntimeError("native helper missing")
 rows=[]
 for name in EXPECTED:
  case={"name":name}
  # Native-first, unlike O228c's fixed-first; different temporary tree per arm.
  for mode in ("native","fallback"):
   codec._cdc=helper if mode=="native" else None
   with tempfile.TemporaryDirectory(prefix="o228d-"+name+"-"+mode+"-") as d:
    obs=profile(name,Path(d))
   case[mode]={
    "archive_sha256":obs["archive_sha256"],"archive_bytes":obs["archive_bytes"],
    "logical_sha256":obs["logical_sha256"],"builder_sha":obs["builder_sha"],
    "reader_sha":obs["reader_sha"],"ref_semantic_sha256":obs["ref_semantic_sha256"],
    "refs":obs["cdc_ref_count"],"owners":obs["distinct_owners"],
    "verified":obs["file_integrity_pass"],"native_helper_loaded":codec._cdc is not None,
    "matches_original":obs["archive_sha256"]==EXPECTED[name][mode]}
  assert case["native"]["logical_sha256"]==case["fallback"]["logical_sha256"]
  rows.append(case)
 codec._cdc=helper
 pass_all=all(c[mode]["matches_original"] and c[mode]["verified"]
              for c in rows for mode in ("native","fallback"))
 verdict="REPLICATED_ORDER_INDEPENDENCE" if pass_all else "ORDER_INDEPENDENCE_NOT_PROVEN"
 result={"schema":"cmpct-o228d-reverse-mode-order-v1","status":"RESEARCH_ONLY_NO_PRODUCT_CREDIT",
         "original_o228c_run":40534143700,"expected_original_archive_sha":EXPECTED,
         "mode_order":["native","fallback"],
         "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "native_source_sha256":hashlib.sha256(Path("native/cmpct_cdc.c").read_bytes()).hexdigest(),
         "rows":rows,"decision":verdict}
 Path(output).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print(json.dumps({"decision":verdict,"profiles":len(rows),"exact_matches":sum(c[m]["matches_original"] for c in rows for m in ("native","fallback"))}))
 if not pass_all:raise RuntimeError("Order-independence exact original archive hash mismatch")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",required=True);run(p.parse_args().output)
