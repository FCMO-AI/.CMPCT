"""O79b held-out: strong VZIP proof rejects physical mutation in unselected ZIP member.

Separate prospectively frozen follow-up to completed single-member O79 original court.
Uses its original source-exact verified_zip_range without modifying it.
"""
from __future__ import annotations
import hashlib, io, json, os, struct, tempfile, time, zipfile
from pathlib import Path
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP
from v031_o79_vzip_whole_sha_range_oracle import authenticated_zip_range, mutate_to, location, probe, sha

def verify(path):
    try:
        with CMPCT(path) as r:
            count=r.verify()
        return {"outcome":"accepted","count":count}
    except Exception as e:
        return {"outcome":"rejected","type":type(e).__name__,"reason":str(e)[:200]}

def main():
    out=Path("o79b-evidence.json")
    with tempfile.TemporaryDirectory(prefix="cmpct-o79b-") as td:
        p=Path(td)
        root=p/"src";root.mkdir()
        archive=p/"three.cmpct"
        zpath=root/"three.zip"
        entries=[
          ("first.bin",b"A"*(2<<20),zipfile.ZIP_DEFLATED),
          ("note.txt",(b"held-out-stored-note-"*130),zipfile.ZIP_STORED),
          ("second.bin",bytes(range(256))*4096,zipfile.ZIP_DEFLATED),
        ]
        zbuf=io.BytesIO()
        with zipfile.ZipFile(zbuf,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,data,method in entries:
                z.writestr(name,data,compress_type=method,compresslevel=6)
        original=zbuf.getvalue()
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            assert len(z.infolist())==len(entries)
            assert all(z.read(n)==b for n,b,m in entries)
            info=z.infolist()[0]
            fields=struct.unpack_from("<IHHHHHIIIHH",original,info.header_offset)
            assert fields[0]==0x04034B50
            selected=info.header_offset+30+fields[-2]+fields[-1]+16
            assert selected+64 < info.header_offset+30+fields[-2]+fields[-1]+info.compress_size
        zpath.write_bytes(original)
        Builder(root,deflate_reuse_min=0,workers=1,reproducible=True).build(archive)
        with CMPCT(archive) as r:
            assert r.verify()==1
            assert r.read("three.zip")==original
            assert r.read_range("three.zip",selected,64)==original[selected:selected+64]
            good,met=authenticated_zip_range(r,"three.zip",selected,64)
            assert good==original[selected:selected+64]
            row=r.by["three.zip"]
            assert row[6][0]==S_VZIP, row[6]
            recipe=r.recipes[row[6][1]]
            assert len(recipe[2])==3,recipe[2]
            payloads=recipe[2]
            assert [int(pr[2]) for pr in payloads]==[0,0,0],payloads
            second_deflate_idx=payloads[2][3]
            stored_idx=payloads[1][0]
            targets={"unselected_later_deflate":location(r,second_deflate_idx,16),
                     "unselected_stored":location(r,stored_idx,12)}
        rows=[]
        for name,at in targets.items():
            dest=p/(name+"-corrupt.cmpct")
            changed=mutate_to(archive,dest,at)
            with CMPCT(dest) as rr:
                try:
                    got,proof=authenticated_zip_range(rr,"three.zip",selected,64)
                    strong={"outcome":"returned","sha256":sha(got)}
                except Exception as e:
                    strong={"outcome":"rejected","type":type(e).__name__,"reason":str(e)[:200]}
            with CMPCT(dest) as rr:
                try:
                    raw=rr.read_range("three.zip",selected,64)
                    weak={"outcome":"returned","sha256":sha(raw)}
                except Exception as e:
                    weak={"outcome":"rejected","type":type(e).__name__,"reason":str(e)[:200]}
            full=verify(dest)
            assert strong["outcome"]=="rejected",(name,strong)
            assert full["outcome"]=="rejected",(name,full)
            rows.append({"mutation":name,"physical_change":changed,
                         "verified_sha_range":strong,"legacy_range":weak,"complete_verify":full})
        receipt={"schema":"cmpct-o79b-held-out-v1","source_head":os.getenv("EVIDENCE_HEAD","LOCAL_UNBOUND"),
                 "original_archive_sha256":sha(archive.read_bytes()),"original_nested_zip_sha256":sha(original),
                 "original_nested_zip_bytes":len(original),"selected":[selected,64],
                 "initial_authentication":met,"member_modes":[int(pr[2]) for pr in payloads],
                 "corruptions":rows,"decision":"MULTIMEMBER_UNSELECTED_CORRUPTION_SHA_FAIL_CLOSED"}
        out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        print("O79B_DECISION="+receipt["decision"],flush=True)
        print("O79B_CORRUPTIONS="+str(len(rows)),flush=True)
if __name__=="__main__":
    main()
