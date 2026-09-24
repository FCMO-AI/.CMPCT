from __future__ import annotations

"""Transactional staging for speculative VZIP recipe construction."""
import binascii
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import zipfile
from .codec import LFH,make_vzip_recipe,sha

@dataclass(frozen=True)
class StagedVzipRecipe:
    recipe:object
    candidates:tuple[tuple[bytes,str,bytes|None,bytes],...]

class _BytesView:
    def __init__(self,raw:bytes):self.raw=raw;self.pos=0
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        if whence==0:pos=int(offset)
        elif whence==1:pos=self.pos+int(offset)
        elif whence==2:pos=len(self.raw)+int(offset)
        else:raise ValueError('invalid whence')
        if pos<0:raise ValueError('negative seek')
        self.pos=pos;return pos
    def read(self,n=-1):
        end=len(self.raw) if n is None or int(n)<0 else min(len(self.raw),self.pos+int(n));out=self.raw[self.pos:end];self.pos=end;return out
    def seekable(self):return True
    def readable(self):return True

def _staging_peak_upper_bound(path:Path)->int|None:
    try:
        physical=int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:logical=sum(int(i.file_size) for i in z.infolist() if not i.is_dir())
    except (OSError,ValueError,RuntimeError,zipfile.BadZipFile):return None
    return physical*4+logical

def _staging_peak_upper_bound_bytes(original:bytes)->int|None:
    try:
        with zipfile.ZipFile(_BytesView(original)) as z:logical=sum(int(i.file_size) for i in z.infolist() if not i.is_dir())
    except (OSError,ValueError,RuntimeError,zipfile.BadZipFile):return None
    return len(original)*4+logical

def _make_exact_retained_recipe_bytes(original:bytes,add_content:Callable,validated_deflates:dict|None=None):
    """Build retained-stream VZIP, reusing only previously CRC-validated identical Deflate streams."""
    original=bytes(original);payloads=[];spans=[];view=_BytesView(original);validated_deflates=validated_deflates if validated_deflates is not None else {}
    with zipfile.ZipFile(view) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda x:x.header_offset)
        for info in infos:
            view.seek(info.header_offset);v=LFH.unpack(view.read(LFH.size));nl,xl=v[-2],v[-1];start=info.header_offset+LFH.size+nl+xl;end=start+info.compress_size;stream=original[start:end]
            if info.compress_type==zipfile.ZIP_STORED:
                raw=stream;cref=add_content(raw,Path(info.filename).suffix.lower());stream_hash=b'';level=-1
            elif info.compress_type==zipfile.ZIP_DEFLATED:
                stream_hash=sha(stream);key=(int(info.compress_size),int(info.file_size),int(info.CRC),stream_hash)
                raw=validated_deflates.get(key)
                if raw is None:
                    # ZipFile.read is the authoritative CRC/length validation. Only bytes that survive
                    # it enter the cache, and callers publish a candidate-local cache only after the
                    # source's final live digest rebind succeeds.
                    raw=z.read(info);validated_deflates[key]=raw
                cref=add_content(raw,Path(info.filename).suffix.lower(),stream);level=0
            else:return None
            spans.append((start,end));payloads.append([cref,info.compress_type,stream_hash,len(stream),level])
    literals=[];cursor=0
    for start,end in spans:literals.append(original[cursor:start]);cursor=end
    literals.append(original[cursor:]);skeleton=b''.join(literals);lens=[len(x) for x in literals];skref=add_content(skeleton,'.cmpct-skeleton')
    return [skref,lens,payloads,sha(original),len(original),binascii.crc32(original)&0xffffffff]

def _make_exact_retained_recipe(path:Path,add_content:Callable,validated_deflates=None):return _make_exact_retained_recipe_bytes(Path(path).read_bytes(),add_content,validated_deflates)

def _stage_with(stage_source,*,max_retained_bytes:int|None,exact_stream_retention:bool,validated_deflates:dict|None=None)->StagedVzipRecipe|None:
    staged=[]
    def stage(raw:bytes,hint:str='',deflate_stream:bytes|None=None):
        raw=bytes(raw);stream=None if deflate_stream is None else bytes(deflate_stream);ref=sha(raw);staged.append((raw,hint,stream,ref));return ref
    if isinstance(stage_source,bytes):
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound_bytes(stage_source)
            if bound is None or bound>int(max_retained_bytes):return None
        recipe=_make_exact_retained_recipe_bytes(stage_source,stage,validated_deflates) if exact_stream_retention else None
    else:
        path=Path(stage_source)
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound(path)
            if bound is None or bound>int(max_retained_bytes):return None
        recipe=_make_exact_retained_recipe(path,stage,validated_deflates) if exact_stream_retention else make_vzip_recipe(path,stage)
    if recipe is None:return None
    return StagedVzipRecipe(recipe,tuple(staged))

def stage_vzip_recipe(path:Path,*,max_retained_bytes:int|None=None,exact_stream_retention:bool=False,validated_deflates:dict|None=None)->StagedVzipRecipe|None:
    return _stage_with(Path(path),max_retained_bytes=max_retained_bytes,exact_stream_retention=exact_stream_retention,validated_deflates=validated_deflates)
def stage_vzip_recipe_bytes(raw:bytes,*,max_retained_bytes:int|None=None,exact_stream_retention:bool=True,validated_deflates:dict|None=None)->StagedVzipRecipe|None:
    if not exact_stream_retention:raise ValueError('in-memory staging is currently scoped to hidden exact-stream retention')
    return _stage_with(bytes(raw),max_retained_bytes=max_retained_bytes,exact_stream_retention=True,validated_deflates=validated_deflates)
def commit_staged_vzip(staged:StagedVzipRecipe,add_content:Callable):
    for raw,hint,stream,expected in staged.candidates:
        got=add_content(raw,hint,stream)
        if got!=expected:raise ValueError('transactional VZIP add_content returned a non-content-addressed reference')
    return staged.recipe
def commit_staged_vzip_prehashed(staged:StagedVzipRecipe,builder):
    from .builder import Candidate
    for raw,hint,stream,expected in staged.candidates:
        h=bytes(expected);c=builder.cands.get(h)
        if c is None:c=Candidate(raw,{hint} if hint else set(),{});builder.cands[h]=c
        elif hint:c.hints.add(hint)
        if stream is not None:
            sh=sha(stream);slot=c.deflates.get(sh)
            if slot is None:c.deflates[sh]=[stream,1]
            else:slot[1]+=1
    return staged.recipe
def make_vzip_recipe_transactional(path:Path,add_content:Callable):
    staged=stage_vzip_recipe(path)
    if staged is None:return None
    return commit_staged_vzip(staged,add_content)
