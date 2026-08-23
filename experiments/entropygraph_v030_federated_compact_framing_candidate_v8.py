from __future__ import annotations

"""C25EG08: EG07 payload/metadata semantics with compact self-describing physical framing.

Exact EG07 evidence leaves office 42 bytes above the immutable accepted-v0.29 floor while already beating ZIP
and Zstd on size and verified creation time. EG08 deliberately stops changing filesystem-control semantics and
moves one layer down: Zstd frames already carry their decoded content size, and authenticated metadata already
carries ``pack_count``. The inherited CMPNX5 physical header redundantly stores those values again.

EG08 removes only those redundant physical integers:
- primary/tail metadata raw size is recovered from the Zstd frame content-size field;
- pack count is recovered from authenticated metadata;
- a Zstd pack's raw size is recovered from its frame, while an uncompressed pack's raw size equals its payload.

SHA-256 metadata/pack authentication, CRC32 hot integrity, duplicated primary/tail metadata, pack payload bytes,
reconstruction graph, filesystem semantics and locality limits are unchanged. Research-only; shipping/native/
Android dispatch remain untouched.
"""

import hashlib
from pathlib import Path
import struct
import tempfile

import msgpack
import zstandard as zstd

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

MAGIC = b"C25EG08\0"
TAIL_MAGIC = b"C25EG8T\0"
# magic + compressed metadata size + SHA-256(raw metadata)
HDR = struct.Struct("<8sQ32s")
# codec + compressed payload size + CRC32(raw payload) + SHA-256(raw payload)
PH = struct.Struct("<BQI32s")
# tail magic + compressed metadata size + SHA-256(raw metadata)
FTR = struct.Struct("<8sQ32s")

MAX_DECODE_UNIT = EG07.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG07.MAX_MEMBER_AMPLIFICATION


def _frame_size(payload: bytes, *, label: str) -> int:
    try:
        size = int(zstd.frame_content_size(payload))
    except Exception as exc:
        raise RuntimeError(f"{label} has no bounded Zstd frame size") from exc
    if size < 0:
        raise RuntimeError(f"{label} has unknown Zstd frame size")
    return size


def _validate_metadata_map(value, *, root: bool = False) -> None:
    """Keep EG07's metadata-key contract after its temporary EG06 binding is restored.

    EG07 emits exactly one compact integer root key (7). Its implementation temporarily rebinds EG06's
    ``EMBEDDED_FS_KEY`` while building/reading an EG07 archive, then restores EG06 to key 6. EG08 parses EG07
    metadata outside that mutation context, so delegating to EG06's validator would incorrectly reject valid
    EG07 metadata. Own the narrow key contract here instead: key 7 is allowed only at the authenticated root;
    every other root key and every nested map key must remain a string.
    """

    if isinstance(value, dict):
        for key, nested in value.items():
            if root:
                if not isinstance(key, str) and key != EG07.EMBEDDED_FS_KEY:
                    raise RuntimeError("EG08 metadata contains an unauthorized non-string root key")
            elif not isinstance(key, str):
                raise RuntimeError("EG08 metadata contains a non-string nested key")
            _validate_metadata_map(nested, root=False)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_metadata_map(nested, root=False)


def _decode_metadata(payload: bytes, digest: bytes) -> tuple[bytes, dict]:
    raw_size = _frame_size(payload, label="metadata")
    raw = V25.zd(payload, raw_size)
    if hashlib.sha256(raw).digest() != digest:
        raise RuntimeError("compact framing metadata authentication")
    try:
        meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    except Exception as exc:
        raise RuntimeError("compact framing metadata decode") from exc
    _validate_metadata_map(meta, root=True)
    if not isinstance(meta, dict) or meta.get("v") != 4:
        raise RuntimeError("compact framing metadata version")
    return raw, meta


def _parse(path: Path) -> dict:
    blob = path.read_bytes()
    if len(blob) < HDR.size + FTR.size:
        raise RuntimeError("compact framing archive truncated")

    primary_error: Exception | None = None
    meta_comp: bytes | None = None
    meta_raw: bytes | None = None
    meta: dict | None = None
    mcs: int | None = None
    digest: bytes | None = None
    try:
        magic, pmcs, pdigest = HDR.unpack_from(blob, 0)
        if magic != MAGIC:
            raise RuntimeError("compact framing primary magic")
        start = HDR.size
        end = start + int(pmcs)
        if end > len(blob) - FTR.size:
            raise RuntimeError("compact framing primary metadata bounds")
        candidate = blob[start:end]
        raw, decoded = _decode_metadata(candidate, pdigest)
        meta_comp, meta_raw, meta, mcs, digest = candidate, raw, decoded, int(pmcs), pdigest
    except Exception as exc:
        primary_error = exc

    if meta is None:
        try:
            tail, tmcs, tdigest = FTR.unpack_from(blob, len(blob) - FTR.size)
            if tail != TAIL_MAGIC:
                raise RuntimeError("compact framing tail magic")
            footer_off = len(blob) - FTR.size
            start = footer_off - int(tmcs)
            if start < HDR.size:
                raise RuntimeError("compact framing tail metadata bounds")
            candidate = blob[start:footer_off]
            raw, decoded = _decode_metadata(candidate, tdigest)
            meta_comp, meta_raw, meta, mcs, digest = candidate, raw, decoded, int(tmcs), tdigest
        except Exception as tail_error:
            raise RuntimeError(
                f"no authenticated compact metadata copy: primary={primary_error!r}; tail={tail_error!r}"
            ) from tail_error

    assert meta_comp is not None and meta_raw is not None and meta is not None and mcs is not None and digest is not None
    pack_count = int(meta.get("pack_count", -1))
    if pack_count < 0:
        raise RuntimeError("compact framing pack count")

    pos = HDR.size + mcs
    packs = []
    for index in range(pack_count):
        if pos + PH.size > len(blob) - FTR.size:
            raise RuntimeError(f"compact framing pack-header bounds {index}")
        codec, csize, crc, pdigest = PH.unpack_from(blob, pos)
        pos += PH.size
        end = pos + int(csize)
        if end > len(blob) - FTR.size:
            raise RuntimeError(f"compact framing pack-payload bounds {index}")
        payload = blob[pos:end]
        usize = _frame_size(payload, label=f"pack {index}") if int(codec) == 1 else len(payload)
        packs.append((int(codec), usize, int(csize), int(crc), pdigest, payload))
        pos = end

    tail_meta_start = len(blob) - FTR.size - mcs
    if pos != tail_meta_start:
        raise RuntimeError("compact framing physical/tail boundary")
    return {
        "meta_comp": meta_comp,
        "meta_raw": meta_raw,
        "meta": meta,
        "mcs": mcs,
        "digest": digest,
        "packs": packs,
        "primary_error": primary_error,
    }


def _expand_to_eg07(path: Path, target: Path) -> dict:
    parsed = _parse(path)
    meta_comp = parsed["meta_comp"]
    meta_raw = parsed["meta_raw"]
    digest = parsed["digest"]
    packs = parsed["packs"]
    parts = [V25.HDR.pack(EG07.MAGIC, len(meta_comp), len(meta_raw), len(packs), digest), meta_comp]
    for codec, usize, csize, crc, pdigest, payload in packs:
        parts.extend((V25.PH.pack(codec, usize, csize, crc, pdigest), payload))
    parts.extend((meta_comp, V25.FTR.pack(EG07.TAIL_MAGIC, len(meta_comp), len(meta_raw), digest)))
    target.write_bytes(b"".join(parts))
    return parsed


def compact_existing(source: Path, target: Path) -> dict:
    """Convert one verified EG07 archive without touching metadata or payload bytes."""
    verified = EG07.strong_verify(source)
    raw = source.read_bytes()
    magic, mcs, mus, pack_count, digest = V25.HDR.unpack_from(raw, 0)
    if magic != EG07.MAGIC:
        raise RuntimeError("compact source is not C25EG07")
    meta_start = V25.HDR.size
    meta_end = meta_start + int(mcs)
    meta_comp = raw[meta_start:meta_end]
    meta_raw = V25.zd(meta_comp, int(mus))
    if hashlib.sha256(meta_raw).digest() != digest:
        raise RuntimeError("compact source metadata authentication")
    meta = msgpack.unpackb(meta_raw, raw=False, strict_map_key=False)
    _validate_metadata_map(meta, root=True)
    if int(meta.get("pack_count", -1)) != int(pack_count):
        raise RuntimeError("compact source pack-count disagreement")

    pos = meta_end
    out = [HDR.pack(MAGIC, int(mcs), digest), meta_comp]
    for index in range(int(pack_count)):
        codec, usize, csize, crc, pdigest = V25.PH.unpack_from(raw, pos)
        pos += V25.PH.size
        payload = raw[pos : pos + int(csize)]
        if len(payload) != int(csize):
            raise RuntimeError(f"compact source truncated pack {index}")
        inferred = _frame_size(payload, label=f"source pack {index}") if int(codec) == 1 else len(payload)
        if inferred != int(usize):
            raise RuntimeError(f"compact source pack {index} frame-size disagreement")
        out.extend((PH.pack(int(codec), int(csize), int(crc), pdigest), payload))
        pos += int(csize)
    tail, tmcs, tmus, tdigest = V25.FTR.unpack_from(raw, len(raw) - V25.FTR.size)
    if tail != EG07.TAIL_MAGIC or int(tmcs) != int(mcs) or int(tmus) != int(mus) or tdigest != digest:
        raise RuntimeError("compact source tail disagreement")
    if raw[pos : pos + int(mcs)] != meta_comp:
        raise RuntimeError("compact source metadata copies differ")
    out.extend((meta_comp, FTR.pack(TAIL_MAGIC, int(mcs), digest)))
    target.write_bytes(b"".join(out))
    saved = len(raw) - target.stat().st_size
    expected = (V25.HDR.size - HDR.size) + int(pack_count) * (V25.PH.size - PH.size) + (V25.FTR.size - FTR.size)
    if saved != expected:
        raise RuntimeError(f"compact framing saving mismatch: {saved} != {expected}")
    return {
        "profile": "federated-eg08-compact-physical-framing",
        "source_bytes": len(raw),
        "archive_bytes": target.stat().st_size,
        "framing_saving_bytes": saved,
        "pack_count": int(pack_count),
        "expected_framing_saving_bytes": expected,
        "source_verified": bool(verified.get("ok")),
    }


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-verify-") as td:
        expanded = Path(td) / "expanded.cmpct"
        parsed = _expand_to_eg07(archive, expanded)
        result = dict(EG07.strong_verify(expanded, expected_tree=expected_tree))
    result.update({
        "profile": "federated-eg08-compact-physical-framing",
        "compact_pack_count": len(parsed["packs"]),
        "recovered_from_tail": parsed["primary_error"] is not None,
    })
    return result


def extract(archive: Path, destination: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-extract-") as td:
        expanded = Path(td) / "expanded.cmpct"
        _expand_to_eg07(archive, expanded)
        EG07.extract(expanded, destination)


def locality_report(archive: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-locality-") as td:
        expanded = Path(td) / "expanded.cmpct"
        _expand_to_eg07(archive, expanded)
        return EG07.locality_report(expanded)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-build-") as td:
        standard = Path(td) / "standard-eg07.cmpct"
        base = EG07.build(source, standard)
        framing = compact_existing(standard, archive)
    verified = strong_verify(archive, expected_tree=EG07._treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("compact-framing candidate exceeds frozen locality/decode limits")
    return {
        "profile": "federated-eg08-compact-physical-framing",
        "format_revision": 25,
        "archive_bytes": archive.stat().st_size,
        "base": base,
        "framing": framing,
        "verified": verified,
        "locality": locality,
    }
