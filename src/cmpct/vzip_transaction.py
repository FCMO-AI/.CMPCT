from __future__ import annotations

"""Transactional staging for speculative VZIP recipe construction."""

import binascii
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import zipfile

from .codec import LFH, make_vzip_recipe, sha


@dataclass(frozen=True)
class StagedVzipRecipe:
    recipe: object
    candidates: tuple[tuple[bytes, str, bytes | None, bytes], ...]


class _BytesView:
    """Minimal seekable read-only view over immutable bytes without a second full-buffer copy."""
    def __init__(self, raw: bytes): self.raw=raw;self.pos=0
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        if whence==0:pos=int(offset)
        elif whence==1:pos=self.pos+int(offset)
        elif whence==2:pos=len(self.raw)+int(offset)
        else:raise ValueError("invalid whence")
        if pos<0:raise ValueError("negative seek")
        self.pos=pos;return pos
    def read(self, n=-1):
        if n is None or int(n)<0:end=len(self.raw)
        else:end=min(len(self.raw),self.pos+int(n))
        out=self.raw[self.pos:end];self.pos=end;return out
    def seekable(self):return True
    def readable(self):return True


def _staging_peak_upper_bound(path: Path) -> int | None:
    try:
        physical=int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:logical=sum(int(i.file_size) for i in z.infolist() if not i.is_dir())
    except (OSError,ValueError,RuntimeError,zipfile.BadZipFile):return None
    return physical*4+logical


def _staging_peak_upper_bound_bytes(original: bytes) -> int | None:
    try:
        with zipfile.ZipFile(_BytesView(original)) as z:logical=sum(int(i.file_size) for i in z.infolist() if not i.is_dir())
    except (OSError,ValueError,RuntimeError,zipfile.BadZipFile):return None
    return len(original)*4+logical


def _make_exact_retained_recipe_bytes(original: bytes, add_content: Callable):
    """Build retained-stream VZIP from Builder's one immutable discovery snapshot."""
    original=bytes(original);payloads=[];spans=[];view=_BytesView(original)
    with zipfile.ZipFile(view) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda x:x.header_offset)
        for info in infos:
            view.seek(info.header_offset);v=LFH.unpack(view.read(LFH.size));nl,xl=v[-2],v[-1]
            start=info.header_offset+LFH.size+nl+xl;end=start+info.compress_size
            raw=z.read(info);stream=original[start:end]
            if info.compress_type==zipfile.ZIP_STORED:
                cref=add_content(raw,Path(info.filename).suffix.lower());stream_hash=b'';level=-1
            elif info.compress_type==zipfile.ZIP_DEFLATED:
                cref=add_content(raw,Path(info.filename).suffix.lower(),stream);stream_hash=sha(stream);level=0
            else:return None
            spans.append((start,end));payloads.append([cref,info.compress_type,stream_hash,len(stream),level])
    literals=[];cursor=0
    for start,end in spans:literals.append(original[cursor:start]);cursor=end
    literals.append(original[cursor:]);skeleton=b''.join(literals);lens=[len(x) for x in literals]
    skref=add_content(skeleton,'.cmpct-skeleton')
    return [skref,lens,payloads,sha(original),len(original),binascii.crc32(original)&0xffffffff]


def _make_exact_retained_recipe(path: Path, add_content: Callable):
    return _make_exact_retained_recipe_bytes(Path(path).read_bytes(),add_content)


def _stage_with(stage_source, *, max_retained_bytes: int | None, exact_stream_retention: bool) -> StagedVzipRecipe | None:
    staged=[]
    def stage(raw:bytes,hint:str="",deflate_stream:bytes|None=None):
        raw=bytes(raw);stream=None if deflate_stream is None else bytes(deflate_stream);ref=sha(raw);staged.append((raw,hint,stream,ref));return ref
    if isinstance(stage_source,bytes):
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound_bytes(stage_source)
            if bound is None or bound>int(max_retained_bytes):return None
        recipe=_make_exact_retained_recipe_bytes(stage_source,stage) if exact_stream_retention else None
    else:
        path=Path(stage_source)
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound(path)
            if bound is None or bound>int(max_retained_bytes):return None
        recipe=_make_exact_retained_recipe(path,stage) if exact_stream_retention else make_vzip_recipe(path,stage)
    if recipe is None:return None
    return StagedVzipRecipe(recipe,tuple(staged))


def stage_vzip_recipe(path:Path,*,max_retained_bytes:int|None=None,exact_stream_retention:bool=False)->StagedVzipRecipe|None:
    return _stage_with(Path(path),max_retained_bytes=max_retained_bytes,exact_stream_retention=exact_stream_retention)


def stage_vzip_recipe_bytes(raw:bytes,*,max_retained_bytes:int|None=None,exact_stream_retention:bool=True)->StagedVzipRecipe|None:
    if not exact_stream_retention:raise ValueError("in-memory staging is currently scoped to hidden exact-stream retention")
    return _stage_with(bytes(raw),max_retained_bytes=max_retained_bytes,exact_stream_retention=True)


def commit_staged_vzip(staged:StagedVzipRecipe,add_content:Callable):
    for raw,hint,stream,expected in staged.candidates:
        got=add_content(raw,hint,stream)
        if got!=expected:raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return staged.recipe


def make_vzip_recipe_transactional(path:Path,add_content:Callable):
    staged=stage_vzip_recipe(path)
    if staged is None:return None
    return commit_staged_vzip(staged,add_content)
