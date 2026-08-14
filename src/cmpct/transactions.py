from __future__ import annotations

# Footnote: mutations are isolated from the read path so transactional evolution cannot accidentally
# complicate basic archive parsing. The footer remains the atomic commit marker; incomplete tails must
# always leave the last committed generation readable.

import binascii, hashlib, os, stat, struct, tempfile, zipfile, zlib
from pathlib import Path
import msgpack

from .codec import *
from .builder import Builder
from .reader import CMPCT

def _encode_update_blob(raw:bytes,hint:str,dictionary:bytes|None):
    wf=wavflac_compress(raw) if hint=='.wav' else None
    if wf:
        comp,meta=wf
        if len(comp)+len(meta)+32 < len(raw)*0.92:return CODEC_WAVFLAC,comp,meta
    if dictionary and hint in TEXT_EXT:
        dc=zcd(raw,dictionary,9)
        if len(dc)+16<len(raw):return CODEC_ZSTDDICT,dc,msgpack.packb([9],use_bin_type=True)
    comp=zc(raw,3)
    if len(comp)+16<len(raw):return CODEC_ZSTD,comp,msgpack.packb([3],use_bin_type=True)
    return CODEC_RAW,raw,b''

def _append_generation(archive:Path,delta:dict,prev_footer:int,checkpoint_index:dict|None=None):
    if checkpoint_index is not None:
        payload=msgpack.packb(checkpoint_index,use_bin_type=True);kind=0
    else:
        payload=msgpack.packb(delta,use_bin_type=True);kind=1
    comp=zc(payload,3)
    if len(comp)<len(payload):enc=comp;codec=1
    else:enc=payload;codec=0
    footer=FTR.pack(FMAGIC,kind,codec,0,0,len(enc),len(payload),prev_footer,sha(payload))
    with open(archive,'ab',buffering=0) as f:
        f.write(enc);os.fsync(f.fileno());footer_pos=f.tell();f.write(footer);os.fsync(f.fileno())
    return footer_pos,len(enc)+FTR.size

def append_update(archive:Path,member:str,source:Path):
    """Crash-safely append/replace one logical member, reusing CDC chunks when possible.

    Footnote: a traditional append-only ZIP update writes the entire replacement member again. Large
    CMPCT files are content-defined-chunked, so a local edit can append only the chunks whose contents
    actually changed. Existing chunk hashes are resolved against the archive's content-addressed blob
    table; the new generation's file row merely points at the reused + newly appended chunks.
    """
    archive=Path(archive);source=Path(source);raw=source.read_bytes();rh=sha(raw);st=source.stat();hint=source.suffix.lower()
    with CMPCT(archive) as ar:
        index=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False);record_base=ar.record_base;prev=ar.latest_footer_pos;depth=ar.delta_depth
        blob_by_hash={}
        for i,b in enumerate(ar.blobs):
            off=b[0];rrh=bytes(BHDR.unpack_from(ar.mm,record_base+off)[-1]);blob_by_hash.setdefault(rrh,i)
        dictionary=ar._blob(ar.dict_idx) if ar.dict_idx is not None else None

    records=[];newblobs=[];archive_end=archive.stat().st_size;next_off=archive_end-record_base
    def ensure_blob(part:bytes):
        nonlocal next_off
        h=sha(part);existing=blob_by_hash.get(h)
        if existing is not None:return existing,True
        codec,comp,meta=_encode_update_blob(part,hint,dictionary)
        rec=BHDR.pack(BMAGIC,codec,0,0,len(part),len(comp),len(meta),binascii.crc32(part)&0xffffffff,h)+meta+comp
        idx=len(index['blobs'])+len(newblobs);newblobs.append([next_off,len(part),len(comp),codec,len(meta)]);records.append(rec)
        next_off+=len(rec);blob_by_hash[h]=idx
        return idx,False

    reused=0
    if len(raw)>4*CHUNK and hint!='.wav':
        entries=[]
        for part in cdc_chunks(raw):
            idx,was_reused=ensure_blob(part);reused+=int(was_reused);entries.append([len(part),idx])
        storage=[S_CDC,entries];logical_hash=rh
    else:
        idx,was_reused=ensure_blob(raw);reused+=int(was_reused);storage=[S_BLOB,idx];logical_hash=None

    row=[member,K_FILE,stat.S_IMODE(st.st_mode),st.st_mtime_ns,len(raw),logical_hash,storage]
    delta={'blobs':newblobs,'ops':[['put',row]]}
    # Every 64 deltas write a compact full checkpoint. This bounds open-time chain traversal while
    # amortizing checkpoint bytes to only a few hundred bytes per update.
    checkpoint=None
    if depth>=63:
        index['blobs'].extend(newblobs)
        done=False
        for i,x in enumerate(index['files']):
            if x[0]==member:index['files'][i]=row;done=True;break
        if not done:index['files'].append(row)
        index['files'].sort(key=lambda x:x[0]);checkpoint=index
    if checkpoint is not None:
        payload=msgpack.packb(checkpoint,use_bin_type=True);kind=0
    else:
        payload=msgpack.packb(delta,use_bin_type=True);kind=1
    comp2=zc(payload,3);enc=comp2 if len(comp2)<len(payload) else payload;codec2=1 if len(comp2)<len(payload) else 0
    footer=FTR.pack(FMAGIC,kind,codec2,0,0,len(enc),len(payload),prev,sha(payload))
    record=b''.join(records)
    # Two-phase durable commit: all uncommitted bytes are flushed together, then the tiny footer
    # commit marker is flushed separately. A crash before phase 2 leaves the previous footer valid.
    with open(archive,'ab',buffering=0) as f:
        if record:f.write(record)
        f.write(enc);os.fsync(f.fileno());f.write(footer);os.fsync(f.fileno())
    return {'reused_chunks':reused,'new_chunks':len(newblobs),'new_size':archive.stat().st_size,
            'generation_bytes':len(record)+len(enc)+FTR.size,'member':member,'checkpoint':checkpoint is not None}

def _index_after_op(index:dict,op:list):
    if op[0]=='del':index['files']=[x for x in index['files'] if x[0]!=op[1]]
    elif op[0]=='ren':
        for x in index['files']:
            if x[0]==op[1]:x[0]=op[2];break
    index['files'].sort(key=lambda x:x[0]);return index

def append_delete(archive:Path,member:str):
    archive=Path(archive)
    with CMPCT(archive) as ar:
        if member not in ar.by:raise KeyError(member)
        prev=ar.latest_footer_pos;depth=ar.delta_depth;idx=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False)
    op=['del',member];checkpoint=_index_after_op(idx,op) if depth>=63 else None
    _append_generation(archive,{'blobs':[],'ops':[op]},prev,checkpoint)

def append_rename(archive:Path,old:str,new:str):
    archive=Path(archive)
    with CMPCT(archive) as ar:
        if old not in ar.by:raise KeyError(old)
        if new in ar.by:raise FileExistsError(new)
        # Footnote: rename follows real filesystem semantics. A destination parent must already
        # exist as a logical directory; otherwise compaction/extraction could silently invent a
        # directory entry and its metadata. Root-level destinations remain valid.
        parent=Path(new).parent.as_posix()
        if parent not in ('','.','/'):
            prow=ar.by.get(parent)
            if prow is None or prow[1]!=K_DIR:raise FileNotFoundError(f'destination parent directory does not exist: {parent}')
        prev=ar.latest_footer_pos;depth=ar.delta_depth;idx=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False)
    op=['ren',old,new];checkpoint=_index_after_op(idx,op) if depth>=63 else None
    _append_generation(archive,{'blobs':[],'ops':[op]},prev,checkpoint)

def recover_blob_records(archive:Path):
    # Last-resort content salvage independent of either index. It returns valid self-hashed blobs;
    # names require an index, but content remains recoverable even after severe metadata damage.
    data=Path(archive).read_bytes();out=[];p=0
    while True:
        i=data.find(BMAGIC,p)
        if i<0:break
        if i+BHDR.size<=len(data):
            try:
                m,c,fl,res,us,cs,ml,rcrc,rh=BHDR.unpack_from(data,i);end=i+BHDR.size+ml+cs
                if end<=len(data):out.append({'offset':i,'codec':c,'usize':us,'csize':cs,'crc32':rcrc,'sha256':bytes(rh).hex()})
            except Exception:pass
        p=i+1
    return out

def compact_archive(src:Path,dst:Path):
    # Compaction is deliberately simple and conservative in the prototype: reconstruct the exact
    # live filesystem view into a temporary tree, then rebuild. Dead generations/blobs disappear.
    with tempfile.TemporaryDirectory(prefix='cmpct-compact-') as td:
        root=Path(td)/'tree'
        with CMPCT(src) as ar:ar.extractall(root,metadata=True)
        return Builder(root).build(dst)

def tree_digest(root:Path):
    h=hashlib.sha256();root=Path(root)
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root).as_posix().encode();h.update(struct.pack('<I',len(rel)));h.update(rel)
        if p.is_file():b=p.read_bytes();h.update(b'F');h.update(struct.pack('<Q',len(b)));h.update(hashlib.sha256(b).digest())
        elif p.is_dir():h.update(b'D')
        elif p.is_symlink():h.update(b'L');h.update(os.readlink(p).encode())
    return h.hexdigest()
