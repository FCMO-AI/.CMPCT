from __future__ import annotations
"""v0.30 release-owned bounded r24 materialization.

The v0.29 Builder remains untouched unless the existing v0.30 shipping-owner predicate
matches. Archive grammar, codec choice and canonical ordering are unchanged.
"""
import binascii, tempfile, zipfile
from pathlib import Path
import msgpack
import cmpct.builder as B
from cmpct._ordered_pull import ordered_worker_iter
from cmpct.v030_release_locality import _shipping_release_builder

SPOOL_MEMORY_LIMIT=16*1024*1024
_ORIGINAL_BUILD=B.Builder.build

class StreamedBuilder(B.Builder):
    def build(self,out:Path):
        self.scan(); self._build_micro_packs(); self._prepare_deflate_reuse(); self._train_dictionary()
        hashes=sorted(self.cands)
        def encode(h):
            c=self.cands[h]; raw=c.raw
            codec,comp,meta=self._encode_candidate(h,c)
            return h,len(raw),binascii.crc32(raw)&0xffffffff,codec,comp,meta
        blobs=[]; offset=0; href={}; out=Path(out)
        with tempfile.SpooledTemporaryFile(max_size=SPOOL_MEMORY_LIMIT,prefix='cmpct-r24-records-',dir=out.parent) as spool:
            for h,raw_len,crc,codec,comp,meta in ordered_worker_iter(encode,hashes,self.encode_workers):
                rec_header=B.BHDR.pack(B.BMAGIC,codec,0,0,raw_len,len(comp),len(meta),crc,h)
                idx=len(blobs); href[h]=idx; rec_len=len(rec_header)+len(meta)+len(comp)
                blobs.append([offset,raw_len,len(comp),codec,len(meta)]); offset+=rec_len
                spool.write(rec_header); spool.write(meta); spool.write(comp)
                self.cands[h].raw=b''; del comp,meta
            def mapref(x): return href[bytes(x)]
            files=[]
            for row in self.files:
                rel,k,mode,mt,size,h,storage=row
                if storage and storage[0]==B.S_BLOB: storage=[B.S_BLOB,mapref(storage[1])]
                elif storage and storage[0]==B.S_CHUNKS: storage=[B.S_CHUNKS,[mapref(x) for x in storage[1]]]
                elif storage and storage[0]==B.S_CDC: storage=[B.S_CDC,[[ln,mapref(x)] for ln,x in storage[1]]]
                elif storage and storage[0]==B.S_SPARSE: storage=[B.S_SPARSE,[[off,ln,[mapref(x) for x in refs]] for off,ln,refs in storage[1]]]
                elif storage and storage[0]==B.S_PACK: storage=[B.S_PACK,mapref(storage[1]),storage[2],storage[3]]
                keep_hash=h if (storage and storage[0] in (B.S_CHUNKS,B.S_CDC,B.S_SPARSE)) else None
                files.append([rel,k,mode,mt,size,keep_hash,storage])
            recipes=[]
            for skref,lens,payloads,vsha,vsize,vcrc in self.recipes:
                mapped=[]
                for rawref,method,stream_hash,csize,level in payloads:
                    rawidx=mapref(rawref)
                    if method==zipfile.ZIP_STORED: mapped.append([rawidx,method,0,rawidx,csize,-1]); continue
                    if bytes(stream_hash)==self.canonical_deflate.get(bytes(rawref)): mapped.append([rawidx,method,0,rawidx,csize,level])
                    elif bytes(stream_hash) in self.secondary_stream_hashes: mapped.append([rawidx,method,1,mapref(stream_hash),csize,level])
                    else: mapped.append([rawidx,method,2,rawidx,csize,level])
                recipes.append([mapref(skref),lens,mapped,vsha,vsize,vcrc])
            owner_counts={}
            for row in files:
                uid,gid,_=self.meta_by_rel.get(row[0],(0,0,{})); owner_counts[(uid,gid)]=owner_counts.get((uid,gid),0)+1
            common_owner=max(owner_counts,key=owner_counts.get) if owner_counts else (0,0); owner_overrides=[]; xattrs=[]
            for i,row in enumerate(files):
                uid,gid,xa=self.meta_by_rel.get(row[0],(*common_owner,{}))
                if (uid,gid)!=common_owner: owner_overrides.append([i,uid,gid])
                if xa: xattrs.append([i,[[k,v] for k,v in sorted(xa.items())]])
            fsmeta={'owner':list(common_owner),'owner_overrides':owner_overrides,'xattrs':xattrs}
            index={'v':B.VERSION,'files':files,'blobs':blobs,'recipes':recipes,'dict_blob':(mapref(self.dict_hash) if self.dict_hash else None),'fsmeta':fsmeta,'features':['micro-solid-packs','nested-container-packs','transitive-pack-integrity','dedup','hardlinks','sparse-files','content-defined-chunking','chunk-seeking','parallel-chunks','zstd','zstd-dictionary','wavflac','deflate-reuse','virtual-zip-hybrid-recompress','crc32-fastpath','sha256','dual-index','transaction-journal','uid-gid','xattrs']}
            ib=msgpack.packb(index,use_bin_type=True); ic=B.zc(ib,12); ih=B.sha(ib)
            header=B.HDR.pack(B.MAGIC,B.VERSION,0,len(ic),len(ib),offset,ih); footer=B.FTR.pack(B.FMAGIC,0,1,0,0,len(ic),len(ib),0,ih)
            spool.flush(); spool.seek(0)
            with out.open('wb') as dst:
                dst.write(header); dst.write(ic)
                while True:
                    chunk=spool.read(1024*1024)
                    if not chunk: break
                    dst.write(chunk)
                dst.write(ic); dst.write(footer)
        return {'bytes':out.stat().st_size,'logical_bytes':sum(x[4] for x in files if x[1]!=B.K_DIR),'unique_blobs':len(blobs),'logical_files':sum(x[1]!=B.K_DIR for x in files),'recipes':len(recipes),'index_raw':len(ib),'index_comp':len(ic),'data_bytes':offset,'encode_workers':self.encode_workers,'reproducible':self.reproducible}

def _release_owned_build(self,out):
    if _shipping_release_builder(self):
        return StreamedBuilder.build(self,out)
    return _ORIGINAL_BUILD(self,out)

def install_v030_release_materialization_guard()->None:
    if B.Builder.build is not _release_owned_build:
        B.Builder.build=_release_owned_build

install_v030_release_materialization_guard()
