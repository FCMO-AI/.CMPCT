from __future__ import annotations

"""C25EG06: EG05 physical graph with run-length implicit filesystem control.

EG05 left office only 50 bytes above the immutable accepted-v0.29 floor at the all-best physical-pack bound.
EG06 changes only the bounded filesystem-control encoding: consecutive identical regular metadata overrides are
run-length encoded and the embedded metadata key uses a compact integer key.  The EntropyGraph reconstruction
graph, physical packs, integrity model, locality limits, recovery layout and compression-effort search are
otherwise unchanged.  Research-only; shipping selector/native/Android dispatch remain untouched.
"""

from contextlib import contextmanager
import os
from pathlib import Path

import msgpack

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05
from experiments import entropygraph_v030_fs_implicit_v5 as IFS5

MAGIC = b"C25EG06\0"
TAIL_MAGIC = b"C25EG6T\0"
EMBEDDED_FS_KEY = 6
LEVEL_CAP = EG05.LEVEL_CAP
MAX_PATH_BYTES = EG05.MAX_PATH_BYTES
MAX_PROFILE_FILES = EG05.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = EG05.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = EG05.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = EG05.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG05.MAX_MEMBER_AMPLIFICATION
# Benchmark adapters temporarily rebind the historical V25 engine while changing candidate identity.  EG06 is a
# framing-only child of EG05 and must therefore expose the exact same semantic lock, not a fresh lock and not an
# implicit private dependency.  Sharing the lock preserves the existing single-owner mutation boundary when the
# selective-effort oracle swaps CAND from EG01/EG05 to EG06.
_LOCK = EG05._LOCK
_PENDING_CONTROL = EG05._PENDING_CONTROL


def _validate_metadata_map(value, *, root: bool = False) -> None:
    """Preserve V25's string-key policy except for EG06's single compact root key.

    ``msgpack.unpackb`` defaults to ``strict_map_key=True`` and the inherited CMPNX5 reader therefore rejects
    EG06 before authentication/recovery can be exercised.  Disabling that globally would broaden every historical
    reader.  EG06 instead owns a candidate-local decoder which accepts exactly one integer map key (6) at the
    authenticated top level and retains string-only keys for every nested map.
    """

    if isinstance(value, dict):
        for key, nested in value.items():
            if root:
                if not isinstance(key, str) and key != EMBEDDED_FS_KEY:
                    raise RuntimeError("EG06 metadata contains an unauthorized non-string root key")
            elif not isinstance(key, str):
                raise RuntimeError("EG06 metadata contains an unauthorized nested non-string map key")
            _validate_metadata_map(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_metadata_map(nested)


def _unpack_authenticated_metadata(raw: bytes) -> dict:
    try:
        value = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid EG06 authenticated metadata") from exc
    if not isinstance(value, dict):
        raise RuntimeError("EG06 authenticated metadata is not a map")
    _validate_metadata_map(value, root=True)
    return value


def _open_ar_intkey():
    """V25 ``open_ar`` with EG06's narrowly-authorized integer root key.

    Layout, authentication, primary/tail recovery and pack-table parsing are intentionally byte-for-byte the
    inherited implementation.  Only the MessagePack key policy differs, and only inside the EG06 variant lock.
    """

    V25 = EG05.V25
    f = open(V25.OUT, "rb")
    primary_error = None
    metadata = None
    metadata_comp_size = None
    try:
        f.seek(0)
        header = f.read(V25.HDR.size)
        if len(header) != V25.HDR.size:
            raise RuntimeError("short header")
        magic, primary_comp_size, primary_raw_size, _pack_count, primary_hash = V25.HDR.unpack(header)
        if magic != V25.MAG:
            raise RuntimeError("primary magic")
        metadata_comp = f.read(primary_comp_size)
        metadata_raw = V25.zd(metadata_comp, primary_raw_size)
        if V25.H(metadata_raw) != primary_hash:
            raise RuntimeError("primary metadata authentication")
        metadata = _unpack_authenticated_metadata(metadata_raw)
        metadata_comp_size = primary_comp_size
    except Exception as exc:
        primary_error = exc

    if metadata is None:
        try:
            f.seek(-V25.FTR.size, os.SEEK_END)
            footer = f.read(V25.FTR.size)
            if len(footer) != V25.FTR.size:
                raise RuntimeError("short footer")
            tail, tail_comp_size, tail_raw_size, tail_hash = V25.FTR.unpack(footer)
            if tail != V25.TAIL:
                raise RuntimeError("tail magic")
            footer_offset = f.tell() - V25.FTR.size
            metadata_offset = footer_offset - tail_comp_size
            if metadata_offset < V25.HDR.size:
                raise RuntimeError("tail metadata offset")
            f.seek(metadata_offset)
            metadata_comp = f.read(tail_comp_size)
            metadata_raw = V25.zd(metadata_comp, tail_raw_size)
            if V25.H(metadata_raw) != tail_hash:
                raise RuntimeError("tail metadata authentication")
            metadata = _unpack_authenticated_metadata(metadata_raw)
            metadata_comp_size = tail_comp_size
        except Exception as tail_error:
            f.close()
            raise RuntimeError(
                f"no authenticated metadata copy: primary={primary_error!r}; tail={tail_error!r}"
            ) from tail_error

    if metadata.get("v") != 4:
        f.close()
        raise RuntimeError("unsupported CMPNX5 metadata version")
    pack_count = int(metadata["pack_count"])
    pack_start = V25.HDR.size + int(metadata_comp_size)
    f.seek(pack_start)
    pack_offsets = []
    for _ in range(pack_count):
        header = f.read(V25.PH.size)
        if len(header) != V25.PH.size:
            f.close()
            raise RuntimeError("truncated pack header")
        codec, raw_size, comp_size, crc, digest = V25.PH.unpack(header)
        offset = f.tell()
        pack_offsets.append((offset, codec, raw_size, comp_size, crc, digest))
        f.seek(comp_size, 1)
    return f, metadata, pack_offsets


@contextmanager
def _variant():
    old = (EG05.MAGIC, EG05.TAIL_MAGIC, EG05.EMBEDDED_FS_KEY, EG05.IFS4, EG05.V25.open_ar)
    EG05.MAGIC = MAGIC
    EG05.TAIL_MAGIC = TAIL_MAGIC
    EG05.EMBEDDED_FS_KEY = EMBEDDED_FS_KEY
    EG05.IFS4 = IFS5
    EG05.V25.open_ar = _open_ar_intkey
    try:
        yield
    finally:
        EG05.MAGIC, EG05.TAIL_MAGIC, EG05.EMBEDDED_FS_KEY, EG05.IFS4, EG05.V25.open_ar = old


@contextmanager
def _engine(archive: Path, profile: Path | None = None):
    with _variant():
        with EG05._engine(archive, profile):
            yield


def _treehash(root: Path) -> str:
    return EG05._treehash(root)


def _profile_key(profile: Path) -> str:
    return EG05._profile_key(profile)


def _prepare_profile(source: Path, profile: Path) -> dict:
    with _variant():
        stats = dict(EG05._prepare_profile(source, profile))
    stats["filesystem_control_encoding"] = "implicit-v5-rle-regular-metadata"
    return stats


def finalize_research_archive(archive: Path, profile: Path, fs: dict | None = None) -> dict:
    with _variant():
        return EG05.finalize_research_archive(archive, profile, fs)


def extract(archive: Path, destination: Path) -> None:
    with _variant():
        EG05.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    with _variant():
        result = dict(EG05.strong_verify(archive, expected_tree=expected_tree))
    result["profile"] = "federated-eg06-rle-fs"
    return result


def locality_report(archive: Path) -> dict:
    with _variant():
        return EG05.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    with _variant():
        result = dict(EG05.build(source, archive))
    result["profile"] = "federated-eg06-rle-fs"
    result["filesystem_control_encoding"] = "implicit-v5-rle-regular-metadata"
    return result
