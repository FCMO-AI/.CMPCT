from __future__ import annotations

"""Research-only Builder that discovers valid ZIP containers by content, not suffix.

It publishes the *existing* S_VZIP representation and therefore changes no reader grammar.  Malformed suffix-routed
ZIPs fail closed to ordinary storage instead of aborting the build.  This module exists to validate discovery and
product economics before any change to the shipping Builder.
"""

from pathlib import Path
import os, stat, zipfile
from cmpct import builder as B

SUPPORTED={zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED}


def _valid_zip_content(path:Path)->bool:
    try:
        if path.stat().st_size<64:return False
        with path.open('rb') as f:
            if f.read(4)!=b'PK\x03\x04':return False
        with zipfile.ZipFile(path) as z:
            infos=[i for i in z.infolist() if not i.is_dir()]
            if not infos or any(i.compress_type not in SUPPORTED for i in infos):return False
            first=infos[0]
            with z.open(first) as r:r.read(min(first.file_size,4096))
        return True
    except Exception:return False


class ContentZipBuilder(B.Builder):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.content_zip_observed_files=0;self.content_zip_sniffed_bytes=0;self.content_zip_valid=0;self.content_zip_hidden=0;self.content_zip_parse_fallbacks=0

    def scan(self):
        virtual_ext={'.zip','.whl'};deferred=[]
        def walk(absdir:str,prefix:str=''):
            with os.scandir(absdir) as it:entries=sorted(it,key=lambda e:e.name)
            for e in entries:
                rel=f'{prefix}/{e.name}' if prefix else e.name
                st=e.stat(follow_symlinks=False);mode=stat.S_IMODE(st.st_mode);self._capture_fs_meta(e.path,rel,st)
                if stat.S_ISLNK(st.st_mode):
                    raw=os.readlink(e.path).encode();ref=self.add_content(raw,'.symlink');self.files.append([rel,B.K_SYMLINK,mode,st.st_mtime_ns,len(raw),B.sha(raw),[B.S_BLOB,ref]]);continue
                if stat.S_ISDIR(st.st_mode):
                    self.files.append([rel,B.K_DIR,mode,st.st_mtime_ns,0,b'',None]);walk(e.path,rel);continue
                if not stat.S_ISREG(st.st_mode):continue
                if st.st_nlink>1:
                    ik=(st.st_dev,st.st_ino)
                    if ik in self.inode_first:
                        self.files.append([rel,B.K_HARDLINK,mode,st.st_mtime_ns,st.st_size,None,[self.inode_first[ik]]]);continue
                    self.inode_first[ik]=rel
                ext=os.path.splitext(e.name)[1].lower();p=Path(e.path)
                self.content_zip_observed_files+=1;self.content_zip_sniffed_bytes+=min(4096,st.st_size)
                valid_zip=_valid_zip_content(p)
                if valid_zip:
                    self.content_zip_valid+=1
                    if ext not in virtual_ext:self.content_zip_hidden+=1
                    deferred.append((p,rel,st,mode));continue
                # A misleading .zip/.whl suffix is ordinary content, not a fatal parser command.
                if ext in virtual_ext:self.content_zip_parse_fallbacks+=1
                sparse=B._sparse_data_extents(p,st.st_size)
                if sparse is not None:
                    ex=[]
                    for off,data in sparse:
                        refs=[self.add_content(data[i:i+B.CHUNK],ext) for i in range(0,len(data),B.CHUNK)];ex.append([off,len(data),refs])
                    self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,st.st_size,B._hash_sparse(st.st_size,sparse),[B.S_SPARSE,ex]]);continue
                with open(e.path,'rb') as fh:raw=fh.read()
                if len(raw)>4*B.CHUNK and ext!='.wav':
                    parts=B.cdc_chunks(raw);entries=[[len(part),self.add_content(part,ext)] for part in parts];self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,len(raw),B.sha(raw),[B.S_CDC,entries]])
                else:
                    ref=self.add_content(raw,ext);self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,len(raw),B.sha(raw),[B.S_BLOB,ref]])
        walk(os.fspath(self.root))
        if len(deferred)>=8:
            buf=bytearray();packed=[]
            for p,rel,st,mode in deferred:
                raw=p.read_bytes();off=len(buf);buf+=raw;packed.append((rel,st,mode,off,len(raw),B.sha(raw)))
            ph=self.add_content(bytes(buf),'.cmpct-container-pack')
            for rel,st,mode,off,ln,rh in packed:self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,ln,rh,[B.S_PACK,ph,off,ln]])
        else:
            for p,rel,st,mode in deferred:
                try:recipe=B.make_vzip_recipe(p,self.add_content)
                except (zipfile.BadZipFile,EOFError,OSError,ValueError):
                    recipe=None;self.content_zip_parse_fallbacks+=1
                if recipe is None:
                    raw=p.read_bytes();ref=self.add_content(raw,p.suffix.lower());storage=[B.S_BLOB,ref]
                else:
                    rid=len(self.recipes);self.recipes.append(recipe);storage=[B.S_VZIP,rid]
                self.files.append([rel,B.K_FILE,mode,st.st_mtime_ns,st.st_size,B.sha(p.read_bytes()),storage])
        if self.reproducible:
            for row in self.files:row[3]=self.reproducible_epoch_ns
        self.files.sort(key=lambda x:x[0])

    def build(self,out:Path):
        stats=dict(super().build(out))
        stats.update({'content_zip_files_observed':self.content_zip_observed_files,'content_zip_sniffed_bytes_upper_bound':self.content_zip_sniffed_bytes,'content_zip_valid':self.content_zip_valid,'content_zip_hidden':self.content_zip_hidden,'content_zip_parse_fallbacks':self.content_zip_parse_fallbacks})
        return stats
