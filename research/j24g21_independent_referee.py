#!/usr/bin/env python3
"""Independent J24G21 signed first-party transfer referee.

No CMPCT import, no J24G21 court import, no certified-projection import.
Physical footer/decoded SHA, Writer delta map, raw ABBA, Reader outcomes,
and deliberate receipt mutations are checked separately from the measured code.
This is not an independent complete CMPCT Reader.
"""
from __future__ import annotations
import copy, ctypes, ctypes.util, hashlib, json, pathlib, statistics, struct, sys
import msgpack

FTR=struct.Struct("<8sBBBBQQQ32s")
PARENT="e24f9b1ed58ba6208b53bdd8d92aacb48e7442ed"
RESEARCH_READER="f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PUBLISHED_READER="e716233403dabd0966863c45635e18fa5ac6afb8"
NAMES={"rename","delete","update","rename_unicode","rename_long"}

def sha(b): return hashlib.sha256(b).hexdigest()
def require(ok,why):
    if not ok: raise AssertionError(why)
def zstd_decode(encoded, n):
    lib=ctypes.CDLL(ctypes.util.find_library("zstd") or "libzstd.so.1")
    lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
    lib.ZSTD_decompress.restype=ctypes.c_size_t
    lib.ZSTD_isError.argtypes=[ctypes.c_size_t]
    lib.ZSTD_isError.restype=ctypes.c_uint
    out=ctypes.create_string_buffer(n); src=ctypes.create_string_buffer(encoded)
    result=lib.ZSTD_decompress(out,n,src,len(encoded))
    require(not lib.ZSTD_isError(result) and result==n,"zstd exact length")
    return out.raw

def audit(root,record=None):
    root=pathlib.Path(root)
    r=json.loads((root/"result.json").read_text()) if record is None else record
    checks=0
    def check(condition,why):
        nonlocal checks
        require(condition,why);checks+=1
    check(r["schema"]=="cmpct-j24g21-first-party-writer-v1","schema")
    check(r["parent"]==PARENT,"parent source")
    check(r["reader_blob"]==RESEARCH_READER and r["published_reader_blob"]==PUBLISHED_READER,"readers")
    check(r["release_credit"]==0 and r["no_product_source_changes"] is True,"no release")
    check(r["all_first_party_ignored_fields_absent"] and r["all_readers_semantics_equal"],"summaries")
    check(all(set(r[k])==NAMES for k in ("physical_payloads","raw_decode","raw_reader","summary")),"case coverage")
    for name in sorted(NAMES):
        info=r["physical_payloads"][name]
        data=(root/"physical"/(name+".cmpct")).read_bytes()
        magic,kind,codec,flags,reserved,csize,usize,prev,payload_sha=FTR.unpack_from(data,len(data)-FTR.size)
        check(magic==b"CMPTF24\0" and kind==1 and codec in (0,1),"signed delta framing "+name)
        check(flags==0 and reserved==0 and 0<prev<info["footer_position"],"parent/framing "+name)
        check(len(data)==info["physical_bytes"] and sha(data)==info["physical_sha256"],"archive digest "+name)
        check(info["footer_position"]==len(data)-FTR.size,"footer byte offset "+name)
        wire=data[-FTR.size-csize:-FTR.size]
        raw=wire if codec==0 else zstd_decode(wire,usize)
        check(len(raw)==usize and sha(raw)==payload_sha.hex(),"signed payload sha "+name)
        check(sha(raw)==info["sha256"] and usize==info["decoded_bytes"],"metadata digest "+name)
        check(len(wire)==info["encoded_bytes"] and info["codec"]==codec,"physical encoding "+name)
        check(raw==(root/(name+".mpk")).read_bytes(),"payload receipt "+name)
        value=msgpack.unpackb(raw,raw=False)
        check(isinstance(value,dict) and set(value)=={"ops","blobs"},"Writer known fields only "+name)
        check(info["ignored_fields"]==0 and info["known_fields_exact"],"no avoided ignored subtree "+name)
        check(isinstance(value["ops"],list) and isinstance(value["blobs"],list),"delta shape "+name)
        observations=r["raw_decode"][name]
        check(len(observations)>=8 and {x["arm"] for x in observations}=={"direct","projected"},"ABBA arms "+name)
        check(all(x["loops"]>0 and x["cpu_ns"]>0 and x["wall_ns"]>0 and x["input_sha256"]==sha(raw) for x in observations),"raw per sample provenance "+name)
        for arm in ("direct","projected"):
            v=[x["cpu_ns"]/x["loops"] for x in observations if x["arm"]==arm]
            check(abs(statistics.median(v)-r["summary"][name][arm+"_cpu_ns_per_decode"])<0.0001,"CPU median "+name+arm)
            v=[x["wall_ns"]/x["loops"] for x in observations if x["arm"]==arm]
            check(abs(statistics.median(v)-r["summary"][name][arm+"_wall_ns_per_decode"])<0.0001,"wall median "+name+arm)
        stats=r["summary"][name]
        check(abs(stats["projected_cpu_ns_per_decode"]/stats["direct_cpu_ns_per_decode"]-stats["cpu_ratio"])<1e-9,"CPU ratio "+name)
        readers=r["raw_reader"][name]
        check(set(readers)=={"parent","projected"},"Reader arms "+name)
        for arm,rows in readers.items():
            check(len(rows)>=2,"Reader repetition "+name+arm)
            check(all(x["status"]=="opened" and x["depth"]==1 for x in rows),"Reader decode "+name+arm)
            check(all(x["footer"]==info["footer_position"] for x in rows),"Reader footer "+name+arm)
            check(all(x["names"]==rows[0]["names"] and x["members"]==rows[0]["members"] for x in rows),"Reader stable tree "+name+arm)
            check(all(x["cpu_ns"]>=0 and x["wall_ns"]>=0 for x in rows),"Reader timing "+name+arm)
        check(all((a["footer"],a["members"],a["names"],a["verified"])==
                  (b["footer"],b["members"],b["names"],b["verified"])
                  for a,b in zip(readers["parent"],readers["projected"])),"Reader parity "+name)
    return checks

def hostile(root):
    source=json.loads((pathlib.Path(root)/"result.json").read_text())
    falsifiers=[
      lambda r:r["physical_payloads"]["rename"].update(ignored_fields=1),
      lambda r:r["physical_payloads"]["delete"].update(physical_sha256="00"*32),
      lambda r:r.update(reader_blob="00"*20),
      lambda r:r["summary"]["rename"].update(cpu_ratio=0.0),
      lambda r:r["raw_reader"]["update"]["parent"][0].update(footer=0),
      lambda r:r["raw_reader"]["rename_long"]["projected"][0].update(status="error"),
      lambda r:r["raw_decode"]["rename"][0].update(cpu_ns=-1),
      lambda r:r["raw_reader"]["delete"]["parent"][0].update(members={"wrong":"sha"})]
    rejected=0
    for mutate in falsifiers:
        candidate=copy.deepcopy(source); mutate(candidate)
        try: audit(root,candidate)
        except AssertionError: rejected+=1
        else: raise AssertionError("forged receipt passed independent audit")
    return rejected

if __name__=="__main__":
    root=pathlib.Path(sys.argv[1])
    print(json.dumps({"independent_checks":audit(root),"tampered_receipts_rejected":hostile(root),
                      "not_a_second_reader":True},sort_keys=True))
