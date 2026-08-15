from __future__ import annotations

# Footnote: the builder is intentionally separated from reader semantics. Encoder heuristics may
# evolve aggressively pre-1.0, while a frozen reader must eventually remain compatible with old
# archives. Keep representation-selection policy here rather than teaching the reader heuristics.

import base64, binascii, concurrent.futures, ctypes, ctypes.util, hashlib, io, json, os, shutil, stat, struct, subprocess, tempfile, time, zipfile, zlib
from dataclasses import dataclass
from pathlib import Path
import msgpack

from .codec import *
from .codec import _audio_modules, _compressed_payload, _hash_sparse, _sparse_data_extents, _wav_parts

@dataclass
class Candidate:
    raw:bytes; hints:set; deflates:dict

class Builder:
    def __init__(self,root:Path, deflate_reuse_min:int|None=None):
        self.root=Path(root);self.cands:{}={};self.files=[];self.recipes=[];self.dictionary=b'';self.dict_hash=None;self.canonical_deflate={};self.secondary_stream_hashes=set();self.inode_first={};self.meta_by_rel={}
        # Exact Deflate streams below this size are regenerated from raw data + a one-byte zlib level.
        # 0 reproduces v0.17's maximum-speed policy; a huge value is the compact policy.
        self.deflate_reuse_min=int(os.environ.get('CMPCT_DEFLATE_REUSE_MIN','65536')) if deflate_reuse_min is None else int(deflate_reuse_min)
        self.micro_pack_target=int(os.environ.get('CMPCT_MICRO_PACK_TARGET',str(256*1024)))
        self.micro_pack_max_file=int(os.environ.get('CMPCT_MICRO_PACK_MAX_FILE',str(32*1024)))
    def add_content(self,raw:bytes,hint='',deflate_stream:bytes|None=None):
        h=sha(raw);c=self.cands.get(h)
        if c is None:
            c=Candidate(raw,{hint} if hint else set(),{});self.cands[h]=c
        elif hint:c.hints.add(hint)
        if deflate_stream is not None:
            sh=sha(deflate_stream);slot=c.deflates.get(sh)
            if slot is None:c.deflates[sh]=[deflate_stream,1]
            else:slot[1]+=1
        return h

    def _capture_fs_meta(self,path:str,rel:str,st):
        """Capture ownership and xattrs without bloating every file row.

        Footnote: uid/gid are later stored as one common owner plus sparse overrides. Extended
        attributes are only emitted for paths that actually have them. This keeps normal archives tiny
        while preserving Linux/macOS metadata that ZIP commonly drops. Unsupported filesystems simply
        produce an empty metadata record; no archive operation depends on xattr availability.
        """
        xa={}
        if hasattr(os,'listxattr'):
            try:
                for name in os.listxattr(path,follow_symlinks=False):
                    try:xa[name]=os.getxattr(path,name,follow_symlinks=False)
                    except OSError:pass
            except OSError:pass
        self.meta_by_rel[rel]=(int(getattr(st,'st_uid',0)),int(getattr(st,'st_gid',0)),xa)

    def scan(self):
        """Scan once with ``os.scandir`` and reuse each DirEntry stat result.

        Footnote: the pathlib implementation was pleasant but performed thousands of path parses,
        parent constructions and repeated ``stat`` calls on tiny-file trees. Archive creation is an I/O
        primitive; paying object-model overhead per member gave ZIP an artificial lead on source trees.
        This walker keeps deterministic lexical ordering and all link/sparse semantics while reducing
        the hot path to one directory enumeration + one lstat per entry.
        """
        virtual_ext={'.zip','.whl'};deferred=[]

        def walk(absdir:str,prefix:str=''):
            with os.scandir(absdir) as it: entries=sorted(it,key=lambda e:e.name)
            for e in entries:
                rel=f'{prefix}/{e.name}' if prefix else e.name
                st=e.stat(follow_symlinks=False);mode=stat.S_IMODE(st.st_mode);self._capture_fs_meta(e.path,rel,st)
                if stat.S_ISLNK(st.st_mode):
                    b=os.readlink(e.path).encode();ref=self.add_content(b,'.symlink')
                    self.files.append([rel,K_SYMLINK,mode,st.st_mtime_ns,len(b),sha(b),[S_BLOB,ref]]);continue
                if stat.S_ISDIR(st.st_mode):
                    self.files.append([rel,K_DIR,mode,st.st_mtime_ns,0,b'',None]);walk(e.path,rel);continue
                if not stat.S_ISREG(st.st_mode):continue
                if st.st_nlink>1:
                    ik=(st.st_dev,st.st_ino)
                    if ik in self.inode_first:
                        self.files.append([rel,K_HARDLINK,mode,st.st_mtime_ns,st.st_size,None,[self.inode_first[ik]]]);continue
                    self.inode_first[ik]=rel
                ext=os.path.splitext(e.name)[1].lower();p=Path(e.path)
                if ext in virtual_ext:deferred.append((p,rel,st,mode));continue
                sparse=_sparse_data_extents(p,st.st_size)
                if sparse is not None:
                    ex=[]
                    for off,data in sparse:
                        refs=[self.add_content(data[i:i+CHUNK],ext) for i in range(0,len(data),CHUNK)]
                        ex.append([off,len(data),refs])
                    self.files.append([rel,K_FILE,mode,st.st_mtime_ns,st.st_size,_hash_sparse(st.st_size,sparse),[S_SPARSE,ex]]);continue
                with open(e.path,'rb') as fh:raw=fh.read()
                if len(raw)>4*CHUNK and ext!='.wav':
                    # Large ordinary files use content-defined chunks. Explicit lengths make range
                    # reads independent of the chunker and let shifted/edited siblings reuse content.
                    parts=cdc_chunks(raw);entries=[[len(part),self.add_content(part,ext)] for part in parts]
                    self.files.append([rel,K_FILE,mode,st.st_mtime_ns,len(raw),sha(raw),[S_CDC,entries]])
                else:
                    ref=self.add_content(raw,ext);self.files.append([rel,K_FILE,mode,st.st_mtime_ns,len(raw),sha(raw),[S_BLOB,ref]])

        walk(os.fspath(self.root))

        # Many nested archives are a special case where *not* parsing them can be superior. Their
        # exact byte streams often share headers, names and compressor structure. Packing a cohort into
        # one modest Zstd block exploits that redundancy while the CMPCT index still gives each archive
        # its own offset/length. We require a cohort of 8+ so smaller sets can still use structural
        # virtualization/deduplication when that representation is better.
        if len(deferred)>=8:
            buf=bytearray();packed=[]
            for p,rel,st,mode in deferred:
                raw=p.read_bytes();off=len(buf);buf+=raw;packed.append((rel,st,mode,off,len(raw),sha(raw)))
            ph=self.add_content(bytes(buf),'.cmpct-container-pack')
            for rel,st,mode,off,ln,rh in packed:
                self.files.append([rel,K_FILE,mode,st.st_mtime_ns,ln,rh,[S_PACK,ph,off,ln]])
        else:
            for p,rel,st,mode in deferred:
                recipe=make_vzip_recipe(p,self.add_content)
                if recipe is None:
                    raw=p.read_bytes();ref=self.add_content(raw,p.suffix.lower());storage=[S_BLOB,ref]
                else:
                    rid=len(self.recipes);self.recipes.append(recipe);storage=[S_VZIP,rid]
                rawsha=sha(p.read_bytes());self.files.append([rel,K_FILE,mode,st.st_mtime_ns,st.st_size,rawsha,storage])
        self.files.sort(key=lambda x:x[0])

    def _build_micro_packs(self):
        """Pack tiny independent text-like blobs into seekable micro-solid Zstd blocks.

        Footnote: this is the universal-format answer to solid tar.zst's tiny-file advantage.
        A pack is small enough that one cold selective read still decompresses only ~256 KiB, while
        hundreds of related files share one compression context and one physical blob header. Files
        referenced by nested ZIP recipes are left independent so exact-container reconstruction does
        not gain a second representation. Duplicate logical files share the same slice automatically.
        """
        refs={}
        for row in self.files:
            if row[1]!=K_FILE or not row[6] or row[6][0]!=S_BLOB:continue
            h=bytes(row[6][1]);refs.setdefault(h,[]).append(row)
        eligible=[]
        for h,rows in refs.items():
            c=self.cands.get(h)
            if c is None or c.deflates or len(c.raw)>self.micro_pack_max_file:continue
            if not any(x in TEXT_EXT for x in c.hints):continue
            eligible.append((h,c))
        # Group by dominant extension before size packing. This gives Zstd a cleaner local model
        # without making the format depend on filenames or a language-specific codec.
        buckets={}
        for h,c in eligible:
            ext=next((x for x in sorted(c.hints) if x in TEXT_EXT),'.text')
            buckets.setdefault(ext,[]).append((h,c))
        for ext,items in sorted(buckets.items()):
            items.sort(key=lambda hc:(len(hc[1].raw),hc[0]))
            group=[];used=0
            def flush(group):
                if not group:return
                buf=bytearray();slots={}
                for h,c in group:
                    off=len(buf);buf+=c.raw;slots[h]=(off,len(c.raw))
                ph=self.add_content(bytes(buf),'.cmpct-pack')
                for h,(off,ln) in slots.items():
                    for row in refs[h]:row[6]=[S_PACK,ph,off,ln]
                # Once every logical reference points into the authenticated pack, the old tiny
                # content blob is physically redundant. The pack hash + hashed index authenticate
                # each slice, so no 32-byte per-file digest is needed in the logical table.
                for h in slots:
                    if h!=ph:self.cands.pop(h,None)
            for h,c in items:
                if group and used+len(c.raw)>self.micro_pack_target:
                    flush(group);group=[];used=0
                group.append((h,c));used+=len(c.raw)
            flush(group)

    def _prepare_deflate_reuse(self):
        # Choose one exact Deflate variant as the canonical physical representation for every
        # content blob that appears inside a nested ZIP/WHL. Secondary variants are tiny in this
        # corpus (~49 KiB total) and are stored once as opaque stream blobs.
        additions=[]
        for rh,c in list(self.cands.items()):
            if not c.deflates:continue
            chosen_hash,(chosen_bytes,chosen_count)=max(c.deflates.items(),key=lambda kv:(kv[1][1],-len(kv[1][0])))
            if len(chosen_bytes) >= self.deflate_reuse_min:
                self.canonical_deflate[rh]=chosen_hash
            for sh,(stream,count) in c.deflates.items():
                if sh==chosen_hash:continue
                if len(stream) >= self.deflate_reuse_min:additions.append((sh,stream))
        # Secondary variants obey the same retention cutoff. Large/hot variants stay zero-recompress;
        # tiny variants collapse to raw-content + zlib-level recipes.
        for sh,stream in additions:
            if sh not in self.cands:self.cands[sh]=Candidate(stream,{'.opaque-deflate'}, {})
            else:self.cands[sh].hints.add('.opaque-deflate')
            self.secondary_stream_hashes.add(sh)

    def _train_dictionary(self):
        # A dictionary recovers cross-file redundancy without grouping files into solid blocks, so
        # selective extraction remains one-file granular. The CLI trainer is a prototype stand-in
        # for libzstd's ZDICT API in a future native implementation.
        samples=[c.raw for c in self.cands.values() if len(c.raw)>=64 and '.cmpct-pack' not in c.hints and any(x in TEXT_EXT for x in c.hints)]
        # Micro-packing already recovers cross-file redundancy for tiny-source workloads. Training a
        # 24 KiB dictionary on a handful of survivors would only burn startup time and add bytes.
        if len(samples)<16 or sum(map(len,samples))<96*1024:return
        exe=shutil.which('zstd')
        if not exe:return
        with tempfile.TemporaryDirectory(prefix='cmpct-dict-') as td:
            d=Path(td);paths=[]
            for i,b in enumerate(samples):q=d/f'{i:05d}.sample';q.write_bytes(b);paths.append(str(q))
            out=d/'dict';r=subprocess.run([exe,'--train-fastcover=k=50,d=8,f=20,steps=4,split=75,accel=10',*paths,'--maxdict=24576','-o',str(out)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if r.returncode==0 and out.exists():
                self.dictionary=out.read_bytes();self.dict_hash=self.add_content(self.dictionary,'.zdict')

    def _encode_candidate(self,h:bytes,c:Candidate):
        raw=c.raw
        if self.dict_hash is not None and h==self.dict_hash:return CODEC_RAW,raw,b''
        if h in self.secondary_stream_hashes:return CODEC_RAW,raw,b''
        if h in self.canonical_deflate:
            sh=self.canonical_deflate[h];stream=c.deflates[sh][0]
            return CODEC_DEFLATE,stream,msgpack.packb([sh],use_bin_type=True)
        # Codec competition is intentional. A file extension is evidence, not a command: for example,
        # periodic PCM can compress *far* better with Deflate than FLAC even though FLAC is the obvious
        # audio codec. CMPCT therefore measures reversible candidates and chooses the smallest payload.
        # This keeps the format lossless while avoiding the classic archive mistake of hard-wiring one
        # compressor to one media type.
        best=None  # tuple(total_physical_bytes, codec, compressed_payload, metadata)
        def consider(codec:int, comp:bytes, meta:bytes=b''):
            nonlocal best
            total=len(comp)+len(meta)
            if best is None or total<best[0]:best=(total,codec,comp,meta)

        if '.wav' in c.hints:
            wf=wavflac_compress(raw)
            if wf:
                comp,meta=wf;consider(CODEC_WAVFLAC,comp,meta)
            # Raw DEFLATE remains valuable for some highly regular PCM waveforms. It is also directly
            # reusable by the legacy ZIP export path, so winning here improves size *and* compatibility.
            co=zlib.compressobj(9,zlib.DEFLATED,-15);dc=co.compress(raw)+co.flush()
            consider(CODEC_DEFLATE,dc,msgpack.packb([b'generated',9],use_bin_type=True))

        # Adaptive Zstd. We test a tiny level set and choose the smallest output, but cap effort for large data.
        levels=(15,12,9) if ('.cmpct-pack' in c.hints or '.cmpct-container-pack' in c.hints) else ((12,9,5) if len(raw)<64*1024 else ((9,5,3) if len(raw)<512*1024 else (5,3)))
        for lvl in levels:
            comp=zc(raw,lvl);consider(CODEC_ZSTD,comp,msgpack.packb([lvl],use_bin_type=True))
        if self.dictionary and any(x in TEXT_EXT for x in c.hints):
            dc=zcd(raw,self.dictionary,12);consider(CODEC_ZSTDDICT,dc,msgpack.packb([12],use_bin_type=True))
        if best and best[0]+16 < len(raw):return best[1],best[2],best[3]
        return CODEC_RAW,raw,b''
    def build(self,out:Path):
        self.scan();self._build_micro_packs();self._prepare_deflate_reuse();self._train_dictionary()
        # Materialize candidates in deterministic hash order. This makes identical logical trees reproducible.
        blobs=[];records=[];offset=0;href={}
        for h in sorted(self.cands):
            c=self.cands[h];codec,comp,meta=self._encode_candidate(h,c);raw=c.raw
            rec=BHDR.pack(BMAGIC,codec,0,0,len(raw),len(comp),len(meta),binascii.crc32(raw)&0xffffffff,h)+meta+comp
            idx=len(blobs);href[h]=idx;blobs.append([offset,len(raw),len(comp),codec,len(meta)]);records.append(rec);offset+=len(rec)
        def mapref(x):return href[bytes(x)]
        files=[]
        for row in self.files:
            rel,k,mode,mt,size,h,storage=row
            if storage and storage[0]==S_BLOB:storage=[S_BLOB,mapref(storage[1])]
            elif storage and storage[0]==S_CHUNKS:storage=[S_CHUNKS,[mapref(x) for x in storage[1]]]
            elif storage and storage[0]==S_CDC:storage=[S_CDC,[[ln,mapref(x)] for ln,x in storage[1]]]
            elif storage and storage[0]==S_SPARSE:
                storage=[S_SPARSE,[[off,ln,[mapref(x) for x in refs]] for off,ln,refs in storage[1]]]
            elif storage and storage[0]==S_PACK:
                storage=[S_PACK,mapref(storage[1]),storage[2],storage[3]]
            # Direct blobs already carry SHA-256 in their physical record; virtual ZIP recipes carry
            # the exact reconstructed-file SHA. Chunked/sparse files need one logical whole-file hash.
            keep_hash=h if (storage and storage[0] in (S_CHUNKS,S_CDC,S_SPARSE)) else None
            files.append([rel,k,mode,mt,size,keep_hash,storage])
        recipes=[]
        for skref,lens,payloads,vsha,vsize,vcrc in self.recipes:
            mapped=[]
            for rawref,method,stream_hash,csize,level in payloads:
                rawidx=mapref(rawref)
                if method==zipfile.ZIP_STORED:mapped.append([rawidx,method,0,rawidx,csize,-1]);continue
                if bytes(stream_hash)==self.canonical_deflate.get(bytes(rawref)):
                    mapped.append([rawidx,method,0,rawidx,csize,level])  # mode 0: canonical stream stored as blob payload.
                elif bytes(stream_hash) in self.secondary_stream_hashes:
                    mapped.append([rawidx,method,1,mapref(stream_hash),csize,level])  # mode 1: retained secondary exact stream.
                else:
                    mapped.append([rawidx,method,2,rawidx,csize,level])  # mode 2: deterministic zlib regeneration.
            recipes.append([mapref(skref),lens,mapped,vsha,vsize,vcrc])
        # Ownership is usually identical across an archive, so store the modal uid/gid once and only
        # encode exceptions. Xattrs are sparse by nature and keyed by file-table index.
        owner_counts={}
        for row in files:
            uid,gid,_=self.meta_by_rel.get(row[0],(0,0,{}));owner_counts[(uid,gid)]=owner_counts.get((uid,gid),0)+1
        common_owner=max(owner_counts,key=owner_counts.get) if owner_counts else (0,0)
        owner_overrides=[];xattrs=[]
        for i,row in enumerate(files):
            uid,gid,xa=self.meta_by_rel.get(row[0],(*common_owner,{}))
            if (uid,gid)!=common_owner:owner_overrides.append([i,uid,gid])
            if xa:xattrs.append([i,[[k,v] for k,v in sorted(xa.items())]])
        fsmeta={'owner':list(common_owner),'owner_overrides':owner_overrides,'xattrs':xattrs}
        index={'v':VERSION,'files':files,'blobs':blobs,'recipes':recipes,'dict_blob':(mapref(self.dict_hash) if self.dict_hash else None),'fsmeta':fsmeta,'features':['micro-solid-packs','nested-container-packs','transitive-pack-integrity','dedup','hardlinks','sparse-files','content-defined-chunking','chunk-seeking','parallel-chunks','zstd','zstd-dictionary','wavflac','deflate-reuse','virtual-zip-hybrid-recompress','crc32-fastpath','sha256','dual-index','transaction-journal','uid-gid','xattrs']}
        ib=msgpack.packb(index,use_bin_type=True);ic=zc(ib,12);ih=sha(ib);data=b''.join(records)
        header=HDR.pack(MAGIC,VERSION,0,len(ic),len(ib),len(data),ih)
        footer=FTR.pack(FMAGIC,0,1,0,0,len(ic),len(ib),0,ih)
        out=Path(out);out.write_bytes(header+ic+data+ic+footer)
        return {'bytes':out.stat().st_size,'logical_bytes':sum(x[4] for x in files if x[1]!=K_DIR),'unique_blobs':len(blobs),'logical_files':sum(x[1]!=K_DIR for x in files),'recipes':len(recipes),'index_raw':len(ib),'index_comp':len(ic),'data_bytes':len(data)}