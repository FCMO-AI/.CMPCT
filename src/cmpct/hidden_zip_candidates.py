from __future__ import annotations
"""Candidate-scoped proof for hidden-ZIP reuse ownership."""
from collections import Counter
from dataclasses import dataclass
import hashlib,io,struct,zipfile
from pathlib import Path
from .hidden_zip import MAX_CANDIDATE_LOGICAL_BYTES,MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES,MAX_OBSERVATION_DESCRIPTORS,MAX_OBSERVATION_FILES,MAX_OBSERVATION_IO_BYTES,MAX_OBSERVATION_LOGICAL_BYTES,MIN_VERIFIED_REUSE,_file_sha256_expected,_metadata_descriptors,_stamp,_verify_candidate,hidden_zip_preflight
from .reuse_ownership import Identity,realized_reuse_fixed_point
Stamp=tuple[int,int,int,int]
@dataclass(frozen=True)
class ZipOwnerSource:rel:str;path:Path;fixed:bool=False;expected_stamp:Stamp|None=None;expected_digest:bytes|None=None
@dataclass(frozen=True)
class CandidateOwnershipProof:realized:frozenset[str];credit:dict[str,int];owner_identities:dict[str,frozenset[Identity]];source_states:dict[str,tuple[Stamp,bytes]];io_bytes:int;logical_bytes:int;rejects:tuple[tuple[str,int],...]
def _budget_refusal(reason,observed,io_bytes=0,logical_bytes=0):return CandidateOwnershipProof(frozenset(),{},{},{},int(io_bytes),int(logical_bytes),((reason,int(observed)),))
def _snapshot_hint_identities(raw,hints):
    identities=set()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                if info.is_dir():continue
                d=(int(info.compress_type),int(info.compress_size),int(info.file_size),int(info.CRC))
                if d not in hints:continue
                off=int(info.header_offset)
                if off<0 or off+30>len(raw) or raw[off:off+4]!=b'PK\x03\x04':return None
                nl,xl=struct.unpack_from('<HH',raw,off+26);start=off+30+nl+xl;end=start+int(info.compress_size)
                if end>len(raw):return None
                identities.add((d[0],d[1],hashlib.sha256(raw[start:end]).digest()))
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,struct.error):return None
    return frozenset(identities)
def _path_hint_identities(path,hints,max_read):
    identities=set();read=0
    try:
        with zipfile.ZipFile(path) as z,Path(path).open('rb') as f:
            for info in z.infolist():
                if info.is_dir():continue
                d=(int(info.compress_type),int(info.compress_size),int(info.file_size),int(info.CRC))
                if d not in hints:continue
                off=int(info.header_offset);f.seek(off);header=f.read(30);read+=len(header)
                if len(header)!=30 or header[:4]!=b'PK\x03\x04':return None,read,'validation_rejected'
                nl,xl=struct.unpack_from('<HH',header,26);need=int(nl)+int(xl)+int(info.compress_size)
                if read+need>int(max_read):return None,read,'io_budget'
                f.seek(nl+xl,1);payload=f.read(int(info.compress_size));read+=need
                if len(payload)!=int(info.compress_size):return None,read,'validation_rejected'
                identities.add((d[0],d[1],hashlib.sha256(payload).digest()))
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,struct.error):return None,read,'validation_rejected'
    return frozenset(identities),read,None
def prove_candidate_zip_ownership(sources,*,min_verified_reuse=MIN_VERIFIED_REUSE,max_io_bytes=MAX_OBSERVATION_IO_BYTES,max_logical_bytes=MAX_OBSERVATION_LOGICAL_BYTES,max_candidate_logical_bytes=MAX_CANDIDATE_LOGICAL_BYTES,max_sources=MAX_OBSERVATION_FILES,max_descriptors=MAX_OBSERVATION_DESCRIPTORS,max_central_directory_bytes=MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES,excluded_owners=frozenset(),source_snapshots=None):
    if len(sources)>int(max_sources):return _budget_refusal('source_budget',len(sources))
    sources=tuple(sources);source_snapshots=source_snapshots or {}
    if len({s.rel for s in sources})!=len(sources):raise ValueError('candidate owner rel paths must be unique')
    rejects=Counter();physical={};source_physical={}
    for s in sources:
        try:st=s.path.stat();stamp=_stamp(st);key=(int(st.st_dev),int(st.st_ino))
        except OSError:rejects['source_changed']+=1;continue
        if s.expected_stamp is not None and stamp!=s.expected_stamp:rejects['source_changed']+=1;continue
        source_physical[s.rel]=key;physical.setdefault(key,[]).append(s.rel)
    aliased={r for rs in physical.values() if len(rs)>1 for r in rs};parsed=[];owners=Counter();io_used=logical_used=declared_used=descriptor_used=cd_used=0
    for s in sources:
        if s.rel not in source_physical:continue
        if s.rel in aliased:rejects['physical_alias']+=1;continue
        pf=hidden_zip_preflight(s.path,max_read_bytes=max(0,int(max_io_bytes)-io_used));io_used+=pf.head_bytes_read+pf.tail_bytes_read
        if not pf.eligible:rejects[pf.reason]+=1;continue
        cd_used+=pf.central_directory_size
        if cd_used>int(max_central_directory_bytes):return _budget_refusal('central_directory_budget',cd_used,io_used,logical_used)
        pc=pf.tail_bytes_read+pf.central_directory_size
        if io_used+pc>int(max_io_bytes):rejects['io_budget']+=1;continue
        io_used+=pc;descriptors,entries,declared,reason=_metadata_descriptors(s.path)
        if descriptors is None:rejects[reason or 'exact_parse_rejected']+=1;continue
        descriptor_used+=entries
        if descriptor_used>int(max_descriptors):return _budget_refusal('descriptor_budget',descriptor_used,io_used,logical_used)
        if declared>int(max_candidate_logical_bytes) or declared_used+declared>int(max_logical_bytes):rejects['logical_work_budget']+=1;continue
        declared_used+=declared;parsed.append((s,set(descriptors),pc));owners.update(descriptors)
    repeated={d for d,n in owners.items() if n>=2};ids={};states={};accepted={}
    for s,descriptors,pc in parsed:
        hints=descriptors&repeated
        if not hints:ids[s.rel]=frozenset();accepted[s.rel]=s;continue
        try:st=s.path.stat();stamp=_stamp(st);size=int(st.st_size)
        except OSError:rejects['source_changed']+=1;continue
        if s.expected_stamp is not None and stamp!=s.expected_stamp:rejects['source_changed']+=1;continue
        if (int(st.st_dev),int(st.st_ino))!=source_physical[s.rel]:rejects['source_changed']+=1;continue
        snap=source_snapshots.get(s.rel) if not s.fixed else None
        if snap is not None:
            if len(snap)!=size or s.expected_digest is None or hashlib.sha256(snap).digest()!=s.expected_digest:rejects['source_changed']+=1;continue
            exact=_snapshot_hint_identities(snap,hints)
            if exact is None:rejects['validation_rejected']+=1;continue
            ids[s.rel]=exact;states[s.rel]=(stamp,s.expected_digest);accepted[s.rel]=s;continue
        if not s.fixed and s.expected_digest is not None:
            # ZipFile reparses the central directory here, so charge that parser pass before reading
            # hinted local headers/payloads. The helper then owns a strict residual I/O budget.
            if io_used+pc>int(max_io_bytes):rejects['io_budget']+=1;continue
            io_used+=pc;exact,read,reason=_path_hint_identities(s.path,hints,int(max_io_bytes)-io_used);io_used+=read
            if exact is None:rejects[reason or 'validation_rejected']+=1;continue
            ids[s.rel]=exact;states[s.rel]=(stamp,s.expected_digest);accepted[s.rel]=s;continue
        if io_used+size+pc>int(max_io_bytes):rejects['io_budget']+=1;continue
        before=_file_sha256_expected(s.path,stamp)
        if before is None or (s.expected_digest is not None and before!=s.expected_digest):rejects['source_changed']+=1;continue
        io_used+=size+pc;verified,read,logical,reason=_verify_candidate(s.path,hints,int(max_io_bytes)-io_used,int(max_logical_bytes)-logical_used);io_used+=read;logical_used+=logical
        if verified is None:rejects[reason or 'validation_rejected']+=1;continue
        if io_used+size>int(max_io_bytes):rejects['io_budget']+=1;continue
        after=_file_sha256_expected(s.path,stamp);io_used+=size
        if after is None or after!=before:rejects['source_changed']+=1;continue
        ids[s.rel]=frozenset(i for group in verified.values() for i in group);states[s.rel]=(stamp,after);accepted[s.rel]=s
    fixed={r for r,s in accepted.items() if s.fixed};hidden=set(accepted)-fixed;excluded=set(excluded_owners)&hidden
    realized,credit=realized_reuse_fixed_point(ids,hidden_owners=hidden,fixed_owners=fixed,excluded_owners=excluded,min_verified_reuse=int(min_verified_reuse))
    return CandidateOwnershipProof(realized,credit,ids,states,int(io_used),int(logical_used),tuple(sorted(rejects.items())))
