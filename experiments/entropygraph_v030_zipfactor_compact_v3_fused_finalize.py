"""Exact-byte ZIP-factor V3 builder experiment with fused group finalization.

The shipping/research format is unchanged: this module emits the exact CMP25Z3 grammar owned by
``entropygraph_v030_zipfactor_compact_v3``. It only removes repeated Python passes over completed group buffers:
pack -> hash -> compress -> descriptor bookkeeping is performed once per group instead of materializing all group
raw buffers and traversing them again for compression and control hashing.

``build_bytes`` exposes the exact in-memory payload before publication. It exists so later recovery experiments can
reuse the single semantic owner without publishing a temporary V3 archive and reading it back before wrapping the
same bytes. ``build`` remains the public research builder and writes those exact bytes unchanged.

Research-only until exact-byte identity and same-runner timing prove a material win.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import zstandard as zstd

from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_fused as FUSED
from experiments import entropygraph_v030_zipfactor_profile as BASE


def build_bytes(root: Path, *, level: int = 6, group_size: int = 7) -> tuple[bytes, dict]:
    """Return the exact CMP25Z3 payload and stats without publishing an intermediate file."""
    root = Path(root)
    if group_size < 1 or group_size > V3.MAX_FILES:
        raise V3.ProfileNotEligible("binary-control ZIP-factor group size exceeds policy")

    manifest_raw, items, fs_stats = FUSED._scan(root)
    if not 2 <= len(items) <= V3.MAX_FILES:
        raise V3.ProfileNotEligible("binary-control ZIP-factor regular-file envelope")

    template_raw = BASE._serialize_template(items[0][1])
    regular_sizes = {rel: int(item["raw_size"]) for rel, item in items}
    compressor = zstd.ZstdCompressor(level=level, threads=0)

    # Direct members are encoded exactly as V3 does.
    manifest_blob = compressor.compress(manifest_raw)
    template_blob = compressor.compress(template_raw)
    manifest_sha = hashlib.sha256(manifest_raw).digest()
    template_sha = hashlib.sha256(template_raw).digest()

    descriptor_rows: list[tuple[int, bytes, int]] = []
    group_blobs: list[bytes] = []
    max_decode = 0
    max_amp = 1.0
    group_count = 0

    # The old V3 builder first materialized every group raw buffer, then traversed the list again for locality,
    # compression, and SHA/control construction. Keep only the compressed publication buffers after each group.
    for index in range(0, len(items), group_size):
        group = items[index:index + group_size]
        raw = V3._pack_group(group)
        context = len(template_raw) + len(raw)
        amp = context / max(1, min(regular_sizes[rel] for rel, _item in group))
        if context > V3.MAX_DECODE or amp > V3.MAX_AMP:
            raise V3.ProfileNotEligible("binary-control ZIP-factor locality ceiling")
        max_decode = max(max_decode, context)
        max_amp = max(max_amp, amp)
        descriptor_rows.append((len(raw), hashlib.sha256(raw).digest(), len(group)))
        group_blobs.append(compressor.compress(raw))
        group_count += 1

    control = bytearray(
        V3._HEADER.pack(
            len(manifest_raw),
            manifest_sha,
            len(template_raw),
            template_sha,
            group_count,
        )
    )
    for raw_size, raw_sha, member_count in descriptor_rows:
        control += V3._GROUP.pack(raw_size, raw_sha, member_count)

    payload = bytearray(V3.MAGIC)
    payload += control
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)

    stats = {
        "archive_bytes": len(payload),
        "format_revision": V3.REVISION,
        "format_profile": V3.PROFILE,
        "user_files": len(items),
        "groups": group_count,
        "control_bytes": len(control),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": level,
        "group_size": group_size,
        "fused_source_scan": True,
        "fused_group_finalize": True,
        **fs_stats,
    }
    return bytes(payload), stats


def build(root: Path, out: Path, *, level: int = 6, group_size: int = 7) -> dict:
    payload, stats = build_bytes(root, level=level, group_size=group_size)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return stats
