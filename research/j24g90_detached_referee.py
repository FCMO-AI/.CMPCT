#!/usr/bin/env python3
"""Detached no-CMPCT J24G90 physical and timing referee; requires msgpack/zstandard only."""
from __future__ import annotations
import copy, hashlib, json, statistics, struct, sys
from pathlib import Path
import msgpack
import zstandard as zstd

FTR=struct.Struct("<8sBBBBQQQ32s")
MAGIC=b"CMPTF24\0"


def h(data):
    return hashlib.sha256(data).hexdigest()


def load_footer(data, off):
    if off<0 or off+FTR.size>len(data):
        raise AssertionError("footer out of bounds")
    magic,kind,codec,flags,reserved,cs,us,previous,digest=FTR.unpack_from(data,off)
    assert magic==MAGIC and kind in (0,1) and codec in (0,1)
    assert flags==reserved==0 and us>0 and cs>0 and previous<off
    assert cs<=off and (previous==0 or previous+FTR.size<=off-cs)
    encoded=data[off-cs:off]
    raw=(zstd.ZstdDecompressor().decompress(encoded,max_output_size=us)
         if codec==1 else encoded)
    assert len(raw)==us and hashlib.sha256(raw).digest()==digest
    payload=msgpack.unpackb(raw,raw=False)
    return {"offset":off,"kind":kind,"prev":previous,
            "sha256":h(raw),"payload":payload}


def chain(data, tail):
    seen=set()
    ans=[]
    off=tail
    while True:
        assert off not in seen and len(seen)<70
        seen.add(off)
        e=load_footer(data,off)
        ans.append(e)
        if not e["prev"]:
            break
        off=e["prev"]
    return list(reversed(ans))


def rebuild(entries):
    assert len(entries)==64 and entries[0]["kind"]==0
    index=copy.deepcopy(entries[0]["payload"])
    assert "files" in index and "blobs" in index
    removed=[]
    for e in entries[1:]:
        assert e["kind"]==1
        payload=e["payload"]
        assert payload["blobs"]==[] and len(payload["ops"])==1
        op=payload["ops"][0]
        assert op[0]=="del" and len(op)==2
        prior=len(index["files"])
        index["files"]=[row for row in index["files"] if row[0]!=op[1]]
        assert len(index["files"])==prior-1
        removed.append(op[1])
        index["files"].sort(key=lambda row:row[0])
    assert len(set(removed))==63
    return index, removed


def audit_case(n,folder,reported):
    raw={label:(folder/f"{n}-{label}.cmpct").read_bytes() for label in "ABC"}
    for label in "ABC":
        assert len(raw[label])==reported["physical"][label]["size"]
        assert h(raw[label])==reported["physical"][label]["sha256"]
    assert raw["B"].startswith(raw["A"])
    assert raw["C"][:-1]==raw["B"][:-1] and raw["C"][-1]!=raw["B"][-1]
    assert len(raw["B"])==len(raw["C"])>len(raw["A"])
    a_tail=len(raw["A"])-FTR.size
    original_chain=chain(raw["A"],a_tail)
    assert original_chain[-1]["offset"]==reported["previous_footer"]
    assert original_chain[-1]["kind"]==1
    actual,deleted=rebuild(original_chain)
    final=load_footer(raw["B"],len(raw["B"])-FTR.size)
    assert final["kind"]==0 and final["prev"]==a_tail
    assert final["payload"]==actual
    assert len(chain(raw["B"],len(raw["B"])-FTR.size))==65
    # The latest footer cannot authenticate once its digest is damaged;
    # authenticated earlier chain is still intact in C.
    try:
        load_footer(raw["C"],len(raw["C"])-FTR.size)
    except (AssertionError,ValueError,zstd.ZstdError):
        invalid_final=True
    else:
        invalid_final=False
    assert invalid_final
    assert raw["C"][:len(raw["A"])]==raw["A"]
    assert rebuild(chain(raw["C"],a_tail))[0]==actual
    wire_fingerprint=h(msgpack.packb(actual,use_bin_type=True))
    assert wire_fingerprint==reported["index_sha256"]
    assert len(actual["files"])==n-63
    for label in "ABC":
        s=reported["semantics"][label]
        assert s["index_sha256"]==wire_fingerprint
        assert s["verified_files"]==n-63
        assert s["delta_depth"]==(0 if label=="B" else 63)
    sampling=reported["timing"]["samples"]
    assert len(sampling)==36
    med={}
    for clock in ("wall_ns","cpu_ns"):
        med[clock]={label:statistics.median(
            item[clock] for item in sampling if item["variant"]==label)
            for label in "ABC"}
        for label in "ABC":
            assert abs(med[clock][label]-reported["timing"]["medians"][clock][label])<1e-6
    assert all(sum(item["variant"]==label for item in sampling)==12 for label in "ABC")
    for row in sampling:
        assert row["depth"]==(0 if row["variant"]=="B" else 63)
        assert row["wall_ns"]>0 and row["cpu_ns"]>0
    s=med["wall_ns"]["A"]/med["wall_ns"]["B"]
    c=med["cpu_ns"]["A"]/med["cpu_ns"]["B"]
    assert abs(s-reported["timing"]["A_over_B_wall_speedup"])<1e-9
    assert abs(c-reported["timing"]["A_over_B_cpu_speedup"])<1e-9
    assert reported["checkpoint_extra_bytes"]==len(raw["B"])-len(raw["A"])
    assert reported["checkpoint_overhead_ratio"]==(len(raw["B"])-len(raw["A"]))/len(raw["A"])
    # An independent adversarial control must fail under the referee itself.
    altered=bytearray(raw["A"])
    altered[a_tail+FTR.size-1]^=0x3A
    try:
        load_footer(bytes(altered),a_tail)
    except (AssertionError,ValueError,zstd.ZstdError):
        refused=True
    else:
        refused=False
    assert refused
    return {"n":n,"prior_signed_footers":64,"new_signed_footers":65,
            "verified_deletes":len(deleted),"same_index_sha256":wire_fingerprint,
            "A_bytes":len(raw["A"]),"B_bytes":len(raw["B"]),
            "checkpoint_extra_bytes":len(raw["B"])-len(raw["A"]),
            "all_three_parity":True,"bad_footer_refused":True,
            "additional_tamper_refused":True,
            "median_wall_ns":med["wall_ns"],"median_cpu_ns":med["cpu_ns"],
            "actual_reader_A_over_B_wall":s,"actual_reader_A_over_B_cpu":c}


def main():
    folder=Path(sys.argv[1])
    reported=json.loads((folder/"receipt.json").read_text())
    assert reported["status"]=="PASS" and reported["product_credit"]==0
    results={str(n):audit_case(n,folder,reported["cases"][str(n)]) for n in (4096,8192)}
    H1=all(x["actual_reader_A_over_B_wall"]>=2.0 and
           x["actual_reader_A_over_B_cpu"]>=1.0 for x in results.values())
    assert H1==reported["H1_survives"]
    assert reported["H2_survives"]
    outcome={"schema":"cmpct-j24g90-detached-referee-v1",
             "result":"PASS","H1_survives":H1,"H2_survives":True,
             "source_head":reported["source"]["head"],
             "cases":results,"product_credit":0}
    (folder/"detached-audit.json").write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n")
    print("J24G90_DETACHED",json.dumps({
        "result":"PASS","H1":H1,
        "N4096_wall":results["4096"]["actual_reader_A_over_B_wall"],
        "N8192_wall":results["8192"]["actual_reader_A_over_B_wall"]}))
if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: audit.py <evidence-directory>")
    main()
