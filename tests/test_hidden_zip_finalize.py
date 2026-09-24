from __future__ import annotations
import io,os,random,stat,struct,zipfile
from pathlib import Path
import pytest
from cmpct.builder import Builder
import cmpct.builder_hidden_zip as hidden_api
import cmpct.hidden_zip_stage as stage_api
from cmpct.builder_hidden_zip import DeferredHiddenFile,finalize_deferred_hidden_files,surface_hidden_candidate
from cmpct.codec import S_BLOB,S_PACK,S_VZIP,sha

def _write_zip(path:Path,payload:bytes)->None:
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('payload.bin',payload)
def _defer(path:Path,rel:str)->DeferredHiddenFile:
    st=path.stat();raw=path.read_bytes();return DeferredHiddenFile(surface_hidden_candidate(rel,path,st,raw),stat.S_IMODE(st.st_mode),st.st_mtime_ns,path.suffix.lower())
def _storage(builder):return {row[0]:row[6] for row in builder.files if row[6] is not None}
def _corrupt_payload_bytes(raw:bytes)->bytes:
    data=bytearray(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:info=z.infolist()[0]
    off=int(info.header_offset);nl,xl=struct.unpack_from('<HH',raw,off+26);pos=off+30+nl+xl+max(0,int(info.compress_size)//2);data[pos]^=1;return bytes(data)

def test_finalize_hidden_winner_appends_vzip_row_from_surfaced_snapshot(tmp_path):
    payload=random.Random(101).randbytes(32*1024);_write_zip(tmp_path/'owner.zip',payload);builder=Builder(tmp_path);builder.scan();assert _storage(builder)['owner.zip'][0]==S_VZIP
    hidden=tmp_path/'document.bin';_write_zip(hidden,payload);item=_defer(hidden,'document.bin');result=finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1);row=next(r for r in builder.files if r[0]=='document.bin');assert result.storage['document.bin'][0]==S_VZIP;assert row[6][0]==S_VZIP;assert row[4]==item.candidate.stamp[2];assert row[5]==item.candidate.digest;assert builder.canonical_deflate
    builder._prepare_deflate_reuse()
    for staged in result.cohort.staged.values():
        for _raw,_hint,stream,ref in staged.candidates:
            if stream is None:continue
            stream_hash=sha(stream);rawref=bytes(ref);assert builder.canonical_deflate.get(rawref)==stream_hash or stream_hash in builder.secondary_stream_hashes

def test_finalize_hidden_loser_returns_through_inherited_blob_policy(tmp_path):
    builder=Builder(tmp_path);builder.scan();hidden=tmp_path/'document.bin';_write_zip(hidden,random.Random(102).randbytes(4096));item=_defer(hidden,'document.bin');result=finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1);row=next(r for r in builder.files if r[0]=='document.bin');assert result.storage=={};assert row[6][0]==S_BLOB;assert row[6][1]==sha(hidden.read_bytes());assert row[5]==item.candidate.digest;assert builder.canonical_deflate=={}

def test_finalize_spack_cannot_subsidize_hidden_and_loser_falls_back(tmp_path):
    payload=random.Random(103).randbytes(32*1024)
    for i in range(8):_write_zip(tmp_path/f'owner-{i}.zip',payload)
    builder=Builder(tmp_path);builder.scan();assert all(_storage(builder)[f'owner-{i}.zip'][0]==S_PACK for i in range(8));hidden=tmp_path/'document.bin';_write_zip(hidden,payload);item=_defer(hidden,'document.bin');result=finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1);assert result.storage=={};assert _storage(builder)['document.bin'][0]==S_BLOB;assert builder.canonical_deflate=={}

def test_finalize_refuses_source_drift_instead_of_pairing_old_metadata_with_new_bytes(tmp_path):
    builder=Builder(tmp_path);builder.scan();hidden=tmp_path/'document.bin';_write_zip(hidden,random.Random(104).randbytes(4096));item=_defer(hidden,'document.bin');replacement=tmp_path/'replacement.bin';_write_zip(replacement,random.Random(105).randbytes(4096));os.replace(replacement,hidden)
    with pytest.raises(RuntimeError,match='changed before ordinary fallback'):finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1)
    assert not any(row[0]=='document.bin' for row in builder.files)

def test_mutation_after_proof_before_snapshot_stage_is_rejected(tmp_path,monkeypatch):
    payload=random.Random(109).randbytes(32*1024);_write_zip(tmp_path/'owner.zip',payload);builder=Builder(tmp_path);builder.scan();hidden=tmp_path/'winner.bin';_write_zip(hidden,payload);item=_defer(hidden,'winner.bin');recipes_before=len(builder.recipes);cands_before=set(builder.cands);original_stage=hidden_api.stage_stable_hidden_cohort
    def mutate_then_stage(*args,**kwargs):
        replacement=tmp_path/'replacement.bin';_write_zip(replacement,random.Random(110).randbytes(32*1024));os.replace(replacement,hidden);return original_stage(*args,**kwargs)
    monkeypatch.setattr(hidden_api,'stage_stable_hidden_cohort',mutate_then_stage)
    with pytest.raises(RuntimeError,match='changed before ordinary fallback'):finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1)
    assert len(builder.recipes)==recipes_before;assert set(builder.cands)==cands_before;assert builder.canonical_deflate=={};assert not any(row[0]=='winner.bin' for row in builder.files)

def test_mutation_during_snapshot_recipe_construction_is_rejected_before_commit(tmp_path,monkeypatch):
    payload=random.Random(111).randbytes(32*1024);_write_zip(tmp_path/'owner.zip',payload);builder=Builder(tmp_path);builder.scan();hidden=tmp_path/'winner.bin';_write_zip(hidden,payload);item=_defer(hidden,'winner.bin');recipes_before=len(builder.recipes);cands_before=set(builder.cands);original=stage_api.stage_vzip_recipe_bytes
    def stage_then_mutate(*args,**kwargs):
        staged=original(*args,**kwargs);replacement=tmp_path/'replacement.bin';_write_zip(replacement,random.Random(112).randbytes(32*1024));os.replace(replacement,hidden);return staged
    monkeypatch.setattr(stage_api,'stage_vzip_recipe_bytes',stage_then_mutate)
    with pytest.raises(RuntimeError,match='changed before ordinary fallback'):finalize_deferred_hidden_files(builder,[item],min_verified_reuse=1)
    assert len(builder.recipes)==recipes_before;assert set(builder.cands)==cands_before;assert builder.canonical_deflate=={};assert not any(row[0]=='winner.bin' for row in builder.files)

def test_provisional_malformed_hidden_peers_are_excluded_before_commit(tmp_path):
    # Identical malformed hidden peers can provisionally match exact compressed bytes. Staging must
    # reject both, recompute ownership to empty, and preserve the original bytes through fallback.
    seed=tmp_path/'seed.zip';_write_zip(seed,random.Random(113).randbytes(32*1024));bad=_corrupt_payload_bytes(seed.read_bytes());seed.unlink();builder=Builder(tmp_path);builder.scan()
    a=tmp_path/'a.bin';b=tmp_path/'b.bin';a.write_bytes(bad);b.write_bytes(bad);ia=_defer(a,'a.bin');ib=_defer(b,'b.bin');recipes_before=len(builder.recipes);result=finalize_deferred_hidden_files(builder,[ia,ib],min_verified_reuse=1)
    assert result.storage=={};assert result.cohort.staged=={};assert result.cohort.realized==frozenset();assert len(builder.recipes)==recipes_before
    assert _storage(builder)['a.bin'][0]==S_BLOB and _storage(builder)['b.bin'][0]==S_BLOB;assert a.read_bytes()==bad and b.read_bytes()==bad

def test_late_loser_drift_aborts_before_prepared_winner_commit(tmp_path):
    payload=random.Random(106).randbytes(32*1024);_write_zip(tmp_path/'owner.zip',payload);builder=Builder(tmp_path);builder.scan();recipes_before=len(builder.recipes);cands_before=set(builder.cands);winner=tmp_path/'winner.bin';loser=tmp_path/'loser.bin';_write_zip(winner,payload);_write_zip(loser,random.Random(107).randbytes(4096));winner_item=_defer(winner,'winner.bin');loser_item=_defer(loser,'loser.bin');replacement=tmp_path/'replacement.bin';_write_zip(replacement,random.Random(108).randbytes(4096));os.replace(replacement,loser)
    with pytest.raises(RuntimeError,match='changed before ordinary fallback'):finalize_deferred_hidden_files(builder,[winner_item,loser_item],min_verified_reuse=1)
    assert len(builder.recipes)==recipes_before;assert set(builder.cands)==cands_before;assert builder.canonical_deflate=={};assert not any(row[0] in {'winner.bin','loser.bin'} for row in builder.files)
