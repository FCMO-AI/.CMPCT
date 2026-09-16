from __future__ import annotations

"""C25EG09: C25EG08 plus the preregistered level-1 RAW effort terminal.

H-EFFORT-5/5B found no later compression win after the existing level-1 encoder
admitted a RAW physical pack across two independent hostile courts.  This Builder
changes only execution: a non-hot pack whose *existing* incumbent codec is RAW
pays no later 3/6/12/19 effort attempts.  All compressed incumbents replay EG08's
historical ladder byte-for-byte; representation, geometry, locality, reader and
filesystem semantics remain owned by EG07/EG08.
"""

import binascii
from pathlib import Path
import resource
import time

from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08

MAGIC = EG08.MAGIC
TAIL_MAGIC = EG08.TAIL_MAGIC
FORMAT_REVISION = EG08.FORMAT_REVISION
EFFORT_LADDER = EG08.EFFORT_LADDER
MAX_DECODE_UNIT = EG08.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG08.MAX_MEMBER_AMPLIFICATION


def _raw_terminal_repack(archive: Path) -> dict:
    owner = EG08.EG07.EG06.EG05
    V25 = owner.V25
    uncapped_zc = V25.zc
    raw_archive = archive.read_bytes()
    magic, meta_comp_size, _meta_raw_size, _pack_count, _meta_hash = V25.HDR.unpack_from(raw_archive, 0)
    if magic != MAGIC:
        raise RuntimeError("EG09 expected EG07 primary identity")
    meta_end = V25.HDR.size + int(meta_comp_size)

    packs: list[dict] = []
    with EG08.EG07._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi, (offset, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                stream.seek(offset)
                payload = stream.read(csize)
                if len(payload) != csize:
                    raise RuntimeError(f"EG09 truncated pack {pi}")
                raw = V25.zd(payload, usize) if codec == 1 else payload
                if len(raw) != usize:
                    raise RuntimeError(f"EG09 pack-size mismatch {pi}")
                if (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                    raise RuntimeError(f"EG09 pack CRC mismatch {pi}")
                if V25.H(raw) != expected_sha:
                    raise RuntimeError(f"EG09 pack SHA mismatch {pi}")
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

    stream_indices, hot_indices = EG08._stream_roles(dict(meta), len(packs))
    old_physical_end = meta_end
    if packs:
        last = packs[-1]
        old_physical_end = int(offsets[-1][0]) + int(last["csize"])
    prefix = raw_archive[:meta_end]
    suffix = raw_archive[old_physical_end:]

    before_physical = sum(V25.PH.size + int(row["csize"]) for row in packs)
    rebuilt = bytearray()
    attempts = 0
    stopped_early = 0
    changed = 0
    raw_terminal_skips = 0
    raw_terminal_bytes = 0
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
        raw_terminal = pi not in hot_indices and best_codec == 0

        if raw_terminal:
            raw_terminal_skips += 1
            raw_terminal_bytes += len(raw)
        elif pi not in hot_indices:
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
                "raw_sha256": EG08._sha(raw),
                "current_codec": int(row["codec"]),
                "current_payload_bytes": int(row["csize"]),
                "raw_terminal": raw_terminal,
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
        raise RuntimeError("EG09 effort ladder enlarged the physical region")
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
        "raw_terminal_skips": raw_terminal_skips,
        "raw_terminal_bytes": raw_terminal_bytes,
        "selected_levels": selected_levels,
        "repack_cpu_s": repack_cpu,
        "repack_wall_s": repack_wall,
        "packs": rows,
    }


def build(source: Path, archive: Path) -> dict:
    source = source.resolve(); archive = archive.resolve()
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    base = dict(EG08.EG07.build(source, archive))
    locality_before = dict(base["locality"])
    bytes_before = archive.stat().st_size

    effort = _raw_terminal_repack(archive)
    verified = EG08.EG07.strong_verify(archive, expected_tree=EG08.EG07._treehash(source))
    locality = EG08.EG07.locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("EG09 exceeds frozen locality/decode limits")
    if (
        locality.get("max_decode_unit_bytes") != locality_before.get("max_decode_unit_bytes")
        or locality.get("max_member_read_amplification") != locality_before.get("max_member_read_amplification")
        or locality.get("member_count") != locality_before.get("member_count")
    ):
        raise RuntimeError("EG09 changed physical locality geometry")

    result = dict(base)
    result.update(
        {
            "profile": "federated-eg09-raw-terminal-effort",
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
    EG08.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return EG08.strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    return EG08.locality_report(archive)
