"""Exact-byte bounded-parallel builder for the C25Z3 ZIP framing-factor candidate.

Research/productization proof only.  This module intentionally emits the *same* binary-control-v3 grammar as
``entropygraph_v030_zipfactor_compact_v3``.  The only changed variable is scheduling of independent Zstandard
compression jobs for the canonical filesystem manifest, ZIP framing template and bounded group payloads.

A separate ``ZstdCompressor`` is used per job.  Candidate order, source scan, locality accounting, metadata,
recovery/product semantics and verification are unchanged.  Promotion is forbidden until the exact-byte oracle
proves both archive identity and a strict complete-boundary creation win.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path

import zstandard as zstd

from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_profile as BASE
from experiments import entropygraph_v030_zipfactor_fused as FUSED


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _compress_one(raw: bytes, level: int) -> bytes:
    # Do not share a mutable compressor between workers.  Independent frames are deterministic for the
    # same zstandard version/settings and therefore remain directly comparable to V3.build().
    return zstd.ZstdCompressor(level=level, threads=0).compress(raw)


def _compress_all(raws: list[bytes], *, level: int, workers: int) -> list[bytes]:
    if workers <= 1 or len(raws) <= 1:
        return [_compress_one(raw, level) for raw in raws]
    worker_count = min(int(workers), len(raws), 4)
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-zf") as pool:
        futures = [pool.submit(_compress_one, raw, int(level)) for raw in raws]
        # Preserve physical member order exactly; scheduling completion order never affects bytes.
        return [future.result() for future in futures]


def build(root: Path, out: Path, *, level: int = 3, group_size: int = 7, workers: int = 4) -> dict:
    """Build binary-control-v3 bytes with only independent compression scheduled concurrently."""
    root = Path(root)
    out = Path(out)
    if group_size < 1 or group_size > V3.MAX_FILES:
        raise V3.ProfileNotEligible("parallel ZIP-factor group size exceeds policy")
    if workers < 1 or workers > 4:
        raise V3.ProfileNotEligible("parallel ZIP-factor worker count exceeds bounded policy")

    manifest_raw, items, fs_stats = FUSED._scan(root)
    if not 2 <= len(items) <= V3.MAX_FILES:
        raise V3.ProfileNotEligible("parallel ZIP-factor regular-file envelope")

    template_raw = BASE._serialize_template(items[0][1])
    groups = [items[index:index + group_size] for index in range(0, len(items), group_size)]
    group_raws = [V3._pack_group(group) for group in groups]
    regular_sizes = {rel: int(item["raw_size"]) for rel, item in items}
    max_decode = max(len(template_raw) + len(raw) for raw in group_raws)
    max_amp = max(
        (len(template_raw) + len(raw)) / max(1, min(regular_sizes[rel] for rel, _item in group))
        for group, raw in zip(groups, group_raws, strict=True)
    )
    if max_decode > V3.MAX_DECODE or max_amp > V3.MAX_AMP:
        raise V3.ProfileNotEligible("parallel ZIP-factor locality ceiling")

    all_raws = [manifest_raw, template_raw, *group_raws]
    compressed = _compress_all(all_raws, level=int(level), workers=int(workers))
    manifest_blob, template_blob, *group_blobs = compressed

    control = bytearray(
        V3._HEADER.pack(
            len(manifest_raw),
            _sha(manifest_raw),
            len(template_raw),
            _sha(template_raw),
            len(groups),
        )
    )
    for group, raw in zip(groups, group_raws, strict=True):
        control += V3._GROUP.pack(len(raw), _sha(raw), len(group))

    payload = bytearray(V3.MAGIC)
    payload += control
    payload += BASE._blob(manifest_blob)
    payload += BASE._blob(template_blob)
    for blob in group_blobs:
        payload += BASE._blob(blob)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return {
        "archive_bytes": len(payload),
        "format_revision": V3.REVISION,
        "format_profile": V3.PROFILE,
        "user_files": len(items),
        "groups": len(groups),
        "control_bytes": len(control),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
        "level": int(level),
        "group_size": int(group_size),
        "compression_workers": min(int(workers), len(all_raws), 4),
        "compression_jobs": len(all_raws),
        "scheduling_only": True,
        "fused_source_scan": True,
        **fs_stats,
    }
