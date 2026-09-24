from __future__ import annotations
import random,zipfile
from pathlib import Path
from cmpct.builder import Builder
from cmpct.codec import S_VZIP,sha
from cmpct.hidden_zip_candidates import ZipOwnerSource,prove_candidate_zip_ownership
import cmpct.hidden_zip_stage as stage_api
from cmpct.hidden_zip_stage import STAGE_SOURCE_PASSES,commit_stable_hidden_cohort,stage_stable_hidden_cohort

def _write_zip(path:Path,payload:bytes)->None:
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('payload.bin',payload)
def _noise(seed:int,size:int=32*1024)->bytes:return random.Random(seed).randbytes(size)
def test_stage_failure_cascades_and_discards_previously_staged_peer(tmp_path):
    payload=_noise(20);a=tmp_path/'a.bin';b=tmp_path/'b.bin';_write_zip(a,payload);_write_zip(b,payload);sources=[ZipOwnerSource('a.bin',a),ZipOwnerSource('b.bin',b)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);assert proof.realized==frozenset({'a.bin','b.bin'});b.unlink();cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1);assert cohort.realized==frozenset();assert cohort.staged=={};assert cohort.excluded==frozenset({'b.bin'});assert cohort.retained_candidate_bytes==0
def test_post_proof_replacement_is_rejected_before_recipe_staging(tmp_path):
    payload=_noise(23);explicit=tmp_path/'owner.zip';hidden=tmp_path/'hidden.bin';_write_zip(explicit,payload);_write_zip(hidden,payload);sources=[ZipOwnerSource('owner.zip',explicit,fixed=True),ZipOwnerSource('hidden.bin',hidden)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);assert 'hidden.bin' in proof.realized;hidden.write_bytes(b'PK\x03\x04'+b'hostile-replacement'*10000);cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1);assert cohort.realized==frozenset({'owner.zip'});assert cohort.excluded==frozenset({'hidden.bin'});assert cohort.staged=={};assert cohort.temporary_bytes_written==0
def test_staging_memory_refusal_becomes_owner_exclusion_before_commit(tmp_path):
    payload=_noise(21);explicit=tmp_path/'owner.zip';hidden=tmp_path/'hidden.bin';_write_zip(explicit,payload);_write_zip(hidden,payload);sources=[ZipOwnerSource('owner.zip',explicit,fixed=True),ZipOwnerSource('hidden.bin',hidden)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1,max_staged_candidate_bytes=1);assert cohort.realized==frozenset({'owner.zip'});assert cohort.staged=={};assert cohort.excluded==frozenset({'hidden.bin'});assert cohort.retained_candidate_bytes==0
def test_stage_io_budget_covers_source_snapshot_write_and_private_parser_reads(tmp_path):
    payload=_noise(25);explicit=tmp_path/'owner.zip';hidden=tmp_path/'hidden.bin';_write_zip(explicit,payload);_write_zip(hidden,payload);sources=[ZipOwnerSource('owner.zip',explicit,fixed=True),ZipOwnerSource('hidden.bin',hidden)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);physical=hidden.stat().st_size;cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1,max_stage_source_bytes=physical*(STAGE_SOURCE_PASSES-1));assert cohort.realized==frozenset({'owner.zip'});assert cohort.excluded==frozenset({'hidden.bin'});assert cohort.staged=={};assert cohort.source_bytes_read==0;assert cohort.temporary_bytes_written==0;assert cohort.temporary_bytes_read==0
def test_successful_staging_uses_content_bound_private_snapshot_with_explicit_io_account(tmp_path):
    payload=_noise(22,8*1024);explicit=tmp_path/'owner.zip';hidden=tmp_path/'hidden.bin';_write_zip(explicit,payload);_write_zip(hidden,payload);sources=[ZipOwnerSource('owner.zip',explicit,fixed=True),ZipOwnerSource('hidden.bin',hidden)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);ceiling=64*1024;physical=hidden.stat().st_size;cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1,max_staged_candidate_bytes=ceiling);assert cohort.realized==frozenset({'owner.zip','hidden.bin'});assert set(cohort.staged)=={'hidden.bin'};assert 0<cohort.retained_candidate_bytes<=ceiling;assert cohort.source_bytes_read==physical*2;assert cohort.temporary_bytes_written==physical;assert cohort.temporary_bytes_read==physical*3
def test_failed_final_rebind_cannot_seed_cross_winner_decode_cache(tmp_path,monkeypatch):
    payload=_noise(26,64*1024);a=tmp_path/'a.bin';b=tmp_path/'b.bin';_write_zip(a,payload);_write_zip(b,payload);sources=[ZipOwnerSource('a.bin',a),ZipOwnerSource('b.bin',b)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);snapshots={'a.bin':a.read_bytes(),'b.bin':b.read_bytes()};real_rebind=stage_api._revalidate_proven_source;real_read=zipfile.ZipFile.read;reads=0
    def selective_rebind(source,proof_arg):
        if source.rel=='a.bin':return False,0
        return real_rebind(source,proof_arg)
    def counted_read(self,*args,**kwargs):
        nonlocal reads;reads+=1;return real_read(self,*args,**kwargs)
    monkeypatch.setattr(stage_api,'_revalidate_proven_source',selective_rebind);monkeypatch.setattr(zipfile.ZipFile,'read',counted_read);cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1,source_snapshots=snapshots)
    assert reads==2;assert 'a.bin' in cohort.excluded;assert cohort.realized==frozenset();assert cohort.staged=={}
def test_staging_does_not_mutate_builder_until_explicit_commit(tmp_path):
    payload=_noise(24);a=tmp_path/'a.bin';b=tmp_path/'b.bin';_write_zip(a,payload);_write_zip(b,payload);sources=[ZipOwnerSource('a.bin',a),ZipOwnerSource('b.bin',b)];proof=prove_candidate_zip_ownership(sources,min_verified_reuse=1);cohort=stage_stable_hidden_cohort(proof,sources,min_verified_reuse=1);builder=Builder(tmp_path);assert builder.cands=={};assert builder.recipes==[];storage=commit_stable_hidden_cohort(builder,cohort);assert set(storage)=={'a.bin','b.bin'};assert all(value[0]==S_VZIP for value in storage.values());assert len(builder.recipes)==2;assert builder.cands
