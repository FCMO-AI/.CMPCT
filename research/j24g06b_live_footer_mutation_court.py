#!/usr/bin/env python3
"""Bounded deterministic same-inode source mutation falsifier, real original/candidate Readers."""
from __future__ import annotations
import hashlib,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
import msgpack
from cmpct.builder import Builder
from cmpct.codec import FTR,FMAGIC,sha
from cmpct.reader import CMPCT as Candidate
from j24g04_false_footer_recovery_court import PAYLOAD,append_orphan_deltas,digest
from j24g06_bounded_footer_product_court import exact_historical_reader


def read_case(cls,raw:bytes,base_footer:int,a_pos:int,b_pos:int,mutate:bool,root:Path,label:str):
    path=root/f"{label}.cmpct"
    path.write_bytes(raw)
    before=digest(path.read_bytes())
    orig=cls._decode_generation_payload
    visits=[];did=False
    def injection(self,pos):
        nonlocal did
        val=orig(self,pos)
        visits.append(pos)
        if mutate and pos==a_pos and not did:
            assert val is not None and val[2]==0
            payload=msgpack.packb({"blobs":[],"ops":[]},use_bin_type=True)
            updated=FTR.pack(FMAGIC,1,0,0,0,len(payload),len(payload),base_footer,sha(payload))
            with open(path,"r+b",buffering=0) as f:
                f.seek(a_pos); old=f.read(FTR.size)
                assert FTR.unpack(old)[-2]==0, FTR.unpack(old)
                f.seek(a_pos); f.write(updated);os.fsync(f.fileno())
            did=True
        return val
    with patch.object(cls,"_decode_generation_payload",injection):
        with cls(path) as ar:
            assert ar.read("owner.bin")==PAYLOAD
            assert ar.read_range("owner.bin",3,15)==PAYLOAD[3:18]
            ar.verify()
            selected=ar.latest_footer_pos
            depth=ar.delta_depth
    after=digest(path.read_bytes())
    assert did is mutate
    assert (after!=before)==mutate
    assert len(path.read_bytes())==len(raw)
    return {"label":label,"injected":did,"archive_sha256_before":before,"archive_sha256_after":after,
            "selected_footer":selected,"delta_depth":depth,"visits":visits,"decode_calls":len(visits),
            "logical_sha256":digest(PAYLOAD),"physical_bytes":len(raw)}


def main():
    out=Path(os.environ.get("J24G06B_ARTIFACTS","j24g06b-artifacts"));out.mkdir(exist_ok=True)
    Historical=exact_historical_reader()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g06b-") as td:
        root=Path(td);source=root/"source";source.mkdir()
        (source/"owner.bin").write_bytes(PAYLOAD)
        clean=root/"clean.cmpct";Builder(source).build(clean)
        base=clean.read_bytes()
        with Historical(clean) as ar:base_footer=ar.latest_footer_pos
        raw=append_orphan_deltas(base,2)
        payload=msgpack.packb({"blobs":[],"ops":[]},use_bin_type=True)
        a_pos=len(base)+len(payload)
        b_pos=a_pos+FTR.size+len(payload)
        assert b_pos+FTR.size==len(raw)
        control_old=read_case(Historical,raw,base_footer,a_pos,b_pos,False,root,"historical-control")
        control_new=read_case(Candidate,raw,base_footer,a_pos,b_pos,False,root,"candidate-control")
        assert control_old["selected_footer"]==control_new["selected_footer"]==base_footer
        assert control_old["delta_depth"]==control_new["delta_depth"]==0
        attacked_old=read_case(Historical,raw,base_footer,a_pos,b_pos,True,root,"historical-mutate")
        attacked_new=read_case(Candidate,raw,base_footer,a_pos,b_pos,True,root,"candidate-mutate")
        assert attacked_old["selected_footer"]==a_pos and attacked_old["delta_depth"]==1,attacked_old
        assert attacked_new["selected_footer"]==base_footer and attacked_new["delta_depth"]==0,attacked_new
        assert attacked_old["archive_sha256_after"]==attacked_new["archive_sha256_after"]
        assert attacked_old["logical_sha256"]==attacked_new["logical_sha256"]==digest(PAYLOAD)
        j={"question":"J24G06b same-inode reparenting invalid-cache temporal source-custody",
           "result":"TEMPORAL_GENERATION_SELECTION_DIVERGENCE_CONFIRMED",
           "product_source_changed":False,"release_credit":0,
           "source_builder_sha256":digest(base),"source_orphan_archive_sha256":digest(raw),
           "physical_bytes":len(raw),"valid_builder_footer":base_footer,"older_mutated_footer":a_pos,
           "newest_orphan_footer":b_pos,"historical_control":control_old,
           "candidate_control":control_new,"historical_mutated":attacked_old,
           "candidate_mutated":attacked_new}
        (out/"mutation.json").write_text(json.dumps(j,sort_keys=True,indent=2)+"\n")
        print("J24G06B_SOURCE_EXACT_MUTATION="+json.dumps(j,sort_keys=True))
        print("J24G06B_DECISION=TEMPORAL_GENERATION_SELECTION_DIVERGENCE_CONFIRMED")


if __name__=="__main__":
    main()
