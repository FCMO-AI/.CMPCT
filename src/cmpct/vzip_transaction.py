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


def _staging_peak_upper_bound(path: Path) -> int | None:
    """Conservatively bound dominant recipe-construction byte buffers before allocation.

    ``make_vzip_recipe`` can simultaneously hold: the original container (P), a mutable skeleton
    copy (P), the immutable skeleton bytes passed to staging (P), exact compressed streams whose
    aggregate is at most P, and decoded member payloads (L). Therefore ``4*P + L`` is the relevant
    conservative peak bound for this implementation, not the smaller steady retained state after the
    original/skeleton temporaries leave scope.
    """
    try:
        physical = int(path.stat().st_size)
        with zipfile.ZipFile(path) as z:
            logical = sum(int(info.file_size) for info in z.infolist() if not info.is_dir())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile):
        return None
    return physical * 4 + logical


def _make_exact_retained_recipe(path: Path, add_content: Callable):
    """Build VZIP without searching for a zlib regeneration level.

    Hidden winners now retain every exact Deflate stream they introduce. Their recipes therefore never
    need mode-2 regeneration, making the ten-level search pure exported create work. Keep the ordinary
    recipe builder unchanged; this fast path is valid only when the caller also guarantees exact-stream
    retention before Builder maps the recipe. ``level=0`` is a schema-valid inert placeholder for the
    retained modes and must never become a mode-2 fallback.
    """
    path=Path(path);original=path.read_bytes();payloads=[];spans=[]
    with zipfile.ZipFile(path) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda x:x.header_offset)
        with path.open('rb') as f:
            for info in infos:
                f.seek(info.header_offset);v=LFH.unpack(f.read(LFH.size));nl,xl=v[-2],v[-1]
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


def stage_vzip_recipe(path: Path, *, max_retained_bytes: int | None = None, exact_stream_retention: bool = False) -> StagedVzipRecipe | None:
    """Build a complete recipe/candidate set without mutating Builder state.

    ``max_retained_bytes`` is a peak staging-memory ceiling despite the historical parameter name.
    Refusal happens from central-directory metadata before recipe construction can allocate decoded
    member/skeleton buffers; a separate post-stage check remains at the cohort layer.
    """
    if max_retained_bytes is not None:
        bound = _staging_peak_upper_bound(Path(path))
        if bound is None or bound > int(max_retained_bytes): return None
    staged: list[tuple[bytes, str, bytes | None, bytes]] = []
    def stage(raw: bytes, hint: str = "", deflate_stream: bytes | None = None):
        raw = bytes(raw); stream = None if deflate_stream is None else bytes(deflate_stream); ref = sha(raw)
        staged.append((raw, hint, stream, ref)); return ref
    recipe = _make_exact_retained_recipe(Path(path), stage) if exact_stream_retention else make_vzip_recipe(Path(path), stage)
    if recipe is None:return None
    return StagedVzipRecipe(recipe, tuple(staged))


def commit_staged_vzip(staged: StagedVzipRecipe, add_content: Callable):
    for raw, hint, stream, expected in staged.candidates:
        got = add_content(raw, hint, stream)
        if got != expected:raise ValueError("transactional VZIP add_content returned a non-content-addressed reference")
    return staged.recipe


def make_vzip_recipe_transactional(path: Path, add_content: Callable):
    staged = stage_vzip_recipe(path)
    if staged is None:return None
    return commit_staged_vzip(staged, add_content)
