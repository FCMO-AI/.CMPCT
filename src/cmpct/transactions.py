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
from .path_policy import canonical_logical_path

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

def _require_valid_update_member(index:dict, member:str):
    # Footnote: CMPCT Reader rejects unsafe/alias-colliding logical paths
    # before exposing this index. A put only needs the relevant path/parent
    # rows: scan once with constant extra memory, not a second O(N) dict.
    logical, _ = canonical_logical_path(member)
    parent = logical.rpartition('/')[0]
    previous = None
    parent_row = None
    alias_references_owner = False
    for row in index['files']:
        # Reader already canonical-validated each stored row on open.
        key = row[0].replace('\\', '/')
        if key == logical:
            previous = row
        if parent and key == parent:
            parent_row = row
        if row[1] == K_HARDLINK and row[6][0].replace('\\', '/') == logical:
            alias_references_owner = True
    if logical != member and (previous is None or previous[0] != member):
        raise ValueError(f"new update member must use canonical slash spelling: {member!r}")
    if previous is not None:
        if previous[0] != member:
            raise FileExistsError(f"canonical member path already exists: {previous[0]!r}")
        if previous[1] != K_FILE:
            raise OSError(f"cannot replace non-regular member {member!r} with a file")
        # One-row put changes owner metadata without syncing hardlink aliases.
        if alias_references_owner:
            raise ValueError(
                f"cannot update hardlink owner {member!r}: "
                "surviving aliases require atomic metadata synchronization"
            )
    if parent and (parent_row is None or parent_row[1] != K_DIR):
        raise FileNotFoundError(f"update destination parent is not an explicit directory: {parent!r}")

def append_update(archive:Path,member:str,source:Path):
    """Crash-safely append/replace one logical member, reusing CDC chunks when possible.

    Footnote: a traditional append-only ZIP update writes the entire replacement member again. Large
    CMPCT files are content-defined-chunked, so a local edit can append only the chunks whose contents
    actually changed. Existing chunk hashes are resolved against the archive's content-addressed blob
    table; the new generation's file row merely points at the reused + newly appended chunks.
    """
    archive=Path(archive);source=Path(source);raw=source.read_bytes();rh=sha(raw);st=source.stat();hint=source.suffix.lower()
    with CMPCT(archive) as ar:
        _require_valid_update_member(ar.index, member)
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

def _reject_hardlink_owner_mutation(index:dict, member:str, operation:str):
    # Footnote: a K_HARDLINK references its owner by logical path. Dropping or renaming that
    # owner without reparenting every alias would write a committed generation that fails
    # structural preflight. Until atomic reparenting is implemented, fail *before* the
    # append-only footer (or any archive mutation), never publish a dangling reference.
    for row in index['files']:
        if row[1] == K_HARDLINK and row[6] == [member]:
            raise ValueError(
                f"cannot {operation} hardlink owner {member!r}: "
                f"surviving alias {row[0]!r} would dangle"
            )

def _reject_nonempty_directory_mutation(index:dict, member:str, operation:str):
    # Footnote: revision-24 rename/delete deltas mutate exactly one row. A
    # nonempty directory has descendants whose logical paths and parent
    # metadata cannot be rewritten by that one-row grammar. Never commit a
    # generation that reports success but reconstructs a different tree.
    # Compare canonical path components, not raw prefixes: an accepted
    # archive may contain backslash spellings, and 'dir2' is not in 'dir/'.
    directory = next((row for row in index['files'] if row[0] == member), None)
    if directory is None or directory[1] != K_DIR:
        return
    owner_key, _ = canonical_logical_path(member)
    descendant_prefix = owner_key + '/'
    for row in index['files']:
        child_key, _ = canonical_logical_path(row[0])
        if child_key.startswith(descendant_prefix):
            raise OSError(
                f"cannot {operation} nonempty directory {member!r}: "
                f"surviving descendant {row[0]!r} requires a subtree transaction"
            )

def _require_valid_rename_destination(index:dict, old:str, new:str):
    # Footnote: rename is a one-row committed generation. The Reader's
    # canonical path policy must be enforced *before* appending the footer:
    # pathlib parent parsing and literal dict lookup miss slash aliases,
    # double separators and absolute/dot spellings (scientific PR #249).
    logical, _ = canonical_logical_path(new)
    if logical != new:
        raise ValueError(f"rename destination must use canonical slash spelling: {new!r}")
    parent = logical.rpartition('/')[0]
    parent_kind = None
    source_directory_key = None
    for row in index['files']:
        # Reader.__init__ has already validated every source row using
        # canonical_logical_path. Reusing its exact slash normalization avoids
        # rechecking UTF-8 and path components O(files) times per rename.
        key = row[0].replace('\\\\', '/')
        if row[0] == old and row[1] == K_DIR:
            source_directory_key = key
        if key == logical:
            raise FileExistsError(f"canonical rename destination exists: {row[0]!r}")
        if parent and key == parent:
            parent_kind = row[1]
    # A one-row rename cannot move a directory into its own child: it
    # removes the very parent path required by the new row. Fail closed
    # even for an empty source directory (scientific PR #249).
    if source_directory_key is not None and logical.startswith(source_directory_key + '/'):
        raise OSError(f"cannot rename directory {old!r} into its own descendant {new!r}")
    if parent and parent_kind != K_DIR:
        raise FileNotFoundError(f"destination parent is not an explicit directory: {parent!r}")


def append_delete(archive:Path,member:str):
    archive=Path(archive)
    with CMPCT(archive) as ar:
        if member not in ar.by:raise KeyError(member)
        _reject_hardlink_owner_mutation(ar.index,member,'delete')
        _reject_nonempty_directory_mutation(ar.index,member,'delete')
        prev=ar.latest_footer_pos;depth=ar.delta_depth;idx=msgpack.unpackb(msgpack.packb(ar.index,use_bin_type=True),raw=False)
    op=['del',member];checkpoint=_index_after_op(idx,op) if depth>=63 else None
    _append_generation(archive,{'blobs':[],'ops':[op]},prev,checkpoint)

def append_rename(archive:Path,old:str,new:str):
    archive=Path(archive)
    with CMPCT(archive) as ar:
        if old not in ar.by:raise KeyError(old)
        if new in ar.by:raise FileExistsError(new)
        _reject_hardlink_owner_mutation(ar.index,old,'rename')
        _reject_nonempty_directory_mutation(ar.index,old,'rename')
        _require_valid_rename_destination(ar.index, old, new)
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
