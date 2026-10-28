from __future__ import annotations

# Footnote: this module contains the compatibility contract that matters most. Refactors must not
# silently drop recovery, range-read, path-safety, transactional-generation, or metadata semantics.

import base64, binascii, concurrent.futures, ctypes, ctypes.util, errno, hashlib, io, json, mmap, os, shutil, stat, struct, sys, tempfile, threading, time, zipfile, zlib
from pathlib import Path
import msgpack

from .codec import *
from .codec import _hash_sparse, _wav_parts, _ld, _sz
from .native_codec import DictDecoder
from .path_policy import canonical_logical_path
from ._chunk_admission import native_chunk_ok, native_uniform_stride

def _safe_output_path(dest:Path,rel:str)->Path:
    # Logical path validation is lexical and allocation-cheap. Absolute paths, NULs and parent
    # components are sufficient to block classic Zip-Slip paths. Archive-created symlink pivots
    # are checked once per extraction below rather than resolving every file through the filesystem.
    if '\x00' in rel:raise IOError('NUL in archive path')
    pp=Path(rel)
    if pp.is_absolute() or any(x in ('..','') for x in pp.parts):raise IOError(f'unsafe archive path: {rel!r}')
    return dest/pp

# POSIX RAW extraction avoids touching a borrowed mmap after the Reader has opened.
# A writer may shrink the same inode while a mapping is alive: dereferencing it can
# SIGBUS the *process*. pread on the already-pinned descriptor instead fails with a
# short read/ordinary I/O error, while preserving small immutable SHA/write windows.
class _FdRawExtractWindows:
    __slots__=('fd','start','length')
    def __init__(self,fd:int,start:int,length:int):
        self.fd=fd;self.start=start;self.length=length
    def __len__(self):return self.length
    def __getitem__(self,key):
        if not isinstance(key,slice):raise TypeError('RAW extraction requires bounded window slices')
        a,b,step=key.indices(self.length)
        if step!=1:raise ValueError('noncontiguous RAW extraction slice')
        size=b-a
        if size<=0:return b''
        out=os.pread(self.fd,size,self.start+a)
        if len(out)!=size:raise IOError('RAW archive source shortened during verified extraction')
        return out

# Linux's O_TMPFILE + linkat publishes an *already verified inode* directly.
# This is deliberately create-only: AT_EMPTY_PATH refuses an occupied leaf with
# EEXIST. It cannot solve atomic replacement of an existing output (issue #528).
# See the independently established Linux kernel primitive at J24P02 PR #523.
def _publish_unnamed_chunk_fd(fd:int,parentfd:int,leaf:str)->str:
    libc=ctypes.CDLL(None,use_errno=True)
    link=libc.linkat
    link.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_int]
    link.restype=ctypes.c_int
    name=os.fsencode(leaf)
    def checked(srcfd,srcname,flags):
        ctypes.set_errno(0)
        if link(srcfd,srcname,parentfd,name,flags)!=0:
            code=ctypes.get_errno()
            raise OSError(code,os.strerror(code),leaf)
    try:
        checked(fd,b'',0x1000)  # Linux AT_EMPTY_PATH; no staged pathname exists.
        return 'AT_EMPTY_PATH'
    except OSError as exc:
        if exc.errno not in (errno.EPERM,errno.ENOENT,errno.EINVAL):
            raise  # Especially EEXIST: never fall back to replace over another inode.
        checked(-100,os.fsencode('/proc/self/fd/%d'%fd),0x400)  # AT_SYMLINK_FOLLOW.
        return 'PROC_SELF_FD_FOLLOW'

# --- Reader ----------------------------------------------------------------
class CMPCT:
    def __init__(self,path:Path):
        self.path=Path(path)
        self.f=open(path,'rb')
        self._io_lock=threading.Lock()
        try:
            self.index,self.record_base=self._load_index()
            self.files=self.index['files']
            self.by={x[0]:x for x in self.files}
            if len(self.by)!=len(self.files):raise IOError('duplicate logical path in CMPCT index')
            # The authenticated effective index must have one host-visible spelling for each member.
            # Sparse/CDC descriptors and fixed-chunk totals must agree with physical blob lengths.
            # Otherwise authenticated metadata can admit logically in-bounds range reads that return
            # too few bytes (O215); validate the SAME effective index before mmap (O208/O212/O214).
            # Validate this SAME in-memory index, never a separately reopened pathname (#546).
            canonical_seen=set()
            storage_validator=None
            for row in self.files:
                try:
                    key,_=canonical_logical_path(row[0])
                except ValueError as exc:
                    raise IOError(f'unsafe CMPCT logical path: {exc}') from exc
                if key in canonical_seen:raise IOError(f'duplicate canonical logical path: {row[0]!r}')
                canonical_seen.add(key)
                storage=row[6]
                if row[1]==K_FILE and isinstance(storage,list) and storage and storage[0] in (S_SPARSE, S_CDC, S_CHUNKS):
                    # ABI3 is an optional positive-only proof for exact built-in S_CHUNKS.
                    # Invalid, unknown and unavailable cases ALWAYS run the inherited strict validator.
                    # This happens after canonical path admission and before mmap allocation.
                    if storage[0]==S_CHUNKS and native_chunk_ok(storage,self.index['blobs'],row[4]):
                        continue
                    if storage_validator is None:
                        from .validation import _validate_storage
                        storage_validator=_validate_storage
                    storage_validator(row[0],row[1],row[4],storage,self.index['blobs'],self.index['recipes'])
            # Allocate mmap only after structural admission. Rejected hostile indexes do not leak
            # a mapped source, and failures above close the one source descriptor opened here.
            self.mm=mmap.mmap(self.f.fileno(),0,access=mmap.ACCESS_READ)
        except BaseException:
            self.f.close()
            raise
        self._chunk_stride_cache={};self.blobs=self.index['blobs'];self.recipes=self.index['recipes'];self.dict_idx=self.index.get('dict_blob');self.fsmeta=self.index.get('fsmeta',{});self.cache={};self.vcache={};self._cache_lock=threading.Lock();self._zdict_lock=threading.Lock();self._zdict_decoder=None;self._inflate_lock=threading.Lock();self._inflater=(_ld.libdeflate_alloc_decompressor() if _ld is not None else None);self._executor=None
    def close(self):
        if getattr(self,'mm',None):self.mm.close();self.mm=None
        if self._zdict_decoder:self._zdict_decoder.close();self._zdict_decoder=None
        if self._inflater and _ld is not None:_ld.libdeflate_free_decompressor(self._inflater);self._inflater=None
        if self._executor:self._executor.shutdown(wait=True);self._executor=None
        self.f.close()
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
    def _decode_generation_payload(self,footer_pos:int):
        if footer_pos<0:return None
        self.f.seek(footer_pos);fb=self.f.read(FTR.size)
        if len(fb)!=FTR.size:return None
        m,kind,codec,flags,res,cs,us,prev,ph=FTR.unpack(fb)
        if m!=FMAGIC or cs>footer_pos:return None
        self.f.seek(footer_pos-cs);enc=self.f.read(cs)
        try:payload=enc if codec==0 else zd(enc,us)
        except Exception:return None
        if len(payload)!=us or sha(payload)!=ph:return None
        return kind,payload,prev
    def _index_from_footer(self,footer_pos:int):
        chain=[];pos=footer_pos;depth=0;seen=set()
        while pos and pos not in seen:
            seen.add(pos);g=self._decode_generation_payload(pos)
            if g is None:return None
            kind,payload,prev=g
            if kind==0:
                idx=msgpack.unpackb(payload,raw=False)
                for delta in reversed(chain):
                    for b in delta.get('blobs',[]):idx['blobs'].append(b)
                    for op in delta.get('ops',[]):
                        if op[0]=='put':
                            row=op[1];done=False
                            for i,x in enumerate(idx['files']):
                                if x[0]==row[0]:idx['files'][i]=row;done=True;break
                            if not done:idx['files'].append(row)
                        elif op[0]=='del':idx['files']=[x for x in idx['files'] if x[0]!=op[1]]
                        elif op[0]=='ren':
                            for x in idx['files']:
                                if x[0]==op[1]:x[0]=op[2];break
                    idx['files'].sort(key=lambda x:x[0])
                return idx,depth
            if kind!=1:return None
            chain.append(msgpack.unpackb(payload,raw=False));depth+=1;pos=prev
        return None
    def _latest_generation(self):
        # Scan backward for the newest valid commit footer. A partial append after an older footer
        # is harmless: the older footer remains discoverable and its hash/parent chain still validates.
        self.f.seek(0,2);size=self.f.tell();block=1024*1024;pos=size;carry=b'';magic=FMAGIC
        while pos>0:
            n=min(block,pos);pos-=n;self.f.seek(pos);chunk=self.f.read(n)+carry;search=len(chunk)
            while True:
                i=chunk.rfind(magic,0,search)
                if i<0:break
                fp=pos+i
                if fp+FTR.size<=size:
                    got=self._index_from_footer(fp)
                    if got is not None:return got[0],fp,got[1]
                search=i
            carry=chunk[:len(magic)-1]
        return None
    def _load_index(self):
        latest=self._latest_generation()
        self.f.seek(0);m,v,fl,cs,us,ds,ih=HDR.unpack(self.f.read(HDR.size))
        if m!=MAGIC:raise IOError('not CMPCT v0.24')
        if latest is not None:
            self.latest_footer_pos=latest[1];self.delta_depth=latest[2];return latest[0],HDR.size+cs
        ic=self.f.read(cs);ib=zd(ic,us)
        if sha(ib)!=ih:raise IOError('both CMPCT indexes unavailable/corrupt')
        self.latest_footer_pos=0;self.delta_depth=0;return msgpack.unpackb(ib,raw=False),HDR.size+cs
    def _inflate(self,comp:bytes,usize:int)->bytes:
        if _ld is None or self._inflater is None:
            raw=zlib.decompress(comp,-15)
            if len(raw)!=usize:raise IOError(f'Deflate decode size mismatch: {len(raw)}/{usize}')
            return raw
        src=ctypes.create_string_buffer(comp);dst=ctypes.create_string_buffer(usize);actual=_sz()
        with self._inflate_lock:
            rc=_ld.libdeflate_deflate_decompress(self._inflater,src,len(comp),dst,usize,ctypes.byref(actual))
        if rc!=0 or actual.value!=usize:raise IOError(f'Deflate decode failure rc={rc} size={actual.value}/{usize}')
        return dst.raw[:usize]

    def _zdict_decode(self,comp:bytes,usize:int)->bytes:
        # Load the archive dictionary once into the package-owned native DCtx.  This preserves the
        # measured tiny-file lifetime benefit without retaining a second Python-owned DDict/buffer.
        with self._zdict_lock:
            if self._zdict_decoder is None:
                if self.dict_idx is None:raise IOError('missing Zstd dictionary')
                self._zdict_decoder=DictDecoder(self._blob(self.dict_idx))
            return self._zdict_decoder.decompress(comp,usize)

    def _blob(self,idx:int)->bytes:
        with self._cache_lock:
            cached=self.cache.get(idx)
        if cached is not None:return cached
        off,us,cs,codec,ml=self.blobs[idx];pos=self.record_base+off
        # Immutable committed generations are memory-mapped. Slicing an mmap avoids seek/read
        # syscalls and is naturally safe for concurrent readers; the OS still faults pages lazily.
        m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos);p=pos+BHDR.size
        if m!=BMAGIC or rus!=us or flags or res:raise IOError('blob header mismatch')
        meta=self.mm[p:p+rml];comp=self.mm[p+rml:p+rml+rcs]
        if c==CODEC_RAW:raw=comp
        elif c==CODEC_ZSTD:raw=zd(comp,rus)
        elif c==CODEC_WAVFLAC:raw=wavflac_decompress(comp,meta)
        elif c==CODEC_ZSTDDICT:
            if self.dict_idx is None:raise IOError('missing Zstd dictionary')
            raw=self._zdict_decode(comp,rus)
        elif c==CODEC_DEFLATE:raw=self._inflate(comp,rus)
        else:raise IOError(f'unknown codec {c}')
        if len(raw)!=rus or (binascii.crc32(raw)&0xffffffff)!=rcrc:raise IOError('blob integrity failure')
        # Cache only modest blobs; huge archives should not become accidental RAM copies.
        if len(raw)<=2*1024*1024:
            with self._cache_lock:self.cache[idx]=raw
        return raw
    def _stream(self,mode:int,idx:int,level:int=-1)->bytes:
        if mode==1:
            return self._blob(idx)
        if mode==2:
            raw=self._blob(idx);co=zlib.compressobj(int(level),zlib.DEFLATED,-15);return co.compress(raw)+co.flush()
        off,us,cs,codec,ml=self.blobs[idx]
        if codec!=CODEC_DEFLATE:raise IOError('canonical Deflate stream requested from non-Deflate blob')
        pos=self.record_base+off;m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos);p=pos+BHDR.size+rml
        if m!=BMAGIC or c!=CODEC_DEFLATE:return b''
        return self.mm[p:p+rcs]

    def file_sha256(self,name:str)->bytes:
        row=self.by[name];storage=row[6]
        if row[1]==K_HARDLINK:return self.file_sha256(storage[0])
        if storage[0]==S_BLOB:
            off=self.blobs[storage[1]][0];pos=self.record_base+off;return bytes(BHDR.unpack_from(self.mm,pos)[-1])
        if storage[0]==S_VZIP:return bytes(self.recipes[storage[1]][3])
        if storage[0]==S_PACK:return sha(self.read(name))
        if row[5] is not None:return bytes(row[5])
        return sha(self.read(name))

    def read(self,name:str)->bytes:
        row=self.by[name];rel,k,mode,mt,size,h,storage=row
        if k==K_DIR:raise IsADirectoryError(name)
        if k==K_HARDLINK:return self.read(storage[0])
        if k==K_SYMLINK:
            # Symlink bytes must have the same logical length as their authenticated physical owner.
            idx=storage[1]
            if type(size) is not int or size!=self.blobs[idx][1]:
                raise IOError(f'symlink size failure: {name}')
            raw=self._blob(idx)
            if len(raw)!=size:raise IOError(f'symlink size failure: {name}')
            return raw
        sk=storage[0]
        if sk==S_PACK:
            pack=self._blob(storage[1]);raw=pack[storage[2]:storage[2]+storage[3]]
            if len(raw)!=size:raise IOError(f'packed file size failure: {name}')
            return raw
        if sk==S_BLOB:
            raw=self._blob(storage[1])
            # Direct files inherit the blob's already-verified SHA-256; hashing the exact same bytes
            # again was redundant and disproportionately hurt sub-millisecond reads.
            if len(raw)!=size:raise IOError(f'file size failure: {name}')
            return raw
        elif sk==S_CHUNKS:
            ids=storage[1]
            if len(ids)>=4:
                if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
                raw=b''.join(self._executor.map(self._blob,ids))
            else:raw=b''.join(self._blob(i) for i in ids)
        elif sk==S_CDC:
            entries=storage[1];ids=[x[1] for x in entries]
            if len(ids)>=4:
                if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
                raw=b''.join(self._executor.map(self._blob,ids))
            else:raw=b''.join(self._blob(i) for i in ids)
        elif sk==S_SPARSE:
            # Full reads are provided for API parity, but extraction/range reads below avoid
            # materializing holes and are the intended path for very large sparse files.
            buf=bytearray(size)
            for off,ln,ids in storage[1]:
                q=off
                for idx in ids:
                    b=self._blob(idx);buf[q:q+len(b)]=b;q+=len(b)
            raw=bytes(buf)
        elif sk==S_VZIP:
            rid=storage[1]
            raw=self.vcache.get(rid)
            if raw is None:
                raw=rebuild_vzip(self.recipes[rid],self._blob,self._stream);self.vcache[rid]=raw
            # rebuild_vzip has already verified the virtual file's exact SHA-256.
            if len(raw)!=size:raise IOError(f'file size failure: {name}')
            return raw
        else:raise IOError('unknown storage kind')
        if len(raw)!=size or sha(raw)!=bytes(h):raise IOError(f'file integrity failure: {name}')
        return raw
    def read_range(self,name,start,length):
        row=self.by[name];size=row[4];storage=row[6];end=start+length
        if row[1]==K_HARDLINK:return self.read_range(storage[0],start,length)
        if start<0 or length<0 or end>size:raise ValueError('range outside member')
        if storage[0]==S_PACK:
            pack=self._blob(storage[1]);base=storage[2];return pack[base+start:base+end]
        if storage[0]==S_BLOB:
            # STORE/raw members can be range-read straight from the mmap without copying/decompressing
            # the rest of the file. This matters for already-compressed media where recompression is
            # pointless but ZIP would still normally inflate the whole member to reach a late range.
            idx=storage[1];off,us,cs,codec,ml=self.blobs[idx]
            # Admit only ranges owned by the entire authenticated direct blob, even for empty reads.
            if type(size) is not int or size!=us:
                raise IOError(f'direct blob size failure: {name}')
            if codec==CODEC_RAW:
                pos=self.record_base+off
                if pos<self.record_base or pos+BHDR.size>len(self.mm):
                    raise IOError('RAW blob header outside archive')
                m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos)
                if m!=BMAGIC or c!=CODEC_RAW or rus!=us or rcs!=cs or rml!=ml or rcs!=rus or flags or res:
                    raise IOError('RAW blob header mismatch')
                base=pos+BHDR.size+rml
                if base<0 or base+rcs>len(self.mm) or end>rcs:
                    raise IOError('RAW blob range outside physical owner')
                return self.mm[base+start:base+end]
            # Compressed small members remain one independent frame, preserving ZIP-like granularity.
            return self._blob(idx)[start:end]
        if storage[0]==S_CHUNKS:
            ids=storage[1]
            # J24C10: a constant-stride witness is NOT an admission shortcut.
            # Full native proof uses the SAME already-admitted authenticated index,
            # only for late requests; missing/failed proof keeps the original scan.
            # At most one integer per queried member is cached per Reader.
            stride=self._chunk_stride_cache.get(name)
            if stride is None and length and start*2>=size and len(ids)>1:
                # Cheap necessary condition avoids a full C pass for plainly
                # irregular interior lengths; C still proves EVERY reference.
                a=self.blobs[ids[0]][1]
                mid=self.blobs[ids[(len(ids)-1)//2]][1]
                prelast=self.blobs[ids[-2]][1]
                stride=(native_uniform_stride(storage,self.blobs,size)
                        if a>0 and a==mid==prelast else 0)
                self._chunk_stride_cache[name]=stride
            if stride:
                out=[];first=start//stride;p=first*stride
                for j in range(first,len(ids)):
                    idx=ids[j];bsize=self.blobs[idx][1]
                    if p+bsize>start and p<end:
                        b=self._blob(idx);lo=max(start,p)-p;hi=min(end,p+bsize)-p
                        out.append(b[lo:hi])
                    p+=bsize
                    if p>=end:break
                return b''.join(out)
            out=[];p=0
            for idx in ids:
                bsize=self.blobs[idx][1]
                if p+bsize>start and p<end:
                    b=self._blob(idx);a=max(start,p)-p;z=min(end,p+bsize)-p;out.append(b[a:z])
                p+=bsize
                if p>=end:break
            return b''.join(out)
        if storage[0]==S_CDC:
            out=[];p=0
            for ln,idx in storage[1]:
                if p+ln>start and p<end:
                    b=self._blob(idx);a=max(start,p)-p;z=min(end,p+ln)-p;out.append(b[a:z])
                p+=ln
                if p>=end:break
            return b''.join(out)
        if storage[0]==S_SPARSE:
            out=bytearray(length)
            for off,ln,ids in storage[1]:
                extent_end=off+ln
                if extent_end<=start or off>=end:continue
                q=off
                for idx in ids:
                    bs=self.blobs[idx][1];chunk_end=q+bs
                    if chunk_end>start and q<end:
                        b=self._blob(idx);a=max(start,q)-q;z=min(end,chunk_end)-q
                        out[max(q,start)-start:min(chunk_end,end)-start]=b[a:z]
                    q=chunk_end
                    if q>=end:break
            return bytes(out)
        if storage[0]==S_VZIP:return range_vzip(self.recipes[storage[1]],self._blob,self._stream,start,length)
        return self.read(name)[start:end]

    def _raw_blob_view_for_extract(self,idx:int):
        """Return bounded RAW extraction source, descriptor-backed on POSIX.

        The trusted index and physical RAW header are cross-checked before transfer.
        Unlike an mmap window, `pread` on the already-open descriptor cannot fault
        SIGBUS merely because another actor truncated its inode. The returned source
        materializes only the requested <=64-KiB immutable SHA/write window; it
        never retains a full physical RAW chunk. The whole logical file is still
        SHA-256 authenticated before staged publication. Ordinary `read()` and
        compressed/mixed extraction remain separate and keep their existing law.
        On hosts without pread, preserve the existing mmap-backed fallback.
        """
        off,us,cs,codec,ml=self.blobs[idx]
        if codec!=CODEC_RAW:raise ValueError('RAW extraction view requested for compressed blob')
        pos=self.record_base+off
        if pos<0:raise IOError('blob header outside archive')
        if hasattr(os,'pread'):
            # The file descriptor pins the original inode even if its pathname is replaced.
            # A concurrent same-inode shrink yields short pread, not mapped-memory SIGBUS.
            header=os.pread(self.f.fileno(),BHDR.size,pos)
            if len(header)!=BHDR.size:raise IOError('RAW blob header shortened')
            m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack(header)
        else:
            if pos+BHDR.size>len(self.mm):raise IOError('blob header outside archive')
            m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos)
        if m!=BMAGIC or c!=CODEC_RAW or rus!=us or rcs!=cs or rml!=ml or rcs!=rus or flags or res:
            raise IOError('RAW blob header mismatch')
        start=pos+BHDR.size+rml;end=start+rcs
        if start<0:raise IOError('RAW blob payload outside archive')
        if hasattr(os,'pread'):
            if end>os.fstat(self.f.fileno()).st_size:
                raise IOError('RAW blob payload shortened before extraction')
            return _FdRawExtractWindows(self.f.fileno(),start,rcs)
        if end>len(self.mm):raise IOError('RAW blob payload outside archive')
        return memoryview(self.mm)[start:end]

    def _extract_chunked_verified(self,row,full:str):
        """Stream a chunked logical file to disk and commit it only after whole-file verification.

        Footnote: ``read()`` deliberately returns one contiguous ``bytes`` object for API callers, but
        extraction does not need that ownership model. The old extraction path decoded every chunk,
        joined the complete logical file, hashed the joined copy, and only then copied it again into the
        destination. ZIP's streaming extractor never pays that extra whole-file allocation/copy. This
        path preserves CMPCT's stronger SHA-256 check while hashing each decoded chunk as it is written.

        The temporary file is created beside the final destination and atomically replaced only after
        size + SHA verification. That retains the previous corruption behavior: a damaged archive cannot
        truncate a pre-existing destination merely because streaming began before integrity was known.
        """
        rel,k,mode,mt,size,h,storage=row;sk=storage[0]
        if sk==S_CHUNKS:
            ids=list(storage[1]);lengths=[self.blobs[idx][1] for idx in ids]
        elif sk==S_CDC:
            lengths=[int(x[0]) for x in storage[1]];ids=[x[1] for x in storage[1]]
        else:raise ValueError('chunked extraction requires fixed or CDC storage')

        # POSIX RAW windows use a pinned-descriptor pread source; unsupported hosts
        # preserve the earlier borrowed-mmap source. Every <=64-KiB owned window is
        # both authenticated and written from the same immutable bytes. Short descriptor
        # reads fail closed when a writer shrinks the source. Other codecs are unchanged.
        raw_direct=bool(ids) and all(self.blobs[idx][3]==CODEC_RAW for idx in ids)
        raw_window=64*1024
        if raw_direct:
            decoded=(self._raw_blob_view_for_extract(idx) for idx in ids)
        elif len(ids)>=4:
            if self._executor is None:self._executor=concurrent.futures.ThreadPoolExecutor(max_workers=min(8,os.cpu_count() or 4))
            decoded=self._executor.map(self._blob,ids)
        else:
            decoded=(self._blob(idx) for idx in ids)

        parent=os.path.dirname(full) or '.';prefix=f'.{os.path.basename(full)}.cmpct-part-'
        # A fresh Linux leaf can use a descriptor-only stage: the directory writer
        # cannot replace a stage *name* between SHA and publication because none exists.
        # Existing leaves retain inherited overwrite semantics (and issue #528 debt).
        fd=-1;parentfd=-1;tmp=None;unnamed=False;committed=False
        if sys.platform.startswith('linux') and hasattr(os,'O_TMPFILE') and not os.path.lexists(full):
            try:
                # The parent is a directory *capability*, not a source to enumerate.
                # O_RDONLY incorrectly rejects write+search-only (0300) output directories
                # even though O_TMPFILE and linkat can publish there. O_PATH preserves
                # the fd-bound fresh-leaf guarantee without requiring directory read rights.
                parentfd=os.open(parent,os.O_PATH|os.O_DIRECTORY)
                # Open relative to the pinned O_PATH parent. No second lookup
                # of its mutable pathname or procfs dependency is required.
                fd=os.open('.',os.O_TMPFILE|os.O_RDWR,0o600,dir_fd=parentfd)
                unnamed=True
            except OSError as exc:
                if parentfd>=0:os.close(parentfd);parentfd=-1
                if exc.errno not in (errno.EOPNOTSUPP,errno.ENOTSUP,errno.ENOSYS,errno.EINVAL,errno.EISDIR):
                    raise
                # On unsupported filesystems fall back to inherited, explicitly
                # not inode-authentic publication semantics; no security claim.
        if fd<0:fd,tmp=tempfile.mkstemp(prefix=prefix,dir=parent)
        digest=hashlib.sha256();written=0
        try:
            # Match the ordinary extraction mode through the already-owned descriptor when supported.
            # Win32 Python can omit os.fchmod entirely: never reopen the stage by mutable pathname just
            # to change a best-effort mode, since that would create another path-substitution seam.
            # Extended metadata restoration remains governed by extractall(metadata=...).
            fd_chmod=getattr(os,'fchmod',None)
            if fd_chmod is not None:
                try:fd_chmod(fd,mode or 0o666)
                except OSError:pass
            for expected,b in zip(lengths,decoded):
                try:
                    if len(b)!=expected:raise IOError(f'chunk length failure while extracting {rel}')
                    # Every detached window is the single immutable object consumed by the
                    # digest and write(2); full indexed SHA still gates publication.
                    pieces=(bytes(b[start:start+raw_window])
                            for start in range(0,len(b),raw_window)) if raw_direct else (b,)
                    for piece in pieces:
                        digest.update(piece);written+=len(piece);view=memoryview(piece)
                        try:
                            while view:
                                n=os.write(fd,view)
                                if n<=0:raise IOError(f'short write while extracting {rel}')
                                view=view[n:]
                        finally:
                            try:view.release()
                            except ValueError:pass
                finally:
                    # Release an mmap fallback view, including after a short write.
                    if isinstance(b,memoryview):b.release()
            if written!=size or h is None or digest.digest()!=bytes(h):
                raise IOError(f'file integrity failure: {rel}')
            if unnamed:
                # The verified descriptor is still live. One kernel create links
                # exactly that inode; an occupied/raced destination raises EEXIST
                # rather than clobbering it or publishing an attacker-supplied stage.
                _publish_unnamed_chunk_fd(fd,parentfd,os.path.basename(full))
                committed=True
            else:
                os.close(fd);fd=-1
                os.replace(tmp,full);committed=True
        finally:
            if fd>=0:
                try:os.close(fd)
                except OSError:pass
            if parentfd>=0:
                try:os.close(parentfd)
                except OSError:pass
            if not committed and tmp is not None:
                try:os.unlink(tmp)
                except FileNotFoundError:pass

    def _restore_extra_metadata(self,clean):
        """Restore sparse ownership overrides and xattrs after file materialization.

        Footnote: chown is attempted only when permitted; failing to own a file should not make an
        otherwise valid archive impossible to extract as an unprivileged user. Xattr failures are also
        non-fatal because namespace support differs across filesystems. The metadata remains preserved
        in the archive even when the destination cannot represent it.
        """
        common=tuple(self.fsmeta.get('owner',(0,0)));over={i:(u,g) for i,u,g in self.fsmeta.get('owner_overrides',[])}
        xam={i:xs for i,xs in self.fsmeta.get('xattrs',[])}
        for i,(row,parts,full) in enumerate(clean):
            uid,gid=over.get(i,common)
            if hasattr(os,'chown') and (uid or gid):
                try:os.chown(full,uid,gid,follow_symlinks=False)
                except (OSError,PermissionError):pass
            if i in xam and hasattr(os,'setxattr'):
                for name,value in xam[i]:
                    try:os.setxattr(full,name,value,follow_symlinks=False)
                    except OSError:pass

    def extractall(self,dest:Path,metadata=True,max_bytes:int|None=None,safe_symlinks=True):
        """Extract the logical tree with a low-syscall fast path.

        Footnote: v0.14 called ``mkdir(..., exist_ok=True)`` for nearly every member and built
        ``Path`` objects repeatedly. That work dominated the final few milliseconds after codec
        performance had already surpassed Deflate. v0.15 validates paths once, creates the known
        directory tree once, then writes members using plain OS paths. This changes no archive
        semantics; it only removes Python/filesystem bookkeeping from the hot loop.
        """
        dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);dest_s=os.fspath(dest)
        total=sum(x[4] for x in self.files if x[1]!=K_DIR)
        if max_bytes is not None and total>max_bytes:raise IOError(f'archive expands to {total} bytes, above limit {max_bytes}')

        # Validate every logical path once and reject aliases/symlink pivots before writing anything.
        canonical_rows=[];seen=set();syms=set()
        for row in self.files:
            rel=row[0]
            try:key,parts=canonical_logical_path(rel)
            except ValueError as exc:raise IOError(f'unsafe archive path: {rel!r}: {exc}') from exc
            if key in seen:raise IOError(f'duplicate canonical archive path: {rel!r}')
            seen.add(key);canonical_rows.append((row,key,parts))
            if row[1]==K_SYMLINK:syms.add(key)
        clean=[]
        for row,key,parts in canonical_rows:
            rel=row[0]
            if safe_symlinks:
                for i in range(1,len(parts)):
                    if '/'.join(parts[:i]) in syms:raise IOError(f'archive symlink used as parent path: {rel!r}')
            clean.append((row,parts,os.path.join(dest_s,*parts)))

        # Build all directories first. Parents are guaranteed to exist before regular-file writes,
        # eliminating hundreds of redundant stat/mkdir calls on large source trees.
        dirs=[]
        for row,parts,full in clean:
            if row[1]==K_DIR:
                os.makedirs(full,exist_ok=True);dirs.append((full,row[2],row[3]))
        for row,parts,full in clean:
            rel,k,mode,mt,size,h,storage=row
            if k==K_DIR:continue
            parent=os.path.dirname(full)
            if parent and not os.path.isdir(parent):os.makedirs(parent,exist_ok=True)
            if k==K_HARDLINK:
                try:_,target_parts=canonical_logical_path(storage[0])
                except ValueError as exc:raise IOError(f'unsafe hardlink target: {storage[0]!r}: {exc}') from exc
                target=os.path.join(dest_s,*target_parts)
                if not os.path.exists(target):raise IOError(f'hardlink target not yet extracted: {storage[0]}')
                try:os.unlink(full)
                except FileNotFoundError:pass
                os.link(target,full);continue
            if k==K_SYMLINK:
                target=self.read(rel).decode('utf-8','surrogateescape')
                if safe_symlinks:
                    tp=Path(target)
                    if tp.is_absolute() or any(x=='..' for x in tp.parts):raise IOError(f'unsafe symlink target in {rel!r}: {target!r}')
                try:os.unlink(full)
                except FileNotFoundError:pass
                os.symlink(target,full)
                if metadata:
                    try:os.utime(full,ns=(mt,mt),follow_symlinks=False)
                    except OSError:pass
                continue
            if storage and storage[0] in (S_CHUNKS,S_CDC):
                self._extract_chunked_verified(row,full)
            elif storage and storage[0]==S_SPARSE:
                # Create the logical length first, then write only allocated data extents. The gaps
                # remain filesystem holes instead of consuming disk blocks full of zeros.
                fd=os.open(full,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,'O_BINARY',0),mode or 0o666)
                try:
                    os.ftruncate(fd,size)
                    for off,ln,ids in storage[1]:
                        q=off
                        for idx in ids:
                            b=self._blob(idx);view=memoryview(b)
                            while view:
                                if hasattr(os,'pwrite'):
                                    n=os.pwrite(fd,view,q)
                                else:
                                    os.lseek(fd,q,os.SEEK_SET);n=os.write(fd,view)
                                view=view[n:];q+=n
                finally:os.close(fd)
            else:
                raw=self.read(rel)
                fd=os.open(full,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,'O_BINARY',0),mode or 0o666)
                try:
                    view=memoryview(raw)
                    while view:
                        n=os.write(fd,view);view=view[n:]
                finally:os.close(fd)
            if metadata:
                try:
                    # os.open created the requested mode on new files; chmod is needed only when an
                    # existing destination had a different mode (or umask masked creation bits).
                    if stat.S_IMODE(os.stat(full,follow_symlinks=False).st_mode)!=mode:os.chmod(full,mode)
                    os.utime(full,ns=(mt,mt),follow_symlinks=False)
                except OSError:pass
        if metadata:
            self._restore_extra_metadata(clean)
            for full,mode,mt in sorted(dirs,key=lambda x:x[0].count(os.sep),reverse=True):
                try:
                    if stat.S_IMODE(os.stat(full,follow_symlinks=False).st_mode)!=mode:os.chmod(full,mode)
                    os.utime(full,ns=(mt,mt),follow_symlinks=False)
                except OSError:pass
    def verify(self):
        n=0
        for row in self.files:
            if row[1]==K_DIR:continue
            raw=self.read(row[0]);want=self.file_sha256(row[0])
            if sha(raw)!=want:raise IOError(f'SHA-256 verification failure: {row[0]}')
            n+=1
        return n
    def _zip_dos_time(self,mtime_ns:int):
        # ZIP timestamps are DOS-local-time with two-second resolution. The native CMPCT metadata
        # remains nanosecond precision; only this legacy endpoint accepts ZIP's timestamp ceiling.
        t=time.localtime(mtime_ns/1_000_000_000 if mtime_ns else 315532800)
        y=min(2107,max(1980,t.tm_year));mo=min(12,max(1,t.tm_mon));d=min(31,max(1,t.tm_mday))
        zdate=((y-1980)<<9)|(mo<<5)|d;ztime=(t.tm_hour<<11)|(t.tm_min<<5)|(t.tm_sec//2)
        return ztime,zdate

    def _direct_deflate_stream(self,row):
        """Return (stream, crc32, usize) when a file already lives as exact raw Deflate bytes."""
        storage=row[6]
        if row[1] not in (K_FILE,K_SYMLINK) or not storage or storage[0]!=S_BLOB:return None
        idx=storage[1];off,us,cs,codec,ml=self.blobs[idx]
        if codec!=CODEC_DEFLATE:return None
        # ZIP's zero-recompression path bypasses _blob(). It must independently honor the
        # same signed logical owner and physical BHDR restrictions as ordinary reads.
        if type(row[4]) is not int or row[4]!=us:
            raise IOError('Deflate export logical owner size mismatch')
        pos=self.record_base+off
        if pos<self.record_base or pos+BHDR.size>len(self.mm):
            raise IOError('Deflate export blob header outside archive')
        m,c,flags,res,rus,rcs,rml,rcrc,rh=BHDR.unpack_from(self.mm,pos)
        if m!=BMAGIC or c!=CODEC_DEFLATE or flags or res or rus!=us or rcs!=cs or rml!=ml:
            raise IOError('Deflate export blob header mismatch')
        p=pos+BHDR.size+rml
        if p<0 or p+rcs>len(self.mm):
            raise IOError('Deflate export stream outside archive')
        return self.mm[p:p+rcs],rcrc,rus

    def export_zip(self,out:Path,level=6):
        """Export a conventional Deflate ZIP while reusing CMPCT's existing compressed streams.

        Footnote: Python's ZipFile API necessarily inflates and re-Deflates every member. CMPCT can
        do better because many physical blobs already *are* exact raw Deflate streams inherited from
        nested ZIP provenance. This writer copies those bytes straight into standards-compliant ZIP
        local records. Members without a reusable stream are compressed normally; if Deflate grows
        them, STORE is selected instead. ZIP64-sized members fall back to ZipFile in this prototype.
        """
        out=Path(out);entries=[];offset=0
        # Keep the compatibility writer intentionally conservative until its ZIP64 branch is native.
        if any(x[4]>=0xffffffff for x in self.files):
            with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=level,allowZip64=True) as z:
                for rel,k,mode,mt,size,h,storage in self.files:
                    zi=zipfile.ZipInfo(rel.rstrip('/')+'/' if k==K_DIR else rel)
                    zi.create_system=3
                    typ=stat.S_IFDIR if k==K_DIR else (stat.S_IFLNK if k==K_SYMLINK else stat.S_IFREG)
                    zi.external_attr=((typ|mode)&0xffff)<<16
                    z.writestr(zi,b'' if k==K_DIR else self.read(rel),compress_type=(zipfile.ZIP_STORED if k==K_DIR else zipfile.ZIP_DEFLATED),compresslevel=level)
            return out
        with open(out,'wb') as f:
            for row in self.files:
                rel,k,mode,mt,size,h,storage=row
                name=(rel.rstrip('/')+'/' if k==K_DIR else rel).encode('utf-8');flags=0x800
                ztime,zdate=self._zip_dos_time(mt);local_off=offset
                if k==K_DIR:
                    raw=b'';method=0;comp=b'';crc=0;usize=0
                else:
                    direct=self._direct_deflate_stream(row)
                    if direct is not None:
                        comp,crc,usize=direct;method=8
                    else:
                        raw=self.read(rel);usize=len(raw);crc=binascii.crc32(raw)&0xffffffff
                        co=zlib.compressobj(level,zlib.DEFLATED,-15);dc=co.compress(raw)+co.flush()
                        if len(dc)+4<len(raw):method=8;comp=dc
                        else:method=0;comp=raw
                csize=len(comp)
                lfh=LFH.pack(LFHS,20,flags,method,ztime,zdate,crc,csize,usize,len(name),0)
                f.write(lfh);f.write(name);f.write(comp);offset+=len(lfh)+len(name)+csize
                typ=stat.S_IFDIR if k==K_DIR else (stat.S_IFLNK if k==K_SYMLINK else stat.S_IFREG)
                ext=((typ|mode)&0xffff)<<16
                if k==K_DIR:ext|=0x10
                entries.append((name,flags,method,ztime,zdate,crc,csize,usize,ext,local_off))
            cd_start=offset
            for name,flags,method,ztime,zdate,crc,csize,usize,ext,local_off in entries:
                # 3 = Unix host system in version-made-by high byte; 20 = ZIP 2.0 feature version.
                cdh=ZCDH.pack(0x02014b50,(3<<8)|20,20,flags,method,ztime,zdate,crc,csize,usize,len(name),0,0,0,0,ext,local_off)
                f.write(cdh);f.write(name);offset+=len(cdh)+len(name)
            cd_size=offset-cd_start;n=len(entries)
            if n>0xffff or cd_start>0xffffffff or cd_size>0xffffffff:raise OverflowError('ZIP64 central directory not implemented in fast endpoint')
            eocd=ZEOCD.pack(0x06054b50,0,0,n,n,cd_size,cd_start,0);f.write(eocd)
        return out