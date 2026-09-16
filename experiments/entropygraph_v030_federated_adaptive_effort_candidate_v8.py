from __future__ import annotations

"""C25EG08: EG07 geometry with a threshold-free physical effort ladder.

This is a research Builder following the Office same-geometry effort referee.  EG07
continues to own representation discovery, grouping, filesystem control, integrity,
recovery and locality.  After EG07 emits and verifies its ordinary level-1 physical
packs, EG08 keeps every pack boundary and raw byte fixed and re-encodes only non-hot
packs with a deterministic effort ladder ``3, 6, 12, 19``.

The ladder retains the best storage choice seen.  It continues through a strict win
or a tie and stops at the first strictly worse next effort.  No corpus/path/file-type
threshold is used.  Hot stream roots backing inverse views are never re-compressed,
so the existing no-extra-decode-layer latency policy survives unchanged.

The post-build repack is intentionally a research implementation: it proves the
mechanism before fusing the selected effort into first-pass creation.  Its exported
CPU/RSS cost must therefore be measured rather than inferred from the attribution
oracle.
"""

import binascii
import hashlib
from pathlib import Path
import resource
import time

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

MAGIC = EG07.MAGIC
TAIL_MAGIC = EG07.TAIL_MAGIC
FORMAT_REVISION = 25
EFFORT_LADDER = (3, 6, 12, 19)
MAX_DECODE_UNIT = EG07.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG07.MAX_MEMBER_AMPLIFICATION


def _stream_roles(meta: dict, pack_count: int) -> tuple[set[int], set[int]]:
    stream_packs = [(int(start), int(pi), int(size)) for start, pi, size in meta.get("stream_packs", [])]
    stream_indices = {pi for _start, pi, _size in stream_packs}
    if any(pi < 0 or pi >= pack_count for pi in stream_indices):
        raise RuntimeError("EG08 stream pack index outside authenticated pack table")

    hot_ranges: list[tuple[int, int]] = []
    for _path, desc in meta.get("files", []):
        if isinstance(desc, list) and desc and desc[0] == "inflate_stream":
            start, size = int(desc[1]), int(desc[2])
            hot_ranges.append((start, start + size))

    hot_indices: set[int] = set()
    for slab_start, pi, slab_size in stream_packs:
        slab_end = slab_start + slab_size
        if any(not (slab_end <= start or slab_start >= end) for start, end in hot_ranges):
            hot_indices.add(pi)
    return stream_indices, hot_indices


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _adaptive_repack(archive: Path) -> dict:
    owner = EG07.EG06.EG05
    V25 = owner.V25
    uncapped_zc = V25.zc
    raw_archive = archive.read_bytes()
    magic, meta_comp_size, _meta_raw_size, _pack_count, _meta_hash = V25.HDR.unpack_from(raw_archive, 0)
    if magic != MAGIC:
        raise RuntimeError("EG08 expected EG07 primary identity")
    meta_end = V25.HDR.size + int(meta_comp_size)

    packs: list[dict] = []
    with EG07._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi, (offset, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                stream.seek(offset)
                payload = stream.read(csize)
                if len(payload) != csize:
                    raise RuntimeError(f"EG08 truncated pack {pi}")
                raw = V25.zd(payload, usize) if codec == 1 else payload
                if len(raw) != usize:
                    raise RuntimeError(f"EG08 pack-size mismatch {pi}")
                if (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                    raise RuntimeError(f"EG08 pack CRC mismatch {pi}")
                if V25.H(raw) != expected_sha:
                    raise RuntimeError(f"EG08 pack SHA mismatch {pi}")
                packs.append(
                    {
                        "index": pi,
                        "codec": int(codec),
                        "usize": int(usize),
                        "csize": int(csize),
                        "crc": int(crc),
                        "sha": expected_sha,
                        "raw": raw,
                        "payload": payload,
                    }
                )
        finally:
            stream.close()

    stream_indices, hot_indices = _stream_roles(dict(meta), len(packs))
    old_physical_end = meta_end
    if packs:
        # The last offset points just after its PH header.
        last = packs[-1]
        old_physical_end = int(offsets[-1][0]) + int(last["csize"])
    prefix = raw_archive[:meta_end]
    suffix = raw_archive[old_physical_end:]

    before_physical = sum(V25.PH.size + int(row["csize"]) for row in packs)
    rebuilt = bytearray()
    attempts = 0
    stopped_early = 0
    changed = 0
    selected_levels: dict[str, int] = {"current": 0, "3": 0, "6": 0, "12": 0, "19": 0}
    rows = []
    cpu0 = time.process_time(); wall0 = time.perf_counter()

    for row in packs:
        pi = int(row["index"])
        raw = row["raw"]
        best_codec = int(row["codec"])
        best_payload = row["payload"]
        best_size = len(best_payload)
        best_level = "current"
        tried: list[dict] = []

        if pi not in hot_indices:
            for level in EFFORT_LADDER:
                attempts += 1
                comp = uncapped_zc(raw, level)
                if len(comp) + 8 < len(raw):
                    candidate_codec = 1
                    candidate_payload = comp
                else:
                    candidate_codec = 0
                    candidate_payload = raw
                candidate_size = len(candidate_payload)
                tried.append({"level": level, "storage_bytes": candidate_size})
                if candidate_size <= best_size:
                    if candidate_size < best_size:
                        best_codec = candidate_codec
                        best_payload = candidate_payload
                        best_size = candidate_size
                        best_level = str(level)
                    # A tie is evidence that extra effort has not hurt yet; permit the next fixed rung.
                    continue
                stopped_early += 1
                break

        if best_codec != int(row["codec"]) or best_size != int(row["csize"]):
            changed += 1
        selected_levels[best_level] = selected_levels.get(best_level, 0) + 1
        rebuilt += V25.PH.pack(best_codec, len(raw), best_size, int(row["crc"]), row["sha"])
        rebuilt += best_payload
        rows.append(
            {
                "index": pi,
                "stream_pack": pi in stream_indices,
                "hot_stream_root": pi in hot_indices,
                "raw_sha256": _sha(raw),
                "current_codec": int(row["codec"]),
                "current_payload_bytes": int(row["csize"]),
                "selected_codec": best_codec,
                "selected_payload_bytes": best_size,
                "selected_level": best_level,
                "saved_bytes": int(row["csize"]) - best_size,
                "tried": tried,
            }
        )

    repack_cpu = time.process_time() - cpu0
    repack_wall = time.perf_counter() - wall0
    after_physical = len(rebuilt)
    if after_physical > before_physical:
        raise RuntimeError("EG08 effort ladder enlarged the physical region")
    archive.write_bytes(prefix + bytes(rebuilt) + suffix)

    return {
        "physical_bytes_before": before_physical,
        "physical_bytes_after": after_physical,
        "physical_bytes_saved": before_physical - after_physical,
        "pack_count": len(packs),
        "stream_pack_count": len(stream_indices),
        "hot_stream_root_pack_count": len(hot_indices),
        "changed_packs": changed,
        "effort_attempts": attempts,
        "early_stops": stopped_early,
        "selected_levels": selected_levels,
        "repack_cpu_s": repack_cpu,
        "repack_wall_s": repack_wall,
        "packs": rows,
    }


def build(source: Path, archive: Path) -> dict:
    source = source.resolve(); archive = archive.resolve()
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    base = dict(EG07.build(source, archive))
    locality_before = dict(base["locality"])
    bytes_before = archive.stat().st_size

    effort = _adaptive_repack(archive)
    verified = EG07.strong_verify(archive, expected_tree=EG07._treehash(source))
    locality = EG07.locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("EG08 exceeds frozen locality/decode limits")
    if (
        locality.get("max_decode_unit_bytes") != locality_before.get("max_decode_unit_bytes")
        or locality.get("max_member_read_amplification") != locality_before.get("max_member_read_amplification")
        or locality.get("member_count") != locality_before.get("member_count")
    ):
        raise RuntimeError("EG08 changed physical locality geometry")

    result = dict(base)
    result.update(
        {
            "profile": "federated-eg08-adaptive-effort",
            "format_revision": FORMAT_REVISION,
            "archive_bytes_before_effort": bytes_before,
            "archive_bytes": archive.stat().st_size,
            "adaptive_effort": effort,
            "verified": verified,
            "locality": locality,
            "total_build_cpu_s": time.process_time() - cpu0,
            "total_build_wall_s": time.perf_counter() - wall0,
            "process_peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        }
    )
    return result


def extract(archive: Path, destination: Path) -> None:
    EG07.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return EG07.strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    return EG07.locality_report(archive)
