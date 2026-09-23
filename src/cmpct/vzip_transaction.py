from __future__ import annotations

"""Transactional staging for speculative VZIP recipe construction."""

import binascii
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable
import zipfile

from .codec import LFH, make_vzip_recipe, sha


@dataclass(frozen=True)
class StagedVzipRecipe:
    recipe: object
    candidates: tuple[tuple[bytes, str, bytes | None, bytes], ...]


def _staging_peak_upper_bound(path: Path) -> int | None:
    """Conservatively bound dominant recipe-construction byte buffers before allocation."""
    try:
        physical = int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:
            logical = sum(int(info.file_size) for info in z.infolist() if not info.is_dir())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile):
        return None
    return physical * 4 + logical


def _staging_peak_upper_bound_bytes(original: bytes) -> int | None:
    """Same conservative 4P+L bound, but over Builder's already-read immutable bytes."""
    try:
        with zipfile.ZipFile(BytesIO(original)) as z:
            logical = sum(int(info.file_size) for info in z.infolist() if not info.is_dir())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile):
        return None
    return len(original) * 4 + logical


def _make_exact_retained_recipe_bytes(original: bytes, add_content: Callable):
    """Build the retained-stream recipe from one immutable in-memory ZIP image.

    Hidden discovery already paid to read these exact bytes. Reusing that snapshot removes the later
    private-file write/read cycle without weakening content identity: callers bind the snapshot digest
    and filesystem stamp during discovery/proof, while this parser never re-enters the mutable path.
    """
    original = bytes(original); payloads=[]; spans=[]; bio=BytesIO(original)
    with zipfile.ZipFile(bio) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda x:x.header_offset)
        for info in infos:
            bio.seek(info.header_offset);v=LFH.unpack(bio.read(LFH.size));nl,xl=v[-2],v[-1]
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
    return _make_exact_retained_recipe_bytes(Path(path).read_bytes(), add_content)


def _stage_with(stage_source, *, max_retained_bytes: int | None, exact_stream_retention: bool) -> StagedVzipRecipe | None:
    staged: list[tuple[bytes, str, bytes | None, bytes]] = []
    def stage(raw: bytes, hint: str = "", deflate_stream: bytes | None = None):
        raw = bytes(raw); stream = None if deflate_stream is None else bytes(deflate_stream); ref = sha(raw)
        staged.append((raw, hint, stream, ref)); return ref
    if isinstance(stage_source, bytes):
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound_bytes(stage_source)
            if bound is None or bound > int(max_retained_bytes): return None
        recipe=_make_exact_retained_recipe_bytes(stage_source, stage) if exact_stream_retention else None
    else:
        path=Path(stage_source)
        if max_retained_bytes is not None:
            bound=_staging_peak_upper_bound(path)
            if bound is None or bound > int(max_retained_bytes): return None
        recipe=_make_exact_retained_recipe(path, stage) if exact_stream_retention else make_vzip_recipe(path, stage)
    if recipe is None:return None
    return StagedVzipRecipe(recipe, tuple(staged))


def stage_vzip_recipe(path: Path, *, max_retained_bytes: int | None = None, exact_stream_retention: bool = False) -> StagedVzipRecipe | None:
    """Build a complete recipe/candidate set without mutating Builder state."""
    return _stage_with(Path(path), max_retained_bytes=max_retained_bytes, exact_stream_retention=exact_stream_retention)


def stage_vzip_recipe_bytes(raw: bytes, *, max_retained_bytes: int | None = None, exact_stream_retention: bool = True) -> StagedVzipRecipe | None:
    """Stage a hidden retained-stream recipe from Builder's already-read immutable snapshot."""
    if not exact_stream_retention:
        raise ValueError("in-memory staging is currently scoped to hidden exact-stream retention")
    return _stage_with(bytes(raw), max_retained_bytes=max_retained_bytes, exact_stream_retention=True)


def commit_staged_vzip(staged: StagedVzipRecipe, add_content: Callable):
    for raw, hint, stream, expected in staged.candidates:
        got = add_content(raw, hint, stream)
        if got != expected:raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return staged.recipe


def make_vzip_recipe_transactional(path: Path, add_content: Callable):
    staged = stage_vzip_recipe(path)
    if staged is None:return None
    return commit_staged_vzip(staged, add_content)
