#!/usr/bin/env python3
"""J24G06 actual-source candidate vs exact historical Git Reader, hostile footer corpus.

Unchanged older release code is dynamically compiled from its exact Git blob,
NOT a test reimplementation. Both Readers use the same installed codec/native stack.
"""
from __future__ import annotations
import hashlib,json,os,statistics,subprocess,sys,tempfile,time,types
from pathlib import Path
from unittest.mock import patch

from cmpct.builder import Builder
from cmpct.reader import CMPCT as Candidate
from cmpct.transactions import append_rename
from j24g04_false_footer_recovery_court import PAYLOAD, append_orphan_deltas, digest
from j24g05_negative_ancestry_oracle import flat_orphans

RELEASE_SHA="80c358f8824ec1b20d349c92ed94c898090969b0"
RELEASE_READER_BLOB="e716233403dabd0966863c45635e18fa5ac6afb8"
CASES=(32,128,256)


def exact_historical_reader():
    got=subprocess.check_output(["git","rev-parse",f"{RELEASE_SHA}:src/cmpct/reader.py"],text=True).strip()
    assert got==RELEASE_READER_BLOB,got
    raw=subprocess.check_output(["git","show",f"{RELEASE_SHA}:src/cmpct/reader.py"])
    module=types.ModuleType("cmpct._j24g06_source_original")
    module.__package__="cmpct"
    exec(compile(raw, f"<Git blob {got}>", "exec"), module.__dict__)
    return module.CMPCT


def actual_read(cls, path:Path, member:str)->dict:
    positions=[]
    decoder=cls._decode_generation_payload
    def count(self,footer_pos):
        positions.append(footer_pos)
        return decoder(self,footer_pos)
    wall_start=time.perf_counter();cpu_start=time.process_time()
    with patch.object(cls,"_decode_generation_payload",count):
        with cls(path) as ar:
            actual=ar.read(member)
            assert actual==PAYLOAD
            assert ar.read_range(member,0,17)==PAYLOAD[:17]
            assert ar.read_range(member,len(PAYLOAD)-11,11)==PAYLOAD[-11:]
            ar.verify()
            footer=ar.latest_footer_pos
            depth=ar.delta_depth
    return {"calls":len(positions),"unique_positions":len(set(positions)),
            "footer":footer,"depth":depth,"bytes":len(actual),
            "sha256":digest(actual),
            "wall_s":time.perf_counter()-wall_start,"cpu_s":time.process_time()-cpu_start}


def compare(original,candidate,path,member,expect_old,expect_new,depth):
    old=[];new=[]
    for r in range(3):
        order=(("old","new") if r%2==0 else ("new","old"))
        for kind in order:
            cls=original if kind=="old" else candidate
            got=actual_read(cls,path,member)
            (old if kind=="old" else new).append(got)
    assert all(x["calls"]==expect_old and x["depth"]==depth for x in old),old
    assert all(x["calls"]==expect_new and x["depth"]==depth for x in new),new
    assert {x["footer"] for x in old+new}=={old[0]["footer"]}
    assert all(x["sha256"]==digest(PAYLOAD) and x["bytes"]==len(PAYLOAD) for x in old+new)
    old_wall=statistics.median(x["wall_s"] for x in old)
    new_wall=statistics.median(x["wall_s"] for x in new)
    return {"historical":old,"candidate":new,"median_original_ms":old_wall*1000,
            "median_candidate_ms":new_wall*1000,"wall_ratio_original_over_candidate":old_wall/new_wall,
            "cpu_original_ms":statistics.median(x["cpu_s"] for x in old)*1000,
            "cpu_candidate_ms":statistics.median(x["cpu_s"] for x in new)*1000}


def main():
    out=Path(os.environ.get("J24G06_ARTIFACTS","j24g06-artifacts"));out.mkdir(parents=True,exist_ok=True)
    Historical=exact_historical_reader()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g06-") as td:
        root=Path(td);tree=root/"tree";tree.mkdir()
        (tree/"owner.bin").write_bytes(PAYLOAD)
        archive=root/"original.cmpct";Builder(tree).build(archive);base=archive.read_bytes()
        baseline=compare(Historical,Candidate,archive,"owner.bin",1,1,0)
        committed=root/"valid.cmpct";committed.write_bytes(base)
        append_rename(committed,"owner.bin","renamed.bin")
        committed_control=compare(Historical,Candidate,committed,"renamed.bin",2,2,1)
        cases=[]
        for n in CASES:
            linked=append_orphan_deltas(base,n);flat=flat_orphans(base,n)
            assert len(linked)==len(flat)==len(base)+n*81
            lpath=root/f"linked-{n}.cmpct";lpath.write_bytes(linked)
            fpath=root/f"flat-{n}.cmpct";fpath.write_bytes(flat)
            cases.append({"n":n,"bytes":len(linked),"linked_sha256":digest(linked),
                          "flat_sha256":digest(flat),
                          "linked":compare(Historical,Candidate,lpath,"owner.bin",
                                           1+n*(n+1)//2,1+n,0),
                          "flat":compare(Historical,Candidate,fpath,"owner.bin",1+n,1+n,0)})
        high=cases[-1]
        assert high["linked"]["wall_ratio_original_over_candidate"]>=2.0
        assert high["flat"]["wall_ratio_original_over_candidate"]>=1/1.25, (
            "Flat unaffiliated footer overhead exceeded preregistered +25%",high["flat"])
        assert baseline["median_candidate_ms"]-baseline["median_original_ms"]<=3.0
        result={"question":"J24G06 bounded negative footer ancestor product source",
                "status":"CANDIDATE_HOST_COURT_PASS_WITHIN_SCOPE",
                "product_source_modified":True,"merge":False,"release_credit":0,
                "historical_reader_git_blob":RELEASE_READER_BLOB,
                "candidate_reader_git_blob":subprocess.check_output(
                    ["git","rev-parse","HEAD:src/cmpct/reader.py"],text=True).strip(),
                "builder_archive_sha256":digest(base),"builder_archive_bytes":len(base),
                "logical_sha256":digest(PAYLOAD),"repeats_per_variant":3,
                "baseline":baseline,"committed_rename":committed_control,"orphan_cases":cases}
        (out/"product_court.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("J24G06_SOURCE_EXACT_PRODUCT_COURT="+json.dumps(result,sort_keys=True))
        print("J24G06_PRODUCT_COURT_DECISION=CANDIDATE_HOST_COURT_PASS_WITHIN_SCOPE")


if __name__=="__main__":
    main()
