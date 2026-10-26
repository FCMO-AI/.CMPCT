#!/usr/bin/env python3
"""O198 preregistered zlib-6 physical-compression proxy (PR #516 issuecomment-6422392213).
Authentic native C is compiled by O197's source-verifying importer. Research, not product.
"""
from __future__ import annotations
import hashlib, json, os, platform, statistics, sys, tempfile, time, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from o197_native_cdc_mutation_court import authenticate_and_compile, chunks, SOURCE_BLOB

SIZE=3*1024*1024
SEEDS=(451,452)
POSITIONS=(1,SIZE//3,2*SIZE//3)
MODES=("fixed256","fixed512","fixed1024","native")
FAMILIES=("entropy","repeat","mixed")
MUTATIONS=("overwrite","shift")
RECORD=64
REFERENCE=32

def corpus(family,seed):
    def h(label,n):
        return hashlib.shake_256(f"O198-{seed}-{label}".encode()).digest(n)
    if family=="entropy":
        return h("entropy",SIZE)
    if family=="repeat":
        motif=h("repeat-motif",32)
        block=(motif+b"\x00"*32+b'{"key":"value","count":12345}'+b"\n")*400
        return (block*(SIZE//len(block)+1))[:SIZE]
    if family=="mixed":
        motif=h("mixed-motif",256)
        pieces=[]
        for i in range(SIZE//(64*1024)):
            if i%3==0: pieces.append(h(f"mixed-noise-{i}",64*1024))
            elif i%3==1: pieces.append(motif*256)
            else: pieces.append(h(f"mixed-atom-{i}",4096)*16)
        return b"".join(pieces)
    raise ValueError(family)

def mutant(base,pos,kind):
    if kind=="overwrite":
        buf=bytearray(base);buf[pos]^=0x5a;return bytes(buf)
    if kind=="shift":
        return base[:pos]+b"Q"+base[pos:-1]
    raise ValueError(kind)

def measure(base,other,mode,lib):
    t0=time.perf_counter_ns();c0=time.process_time_ns()
    a,b=chunks(base,mode,lib),chunks(other,mode,lib)
    split_wall=(time.perf_counter_ns()-t0)/1e6
    split_cpu=(time.process_time_ns()-c0)/1e6
    if b"".join(a)!=base or b"".join(b)!=other:
        raise AssertionError("Lossless cut reassembly failed")
    unique={}; refs=[]
    for part in a+b:
        digest=hashlib.sha256(part).hexdigest()
        previous=unique.setdefault(digest,part)
        if previous!=part: raise AssertionError("SHA-256 collision")
        refs.append(digest)
    t1=time.perf_counter_ns();c1=time.process_time_ns()
    compressed={key:zlib.compress(part,6) for key,part in unique.items()}
    zip_wall=(time.perf_counter_ns()-t1)/1e6
    zip_cpu=(time.process_time_ns()-c1)/1e6
    if any(zlib.decompress(compressed[key])!=part for key,part in unique.items()):
        raise AssertionError("Physical chunk inflate mismatch")
    n=len(a)
    if b"".join(zlib.decompress(compressed[s]) for s in refs[:n])!=base:
        raise AssertionError("Indexed base reassembly mismatch")
    if b"".join(zlib.decompress(compressed[s]) for s in refs[n:])!=other:
        raise AssertionError("Indexed sibling reassembly mismatch")
    payload=sum(len(x) for x in compressed.values())
    return {
        "compressed_unique_payload_bytes":payload,
        "unique_chunks":len(unique),"logical_chunk_references":len(refs),
        "charged_storage_proxy_bytes":payload+RECORD*len(unique)+REFERENCE*len(refs),
        "charged_refs16_bytes":payload+RECORD*len(unique)+16*len(refs),
        "charged_refs64_bytes":payload+RECORD*len(unique)+64*len(refs),
        "largest_decode_chunk_bytes":max(len(x) for x in unique.values()),
        "single_pass_split_wall_ms":round(split_wall,3),"single_pass_split_cpu_ms":round(split_cpu,3),
        "single_pass_compress_wall_ms":round(zip_wall,3),"single_pass_compress_cpu_ms":round(zip_cpu,3),
        "exact_reassembly":True,
    }

def main():
    t=time.time();out=ROOT/"o198-evidence";out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="o198-native-") as temp:
        lib,compiler=authenticate_and_compile(ROOT,Path(temp)/"cdc.so")
        entries=[]
        for family in FAMILIES:
            for seed in SEEDS:
                base=corpus(family,seed)
                assert len(base)==SIZE
                for pos in POSITIONS:
                    for kind in MUTATIONS:
                        other=mutant(base,pos,kind)
                        assert len(other)==SIZE
                        metrics={mode:measure(base,other,mode,lib) for mode in MODES}
                        solid=zlib.compress(base+other,6)
                        if zlib.decompress(solid)!=base+other:
                            raise AssertionError("Non-equivalent solid control mismatch")
                        best=min(MODES[:-1],key=lambda m:metrics[m]["charged_storage_proxy_bytes"])
                        fixed=metrics[best]["charged_storage_proxy_bytes"]
                        native=metrics["native"]["charged_storage_proxy_bytes"]
                        entries.append({
                            "family":family,"seed":seed,"position":pos,"mutation":kind,
                            "base_sha256":hashlib.sha256(base).hexdigest(),
                            "variant_sha256":hashlib.sha256(other).hexdigest(),
                            "best_fixed_oracle":best,
                            "non_equivalent_solid_pair_zlib6_bytes":len(solid),
                            "native_saving_vs_best_fixed_bytes":fixed-native,
                            "native_saving_vs_best_fixed_percent":round(100*(fixed-native)/fixed,6),
                            "modes":metrics,
                        })
    summary={}
    for family in FAMILIES:
        for kind in MUTATIONS:
            current=[x["native_saving_vs_best_fixed_percent"] for x in entries
                     if x["family"]==family and x["mutation"]==kind]
            summary[f"{family}/{kind}"]={
                "n":len(current),"wins":sum(x>0 for x in current),
                "losses":sum(x<0 for x in current),
                "median_percent":round(statistics.median(current),6),
                "min_percent":min(current),"max_percent":max(current),
            }
    result={
        "schema":"cmpct-o198-source-exact-codec-proxy-v1",
        "evidence_class":"SOURCE_EXACT_LOW_RUNG_RESEARCH_NO_PRODUCT_CREDIT",
        "native_blob":SOURCE_BLOB,
        "source_head":os.popen(f"git -C {ROOT} rev-parse HEAD").read().strip(),
        "compiler":compiler,"host":platform.platform(),"member_bytes":SIZE,
        "seeds":SEEDS,"positions":POSITIONS,"families":FAMILIES,"mutations":MUTATIONS,
        "policies":MODES,
        "charge":"zlib6 unique physical payload + 64 B per unique chunk + 32 B per logical chunk reference",
        "omissions":"real CMPCT codec/index/archive, pair discovery/admission, format metadata, RSS, temp IO, selective read, platform",
        "elapsed_wall_s":round(time.time()-t,3),"summary":summary,"observations":entries,
    }
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    print("O198_SUMMARY="+json.dumps(summary,sort_keys=True))
    print("O198_EXACT_SOURCE_CODEC_AWARE_RECONSTRUCTION=PASS")
    print("O198_PRODUCT_GATE=UNMEASURED")

if __name__=="__main__":
    main()
