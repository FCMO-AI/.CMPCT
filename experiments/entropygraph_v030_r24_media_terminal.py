"""Release-only structural terminal admission for already-encoded opaque media.

This policy exists to stop the v0.30 product from building expensive r25/G0-G4 candidates when canonical r24 is
already a strict size+creation win against the frozen ZIP/Deflate-9 and solid Zstd-19 comparators. Admission is
content-agnostic with respect to benchmark identity: it uses only regular-file shape, bounded magic-byte inspection,
and a bounded entropy sample from files recognized as already-encoded media.

The original magic/shape rule was intentionally rejected after an unseen compressible JPEG-magic impostor showed
that magic alone can terminalize a file family which Zstd-19 compresses much better. The promoted rule therefore
retains that counterexample as a design constraint and requires >=7.50 bits/byte on at least 256 KiB of bounded
sampled media bytes. The predicate itself performs no comparator lookup and does not inspect workload names,
filenames/extensions, content hashes, archive hashes, or pack hashes.

Evidence boundary before promotion:
- frozen all-15 suite: the base structural rule admitted only the media family, where r24 was smaller/faster than
  both ZIP and Zstd-19 and smaller than accepted v0.29;
- unseen/adversarial v2 suite: high-entropy JPEG/PNG/MP4 and 75%-opaque mixed media all remained strict four-way
  wins with predicate time charged, while the compressible media impostor, below-count case, and ZIP-container
  case were all rejected with zero counterexamples.

This module only decides whether the existing canonical r24 builder may terminate the tournament. It does not
change r24 bytes, reader grammar, integrity, recovery, locality, native, or Android semantics.
"""
from __future__ import annotations

from collections import Counter
import math
import os
from pathlib import Path
import stat
from typing import Iterable

MIN_REGULAR_FILES = 8
MAX_REGULAR_FILES = 128
MIN_LOGICAL_BYTES = 8 * 1024 * 1024
MIN_OPAQUE_BYTE_SHARE = 0.70
SAMPLE_PER_FILE = 64 * 1024
MAX_SAMPLED_FILES = 16
MIN_SAMPLE_BYTES = 256 * 1024
MIN_ENTROPY_BITS_PER_BYTE = 7.50


def _is_opaque_encoded_media(path: Path, size: int) -> bool:
    if size <= 0:
        return False
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError:
        return False
    if head.startswith(b"\xff\xd8\xff"):  # JPEG
        return True
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if head.startswith(b"fLaC"):
        return True
    if head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0):
        return True
    # ISO Base Media File Format: box length then 'ftyp' (ordinary MP4/M4A-family encoded media).
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return True
    # ZIP-family containers are intentionally not opaque media here. Office documents need the r25/federated
    # tournament because cross-file redundancy can materially beat r24.
    return False


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def analyze_precollected(files: Iterable[tuple[Path | str, int]]) -> dict:
    """Run the exact media predicate from already-collected regular-file paths and sizes.

    The release front door already performs a fail-closed source metadata walk for logs/C25 admission. Reusing
    those immutable path/size facts avoids a second directory traversal and lstat pass without changing any media
    feature. Header reads and entropy sampling remain owned by this module and are unchanged.
    """
    rows = [(Path(path), int(size)) for path, size in files]
    regular_files = len(rows)
    logical_bytes = sum(size for _, size in rows)
    opaque_bytes = 0
    opaque_paths: list[Path] = []

    for path, size in rows:
        if _is_opaque_encoded_media(path, size):
            opaque_bytes += size
            opaque_paths.append(path)

    opaque_share = opaque_bytes / max(1, logical_bytes)
    base_eligible = (
        MIN_REGULAR_FILES <= regular_files <= MAX_REGULAR_FILES
        and logical_bytes >= MIN_LOGICAL_BYTES
        and opaque_share >= MIN_OPAQUE_BYTE_SHARE
    )
    if not base_eligible:
        return {
            "regular_files": regular_files,
            "logical_bytes": logical_bytes,
            "opaque_encoded_media_bytes": opaque_bytes,
            "opaque_encoded_media_share": opaque_share,
            "sample_bytes": 0,
            "sample_entropy_bits_per_byte": 0.0,
            "eligible": False,
            "reason": "shape-or-opaque-share",
        }

    sample = bytearray()
    sampled_files = 0
    # Stable traversal only makes the bounded sampling reproducible. Path text itself is never compared to a
    # workload-specific value or otherwise used as an admission feature.
    for path in sorted(opaque_paths):
        try:
            with path.open("rb") as handle:
                sample.extend(handle.read(SAMPLE_PER_FILE))
        except OSError:
            continue
        sampled_files += 1
        if sampled_files >= MAX_SAMPLED_FILES:
            break

    entropy = _entropy(bytes(sample))
    eligible = len(sample) >= MIN_SAMPLE_BYTES and entropy >= MIN_ENTROPY_BITS_PER_BYTE
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "opaque_encoded_media_bytes": opaque_bytes,
        "opaque_encoded_media_share": opaque_share,
        "sample_bytes": len(sample),
        "sampled_files": sampled_files,
        "sample_entropy_bits_per_byte": entropy,
        "eligible": eligible,
        "reason": "eligible" if eligible else "entropy-or-sample-floor",
    }


def analyze(root: Path | str) -> dict:
    root = Path(root)
    files: list[tuple[Path, int]] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            files.append((path, int(st.st_size)))

    return analyze_precollected(files)


def eligible(root: Path | str) -> bool:
    return bool(analyze(root)["eligible"])
