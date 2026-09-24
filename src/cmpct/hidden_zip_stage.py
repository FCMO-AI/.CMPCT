from __future__ import annotations
"""Transactional cohort staging after candidate-scoped hidden-ZIP ownership proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib,os,struct,tempfile,zipfile
from pathlib import Path
from .codec import S_VZIP,sha
from .hidden_zip import _stamp
from .hidden_zip_candidates import CandidateOwnershipProof,ZipOwnerSource
from .reuse_ownership import realized_reuse_fixed_point
from .vzip_transaction import StagedVzipRecipe,commit_staged_vzip_prehashed,stage_vzip_recipe,stage_vzip_recipe_bytes
MAX_STAGED_CANDIDATE_BYTES=256*1024*1024;MAX_STAGE_SOURCE_BYTES=256*1024*1024;SNAPSHOT_CHUNK=1024*1024;STAGE_SOURCE_PASSES=5
MAX_PARALLEL_STAGE_WORKERS=4
STAGE_REJECTS=(OSError,ValueError,RuntimeError,struct.error,zipfile.BadZipFile)
@dataclass(frozen=True)
class StagedHiddenCohort:
    realized:frozenset[str];credit:dict[str,int];staged:dict[str,StagedVzipRecipe];excluded:frozenset[str];retained_candidate_bytes:int;source_bytes_read:int;temporary_bytes_written:int=0;temporary_bytes_read:int=0
def _retained_bytes(staged):return sum(len(raw)+(0 if stream is None else len(stream)) for raw,_hint,stream,_ref in staged.candidates)
def _revalidate_proven_source(source,proof):
    state=proof.source_states.get(source.rel)
    if state is None:return False,0
    expected_stamp,expected_digest=state;expected_size=int(expected_stamp[2]);digest=hashlib.sha256();read=0
    try:
        with source.path.open('rb') as src:
            if _stamp(os.fstat(src.fileno()))!=expected_stamp:return False,0
            while read<expected_size:
                block=src.read(min(SNAPSHOT_CHUNK,expected_size-read))
                if not block:return False,read
                digest.update(block);read+=len(block)
            if src.read(1):return False,read
            if _stamp(os.fstat(src.fileno()))!=expected_stamp:return False,read
    except OSError:return False,read
    return read==expected_size and digest.digest()==expected_digest,read
def _snapshot_proven_source(source,proof,destination):
    state=proof.source_states.get(source.rel)
    if state is None:return False,0
    expected_stamp,expected_digest=state;expected_size=int(expected_stamp[2]);digest=hashlib.sha256();read=0
    try:
        with source.path.open('rb') as src,destination.open('wb') as dst:
            if _stamp(os.fstat(src.fileno()))!=expected_stamp:return False,0
            while read<expected_size:
                block=src.read(min(SNAPSHOT_CHUNK,expected_size-read))
                if not block:return False,read
                dst.write(block);digest.update(block);read+=len(block)
            if src.read(1):return False,read
            if _stamp(os.fstat(src.fileno()))!=expected_stamp:return False,read
            dst.flush()
        if read!=expected_size or digest.digest()!=expected_digest:return False,read
        if int(destination.stat().st_size)!=expected_size:return False,read
    except OSError:return False,read
    return True,read
def _parallel_snapshot_stage(rel,source,state,snapshot,proof,max_retained_bytes):
    """Stage one immutable snapshot privately; Builder mutation remains serial after collection."""
    physical_size=int(state[0][2])
    if len(snapshot)!=physical_size or sha(snapshot)!=state[1]:return rel,None,0
    try:candidate=stage_vzip_recipe_bytes(snapshot,max_retained_bytes=max_retained_bytes,exact_stream_retention=True,validated_deflates={})
    except STAGE_REJECTS:candidate=None
    if candidate is None:return rel,None,0
    current,read=_revalidate_proven_source(source,proof)
    return rel,(candidate if current else None),read
def stage_stable_hidden_cohort(proof,sources,*,min_verified_reuse,max_staged_candidate_bytes=MAX_STAGED_CANDIDATE_BYTES,max_stage_source_bytes=MAX_STAGE_SOURCE_BYTES,source_snapshots=None):
    sources=tuple(sources);source_by_rel={s.rel:s for s in sources};source_snapshots=source_snapshots or {}
    if len(source_by_rel)!=len(sources):raise ValueError('candidate owner rel paths must be unique')
    fixed={rel for rel,s in source_by_rel.items() if s.fixed and rel in proof.owner_identities};hidden=set(proof.owner_identities)-fixed;initial=set(proof.realized)&hidden
    staged={};excluded=set();retained=source_read=temp_written=temp_read=0
    # Parallelism is admitted only when every provisional winner has an immutable Builder snapshot.
    # Give every worker a deterministic disjoint share of the aggregate retained-memory budget; unlike
    # a physical-size heuristic this remains safe for highly compressible/hostile ZIP members whose
    # decoded material can be much larger than the container. Anything outside the envelope falls back.
    parallel_rows=[]
    for rel in sorted(initial):
        source=source_by_rel.get(rel);state=proof.source_states.get(rel);snapshot=source_snapshots.get(rel)
        if source is None or state is None or snapshot is None:parallel_rows=[];break
        parallel_rows.append((rel,source,state,snapshot))
    physical_total=sum(int(r[2][0][2]) for r in parallel_rows)
    per_candidate_reservation=(int(max_staged_candidate_bytes)//len(parallel_rows)) if parallel_rows else 0
    parallel_ok=bool(parallel_rows) and per_candidate_reservation>0 and physical_total<=int(max_stage_source_bytes)
    if parallel_ok:
        workers=min(MAX_PARALLEL_STAGE_WORKERS,len(parallel_rows))
        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix='cmpct-hidden-stage') as pool:
            futures=[pool.submit(_parallel_snapshot_stage,rel,source,state,snapshot,proof,per_candidate_reservation) for rel,source,state,snapshot in parallel_rows]
            results=[f.result() for f in futures]
        # Collection and all Builder mutation are deterministic/serial. The disjoint worker budgets sum
        # to <= max_staged_candidate_bytes, so aggregate retained material is bounded even while workers overlap.
        for rel,candidate,read in sorted(results,key=lambda x:x[0]):
            source_read+=int(read)
            if candidate is None:excluded.add(rel);continue
            cost=_retained_bytes(candidate)
            if retained+cost>int(max_staged_candidate_bytes):excluded.add(rel);continue
            staged[rel]=candidate;retained+=cost
    else:
        # Cache only decodes from candidates that survived authoritative ZIP CRC/length validation *and*
        # the final live digest rebind. Serial fallback retains the previously proven cross-winner cache.
        validated_deflates={}
        for rel in sorted(initial):
            source=source_by_rel.get(rel);state=proof.source_states.get(rel)
            if source is None or state is None:excluded.add(rel);continue
            physical_size=int(state[0][2]);remaining=int(max_staged_candidate_bytes)-retained;candidate=None;snapshot=source_snapshots.get(rel);candidate_cache=dict(validated_deflates)
            if snapshot is not None:
                if len(snapshot)!=physical_size or sha(snapshot)!=state[1]:excluded.add(rel);continue
                if physical_size>int(max_stage_source_bytes)-(source_read+temp_written+temp_read):excluded.add(rel);continue
                try:candidate=stage_vzip_recipe_bytes(snapshot,max_retained_bytes=max(0,remaining),exact_stream_retention=True,validated_deflates=candidate_cache)
                except STAGE_REJECTS:candidate=None
                if candidate is not None:
                    current,read=_revalidate_proven_source(source,proof);source_read+=read
                    if not current:candidate=None
            else:
                required=physical_size*(STAGE_SOURCE_PASSES+1)
                if required>int(max_stage_source_bytes)-(source_read+temp_written+temp_read):excluded.add(rel);continue
                try:
                    with tempfile.TemporaryDirectory(prefix='cmpct-hidden-vzip-') as td:
                        private=Path(td)/'candidate.zip';current,read=_snapshot_proven_source(source,proof,private);source_read+=read
                        if not current:excluded.add(rel);continue
                        temp_written+=physical_size
                        try:candidate=stage_vzip_recipe(private,max_retained_bytes=max(0,remaining),exact_stream_retention=True,validated_deflates=candidate_cache)
                        except STAGE_REJECTS:candidate=None
                        temp_read+=physical_size*3
                        if candidate is not None:
                            current,read=_revalidate_proven_source(source,proof);source_read+=read
                            if not current:candidate=None
                except OSError:candidate=None
            if candidate is None:excluded.add(rel);continue
            cost=_retained_bytes(candidate)
            if cost>remaining:excluded.add(rel);continue
            staged[rel]=candidate;retained+=cost;validated_deflates=candidate_cache
    realized,credit=realized_reuse_fixed_point(proof.owner_identities,hidden_owners=hidden,fixed_owners=fixed,excluded_owners=excluded,min_verified_reuse=int(min_verified_reuse))
    stable=set(realized)&hidden;staged={rel:r for rel,r in staged.items() if rel in stable};retained=sum(_retained_bytes(r) for r in staged.values())
    return StagedHiddenCohort(frozenset(realized),credit,staged,frozenset(excluded),int(retained),int(source_read),int(temp_written),int(temp_read))
def commit_stable_hidden_cohort(builder,cohort):
    storage={}
    for rel in sorted(cohort.staged):
        recipe=commit_staged_vzip_prehashed(cohort.staged[rel],builder);rid=len(builder.recipes);builder.recipes.append(recipe);storage[rel]=[S_VZIP,rid]
    return storage
