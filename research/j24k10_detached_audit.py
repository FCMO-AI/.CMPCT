"""Post-result detached GitHub artifact verifier for J24K10.

Stdlib only, never imports CMPCT or the frozen first-party evaluator.
This is *not* a rewrite of the prospective scientific court.
Use: python research/j24k10_detached_audit.py --ubuntu ubuntu.zip
     --macos macos.zip --windows windows.zip --out audit.json
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import struct
import zipfile

HEAD = "58f630c8a3306bdb7836db034b6d3d33e61d4f67"
BLOBS = {
 "src/cmpct/reader.py":"e77578505985dd264d69425e3bc816c421ae3cdc",
 "src/cmpct/codec.py":"fe692c4595c1303dbc89b7d660501e4ef0f223c3",
 "research/j24k09_physical_witness_economics.py":"e3ad370ff8253fff999f003637e30cde53a5ce52",
}
HOSTS = ("ubuntu","macos","windows")
CELLS = {(n,p,q) for n in (512,4096) for p in (0,64*1024*1024)
         for q in (1,8,64)}
MODES = ("per_query_physical","copy_then_prove_once")
FIELDS = ("wall_ns","cpu_ns","copy_wall_ns","copied_bytes","extra_cache_bytes")

def expected_source_sha(n,pad):
    h = hashlib.sha256()
    hdr = struct.pack("<4sBBHQQII32s",b"CMA4",0,0,0,64,64,0,0,bytes(32))
    for i in range(n+1):
        h.update(hdr);h.update(bytes([i%251])*64)
    for _ in range(pad//(1024*1024)):
        h.update(b"Z"*1024*1024)
    return h.hexdigest()

def verify_zip(host,path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, "artifact ZIP CRC"
        assert set(z.namelist()) == {
            "raw-observations.jsonl","independent-referee.json",
            "source-head.txt","source-blobs.txt"}
        assert z.read("source-head.txt").decode().strip() == HEAD
        blobtext=z.read("source-blobs.txt").decode()
        for name,sha in BLOBS.items():
            assert name in blobtext and sha in blobtext, name
        raw=z.read("raw-observations.jsonl")
        rows=[json.loads(line.split("J24K10_RESULT=",1)[1])
              for line in raw.decode().splitlines()
              if line.startswith("J24K10_RESULT=")]
        original=json.loads(z.read("independent-referee.json"))
    assert original["oracle_receipt_sha256"] == hashlib.sha256(raw).hexdigest()
    assert original["raw_observations"] == 240
    assert original["adversarial_receipts_rejected"] == 5
    assert len(rows)==12
    seen=set()
    measured={}
    for row in rows:
        n,p,q = row["streams"],row["padding_bytes"],row["queries"]
        key=(n,p,q)
        assert key in CELLS and key not in seen
        seen.add(key)
        assert row["source_sha256"] == expected_source_sha(n,p)
        assert row["source_bytes"] == (n+1)*128+p
        assert row["extra_mapped_archive_bytes"] == row["source_bytes"]
        assert row["source_format_not_full_r24"]
        assert row["copy_not_immutable_against_its_owner"]
        assert row["disk_copy_not_atomic_during_source_mutation"]
        assert set(row["raw"]) == set(MODES)
        for mode in MODES:
            samples=row["raw"][mode]
            assert len(samples)==10
            for s in samples:
                assert set(s)==set(FIELDS)
                assert all(type(s[field]) is int and s[field]>=0 for field in FIELDS)
                if mode=="copy_then_prove_once":
                    assert s["copied_bytes"]==row["source_bytes"]
                    assert s["extra_cache_bytes"]>0
                    assert s["copy_wall_ns"]<=s["wall_ns"]
                else:
                    assert not any(s[f] for f in ("copy_wall_ns","copied_bytes","extra_cache_bytes"))
            for field in FIELDS:
                recomputed=statistics.median(s[field] for s in samples)
                assert recomputed==row["medians"][mode][field]
        ratio=(row["medians"][MODES[0]]["wall_ns"]/
               max(1,row["medians"][MODES[1]]["wall_ns"]))
        assert abs(ratio-row["speed_ratio_physical_over_copied"])<1e-10
        match=[r for r in original["audited"]
               if (r["streams"],r["padding_bytes"],r["queries"])==key]
        assert len(match)==1 and abs(match[0]["ratio"]-ratio)<1e-10
        measured[f"{n}/{p}/{q}"]={
            "speed_ratio":ratio,
            "baseline_wall_ms":row["medians"][MODES[0]]["wall_ns"]/1e6,
            "copied_wall_ms":row["medians"][MODES[1]]["wall_ns"]/1e6,
            "source_bytes":row["source_bytes"],
            "extra_cache_bytes":row["medians"][MODES[1]]["extra_cache_bytes"]}
    assert seen==CELLS
    return {"host":host,"artifact_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "raw_sha256":hashlib.sha256(raw).hexdigest(),"cells":measured}

def main():
    ap=argparse.ArgumentParser()
    for host in HOSTS:ap.add_argument("--"+host,required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    audits={host:verify_zip(host,getattr(args,host)) for host in HOSTS}
    for key in next(iter(audits.values()))["cells"]:
        assert all(key in audits[h]["cells"] for h in HOSTS)
    result={
        "schema":"j24k10-detached-threehost-artifact-audit-v1",
        "science_head":HEAD,"scientific_tier":"component_only_not_product",
        "original_run_id":40648529165,"cells":36,"raw_observations":720,
        "original_referee_forged_receipts_rejected":15,"hosts":audits,
        "decision":"size-and-query-dependent crossover; no immutable-source safety proof"}
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("J24K10_DETACHED_THREEHOST_PASS 36 cells 720 observations 3 hosts")
if __name__=="__main__":main()
