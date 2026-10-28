from __future__ import annotations

"""Research-only bounded preflight for hidden ZIP discovery.

This is not a ZIP parser and does not change explicit .zip/.whl behavior. Its sole purpose is to decide whether an
extension-hidden PK candidate is safe enough to hand to the normal parser for *optional* virtualization research.
Rejected candidates simply remain ordinary files, so conservative limits do not weaken reconstruction semantics.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
import os
import struct

EOCD_SIG=b'PK\x05\x06'
EOCD_MIN=22
MAX_COMMENT=65535
MAX_TAIL=EOCD_MIN+MAX_COMMENT
# Security/compute ceilings for optional hidden-container discovery, not density tuning knobs.
MAX_ENTRIES=8192
MAX_CENTRAL_DIRECTORY=16*1024*1024
ZIP64_U16=0xFFFF
ZIP64_U32=0xFFFFFFFF


@dataclass(frozen=True)
class Preflight:
    eligible: bool
    reason: str
    file_size: int
    tail_bytes_read: int
    entries: int=0
    central_directory_size: int=0
    central_directory_offset: int=0
    eocd_offset: int=0

    def to_dict(self): return asdict(self)


def hidden_zip_preflight(path: Path) -> Preflight:
    path=Path(path)
    try:
        size=path.stat().st_size
        if size<EOCD_MIN:
            return Preflight(False,'too_small',size,0)
        tail_n=min(size,MAX_TAIL)
        with path.open('rb') as f:
            f.seek(size-tail_n); tail=f.read(tail_n)
        # Search backwards, then validate comment length so PK bytes inside a comment cannot become a false EOCD.
        pos=len(tail)
        while True:
            idx=tail.rfind(EOCD_SIG,0,pos)
            if idx<0:return Preflight(False,'eocd_not_found',size,len(tail))
            if idx+EOCD_MIN<=len(tail):
                disk,cd_disk,n_disk,n_total,cd_size,cd_off,comment_len=struct.unpack_from('<HHHHIIH',tail,idx+4)
                if idx+EOCD_MIN+comment_len==len(tail):break
            pos=idx
        absolute=size-tail_n+idx
        if disk!=0 or cd_disk!=0 or n_disk!=n_total:
            return Preflight(False,'multi_disk',size,len(tail),n_total,cd_size,cd_off,absolute)
        if n_total==ZIP64_U16 or cd_size==ZIP64_U32 or cd_off==ZIP64_U32:
            return Preflight(False,'zip64_optional_path_rejected',size,len(tail),n_total,cd_size,cd_off,absolute)
        if n_total==0:return Preflight(False,'empty_archive',size,len(tail),0,cd_size,cd_off,absolute)
        if n_total>MAX_ENTRIES:return Preflight(False,'entry_budget',size,len(tail),n_total,cd_size,cd_off,absolute)
        if cd_size>MAX_CENTRAL_DIRECTORY:return Preflight(False,'central_directory_budget',size,len(tail),n_total,cd_size,cd_off,absolute)
        if cd_off>absolute or cd_size>absolute-cd_off:
            return Preflight(False,'central_directory_bounds',size,len(tail),n_total,cd_size,cd_off,absolute)
        return Preflight(True,'eligible',size,len(tail),n_total,cd_size,cd_off,absolute)
    except (OSError,struct.error,ValueError):
        try:size=os.path.getsize(path)
        except OSError:size=0
        return Preflight(False,'io_or_structure_error',size,0)
