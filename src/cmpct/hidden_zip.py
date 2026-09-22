from __future__ import annotations

"""Bounded, fail-closed discovery for optional hidden-ZIP virtualization."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib, os, stat, struct, zipfile
from .codec import _compressed_payload

LOCAL_SIG=b"PK\x03\x04";EOCD_SIG=b"PK\x05\x06";EOCD_MIN=22;MAX_COMMENT=65535;MAX_TAIL=EOCD_MIN+MAX_COMMENT
MAX_ENTRIES=8192;MAX_CENTRAL_DIRECTORY=16*1024*1024;MAX_CANDIDATE_LOGICAL_BYTES=256*1024*1024
MAX_OBSERVATION_FILES=262144;MAX_OBSERVATION_DESCRIPTORS=131072;MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES=256*1024*1024;MAX_OBSERVATION_IO_BYTES=512*1024*1024
ZIP64_U16=0xFFFF;ZIP64_U32=0xFFFFFFFF
SUPPORTED_METHODS=frozenset((zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED));EXPLICIT_SUFFIXES=frozenset((".zip",".whl"));MIN_VERIFIED_REUSE=2176

class _ObservationFileBudget(Exception):pass
@dataclass(frozen=True)
class HiddenZipPreflight:
    eligible:bool;reason:str;file_size:int;head_bytes_read:int;tail_bytes_read:int
    entries:int=0;central_directory_size:int=0;central_directory_offset:int=0;eocd_offset:int=0
@dataclass(frozen=True)
class HiddenZipAdmission:
    rel:str;stamp:tuple[int,int,int,int];verified_reuse_bytes:int;content_sha256:bytes
@dataclass(frozen=True)
class HiddenZipEvidenceState:
    rel:str;stamp:tuple[int,int,int,int];content_sha256:bytes
@dataclass(frozen=True)
class HiddenZipObservation:
    admitted:tuple[HiddenZipAdmission,...];files_observed:int;candidates_parsed:int;head_bytes_read:int;tail_bytes_read:int;verification_bytes_read:int;rejects:tuple[tuple[str,int],...]
    evidence:tuple[HiddenZipEvidenceState,...]=();parser_bytes_read:int=0

def _file_sha256(path:Path)->bytes:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.digest()

def _state_current(root:Path,rel:str,stamp:tuple[int,int,int,int],digest:bytes)->bool:
    path=Path(root)/rel
    try:
        st=os.stat(path,follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode):return False
        current=(int(st.st_dev),int(st.st_ino),int(st.st_size),int(st.st_mtime_ns))
        return current==stamp and _file_sha256(path)==digest
    except OSError:return False

def hidden_zip_preflight(path:Path,*,max_read_bytes:int|None=None)->HiddenZipPreflight:
    path=Path(path);head_read=0
    try:
        size=path.stat().st_size
        if size<EOCD_MIN:return HiddenZipPreflight(False,'too_small',size,0,0)
        if max_read_bytes is not None and int(max_read_bytes)<4:return HiddenZipPreflight(False,'io_budget',size,0,0)
        with path.open('rb') as f:
            head=f.read(4);head_read=len(head)
            if head!=LOCAL_SIG:return HiddenZipPreflight(False,'local_signature_miss',size,head_read,0)
            tail_n=min(size,MAX_TAIL)
            if max_read_bytes is not None and head_read+tail_n>int(max_read_bytes):return HiddenZipPreflight(False,'io_budget',size,head_read,0)
            f.seek(size-tail_n);tail=f.read(tail_n)
        pos=len(tail)
        while True:
            idx=tail.rfind(EOCD_SIG,0,pos)
            if idx<0:return HiddenZipPreflight(False,'eocd_not_found',size,head_read,len(tail))
            if idx+EOCD_MIN<=len(tail):
                disk,cd_disk,n_disk,n_total,cd_size,cd_off,comment_len=struct.unpack_from('<HHHHIIH',tail,idx+4)
                if idx+EOCD_MIN+comment_len==len(tail):break
            pos=idx
        absolute=size-tail_n+idx
        if disk!=0 or cd_disk!=0 or n_disk!=n_total:return HiddenZipPreflight(False,'multi_disk',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
        if n_total==ZIP64_U16 or cd_size==ZIP64_U32 or cd_off==ZIP64_U32:return HiddenZipPreflight(False,'zip64_optional_path_rejected',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
        if n_total==0:return HiddenZipPreflight(False,'empty_archive',size,head_read,len(tail),0,cd_size,cd_off,absolute)
        if n_total>MAX_ENTRIES:return HiddenZipPreflight(False,'entry_budget',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
        if cd_size>MAX_CENTRAL_DIRECTORY:return HiddenZipPreflight(False,'central_directory_budget',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
        if cd_off>absolute or cd_size>absolute-cd_off:return HiddenZipPreflight(False,'central_directory_bounds',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
        return HiddenZipPreflight(True,'eligible',size,head_read,len(tail),n_total,cd_size,cd_off,absolute)
    except (OSError,struct.error,ValueError):
        try:size=os.path.getsize(path)
        except OSError:size=0
        return HiddenZipPreflight(False,'io_or_structure_error',size,head_read,0)

def _physical_observation_files(root:Path,max_entries:int):
    seen:set[tuple[int,int]]=set();visited=0
    def walk(absdir:Path,prefix:str=''):
        nonlocal visited
        entries=[]
        with os.scandir(absdir) as it:
            for e in it:
                visited+=1
                if visited>int(max_entries):raise _ObservationFileBudget
                entries.append(e)
        entries.sort(key=lambda e:e.name)
        for e in entries:
            rel=f'{prefix}/{e.name}' if prefix else e.name;st=e.stat(follow_symlinks=False)
            if stat.S_ISDIR(st.st_mode):yield from walk(Path(e.path),rel);continue
            if not stat.S_ISREG(st.st_mode):continue
            ik=(int(st.st_dev),int(st.st_ino))
            if st.st_nlink>1:
                if ik in seen:continue
                seen.add(ik)
            yield Path(e.path),rel,(ik[0],ik[1],int(st.st_size),int(st.st_mtime_ns)),Path(e.name).suffix.lower() in EXPLICIT_SUFFIXES
    yield from walk(Path(root))

def _metadata_descriptors(path:Path):
    try:
        with zipfile.ZipFile(path) as z:
            infos=[i for i in z.infolist() if not i.is_dir()]
            if not infos:return None,0,0,'empty_members'
            logical=sum(max(0,int(i.file_size)) for i in infos)
            if any(i.flag_bits&1 for i in infos):return None,len(infos),logical,'encrypted'
            if any(i.compress_type not in SUPPORTED_METHODS for i in infos):return None,len(infos),logical,'unsupported_method'
            descriptors={(int(i.compress_type),int(i.compress_size),int(i.file_size),int(i.CRC)) for i in infos if i.file_size>0}
            if not descriptors:return None,len(infos),logical,'no_payload_members'
            return descriptors,len(infos),logical,None
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,struct.error):return None,0,0,'exact_parse_rejected'

def _verify_streams(path:Path,descriptors:set[tuple[int,int,int,int]],max_bytes:int):
    identities={d:set() for d in descriptors};read=0
    try:
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                descriptor=(int(info.compress_type),int(info.compress_size),int(info.file_size),int(info.CRC))
                if info.is_dir() or descriptor not in descriptors:continue
                compressed_size=descriptor[1]
                if read+compressed_size>int(max_bytes):return None,read,True
                payload=_compressed_payload(path,info);read+=len(payload)
                if len(payload)!=compressed_size:return None,read,False
                identities[descriptor].add((descriptor[0],compressed_size,hashlib.sha256(payload).digest()))
        return {d:v for d,v in identities.items() if v},read,False
    except (OSError,ValueError,zipfile.BadZipFile,RuntimeError,struct.error):return None,read,False

def observe_hidden_zip_admission(root:Path,*,min_verified_reuse:int=MIN_VERIFIED_REUSE,max_observation_files:int=MAX_OBSERVATION_FILES,max_observation_descriptors:int=MAX_OBSERVATION_DESCRIPTORS,max_observation_central_directory_bytes:int=MAX_OBSERVATION_CENTRAL_DIRECTORY_BYTES,max_candidate_logical_bytes:int=MAX_CANDIDATE_LOGICAL_BYTES,max_observation_io_bytes:int=MAX_OBSERVATION_IO_BYTES)->HiddenZipObservation:
    root=Path(root);rejects:Counter[str]=Counter();stamps={};hidden=set();parsed=head_bytes=tail_bytes=parser_bytes=verification_bytes=descriptor_count=files_observed=central_directory_bytes=0;candidates=[];metadata_owners:Counter[tuple[int,int,int,int]]=Counter()
    def total_io():return head_bytes+tail_bytes+parser_bytes+verification_bytes
    def result(admitted=(),evidence=()):return HiddenZipObservation(tuple(admitted),files_observed,parsed,head_bytes,tail_bytes,verification_bytes,tuple(sorted(rejects.items())),tuple(evidence),parser_bytes)
    def failed_io_budget():
        rejects['observation_io_budget']+=1
        return result()
    try:
        for path,rel,stamp,explicit in _physical_observation_files(root,max_observation_files):
            files_observed+=1
            remaining=int(max_observation_io_bytes)-total_io()
            pf=hidden_zip_preflight(path,max_read_bytes=remaining);head_bytes+=pf.head_bytes_read;tail_bytes+=pf.tail_bytes_read
            if pf.reason=='io_budget':return failed_io_budget()
            if not pf.eligible:rejects[('explicit_' if explicit else '')+pf.reason]+=1;continue
            central_directory_bytes+=pf.central_directory_size
            if central_directory_bytes>int(max_observation_central_directory_bytes):rejects['observation_central_directory_budget']+=1;return result()
            parser_charge=pf.tail_bytes_read+pf.central_directory_size
            if total_io()+parser_charge>int(max_observation_io_bytes):return failed_io_budget()
            parser_bytes+=parser_charge
            descriptors,entries,logical,reason=_metadata_descriptors(path)
            if descriptors is None:rejects[('explicit_' if explicit else '')+(reason or 'exact_parse_rejected')]+=1;continue
            if logical>int(max_candidate_logical_bytes):rejects[('explicit_' if explicit else '')+'logical_work_budget']+=1;continue
            descriptor_count+=entries
            if descriptor_count>int(max_observation_descriptors):rejects['observation_descriptor_budget']+=1;return result()
            stamps[rel]=stamp
            if not explicit:hidden.add(rel)
            parsed+=1;candidates.append((path,rel,explicit,descriptors,parser_charge));metadata_owners.update(descriptors)
    except _ObservationFileBudget:
        rejects['observation_file_budget']+=1
        return result()
    repeated={d for d,count in metadata_owners.items() if count>=2};exact_owners={};content_hashes={}
    for path,rel,_explicit,descriptors,parser_charge in candidates:
        hints=descriptors&repeated
        if not hints:continue
        file_size=stamps[rel][2]
        if total_io()+file_size>int(max_observation_io_bytes):return failed_io_budget()
        try:content_hashes[rel]=_file_sha256(path);verification_bytes+=file_size
        except OSError:rejects['admission_hash_io']+=1;continue
        if total_io()+parser_charge>int(max_observation_io_bytes):return failed_io_budget()
        parser_bytes+=parser_charge
        remaining=int(max_observation_io_bytes)-total_io()
        verified,read,exhausted=_verify_streams(path,hints,remaining);verification_bytes+=read
        if exhausted:return failed_io_budget()
        if verified is None:rejects['verification_rejected']+=1;continue
        for identities in verified.values():
            for identity in identities:exact_owners.setdefault(identity,set()).add(rel)
    reuse:Counter[str]=Counter()
    for identity,rels in exact_owners.items():
        if len(rels)>=2:
            for rel in rels:reuse[rel]+=identity[1]
    admitted=tuple(HiddenZipAdmission(rel,stamps[rel],int(reuse[rel]),content_hashes[rel]) for rel in sorted(hidden) if reuse[rel]>=int(min_verified_reuse) and rel in content_hashes)
    evidence=tuple(HiddenZipEvidenceState(rel,stamps[rel],content_hashes[rel]) for rel in sorted(content_hashes))
    return result(admitted,evidence)

def admission_is_current(root:Path,admission:HiddenZipAdmission)->bool:return _state_current(Path(root),admission.rel,admission.stamp,admission.content_sha256)
def observation_is_current(root:Path,observation:HiddenZipObservation,*,max_io_bytes:int=MAX_OBSERVATION_IO_BYTES)->bool:
    """Revalidate every proof owner without escaping the same aggregate discovery-I/O ceiling."""
    used=observation.head_bytes_read+observation.tail_bytes_read+observation.parser_bytes_read+observation.verification_bytes_read
    for e in observation.evidence:
        path=Path(root)/e.rel
        try:
            st=os.stat(path,follow_symlinks=False)
            current=(int(st.st_dev),int(st.st_ino),int(st.st_size),int(st.st_mtime_ns))
            if not stat.S_ISREG(st.st_mode) or current!=e.stamp:return False
            if used+int(st.st_size)>int(max_io_bytes):return False
            if _file_sha256(path)!=e.content_sha256:return False
            used+=int(st.st_size)
        except OSError:return False
    return True