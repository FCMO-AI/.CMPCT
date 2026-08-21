"""Release-only locality repair for revision-24 nested archive packs.

The mature r24 builder has a valuable optimization for 8+ nested ZIP/WHL files: it stores the exact container
bytes as slices of one ``S_PACK`` blob instead of parsing/recompressing every archive.  That representation is
fully compatible with r24, but the historical encoder packed the entire cohort into one blob.  A selected read of
one member therefore decodes the whole cohort and can exceed v0.30's frozen <=8x member-read amplification law.

This module preserves the r24 grammar and the historical/default builder byte policy.  It installs a narrow
post-scan repartitioner that activates only for the promoted v0.30 shipping-r24 configuration (exact Deflate
retention + the measured 256 KiB medium-file policy + the release TEXT_EXT dispatcher).  Existing container packs
are split deterministically into smaller ``S_PACK`` blobs.  Every resulting group satisfies both:

    group decoded bytes <= 8 * smallest logical member in the group
    group decoded bytes <= 8 MiB

Thus *every* member in a release container pack, not merely the benchmark-selected largest member, stays within
the same locality ceiling.  No source bytes are transformed and no reader behavior changes.
"""
from __future__ import annotations

from . import builder as B

MAX_MEMBER_READ_AMPLIFICATION = 8
MAX_DECODE_UNIT_BYTES = 8 * 1024 * 1024
RELEASE_MICRO_MAX_FILE_BYTES = 256 * 1024

_ORIGINAL_SCAN = B.Builder.scan


def _shipping_release_builder(builder: B.Builder) -> bool:
    """Recognize the promoted r24-v4 construction without changing ordinary/historical builders."""
    return (
        int(getattr(builder, "deflate_reuse_min", -1)) == 0
        and int(getattr(builder, "micro_pack_max_file", 0)) >= RELEASE_MICRO_MAX_FILE_BYTES
        and type(B.TEXT_EXT).__name__ == "_ReleaseTextHints"
    )


def _container_pack_hashes(builder: B.Builder) -> list[bytes]:
    hashes = []
    for h, candidate in builder.cands.items():
        if ".cmpct-container-pack" in candidate.hints:
            hashes.append(bytes(h))
    return hashes


def _rows_for_pack(builder: B.Builder, pack_hash: bytes) -> list[list]:
    rows = []
    for row in builder.files:
        storage = row[6] if len(row) > 6 else None
        if storage and storage[0] == B.S_PACK and bytes(storage[1]) == pack_hash:
            rows.append(row)
    return sorted(rows, key=lambda row: str(row[0]))


def _groups(members: list[tuple[list, bytes]]) -> list[list[tuple[list, bytes]]]:
    """Greedily retain lexical order while enforcing the strict all-member locality envelope."""
    groups: list[list[tuple[list, bytes]]] = []
    current: list[tuple[list, bytes]] = []
    current_bytes = 0
    current_min = 0

    for row, raw in members:
        member_size = max(1, len(raw))
        if not current:
            current = [(row, raw)]
            current_bytes = len(raw)
            current_min = member_size
            continue

        next_bytes = current_bytes + len(raw)
        next_min = min(current_min, member_size)
        next_limit = min(MAX_DECODE_UNIT_BYTES, MAX_MEMBER_READ_AMPLIFICATION * next_min)
        if next_bytes > next_limit:
            groups.append(current)
            current = [(row, raw)]
            current_bytes = len(raw)
            current_min = member_size
        else:
            current.append((row, raw))
            current_bytes = next_bytes
            current_min = next_min

    if current:
        groups.append(current)
    return groups


def _repartition_container_pack(builder: B.Builder, pack_hash: bytes) -> dict | None:
    candidate = builder.cands.get(pack_hash)
    if candidate is None:
        return None
    rows = _rows_for_pack(builder, pack_hash)
    if len(rows) < 2:
        return None

    source = candidate.raw
    members: list[tuple[list, bytes]] = []
    for row in rows:
        storage = row[6]
        off = int(storage[2]); length = int(storage[3])
        if off < 0 or length < 0 or off + length > len(source):
            raise RuntimeError("r24 nested-container pack slice outside source blob")
        raw = bytes(source[off:off + length])
        if len(raw) != int(row[4]) or B.sha(raw) != bytes(row[5]):
            raise RuntimeError(f"r24 nested-container pack logical identity mismatch: {row[0]!r}")
        members.append((row, raw))

    groups = _groups(members)
    if len(groups) == 1:
        # Already within the strict envelope; retaining the original hash preserves exact bytes.
        return {
            "original_members": len(rows),
            "groups": 1,
            "max_group_bytes": len(source),
            "max_group_amplification": len(source) / max(1, min(len(raw) for _row, raw in members)),
        }

    new_hashes: set[bytes] = set()
    max_group_bytes = 0
    max_group_amp = 0.0
    for group in groups:
        buf = bytearray()
        slots: list[tuple[list, int, int]] = []
        min_member = None
        for row, raw in group:
            off = len(buf); buf.extend(raw)
            slots.append((row, off, len(raw)))
            min_member = len(raw) if min_member is None else min(min_member, len(raw))
        group_raw = bytes(buf)
        if len(group_raw) > MAX_DECODE_UNIT_BYTES:
            raise RuntimeError("release nested-container group exceeds 8 MiB decode-unit ceiling")
        amp = len(group_raw) / max(1, int(min_member or 0))
        if amp > MAX_MEMBER_READ_AMPLIFICATION:
            raise RuntimeError("release nested-container group exceeds 8x all-member locality ceiling")
        new_hash = bytes(builder.add_content(group_raw, ".cmpct-container-pack"))
        new_hashes.add(new_hash)
        for row, off, length in slots:
            row[6] = [B.S_PACK, new_hash, off, length]
        max_group_bytes = max(max_group_bytes, len(group_raw))
        max_group_amp = max(max_group_amp, amp)

    # The old whole-cohort candidate is now unreachable.  Do not delete it if content-addressed dedup happened to
    # reuse the same hash for one of the new groups (normally impossible once a real split occurred).
    if pack_hash not in new_hashes:
        builder.cands.pop(pack_hash, None)

    return {
        "original_members": len(rows),
        "groups": len(groups),
        "max_group_bytes": max_group_bytes,
        "max_group_amplification": max_group_amp,
    }


def _release_locality_scan(self: B.Builder):
    result = _ORIGINAL_SCAN(self)
    if not _shipping_release_builder(self):
        return result

    evidence = []
    # Snapshot hashes: repartitioning mutates ``cands`` by adding replacement packs.
    for pack_hash in _container_pack_hashes(self):
        row = _repartition_container_pack(self, pack_hash)
        if row is not None:
            evidence.append(row)
    self.v030_container_pack_locality = {
        "policy": "deterministic-s-pack-groups-all-members-le-8x-v1",
        "max_member_read_amplification": MAX_MEMBER_READ_AMPLIFICATION,
        "max_decode_unit_bytes": MAX_DECODE_UNIT_BYTES,
        "packs": evidence,
    }
    return result


def install() -> None:
    if getattr(B.Builder, "_cmpct_v030_release_locality_installed", False):
        return
    B.Builder.scan = _release_locality_scan
    B.Builder._cmpct_v030_release_locality_installed = True


install()
