#!/usr/bin/env python3
"""J24G73 independently interpret physical revision-24 signed journals.

No cmpct imports, no reader, no owner simulation helpers. Decode raw footer
struct / Zstd / MessagePack, reconstruct exact index/path-keyed sparse fsmeta,
and compare its complete MessagePack digest against source-attested receipt.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys
import msgpack
import zstandard as zstd

FTR = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPTF24\0"
EXPECT = {"delete": {"del":63,"ren":0,"put":0,"files":2048,"initial":2111},
          "mixed": {"del":21,"ren":21,"put":21,"files":118,"initial":128}}

def wire(raw:bytes):
    pos = raw.rfind(MAGIC)
    assert pos > 0 and pos + FTR.size <= len(raw), "final footer missing"
    entries, seen = [], set()
    while pos:
        assert pos not in seen, "cycle";seen.add(pos)
        assert 0 < pos < len(raw) - FTR.size + 1
        magic,kind,codec,flags,reserved,csize,usize,prev,digest = FTR.unpack_from(raw,pos)
        assert magic == MAGIC and kind in (0,1) and codec in (0,1)
        assert flags == reserved == 0
        assert 0 < csize <= pos and 0 < usize <= 50_000_000
        assert prev == 0 or 0 < prev < pos
        compressed = raw[pos-csize:pos]
        unpacked = (compressed if codec==0 else
                    zstd.ZstdDecompressor().decompress(compressed,max_output_size=usize))
        assert len(unpacked)==usize and hashlib.sha256(unpacked).digest()==digest
        document=msgpack.unpackb(unpacked,raw=False)
        entries.append((kind,document,pos,prev))
        if kind==0:break
        pos=prev
    assert len(entries)==64 and entries[-1][0]==0
    assert all(e[0]==1 for e in entries[:-1])
    return entries

def reconstruct(entries):
    index=entries[-1][1]
    rows={row[0]:list(row) for row in index["files"]}
    base_files=len(rows)
    sparse={}
    for field in ("xattrs","owner_overrides"):
        sparse[field]={index["files"][record[0]][0]:record[1:]
                       for record in (index.get("fsmeta") or {}).get(field,[])}
    counts={key:0 for key in ("del","ren","put")}
    for kind,delta,position,previous in reversed(entries[:-1]):
        assert isinstance(delta,dict) and len(delta["ops"])==1
        index["blobs"].extend(delta.get("blobs",[]))
        op=delta["ops"][0];tag=op[0];counts[tag]+=1
        if tag=="del":
            rows.pop(op[1])
            for field in sparse.values():field.pop(op[1],None)
        elif tag=="ren":
            old,new=op[1:];rows[new]=rows.pop(old);rows[new][0]=new
            for field in sparse.values():
                if old in field:field[new]=field.pop(old)
        elif tag=="put":
            rows[op[1][0]]=op[1]
        else:raise ValueError("unknown signed opcode: "+str(tag))
    index["files"]=sorted(rows.values(),key=lambda row:row[0])
    fs=index.get("fsmeta") or {}
    for field,identity in sparse.items():
        if field in fs:
            fs[field]=[[i,*identity[row[0]]] for i,row in enumerate(index["files"])
                       if row[0] in identity]
    return index,counts,base_files

def audit(result_path, evidence_dir):
    receipt=json.loads(Path(result_path).read_text())
    outcome={}
    for family,expected in EXPECT.items():
        original=(Path(evidence_dir)/(family+"-physical.cmpct")).read_bytes()
        advertised=receipt["cases"][family]["physical"]
        assert hashlib.sha256(original).hexdigest()==advertised["archive_sha256"]
        assert len(original)==advertised["archive_bytes"]
        entries=wire(original)
        index,counts,base_count=reconstruct(entries)
        index_sha=hashlib.sha256(msgpack.packb(index,use_bin_type=True)).hexdigest()
        assert index_sha==advertised["index_sha256"], ("physical index differs", family)
        assert counts=={key:expected[key] for key in ("del","ren","put")}
        assert counts==advertised["ops"]
        assert base_count==expected["initial"]
        assert len(index["files"])==advertised["members"]==expected["files"]
        signed=len((index.get("fsmeta") or {}).get("xattrs",[]))
        assert signed==advertised["xattr_records"]
        if family=="mixed" and receipt["strict_posix_xattrs"]:
            assert signed == 3, ("signed xattr drift", signed)
            tagged={index["files"][row[0]][0] for row in index["fsmeta"]["xattrs"]}
            assert tagged=={"r0000.dat","f0064.dat","f0100.dat"}, tagged
            assert "f0042.dat" in {row[0] for row in index["files"]}
            assert "f0042.dat" not in tagged
        # Intentionally corrupt a complete footer's SHA and verify the no-CMPCT
        # auditor refuses it, rather than crediting a blind parser.
        bad=bytearray(original)
        pos=entries[0][2]
        bad[pos+FTR.size-1] ^= 0x5A
        try:wire(bytes(bad))
        except (AssertionError, ValueError, RuntimeError):pass
        else:raise AssertionError("physical footer mutation undetected")
        outcome[family]={"physical_sha256":advertised["archive_sha256"],
                         "index_sha256":index_sha,"footers":len(entries),
                         "initial_members":base_count,"final_members":len(index["files"]),
                         "xattr_records":signed,"operations":counts,
                         "tampered_footer_rejected":True}
    dest=Path(evidence_dir)/"j24g73-independent-wire.json"
    dest.write_text(json.dumps({"result":"PASS","source_head":receipt["source"]["head"],
                                "independent_wire":outcome},indent=2,sort_keys=True)+"\n")
    print("J24G73_PHYSICAL_INDEPENDENT",json.dumps(outcome,sort_keys=True))
    return outcome

if __name__=="__main__":
    assert len(sys.argv)==3
    audit(sys.argv[1],sys.argv[2])
