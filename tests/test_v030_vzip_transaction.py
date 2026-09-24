from __future__ import annotations
import zipfile
from cmpct.codec import sha
import cmpct.vzip_transaction as tx

def test_failed_recipe_discards_all_staged_candidate_mutations(monkeypatch,tmp_path):
    calls=[]
    def fake_recipe(_path,add_content):add_content(b'first-member','.bin',b'exact-deflate');return None
    def real_add(*args):calls.append(args);return sha(args[0])
    monkeypatch.setattr(tx,'make_vzip_recipe',fake_recipe);assert tx.make_vzip_recipe_transactional(tmp_path/'candidate.bin',real_add) is None;assert calls==[]
def test_successful_recipe_replays_staged_mutations_after_commit_point(monkeypatch,tmp_path):
    calls=[];expected=[b'first',b'second']
    def fake_recipe(_path,add_content):return [[add_content(expected[0],'.a'),add_content(expected[1],'.b',b'stream')]]
    def real_add(raw,hint='',deflate_stream=None):calls.append((raw,hint,deflate_stream));return sha(raw)
    monkeypatch.setattr(tx,'make_vzip_recipe',fake_recipe);recipe=tx.make_vzip_recipe_transactional(tmp_path/'candidate.bin',real_add);assert recipe==[[sha(expected[0]),sha(expected[1])]];assert calls==[(b'first','.a',None),(b'second','.b',b'stream')]
def test_cohort_can_stage_every_recipe_before_any_real_mutation(monkeypatch,tmp_path):
    real_calls=[]
    def fake_recipe(path,add_content):add_content(path.name.encode(),'.bin');return None if path.name=='bad.bin' else [path.name]
    def real_add(raw,hint='',deflate_stream=None):real_calls.append((raw,hint,deflate_stream));return sha(raw)
    monkeypatch.setattr(tx,'make_vzip_recipe',fake_recipe);good=tx.stage_vzip_recipe(tmp_path/'good.bin');bad=tx.stage_vzip_recipe(tmp_path/'bad.bin');assert good is not None and bad is None;assert real_calls==[];assert good.candidates[0][0]==b'good.bin'
def test_stage_peak_budget_rejects_before_recipe_materialization(monkeypatch,tmp_path):
    path=tmp_path/'candidate.bin';payload=b'A'*(2*1024*1024)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('large.bin',payload)
    called=False
    def forbidden_recipe(_path,_add_content):
        nonlocal called;called=True;raise AssertionError('recipe construction must not run after pre-allocation refusal')
    monkeypatch.setattr(tx,'make_vzip_recipe',forbidden_recipe);assert tx.stage_vzip_recipe(path,max_retained_bytes=1024*1024) is None;assert called is False
def test_stage_peak_bound_covers_original_skeleton_copies_streams_and_decoded_bytes(tmp_path):
    path=tmp_path/'candidate.bin';payload=b'bounded-retention-'*4096
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('payload.bin',payload)
    bound=tx._staging_peak_upper_bound(path);assert bound==path.stat().st_size*4+len(payload);staged=tx.stage_vzip_recipe(path,max_retained_bytes=bound);assert staged is not None
    final_retained=sum(len(raw)+(0 if stream is None else len(stream)) for raw,_hint,stream,_ref in staged.candidates);assert final_retained<=path.stat().st_size+len(payload)
def test_exact_retained_staging_records_stream_without_level_search(monkeypatch,tmp_path):
    path=tmp_path/'candidate.bin';payload=b'repeatable-member-'*4096
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr('payload.bin',payload)
    def forbidden_generic(*_args,**_kwargs):raise AssertionError('exact-retained path must not call generic level-search recipe')
    monkeypatch.setattr(tx,'make_vzip_recipe',forbidden_generic);staged=tx.stage_vzip_recipe(path,exact_stream_retention=True);assert staged is not None;deflated=[row for row in staged.recipe[2] if row[1]==zipfile.ZIP_DEFLATED];assert deflated and all(row[4]==0 for row in deflated);assert any(stream is not None for _raw,_hint,stream,_ref in staged.candidates)
def test_in_memory_exact_staging_is_recipe_equivalent_and_keeps_peak_bound(tmp_path):
    path=tmp_path/'candidate.zip';payload=b'in-memory-owner-boundary-'*4096
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload.bin',payload);z.writestr('stored.txt',b'identity',compress_type=zipfile.ZIP_STORED)
    raw=path.read_bytes();bound=len(raw)*4+len(payload)+len(b'identity');by_path=tx.stage_vzip_recipe(path,max_retained_bytes=bound,exact_stream_retention=True);by_bytes=tx.stage_vzip_recipe_bytes(raw,max_retained_bytes=bound,exact_stream_retention=True);assert by_path is not None and by_bytes is not None;assert by_bytes.recipe==by_path.recipe;assert by_bytes.candidates==by_path.candidates;assert tx.stage_vzip_recipe_bytes(raw,max_retained_bytes=bound-1,exact_stream_retention=True) is None
def test_validated_exact_stream_cache_skips_second_deflate_decode(monkeypatch,tmp_path):
    path=tmp_path/'candidate.zip';payload=b'validated-stream-cache-'*8192
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload.bin',payload)
    raw=path.read_bytes();cache={};first=tx.stage_vzip_recipe_bytes(raw,validated_deflates=cache);assert first is not None and cache
    def forbidden_read(*_args,**_kwargs):raise AssertionError('identical validated Deflate stream must reuse prior decoded bytes')
    monkeypatch.setattr(zipfile.ZipFile,'read',forbidden_read);second=tx.stage_vzip_recipe_bytes(raw,validated_deflates=dict(cache));assert second is not None;assert second.recipe==first.recipe;assert second.candidates==first.candidates
def test_native_validation_receives_existing_cohort_cache(monkeypatch,tmp_path):
    import cmpct.native_hidden_zip_batch as native
    path=tmp_path/'candidate.zip';payload=b'native-cohort-cache-'*4096
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload.bin',payload)
    raw=path.read_bytes();cache={b'existing-key':b'existing-raw'};seen=[]
    def fake_native(candidate,known):seen.append((candidate,known));return {}
    monkeypatch.setattr(native,'native_validated_deflates',fake_native);staged=tx.stage_vzip_recipe_bytes(raw,validated_deflates=cache)
    assert staged is not None;assert seen and seen[0][0]==raw and seen[0][1] is cache;assert cache[b'existing-key']==b'existing-raw'
def test_prehashed_commit_reuses_staged_identity_without_rehashing_decoded_member(monkeypatch):
    from types import SimpleNamespace
    raw=b'already-verified-decoded-member';expected=sha(raw);staged=tx.StagedVzipRecipe(['recipe'],((raw,'.bin',None,expected),));builder=SimpleNamespace(cands={});real_sha=tx.sha
    def forbid_raw_rehash(data):
        if data is raw:raise AssertionError('commit must reuse the identity staging already computed')
        return real_sha(data)
    monkeypatch.setattr(tx,'sha',forbid_raw_rehash);assert tx.commit_staged_vzip_prehashed(staged,builder)==['recipe'];assert builder.cands[expected].raw==raw;assert builder.cands[expected].hints=={'.bin'}
def test_prehashed_commit_preserves_deflate_variant_accounting():
    from types import SimpleNamespace
    raw=b'decoded';stream=b'exact-rfc1951';expected=sha(raw);stream_hash=sha(stream);staged=tx.StagedVzipRecipe(['recipe'],((raw,'.bin',stream,expected),(raw,'.bin',stream,expected)));builder=SimpleNamespace(cands={});tx.commit_staged_vzip_prehashed(staged,builder);candidate=builder.cands[expected];assert candidate.raw==raw and candidate.deflates[stream_hash]==[stream,2]
