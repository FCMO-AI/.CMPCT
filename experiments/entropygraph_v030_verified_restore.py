"""Verified-staging filesystem restoration and release-reader fast paths for CMPCT v0.30.

The canonical r25 release streamer authenticates every reconstructed content-graph member before returning a
caller-owned staging tree.  The ordinary filesystem bridge deliberately remains defensive for callers that hand
it an arbitrary staging directory: it re-hashes every regular file before applying metadata and links.

The promoted extraction path has stronger provenance than that generic entry point.  Re-reading every file after
``release_reader_policy.extract_verified_into_staging`` duplicates a full content pass, especially hurting large
ML/model artifacts.  This helper keeps the filesystem bridge as the single grammar/metadata owner while replacing
only the already-proven digest pass with bounded shape checks.  It may be called *only* after the verified streamer
has returned successfully for the same archive/staging tree.

The same release-only reader layer also installs the dependency-free DGO1 inverse that earned exact research
headroom on the promoted ML substrate.  The archive grammar, encoded bytes and cell-work law are unchanged; only
ownership of the reconstructed output changes.  Instead of allocating one Python bytearray per delimiter segment,
the fast path owns one bounded logical output buffer and uses CPython extended-slice assignment for contiguous
runs of equal-length active rows.  Historical/research modules retain their independent inverse implementation, so
byte-identity and hostile-reader gates still have a differently rooted oracle.

No archive grammar, digest, locality, resource limit, link rule, rollback rule, publication rule or release
threshold changes here.  Authentication is moved from "stream then hash again" to "authenticated stream once,
shape-check before metadata", not removed; DGO1 reconstruction remains exact and bounded.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import shutil

from experiments import entropygraph_v030_canonical_final as C
from experiments import entropygraph_v030_product_fs as FS


_PRE_RELEASE_DELIMITER_INVERSE = C.SHARED.G.O.delimiter_inverse
_MAX_PRECOMPUTED_DELIMITER_RUNS = 1024


def release_single_buffer_delimiter_inverse(
    encoded: bytes, logical_size: int, *, bulk_one_byte_table: bool = False
) -> bytes:
    """Invert exact DGO1 into one bounded logical buffer without per-segment output objects.

    DGO1 stores active segment bytes column-major.  For one column, any contiguous run of source segments having
    the same length maps to output positions separated by exactly ``length + 1`` bytes (the extra byte is the
    delimiter).  ``bytearray`` extended-slice assignment performs that scatter in CPython's C loop.  Unequal runs
    remain distinct, preserving original row order without carrying an index map or changing one archive byte.
    """
    O = C.SHARED.G.O
    if (
        not encoded.startswith(b"DGO1")
        or len(encoded) < 6
        or logical_size < 0
        or logical_size > O.MAX_OVERLAY_RECORD
    ):
        raise RuntimeError("invalid Geometry overlay delimiter descriptor")
    delimiter = encoded[4]
    count, pos = O._get_varint(encoded, 5)
    if count < 1 or count > O.MAX_DELIMITER_SEGMENTS:
        raise RuntimeError("Geometry overlay delimiter segment count")

    # A one-byte varint has its continuation bit clear.  Prove the entire length table in one C-level scan and
    # materialize it directly; any high-bit byte or short slice falls back to the historical parser unchanged.
    table = encoded[pos : pos + count]
    if bulk_one_byte_table and len(table) == count and table.isascii():
        lengths = list(table)
        pos += count
        logical_members = sum(lengths)
        if logical_members > O.MAX_OVERLAY_RECORD:
            raise RuntimeError("Geometry overlay delimiter length budget")
        max_len = max(lengths, default=0)
    else:
        lengths = []
        logical_members = 0
        max_len = 0
        for _ in range(count):
            length, pos = O._get_varint(encoded, pos)
            if length > O.MAX_OVERLAY_RECORD or logical_members + length > O.MAX_OVERLAY_RECORD:
                raise RuntimeError("Geometry overlay delimiter length budget")
            lengths.append(length)
            logical_members += length
            max_len = max(max_len, length)
    if logical_members + count - 1 != logical_size:
        raise RuntimeError("Geometry overlay delimiter logical-size mismatch")
    if count * max_len > O.MAX_DELIMITER_CELL_SCANS:
        raise RuntimeError("Geometry overlay delimiter cell-work budget")
    body = encoded[pos:]
    if len(body) != logical_members:
        raise RuntimeError("Geometry overlay delimiter body-size mismatch")

    starts = [0] * count
    output_cursor = 0
    for index, length in enumerate(lengths):
        starts[index] = output_cursor
        output_cursor += length
        if index + 1 < count:
            output_cursor += 1
    if output_cursor != logical_size:
        raise RuntimeError("Geometry overlay delimiter output-shape mismatch")

    out = bytearray(logical_size)
    for index in range(count - 1):
        out[starts[index] + lengths[index]] = delimiter

    # The row partition is invariant across columns.  The earlier promoted implementation rediscovered these
    # equal-length runs inside every column, turning a tokenizer-like record with ~53k segments and only a handful
    # of runs into roughly one million redundant Python length/index comparisons.  Precompute the exact ordered
    # partition once when it is genuinely compact.  If a hostile/high-entropy descriptor would require thousands
    # of run tuples, fall back to the previous bounded scanner instead of exporting multi-MiB metadata or paying a
    # worse per-column iterator cost.  This is an implementation route choice only; both routes scatter identical
    # body bytes under the same descriptor and cell-work law.
    runs: list[tuple[int, int, int]] = []
    first = 0
    while first < count and len(runs) <= _MAX_PRECOMPUTED_DELIMITER_RUNS:
        length = lengths[first]
        end = first + 1
        while end < count and lengths[end] == length:
            end += 1
        runs.append((first, end, length))
        first = end
    use_precomputed_runs = first == count and len(runs) <= _MAX_PRECOMPUTED_DELIMITER_RUNS

    body_cursor = 0
    active_cells = 0
    for column in range(max_len):
        if use_precomputed_runs:
            for first, end, length in runs:
                if length <= column:
                    continue
                run_len = end - first
                source_end = body_cursor + run_len
                if source_end > len(body):
                    raise RuntimeError("short Geometry overlay delimiter body")
                target_start = starts[first] + column
                target_stop = starts[end - 1] + column + 1
                out[target_start:target_stop:length + 1] = body[body_cursor:source_end]
                body_cursor = source_end
                active_cells += run_len
            continue

        index = 0
        while index < count:
            while index < count and lengths[index] <= column:
                index += 1
            if index >= count:
                break
            length = lengths[index]
            first = index
            index += 1
            while index < count and lengths[index] == length:
                index += 1
            run_len = index - first
            source_end = body_cursor + run_len
            if source_end > len(body):
                raise RuntimeError("short Geometry overlay delimiter body")
            target_start = starts[first] + column
            target_stop = starts[index - 1] + column + 1
            out[target_start:target_stop:length + 1] = body[body_cursor:source_end]
            body_cursor = source_end
            active_cells += run_len

    if body_cursor != len(body) or active_cells != logical_members:
        raise RuntimeError("Geometry overlay delimiter trailing/body accounting mismatch")
    return bytes(out)


def release_bulk_one_byte_table_delimiter_inverse(encoded: bytes, logical_size: int) -> bytes:
    """Verified-staging-only DGO1 inverse with bulk one-byte length-table parsing."""
    return release_single_buffer_delimiter_inverse(encoded, logical_size, bulk_one_byte_table=True)


# Release-only installation.  Canonical-final has already isolated its dependency graph before this module is
# imported by the release product front door.  Research modules therefore remain byte-oracle controls rather than
# being silently rewritten along with the promoted implementation.
C.SHARED.G.O.delimiter_inverse = release_single_buffer_delimiter_inverse
if getattr(C.POLICY.R.G04, "O", None) is not None:
    C.POLICY.R.G04.O.delimiter_inverse = release_single_buffer_delimiter_inverse


def restore_verified_manifest_tree(staging: Path, decoded: dict, *, safe_symlinks: bool = True) -> None:
    """Restore an r25 manifest after the release streamer authenticated the staging bytes.

    ``staging`` is unpublished and transaction-owned by the caller.  Regular-file content identity has already
    been checked against the authenticated graph by the release streamer; this function therefore checks only
    path/type/size before applying the exact existing FS metadata/link policy.
    """
    staging = Path(staging)
    entries = decoded["manifest"]["entries"]
    internal = staging.joinpath(*PurePosixPath(FS.INTERNAL_ROOT).parts)
    if internal.exists() or internal.is_symlink():
        shutil.rmtree(internal, ignore_errors=True)

    for row in entries:
        rel, kind = row[0], row[1]
        if kind != "f":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        size, _expected_digest = row[7]
        if not target.is_file() or target.is_symlink() or target.stat().st_size != int(size):
            raise RuntimeError(f"r25 extracted regular-file shape mismatch: {rel}")

    for row in entries:
        rel, kind = row[0], row[1]
        target = staging.joinpath(*PurePosixPath(rel).parts)
        if kind == "d":
            target.mkdir(parents=True, exist_ok=True)
        elif kind == "l":
            target.parent.mkdir(parents=True, exist_ok=True)
            link_target = row[7]
            parsed = PurePosixPath(link_target)
            if safe_symlinks and (parsed.is_absolute() or ".." in parsed.parts):
                raise RuntimeError(f"unsafe r25 symlink target in {rel!r}")
            target.unlink(missing_ok=True)
            os.symlink(link_target, target)
        elif kind == "h":
            target.parent.mkdir(parents=True, exist_ok=True)
            owner = staging.joinpath(*PurePosixPath(row[7]).parts)
            if not owner.is_file() or owner.is_symlink():
                raise RuntimeError(f"r25 hardlink owner is not materialized: {row[7]}")
            target.unlink(missing_ok=True)
            os.link(owner, target)

    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        if kind == "d":
            continue
        target = staging.joinpath(*PurePosixPath(rel).parts)
        follow = kind != "l"
        if follow:
            try:
                os.chmod(target, int(mode), follow_symlinks=False)
            except OSError:
                pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid), follow_symlinks=follow)
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=follow)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)), follow_symlinks=follow)
        except OSError:
            pass

    directories = sorted(
        (row for row in entries if row[1] == "d"),
        key=lambda item: item[0].count("/"),
        reverse=True,
    )
    for row in directories:
        rel, _kind, mode, mtime_ns, uid, gid, xattrs, _extra = row
        target = staging.joinpath(*PurePosixPath(rel).parts)
        try:
            os.chmod(target, int(mode))
        except OSError:
            pass
        if hasattr(os, "chown") and (uid or gid):
            try:
                os.chown(target, int(uid), int(gid))
            except (OSError, PermissionError):
                pass
        FS._apply_xattrs(target, xattrs, follow_symlinks=True)
        try:
            os.utime(target, ns=(int(mtime_ns), int(mtime_ns)))
        except OSError:
            pass
