#!/usr/bin/env python3
"""Independent J24F08 receipt validator; does not import or invoke the target court."""
import argparse
import json
import statistics
from pathlib import Path

ORIGINAL="8b5910725260e7b4db155ee0b393eb48a42f7efa"
WINDOW="41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e"
PREREG="202a13484ee567e3cb6cac97d776bbd08e7f3535"
AMEND="edc2cbc19dcf13659d2a275db2e7736ac693e936"
SEQUENCE=["whole","window","window","whole"]*2
METRICS=("peak_vmhwm_bytes","incremental_vmhwm_bytes","wall_ns","cpu_ns","ru_maxrss_reported_kib")

def validate(path):
    x=json.loads(Path(path).read_text())
    count=0
    def check(test,why):
        nonlocal count
        count+=1
        if not test:raise AssertionError(f"independent receipt check {count}: {why}")
    check(x["prereg_sha"]==PREREG,"original prospective prereg")
    check(x["vmhwm_correction_prereg"]==AMEND,"subsequent explicit meter correction")
    check(x["source_whole"]==ORIGINAL and x["source_window"]==WINDOW,"Reader identity")
    check(len(x["cases"])==4,"complete four cases")
    control=x["positive_control"]
    check(control["growth_bytes"]>=16*1024*1024,"fresh-process positive counter")
    check(control["after"]["VmHWM"]-control["before"]["VmHWM"]==control["growth_bytes"],"positive counter recomputation")
    summary=[]
    seen=set()
    for c in x["cases"]:
        size=c["size_mib"];mode=c["storage_kind"]
        check((size,mode) in {(16,1),(16,5),(64,1),(64,5)},"physical case")
        check(c["logical_bytes"]==size*1024*1024+1024,"logical length")
        check(c["physical_archive_bytes"]>=c["logical_bytes"],"physical archive record overhead")
        check(len(c["trials"])==8,"two ABBA cycles")
        check([t["arm"] for t in c["trials"]]==SEQUENCE,"original alternating order")
        check(len({t["pid"] for t in c["trials"]})==8,"fresh PIDs per case")
        for t in c["trials"]:
            check(t["pid"] not in seen,"no child reused anywhere")
            seen.add(t["pid"])
            check(t["source_blob"]==(ORIGINAL if t["arm"]=="whole" else WINDOW),"exact original Reader arm")
            check(t["head"]==x["head"],"experiment HEAD")
            check(t["archive_sha256"]==c["archive_sha256"],"same archive SHA")
            check(t["logical_sha256"]==c["logical_sha256"]==t["output_sha256"],"exact logical bytes")
            check(t["output_bytes"]==c["logical_bytes"],"output length")
            check(t["storage_kind"]==mode and t["size_mib"]==size,"mode size attribution")
            check(t["wall_ns"]>0 and t["cpu_ns"]>0,"actual cost measurement")
            sample=[t[k] for k in ("kernel_before","kernel_after_open","kernel_after_extract","kernel_after_close")]
            for item in sample:
                check(item["VmHWM"]>=item["VmRSS"]>0,"same-snapshot kernel counters")
            peaks=[m["VmHWM"] for m in sample]
            backward=max((a-b for a,b in zip(peaks,peaks[1:]) if b<a),default=0)
            check(t["peak_vmhwm_bytes"]==max(peaks),"maximum sampled kernel highwater")
            check(t["end_vmhwm_bytes"]==peaks[-1],"true raw final counter")
            check(t["sampled_vmhwm_max_backstep_bytes"]==backward,"record all nonmonotone observations")
            check(t["incremental_vmhwm_bytes"]==max(peaks)-peaks[0],"incremental VmHWM")
            check(t["ru_vs_kernel_bytes"]==t["ru_maxrss_reported_kib"]*1024-max(peaks),"legacy diagnostic")
        for metric in METRICS:
            a=statistics.median(t[metric] for t in c["trials"] if t["arm"]=="whole")
            b=statistics.median(t[metric] for t in c["trials"] if t["arm"]=="window")
            observed=c["medians"][metric]
            check(observed["whole"]==a and observed["window"]==b,"recomputed "+metric+" medians")
            check(observed["delta"]==b-a,"recomputed "+metric+" absolute delta")
            check(abs(observed["ratio"]-b/a)<1e-10 if a else observed["ratio"] is None,"recomputed "+metric+" ratio")
        gap=-c["medians"]["peak_vmhwm_bytes"]["delta"]
        classification=("VMHWM_MEMORY_WIN" if size==64 and gap>=32*1024*1024 else
                        "NO_CONFIRMED_MEMORY_WIN" if size==64 else "SMALL_CASE_REPORTED")
        check(c["classification"]==classification,"precommitted scientific discriminator")
        summary.append(dict(size_mib=size,storage_kind=mode,gap_bytes=gap,decision=classification,
                            nonmonotone_samples=sum(t["sampled_vmhwm_max_backstep_bytes"]>0 for t in c["trials"])))
    expected=("VMHWM_MEMORY_WIN_BOTH_R24_MODES" if
              all(v["decision"]=="VMHWM_MEMORY_WIN" for v in summary if v["size_mib"]==64) else
              "NO_CONFIRMED_BOTH_MODE_MEMORY_WIN")
    check(x["decision"]==expected,"decision independently recomputed")
    check(len(seen)==32,"all 32 subprocess identities unique")
    return dict(checks=count,decision=expected,head=x["head"],results=summary)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--output",default="j24f08-evidence/independent-audit.json")
    a=p.parse_args()
    result=validate(a.source)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("J24F08_INDEPENDENT_RECEIPT_AUDIT=PASS",json.dumps(result,sort_keys=True))

if __name__=="__main__":main()
