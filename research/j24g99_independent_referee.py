#!/usr/bin/env python3
"""J24G99 independent audit of authentic footer boundaries, copy charge and receipts.
No CMPCT import; producer module is never imported.
"""
import argparse,copy,hashlib,io,json,pathlib,statistics,struct,zipfile
F=struct.Struct("<8sBBBBQQQ32s")
SOURCES={
"small-ubuntu":("d4d96daf8e831bb923e0c2c2a4b52c6bef4d7ad4616aadea220f18c7b5fe594d","f29561c5e2d36a8f47aa35f61191911c0611be6b",("16-normal.cmpct","128-normal.cmpct")),
"small-windows":("f7fdc90fdc0d5ca67f3c520bc0d033dece602a2aa3d5ab6320ccb024f890186e","f29561c5e2d36a8f47aa35f61191911c0611be6b",("16-normal.cmpct","128-normal.cmpct")),
"deep-ubuntu":("19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b","129edec976efe8bb604584517de39553487fec34",("4096-A.cmpct","8192-A.cmpct")),
"deep-windows":("c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab","129edec976efe8bb604584517de39553487fec34",("4096-A.cmpct","8192-A.cmpct"))}
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(x,message):
    if not x:raise AssertionError(message)
def footer_ends(raw):
    ends=[];pos=len(raw)-F.size;seen=set()
    while pos:
        ok(0<pos<len(raw) and pos not in seen and len(seen)<128,"footer cycle")
        seen.add(pos)
        magic,kind,codec,flags,res,clen,ulen,prev,h=F.unpack_from(raw,pos)
        ok(magic==b"CMPTF24\0" and kind==(0 if prev==0 else 1),"footer")
        ok(0<clen<=pos and 0<ulen<=32*1024*1024 and 0<=prev<pos,"footer bounds")
        ends.append(pos+F.size);pos=prev
    ends.reverse();ok(len(ends) in (4,64) and ends[-1]==len(raw),"footer depth")
    return ends
def verify(zips,r):
    ok(r["schema"]=="j24g99-rolling-tailpack-O0-v1" and len(r["cases"])==8,"result schema/count")
    for key,(zsha,head,filenames) in SOURCES.items():
        original=zips[key].read_bytes();ok(sha(original)==zsha,"source ZIP SHA")
        with zipfile.ZipFile(io.BytesIO(original)) as archive:
            ok(archive.read("checkout-head.txt").decode().strip()==head,"source HEAD")
            for filename in filenames:
                raw=archive.read(filename)
                v=r["cases"][key+"/"+filename]
                ends=footer_ends(raw);base=ends[0]
                tails=[end-base for end in ends[1:]]
                ok(v["sha256"]==sha(raw) and v["archive_bytes"]==len(raw),"raw archive identity")
                ok(v["footers"]==len(ends) and v["footer_ends"]==ends and v["root_bytes"]==base,"footer geometry")
                ok(v["last_append_bytes"]==ends[-1]-ends[-2],"last append")
                ok(v["total_append_bytes"]==len(raw)-base,"direct append")
                ok(v["tail_copy_bytes_cumulative"]==sum(tails),"cumulative rewrite bytes")
                ok(v["full_archive_copy_bytes_cumulative"]==sum(ends[1:]),"full copy control")
                ok(abs(v["tail_copy_vs_direct"]-sum(tails)/(len(raw)-base))<1e-9,"copy/direct ratio")
                ok(abs(v["tail_copy_vs_full"]-sum(tails)/sum(ends[1:]))<1e-9,"copy/full ratio")
                ok(len(v["timeline"])==len(tails),"timeline length")
                for i, (size,event) in enumerate(zip(tails,v["timeline"]),1):
                    ok(event=={"generation":i,"end":ends[i],"tail_bytes":size},"timeline entry")
                ok(v["mutation_rejected_on_reverify"],"corruption reverify")
                allocation=(v["base_allocated"]+v["latest_tail_allocated"]+v["head_allocated"])/v["contiguous_allocated"]
                ok(abs(v["active_allocation_ratio"]-allocation)<1e-9,"physical allocation")
                blocks=(v["new_tail_allocated_cumulative"]+v["new_head_allocated_cumulative"])/v["total_append_bytes"]
                ok(abs(v["cumulative_allocated_vs_direct"]-blocks)<1e-9,"block write debt")
                ok(v["fsync_file_count"]==1+2*(len(ends)-1)
                   and v["fsync_directory_count"]==len(ends)-1,"synchronization count")
                t=v["read"]["raw_ms_per_read"]
                ok(all(len(t[x])==15 for x in ("contiguous","tailpack")),"repetition count")
                for label in ("contiguous","tailpack"):
                    ok(abs(statistics.median(t[label])-v["read"]["medians_ms_per_read"][label])<1e-9,"raw median")
                ratio=v["read"]["medians_ms_per_read"]["tailpack"]/v["read"]["medians_ms_per_read"]["contiguous"]
                ok(abs(v["read"]["ratio"]-ratio)<1e-8,"reader ratio")
                passed=(allocation<=1.05 and sum(tails)<=40*(len(raw)-base)
                        and sum(tails)<=0.10*sum(ends[1:]) and ratio<=2.0)
                ok(v["local_filter_pass"]==passed,"preregistered admission")
    deep=[v for v in r["cases"].values() if v["footers"]==64]
    expect=("O0_ROLLING_TAILPACK_LOCAL_SCREEN_PASS" if all(v["local_filter_pass"] for v in deep)
            else "ROLLING_TAILPACK_SCREEN_FAIL")
    ok(r["decision"]==expect,"verdict")
    return expect
def main():
    p=argparse.ArgumentParser()
    for name in SOURCES:p.add_argument("--"+name,required=True,type=pathlib.Path)
    p.add_argument("--result",required=True,type=pathlib.Path)
    a=p.parse_args();zips={n:getattr(a,n.replace("-","_")) for n in SOURCES}
    result=json.loads(a.result.read_text());decision=verify(zips,result)
    rejected=0
    for fault in ("sha","count","end","copy","allocation","fsync","median","corrupt","verdict"):
        mutant=copy.deepcopy(result);x=next(iter(mutant["cases"].values()))
        if fault=="sha":x["sha256"]="0"*64
        if fault=="count":x["footers"]+=1
        if fault=="end":x["footer_ends"][0]+=1
        if fault=="copy":x["tail_copy_bytes_cumulative"]+=1
        if fault=="allocation":x["active_allocation_ratio"]=0.5
        if fault=="fsync":x["fsync_file_count"]+=1
        if fault=="median":x["read"]["ratio"]=0.5
        if fault=="corrupt":x["mutation_rejected_on_reverify"]=False
        if fault=="verdict":mutant["decision"]="ROLLING_TAILPACK_SCREEN_FAIL"
        try:verify(zips,mutant)
        except AssertionError:rejected+=1
    ok(rejected==9,"forged receipt escaped independent referee")
    print(json.dumps({"cases":8,"decision":decision,"forgeries_rejected":rejected},sort_keys=True))
if __name__=="__main__":main()
