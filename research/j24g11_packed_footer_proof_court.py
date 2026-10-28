#!/usr/bin/env python3
"""J24G11 installed-source packed-u64 proof court. Research, not release evidence.

Compares immutable #664 source, actual installed candidate, and a faster unbounded
Python-set oracle on the *same physical first-party signed r24 archives*.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
import types
from pathlib import Path
from unittest.mock import patch

import cmpct.reader as product
from cmpct.builder import Builder
from cmpct.transactions import append_rename
from j24g10_exact_spill_court import (
    PAYLOAD, arbitrary_tail, check_archive, digest, measure,
    orphan_tail, variant_orphan_tail,
)

BASE_HEAD = "da5552d4f74113de1887fdad9683b433bb6e6cf2"
BASE_READER = "0a8a7afa036cb4988b80836bcbe550c3b5d0bb40"
PACKED_READER = "4bcedb059316171963d258fc93caaa49fec56f12"
PREREG = "70a54adeae8c77fe8693f84be6fbd0ab15b5b4f6"
N = 16400

def source_class(ref, blob, name):
    assert subprocess.check_output(
        ["git", "rev-parse", ref + ":src/cmpct/reader.py"], text=True
    ).strip() == blob, (ref, blob)
    raw = subprocess.check_output(["git", "show", ref + ":src/cmpct/reader.py"])
    module = types.ModuleType(name)
    module.__package__ = "cmpct"
    exec(compile(raw, "<immutable Git Reader " + ref + ">", "exec"), module.__dict__)
    return module

class Unbounded:
    def __init__(self):
        self.entries = set()
    def __contains__(self, pos): return pos in self.entries
    def __len__(self): return len(self.entries)
    def update(self, positions): self.entries.update(positions)
    def __enter__(self): return self
    def __exit__(self, *args): return None

def isolated_reader():
    m = source_class("HEAD", PACKED_READER, "cmpct._j24g11_unbounded")
    m._FooterInvalidProof = Unbounded
    return m.CMPCT

def membership_audit():
    rng = random.Random(20261028)
    values = set(rng.randrange(1, 1 << 62) for _ in range(30000))
    values.update((0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1))
    probes = set(values)
    for v in sorted(values)[:15000]:
        probes.add((v + 7) % (1 << 64))
    with product._FooterInvalidProof() as proof:
        proof.update(values)
        assert len(proof) == len(values)
        assert proof._db is None and proof._path is None and not proof.hot
        assert proof._packed is not None
        raw_bytes = len(proof._packed) * proof._packed.itemsize
        assert raw_bytes == 8 * len(values) and raw_bytes <= (1 << 20)
        assert all((v in proof) == (v in values) for v in probes)
        proof.update({0, 1, (1 << 63), 42})
        values.add(42)
        assert len(proof) == len(values)
        assert all((v in proof) == (v in values) for v in probes | {42})
        # Deliberately out-of-domain inserts fail closed.
        try:
            proof.update({1 << 64})
        except ValueError:
            pass
        else:
            raise AssertionError("unsigned uint64 overflow accepted")
    # Explicit cap-to-disk transition, no hidden all-in-memory path.
    with product._FooterInvalidProof() as proof:
        proof.update(set(range(131072)))
        assert proof._db is None
        assert len(proof._packed) == 131072
        assert proof._packed.buffer_info()[1] * proof._packed.itemsize == (1 << 20)
        proof.update({1 << 63, (1 << 64) - 1})
        assert proof._db is not None and proof._packed is None
        path = proof._path
        assert path and os.path.isfile(path)
        import sqlite3
        with sqlite3.connect(path) as independent:
            assert independent.execute("SELECT count(*) FROM bad").fetchone()[0] == 131074
        assert len(proof) == 131074
        assert all(v in proof for v in (0, 131071, 1 << 63, (1 << 64) - 1))
        assert 131072 not in proof
        physical = os.stat(path).st_size
    assert not os.path.exists(path)
    return {"positive":len(values), "probe_count":len(probes),
            "packed_payload_bytes":raw_bytes, "tier_cap_bytes":1 << 20,
            "disk_overflow_rows":131074, "disk_overflow_bytes":physical,
            "disk_cleanup":True, "u64_extremes_exact":True, "overflow_rejected":True}

def capture_candidate_proof(path, checkpoint):
    capture=[]
    cls=product._FooterInvalidProof
    old_close=cls.close
    def record(self):
        capture.append({"len":len(self), "packed_count":len(self._packed or ()),
                        "packed_payload_bytes":(len(self._packed) * self._packed.itemsize
                                                if self._packed is not None else 0),
                        "sqlite_created":self._db is not None,
                        "path":self._path})
        return old_close(self)
    with patch.object(cls,"close",record):
        with product.CMPCT(path) as ar:
            check_archive(ar,checkpoint,"owner.bin")
    assert len(capture)==1, capture
    return capture[0]

def court(label,path,checkpoint,classes,repeats=3,target="owner.bin"):
    all_rows={k:[] for k in classes}
    for j in range(repeats):
        names=list(classes) if j%2==0 else list(reversed(classes))
        for name in names:
            all_rows[name].append(measure(classes[name],path,checkpoint,target))
    calls={k:[r["decoder_calls"] for r in rows] for k,rows in all_rows.items()}
    assert len({v for arr in calls.values() for v in arr})==1,(label,calls)
    medians={k:statistics.median(x["wall_ms"] for x in rows) for k,rows in all_rows.items()}
    cpus={k:statistics.median(x["cpu_ms"] for x in rows) for k,rows in all_rows.items()}
    item={"case":label,"archive_sha256":digest(path.read_bytes()),
          "archive_bytes":path.stat().st_size,"calls":calls,
          "raw":all_rows,"median_wall_ms":medians,"median_cpu_ms":cpus,
          "parent_to_candidate_wall":medians["parent"]/medians["candidate"],
          "unbounded_to_candidate_wall":medians["unbounded"]/medians["candidate"]}
    print("J24G11_CASE="+json.dumps(item,sort_keys=True),flush=True)
    return item

def main():
    source=subprocess.check_output(["git","show","HEAD:src/cmpct/reader.py"])
    blob=subprocess.check_output(["git","rev-parse","HEAD:src/cmpct/reader.py"],text=True).strip()
    assert blob==PACKED_READER
    package_path=Path(product.__file__).resolve()
    assert "site-packages" in str(package_path),package_path
    assert package_path.read_bytes()==source
    assert subprocess.check_output(["git","merge-base","--is-ancestor",PREREG,"HEAD"])==b""
    Parent=source_class(BASE_HEAD,BASE_READER,"cmpct._j24g11_original").CMPCT
    Oracle=isolated_reader()
    classes={"parent":Parent,"candidate":product.CMPCT,"unbounded":Oracle}
    audit=membership_audit()
    output=Path(os.environ.get("J24G11_ARTIFACTS","j24g11-artifacts"))
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g11-") as td:
        root=Path(td)
        tree=root/"tree";tree.mkdir()
        (tree/"owner.bin").write_bytes(PAYLOAD)
        pristine=root/"pristine.cmpct"
        Builder(tree).build(pristine)
        original=pristine.read_bytes()
        with product.CMPCT(pristine) as ar:
            checkpoint=ar.latest_footer_pos
            assert checkpoint and ar.read("owner.bin")==PAYLOAD
        result={}
        def run_case(label,physical,expected_calls,repeats=3):
            path=root/(label+".cmpct");path.write_bytes(physical)
            r=court(label,path,checkpoint,classes,repeats=repeats)
            assert all(set(v)=={expected_calls} for v in r["calls"].values()),(label,r["calls"])
            if label.startswith(("alternating","random")):
                proof=capture_candidate_proof(path,checkpoint)
                assert proof["len"]==N,proof
                assert proof["packed_payload_bytes"]==8*N,proof
                assert not proof["sqlite_created"] and proof["path"] is None,proof
                r["physical_proof"]=proof
            result[label]=r
        run_case("alternating-16400",variant_orphan_tail(original,N,"alternating"),N+1)
        run_case("random-16400",arbitrary_tail(original,N,20261028),N+1)
        run_case("uniform-ap-16400",orphan_tail(original,N,True),N+1,5)
        run_case("flat-1024",orphan_tail(original,1024,False),1025,7)
        valid=root/"valid-rename.cmpct"
        valid.write_bytes(original)
        append_rename(valid,"owner.bin","renamed.bin")
        with product.CMPCT(valid) as ar:
            new_checkpoint=ar.latest_footer_pos
            assert new_checkpoint>checkpoint
        result["valid-first-party-rename"]=court(
            "valid-first-party-rename",valid,new_checkpoint,classes,31,"renamed.bin")
        for label in ("alternating-16400","random-16400"):
            assert result[label]["median_wall_ms"]["candidate"]>0
        # Scientific decision, not CI signal: preserve negative ratios if any.
        viable=all(result[label]["parent_to_candidate_wall"]>=1.2 for label in
                   ("alternating-16400","random-16400"))
        overhead_ok=all(result[label]["median_wall_ms"]["candidate"]<=
                        result[label]["median_wall_ms"]["parent"]*1.25 for label in
                        ("uniform-ap-16400","flat-1024","valid-first-party-rename"))
        decision="PROMISING_NARROW_SEED" if viable and overhead_ok else "NARROW_OR_RETIRE"
        out={"decision":decision,"base":BASE_HEAD,"base_reader_blob":BASE_READER,
             "candidate_reader_blob":PACKED_READER,
             "installed_path":str(package_path),"prereg":PREREG,
             "first_party_archive_sha256":digest(original),
             "first_party_archive_bytes":len(original),
             "logical_sha256":digest(PAYLOAD),"oracle":audit,
             "cases":result,"speed_gate_met":viable,"normal_gate_met":overhead_ok,
             "total_RSS_bounded":False,"per_chain_seen_chain_bounded":False,
             "same_inode_mutation_supported":False,"release_credit":0}
        (output/"court.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("J24G11_RESULT="+json.dumps({"decision":decision,
            "ratios":{k:v["parent_to_candidate_wall"] for k,v in result.items()},
            "oracle":audit,"release_credit":0},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
