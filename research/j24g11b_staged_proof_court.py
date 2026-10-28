#!/usr/bin/env python3
"""J24G11b: genuine installed r24 Reader, independent short-invalid ancestries.

Compares frozen source owner #667 (before batching), source #664 SQLite,
and new candidate with the same physical authenticated archive. No fake decode.
"""
from __future__ import annotations
import json,os,statistics,subprocess,tempfile,time,types,hashlib
from pathlib import Path
from unittest.mock import patch

import msgpack
import cmpct.reader as reader
from cmpct.builder import Builder
from cmpct.codec import FMAGIC,FTR,sha
from j24g10_exact_spill_court import PAYLOAD,check_archive,measure
from j24g11_packed_footer_proof_court import Unbounded

OLD_HEAD="19f8d0313a93655af05a365d1777a7a303a550be"
OLD_BLOB="4bcedb059316171963d258fc93caaa49fec56f12"
SQL_HEAD="da5552d4f74113de1887fdad9683b433bb6e6cf2"
SQL_BLOB="0a8a7afa036cb4988b80836bcbe550c3b5d0bb40"
NEW_BLOB="f13c5492f5acfa1cfcfec97cdbe0da71e41e327b"
PREREG="c363ec7dcec370509a8318dae8d5603fe5835808"
PAIRS=9000

def from_git(ref,blob,name,unbounded=False):
    assert subprocess.check_output(["git","rev-parse",ref+":src/cmpct/reader.py"],text=True).strip()==blob
    raw=subprocess.check_output(["git","show",ref+":src/cmpct/reader.py"])
    m=types.ModuleType(name)
    m.__package__="cmpct"
    exec(compile(raw,"<immutable original Reader "+ref+">","exec"),m.__dict__)
    if unbounded:m._FooterInvalidProof=Unbounded
    return m.CMPCT

def paired_chain(base):
    raw=bytearray(base)
    payload=msgpack.packb({"blobs":[],"ops":[]},use_bin_type=True)
    for _ in range(PAIRS):
        first=len(raw)+len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC,1,0,0,0,len(payload),len(payload),0,sha(payload)))
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC,1,0,0,0,len(payload),len(payload),first,sha(payload)))
    return bytes(raw)

def run(label,archive,checkpoint,classes,repeats=3,target="owner.bin"):
    rows={k:[] for k in classes}
    for i in range(repeats):
        order=list(classes) if i%2==0 else list(reversed(classes))
        for name in order:
            rows[name].append(measure(classes[name],archive,checkpoint,target))
    counts={k:[q["decoder_calls"] for q in a] for k,a in rows.items()}
    if label=="independent-pairs":
        # Every paired-invalid ancestry needs exactly two real decodes, and
        # each owner footer is skipped after its negative proof is certified.
        assert all(set(v)=={2*PAIRS+1} for v in counts.values()),counts
    else:assert all(set(v)=={2} for v in counts.values())
    med={k:statistics.median(x["wall_ms"] for x in a) for k,a in rows.items()}
    cpu={k:statistics.median(x["cpu_ms"] for x in a) for k,a in rows.items()}
    result={"label":label,"archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
            "archive_bytes":archive.stat().st_size,"raw":rows,"decoder_counts":counts,
            "median_wall_ms":med,"median_cpu_ms":cpu,
            "old_to_candidate_wall_ratio":med["old"]/med["candidate"],
            "sqlite_to_candidate_wall_ratio":med["sqlite"]/med["candidate"],
            "unbounded_to_candidate_wall_ratio":med["unbounded"]/med["candidate"]}
    print("J24G11B_CASE="+json.dumps({k:v for k,v in result.items() if k!="raw"},sort_keys=True),flush=True)
    return result

def staged_proof_oracle():
    cls=reader._FooterInvalidProof
    with cls() as store:
        store.update(set(range(16385)))
        assert store._packed is not None and not store.hot and store._db is None
        assert len(store)==16385
        # 2000 *small* adds must stay in hot, not rebuild packed 1000 times.
        started=time.perf_counter()
        for i in range(1000):
            store.update({16385+2*i,16386+2*i})
        elapsed=time.perf_counter()-started
        assert len(store)==18385 and len(store.hot)==2000 and len(store._packed)==16385
        assert all(i in store for i in range(18385))
        store.update({16385,16385,18384})
        assert len(store)==18385
        # Cross a FULL 16,384 hot batch. Exact count, no duplicates.
        store.update(set(range(18385,32770)))
        assert not store.hot and len(store)==32770
        assert store._packed is not None and store._db is None
        # Build hot staging *and* packed; cross the 1MiB cap and ensure
        # both physical sources are committed before any candidate is skipped.
        store.update(set(range(32770,32780)))
        assert len(store.hot)==10
        store.update(set(range(32780,131075)))
        assert store._packed is None and store._db is not None
        assert len(store)==131075
        import sqlite3
        path=store._path
        with sqlite3.connect(path) as other:
            assert other.execute("SELECT count(*) FROM bad").fetchone()[0]==131075
        assert all(i in store for i in [0,16385,18384,32769,32770,32779,131074])
        assert 131075 not in store
    assert not os.path.exists(path)
    return {"small_batch_updates":1000,"small_batch_wall_ms":elapsed*1000,
            "staging_positions":2000,"packed_merge_after_hot_cap":True,
            "disk_handoff_copies_hot_and_packed":True,"independent_db_rows":131075,
            "temp_deleted":True}

def main():
    assert subprocess.check_output(["git","rev-parse","HEAD:src/cmpct/reader.py"],text=True).strip()==NEW_BLOB
    assert subprocess.check_output(["git","merge-base","--is-ancestor",PREREG,"HEAD"])==b""
    import cmpct.reader
    installed=Path(cmpct.reader.__file__).resolve()
    assert "site-packages" in str(installed)
    assert installed.read_bytes()==subprocess.check_output(["git","show","HEAD:src/cmpct/reader.py"])
    classes={
        "old":from_git(OLD_HEAD,OLD_BLOB,"cmpct._j24g11b_old"),
        "candidate":reader.CMPCT,
        "sqlite":from_git(SQL_HEAD,SQL_BLOB,"cmpct._j24g11b_sqlite"),
        "unbounded":from_git(OLD_HEAD,OLD_BLOB,"cmpct._j24g11b_set",True)
    }
    oracle=staged_proof_oracle()
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g11b-") as d:
        root=Path(d)
        tree=root/"tree";tree.mkdir()
        (tree/"owner.bin").write_bytes(PAYLOAD)
        basepath=root/"base.cmpct";Builder(tree).build(basepath)
        with reader.CMPCT(basepath) as ar:
            checkpoint=ar.latest_footer_pos
            assert checkpoint and ar.read("owner.bin")==PAYLOAD
        base=basepath.read_bytes()
        chained=root/"pairs.cmpct";chained.write_bytes(paired_chain(base))
        result={"independent-pairs":run("independent-pairs",chained,checkpoint,classes)}
        from cmpct.transactions import append_rename
        valid=root/"valid.cmpct";valid.write_bytes(base)
        append_rename(valid,"owner.bin","renamed.bin")
        with reader.CMPCT(valid) as ar: vcheckpoint=ar.latest_footer_pos
        result["valid-rename"]=run("valid-rename",valid,vcheckpoint,classes,11,"renamed.bin")
        assert result["independent-pairs"]["old_to_candidate_wall_ratio"]>=2.0
        assert result["valid-rename"]["median_wall_ms"]["candidate"]<=1.25*result["valid-rename"]["median_wall_ms"]["old"]
        out={"decision":"NARROW_STAGED_PRODUCT_SEED","prereg":PREREG,
             "source_original":OLD_HEAD,"old_reader_blob":OLD_BLOB,
             "source_sqlite":SQL_HEAD,"sqlite_reader_blob":SQL_BLOB,
             "candidate_reader_blob":NEW_BLOB,"oracle":oracle,"cases":result,
             "global_RSS_bounded":False,"per_chain_bounded":False,
             "same_inode_mutation_supported":False,"release_credit":0}
        target=Path(os.environ.get("J24G11B_ARTIFACTS","j24g11b-artifacts"))
        target.mkdir(parents=True,exist_ok=True)
        (target/"court.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print("J24G11B_RESULT="+json.dumps({
            "decision":out["decision"],"oracle":oracle,
            "wall_ratio_old_to_staged":result["independent-pairs"]["old_to_candidate_wall_ratio"],
            "wall_ratio_sqlite_to_staged":result["independent-pairs"]["sqlite_to_candidate_wall_ratio"],
            "release_credit":0},sort_keys=True),flush=True)

if __name__=="__main__":main()
