from __future__ import annotations

"""C25EG10: EG09 ordinary first-pass fusion + cold-stream-only adaptive rewrite.

Research-only.  Ordinary final object packs receive the exact EG08 effort ladder during
first-pass V25 construction through EG09.  A narrow post-pass then revisits only cold
stream packs, the representation class that cannot be distinguished safely from level-3
geometry probes at the generic compressor boundary.
"""

import binascii
from pathlib import Path

from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_fused_effort_candidate_v9 as EG09

EG07 = EG09.EG07
V25 = EG09.V25
MAGIC = EG07.MAGIC
TAIL_MAGIC = EG07.TAIL_MAGIC
EFFORT_LEVELS = EG09.EFFORT_LEVELS


def _cold_stream_repack(archive: Path) -> dict:
    """Re-encode only authenticated non-hot stream packs through the EG08 ladder."""
    uncapped_zc = V25.zc
    raw_archive = archive.read_bytes()
    magic, meta_comp_size, _meta_raw_size, _pack_count, _meta_hash = V25.HDR.unpack_from(raw_archive, 0)
    if magic != MAGIC:
        raise RuntimeError("EG10 expected EG07/EG09 primary identity")
    meta_end = V25.HDR.size + int(meta_comp_size)

    packs: list[dict] = []
    offsets = []
    with EG07._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi, (offset, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                stream.seek(offset)
                payload = stream.read(csize)
                if len(payload) != csize:
                    raise RuntimeError(f"EG10 truncated pack {pi}")
                packs.append(
                    {
                        "index": pi,
                        "codec": int(codec),
                        "usize": int(usize),
                        "csize": int(csize),
                        "crc": int(crc),
                        "sha": expected_sha,
                        "payload": payload,
                    }
                )
        finally:
            stream.close()

    stream_indices, hot_indices = EG08._stream_roles(dict(meta), len(packs))
    cold_indices = stream_indices - hot_indices
    old_physical_end = meta_end
    if packs:
        old_physical_end = int(offsets[-1][0]) + int(packs[-1]["csize"])
    prefix = raw_archive[:meta_end]
    suffix = raw_archive[old_physical_end:]

    rebuilt = bytearray()
    attempts = 0
    changed = 0
    saved = 0
    rows = []
    for row in packs:
        pi = int(row["index"])
        codec = int(row["codec"])
        usize = int(row["usize"])
        crc = int(row["crc"])
        expected_sha = row["sha"]
        payload = row["payload"]
        selected_codec = codec
        selected_payload = payload
        selected_level = "current"
        tried = []

        if pi in cold_indices:
            raw = V25.zd(payload, usize) if codec == 1 else payload
            if len(raw) != usize:
                raise RuntimeError(f"EG10 cold stream pack-size mismatch {pi}")
            if (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                raise RuntimeError(f"EG10 cold stream pack CRC mismatch {pi}")
            if V25.H(raw) != expected_sha:
                raise RuntimeError(f"EG10 cold stream pack SHA mismatch {pi}")
            best_size = len(payload)
            for effort in EFFORT_LEVELS:
                attempts += 1
                comp = uncapped_zc(raw, effort)
                if len(comp) + 8 < len(raw):
                    candidate_codec = 1
                    candidate_payload = comp
                else:
                    candidate_codec = 0
                    candidate_payload = raw
                candidate_size = len(candidate_payload)
                tried.append({"level": int(effort), "storage_bytes": candidate_size})
                if candidate_size <= best_size:
                    if candidate_size < best_size:
                        selected_codec = candidate_codec
                        selected_payload = candidate_payload
                        best_size = candidate_size
                        selected_level = str(effort)
                    continue
                break
            if selected_codec != codec or len(selected_payload) != len(payload):
                changed += 1
                saved += len(payload) - len(selected_payload)
            rows.append(
                {
                    "index": pi,
                    "current_payload_bytes": len(payload),
                    "selected_payload_bytes": len(selected_payload),
                    "selected_level": selected_level,
                    "saved_bytes": len(payload) - len(selected_payload),
                    "tried": tried,
                }
            )

        rebuilt += V25.PH.pack(selected_codec, usize, len(selected_payload), crc, expected_sha)
        rebuilt += selected_payload

    archive.write_bytes(prefix + bytes(rebuilt) + suffix)
    return {
        "cold_stream_pack_count": len(cold_indices),
        "changed_cold_stream_pack_count": changed,
        "cold_stream_saved_bytes": saved,
        "effort_attempts": attempts,
        "packs": rows,
    }


def _treehash(root: Path) -> str:
    return EG07._treehash(root)


def extract(archive: Path, destination: Path) -> None:
    EG07.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return EG07.strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    return EG07.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    base = dict(EG09.build(source, archive))
    cold = _cold_stream_repack(archive)
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("EG10 hybrid candidate exceeds frozen locality/decode limits")
    before = base["locality"]
    if (
        locality.get("member_count") != before.get("member_count")
        or locality.get("max_decode_unit_bytes") != before.get("max_decode_unit_bytes")
        or locality.get("max_member_read_amplification") != before.get("max_member_read_amplification")
    ):
        raise RuntimeError("EG10 hybrid cold-stream rewrite changed locality geometry")
    result = dict(base)
    result.update(
        {
            "profile": "federated-eg10-hybrid-fusion",
            "archive_bytes": archive.stat().st_size,
            "verified": verified,
            "locality": locality,
            "cold_stream_effort": cold,
        }
    )
    return result
