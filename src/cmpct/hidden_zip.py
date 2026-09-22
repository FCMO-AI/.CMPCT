from __future__ import annotations

"""Bounded, fail-closed envelope checks for optional hidden-ZIP discovery.

This module is deliberately not a second ZIP parser.  It cheaply rejects ordinary
files before any EOCD-tail read, then proves only that a conventional single-disk
central-directory envelope is bounded enough to hand to the existing exact VZIP
recipe machinery.  Any rejection means "store normally", never "fail the build".
"""

from dataclasses import dataclass
from pathlib import Path
import os
import struct

LOCAL_SIG = b"PK\x03\x04"
EOCD_SIG = b"PK\x05\x06"
EOCD_MIN = 22
MAX_COMMENT = 65535
MAX_TAIL = EOCD_MIN + MAX_COMMENT
MAX_ENTRIES = 8192
MAX_CENTRAL_DIRECTORY = 16 * 1024 * 1024
ZIP64_U16 = 0xFFFF
ZIP64_U32 = 0xFFFFFFFF


@dataclass(frozen=True)
class HiddenZipPreflight:
    eligible: bool
    reason: str
    file_size: int
    head_bytes_read: int
    tail_bytes_read: int
    entries: int = 0
    central_directory_size: int = 0
    central_directory_offset: int = 0
    eocd_offset: int = 0


def hidden_zip_preflight(path: Path) -> HiddenZipPreflight:
    """Return a conservative envelope verdict and exact discovery I/O accounting."""
    path = Path(path)
    head_read = 0
    try:
        size = path.stat().st_size
        if size < EOCD_MIN:
            return HiddenZipPreflight(False, "too_small", size, 0, 0)
        with path.open("rb") as f:
            head = f.read(4)
            head_read = len(head)
            # Optional discovery deliberately ignores prefixed/self-extracting ZIPs.  Exactness is
            # unaffected because rejected files continue through ordinary opaque storage.
            if head != LOCAL_SIG:
                return HiddenZipPreflight(False, "local_signature_miss", size, head_read, 0)
            tail_n = min(size, MAX_TAIL)
            f.seek(size - tail_n)
            tail = f.read(tail_n)

        pos = len(tail)
        while True:
            idx = tail.rfind(EOCD_SIG, 0, pos)
            if idx < 0:
                return HiddenZipPreflight(False, "eocd_not_found", size, head_read, len(tail))
            if idx + EOCD_MIN <= len(tail):
                disk, cd_disk, n_disk, n_total, cd_size, cd_off, comment_len = struct.unpack_from(
                    "<HHHHIIH", tail, idx + 4
                )
                if idx + EOCD_MIN + comment_len == len(tail):
                    break
            pos = idx

        absolute = size - tail_n + idx
        if disk != 0 or cd_disk != 0 or n_disk != n_total:
            return HiddenZipPreflight(False, "multi_disk", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if n_total == ZIP64_U16 or cd_size == ZIP64_U32 or cd_off == ZIP64_U32:
            return HiddenZipPreflight(False, "zip64_optional_path_rejected", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if n_total == 0:
            return HiddenZipPreflight(False, "empty_archive", size, head_read, len(tail), 0, cd_size, cd_off, absolute)
        if n_total > MAX_ENTRIES:
            return HiddenZipPreflight(False, "entry_budget", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if cd_size > MAX_CENTRAL_DIRECTORY:
            return HiddenZipPreflight(False, "central_directory_budget", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        if cd_off > absolute or cd_size > absolute - cd_off:
            return HiddenZipPreflight(False, "central_directory_bounds", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
        return HiddenZipPreflight(True, "eligible", size, head_read, len(tail), n_total, cd_size, cd_off, absolute)
    except (OSError, struct.error, ValueError):
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        return HiddenZipPreflight(False, "io_or_structure_error", size, head_read, 0)
