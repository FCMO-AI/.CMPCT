"""Product-side EOCD-indexed parser for the v0.30 ZIP-factor builder.

This parser preserves the mature ZIP-factor acceptance contract while changing traversal only:
locate/validate EOCD first, walk exactly the declared central directory, and validate each owning local header
against that central row immediately. The local stream is still required to be contiguous and every central local
offset must match the next physical record. Interleaving the two validations avoids a second Python pass over an
already-materialized central-row dictionary list while returning the exact mature object shape.

It accepts only the narrow ZIP subset already owned by ``entropygraph_v030_zipfactor_profile`` (single disk, no
encryption, no data descriptors, store/deflate members, contiguous local records, exact central/local metadata
agreement).

EOCD discovery deliberately validates every backwards signature candidate rather than trusting a single ``rfind``
result: ZIP comments are arbitrary bytes and may legally contain the EOCD signature themselves. A candidate is
accepted only if its comment length reaches exact EOF and its complete central/local topology validates.

No benchmark identity or workload metadata participates. Promotion still requires hostile-equivalence, exact archive
identity, recovery, native/Android and release-authority evidence.
"""
from __future__ import annotations

import struct

from experiments import entropygraph_v030_zipfactor_profile as BASE

EOCD_SIG = b"PK\x05\x06"
LOCAL_HDR = struct.Struct("<IHHHHHIIIHH")
CENTRAL_HDR = struct.Struct("<IHHHHHHIIIHHHHHII")
EOCD_HDR = struct.Struct("<IHHHHIIH")
MAX_EOCD_SEARCH = 22 + 65535


def _parse_at(raw: bytes, eocd_at: int) -> dict | None:
    nraw = len(raw)
    if eocd_at < 0 or eocd_at + EOCD_HDR.size > nraw:
        return None
    sig, disk, disk_cd, entries_disk, entries_total, cd_size, cd_offset, comment_len = EOCD_HDR.unpack_from(raw, eocd_at)
    if sig != BASE.EOCD or entries_disk < 1 or entries_disk != entries_total:
        return None
    if eocd_at + EOCD_HDR.size + comment_len != nraw:
        return None
    if cd_offset < 0 or cd_size < 0 or cd_offset + cd_size != eocd_at:
        return None

    central_rows = []
    local_rows = []
    central_at = cd_offset
    local_at = 0
    for _ in range(entries_total):
        if central_at + CENTRAL_HDR.size > eocd_at:
            return None
        fields = CENTRAL_HDR.unpack_from(raw, central_at)
        (_sig, made, needed, flags, method, mtime, mdate, crc, csize, usize,
         name_len, extra_len, row_comment_len, row_disk, internal_attr, external_attr, local_offset) = fields
        if _sig != BASE.CENTRAL:
            return None
        body = central_at + CENTRAL_HDR.size
        end = body + name_len + extra_len + row_comment_len
        if end > eocd_at:
            return None
        central_name = raw[body:body + name_len]
        central_extra = raw[body + name_len:body + name_len + extra_len]
        central_comment = raw[body + name_len + extra_len:end]

        # Validate the owning local frame while the central values are still scalar locals. This preserves the exact
        # acceptance law but removes a second Python pass whose only purpose was to read these values back out of a
        # dictionary. Contiguous local ownership remains fail-closed through local_at.
        if local_offset != local_at or local_at + LOCAL_HDR.size > cd_offset:
            return None
        local_fields = LOCAL_HDR.unpack_from(raw, local_at)
        local_sig, version, local_flags, local_method, local_mtime, local_mdate, local_crc, local_csize, local_usize, local_name_len, local_extra_len = local_fields
        if local_sig != BASE.LOCAL or local_flags & 0x0001 or local_flags & 0x0008 or local_method not in (0, 8):
            return None
        frame_end = local_at + LOCAL_HDR.size + local_name_len + local_extra_len
        payload_end = frame_end + local_csize
        if payload_end > cd_offset:
            return None
        local_name = raw[local_at + LOCAL_HDR.size:local_at + LOCAL_HDR.size + local_name_len]
        local_extra = raw[local_at + LOCAL_HDR.size + local_name_len:frame_end]
        if (
            local_name != central_name
            or local_flags != flags
            or local_method != method
            or local_mtime != mtime
            or local_mdate != mdate
            or local_crc != crc
            or local_csize != csize
            or local_usize != usize
        ):
            return None

        central_rows.append({
            "made": made,
            "needed": needed,
            "flags": flags,
            "method": method,
            "mtime": mtime,
            "mdate": mdate,
            "crc": crc,
            "csize": csize,
            "usize": usize,
            "name": central_name,
            "extra": central_extra,
            "comment": central_comment,
            "disk": row_disk,
            "internal_attr": internal_attr,
            "external_attr": external_attr,
            "local_offset": local_offset,
        })
        local_rows.append({
            "version": version,
            "flags": local_flags,
            "method": local_method,
            "mtime": local_mtime,
            "mdate": local_mdate,
            "crc": local_crc,
            "csize": local_csize,
            "usize": local_usize,
            "name": local_name,
            "extra": local_extra,
            "payload": raw[frame_end:payload_end],
            "offset": local_at,
        })
        central_at = end
        local_at = payload_end
    if central_at != eocd_at or local_at != cd_offset:
        return None

    return {
        "raw_size": nraw,
        "locals": local_rows,
        "centrals": central_rows,
        "eocd": {
            "disk": disk,
            "disk_cd": disk_cd,
            "comment": raw[eocd_at + EOCD_HDR.size:],
        },
    }


def parse_zip(raw: bytes) -> dict | None:
    nraw = len(raw)
    if nraw < EOCD_HDR.size:
        return None

    lower = max(0, nraw - MAX_EOCD_SEARCH)
    search_end = nraw
    while True:
        eocd_at = raw.rfind(EOCD_SIG, lower, search_end)
        if eocd_at < 0:
            return None
        parsed = _parse_at(raw, eocd_at)
        if parsed is not None:
            return parsed
        # A signature inside the arbitrary ZIP comment is not the EOCD. Keep walking backwards
        # through the bounded EOCD search window until a fully valid topology is found.
        search_end = eocd_at
