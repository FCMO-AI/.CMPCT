from __future__ import annotations

"""Candidate v0.30 Builder scan seam for bounded hidden-ZIP discovery.

The ordinary non-PK path stays structurally identical to canonical Builder. Hidden machinery is imported
only after a non-explicit file actually begins with the ZIP local-header signature, so ordinary trees do
not pay parser/proof module import cost merely because the optional capability exists.
"""

import os
import stat
from pathlib import Path

from .builder import Builder
from .codec import *
from .codec import _hash_sparse, _sparse_data_extents


def _scan_with_hidden_zip(self: Builder):
    virtual_ext={'.zip','.whl'};deferred=[];hidden_deferred=[]
    hidden_surface_bytes=0;hidden_surface_overflow=False;hidden_api=None

    def api():
        nonlocal hidden_api
        if hidden_api is None:
            from . import builder_hidden_zip as hidden_api_module
            hidden_api=hidden_api_module
        return hidden_api

    def walk(absdir:str,prefix:str=''):
        nonlocal hidden_surface_bytes,hidden_surface_overflow
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

            # A four-byte discriminator is the only new work on ordinary scan data. Load the colder
            # proof/staging stack only after the signature fires. Enforce cohort ceilings before another
            # deferred record is allocated; once overflow occurs, disable the entire optional cohort.
            if raw.startswith(b'PK\x03\x04') and not hidden_surface_overflow:
                H=api()
                if H.hidden_candidate_size_can_stage(len(raw)):
                    next_bytes=hidden_surface_bytes+len(raw)
                    if len(hidden_deferred)<H.MAX_OBSERVATION_FILES and next_bytes<=H.MAX_HIDDEN_SURFACE_AGGREGATE_BYTES:
                        surfaced=H.surface_hidden_candidate(rel,p,st,raw)
                        hidden_deferred.append(H.DeferredHiddenFile(surfaced,mode,st.st_mtime_ns,ext))
                        hidden_surface_bytes=next_bytes
                        continue
                    hidden_surface_overflow=True

            if len(raw)>4*CHUNK and ext!='.wav':
                parts=cdc_chunks(raw);entries=[[len(part),self.add_content(part,ext)] for part in parts]
                self.files.append([rel,K_FILE,mode,st.st_mtime_ns,len(raw),sha(raw),[S_CDC,entries]])
            else:
                ref=self.add_content(raw,ext);self.files.append([rel,K_FILE,mode,st.st_mtime_ns,len(raw),sha(raw),[S_BLOB,ref]])

    walk(os.fspath(self.root))

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

    if hidden_deferred:
        H=api()
        if hidden_surface_overflow:H.finalize_hidden_fallback_only(self,hidden_deferred)
        else:H.finalize_deferred_hidden_files(self,hidden_deferred)

    if self.reproducible:
        for row in self.files:row[3]=self.reproducible_epoch_ns
    self.files.sort(key=lambda x:x[0])


def install() -> None:
    # Package initialization later wraps scan with release-locality enforcement. A reload of this draft
    # module must not clobber that outer wrapper, so installation is one-shot on the Builder class.
    if getattr(Builder,"_cmpct_v030_hidden_zip_scan_installed",False):return
    Builder.scan=_scan_with_hidden_zip
    Builder._cmpct_v030_hidden_zip_scan_installed=True


install()
