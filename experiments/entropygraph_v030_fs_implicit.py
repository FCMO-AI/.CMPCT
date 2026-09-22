from __future__ import annotations

"""Implicit-regular-path filesystem control plane for the federated r25 campaign.

C25EG02 removed duplicate regular size/SHA ownership but still repeated every regular logical path inside both the
authenticated federated content graph and the filesystem-control manifest.  Exact office evidence leaves only a
few hundred bytes between the all-best C25EG02 bound and the immutable v0.29 floor, so this candidate removes that
remaining duplicate ownership without weakening identity:

* the federated content graph remains the authenticated owner of every regular path and byte identity;
* this control plane stores regular filesystem metadata in sorted graph-path order, without regular path strings;
* directories, symlinks and hardlinks retain explicit path declarations; hardlinks target a regular graph index;
* decoding requires the authenticated graph regular path set and expands to the exact canonical v1 semantics.

This is research/candidate machinery only.  Shipping r25 grammar and every release threshold remain unchanged.
"""

from pathlib import Path, PurePosixPath

import hashlib
import msgpack

from experiments import entropygraph_v030_product_fs as FS

IMPLICIT_VERSION = 3
MAX_IMPLICIT_BYTES = FS.MAX_MANIFEST_BYTES
_KIND_TO_CODE = {"d": 1, "l": 2, "h": 3}
_CODE_TO_KIND = {value: key for key, value in _KIND_TO_CODE.items()}


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, bytes):
        return ("b", value)
    return value


def _common_prefix(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    index = 0
    while index < limit and left[index] == right[index]:
        index += 1
    return index


def _validate_metadata(meta: list) -> None:
    if not isinstance(meta, list) or len(meta) != 5:
        raise RuntimeError("implicit r25 metadata tuple declaration")
    mode, mtime_ns, uid, gid, xattrs = meta
    if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
        raise RuntimeError("implicit r25 mode declaration")
    if (
        not isinstance(mtime_ns, int)
        or isinstance(mtime_ns, bool)
        or not FS.SIGNED_MTIME_MIN <= mtime_ns <= FS.SIGNED_MTIME_MAX
    ):
        raise RuntimeError("implicit r25 mtime declaration")
    for value, label in ((uid, "uid"), (gid, "gid")):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= FS.UID_GID_MAX:
            raise RuntimeError(f"implicit r25 {label} declaration")
    if not isinstance(xattrs, list):
        raise RuntimeError("implicit r25 xattr declaration")
    for item in xattrs:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], bytes)
        ):
            raise RuntimeError("implicit r25 xattr item")


def encode_v1(raw_v1: bytes, *, max_path_bytes: int, max_entries: int) -> bytes:
    decoded = FS.decode_manifest(raw_v1, max_path_bytes=max_path_bytes, max_entries=max_entries)
    entries = decoded["manifest"]["entries"]
    metadata: list[list] = []
    metadata_index: dict[object, int] = {}

    def meta_index(row: list) -> int:
        meta = [row[2], row[3], row[4], row[5], row[6]]
        key = _freeze(meta)
        existing = metadata_index.get(key)
        if existing is not None:
            return existing
        index = len(metadata)
        metadata_index[key] = index
        metadata.append(meta)
        return index

    regular_entries = [row for row in entries if row[1] == "f"]
    regular_paths = [row[0] for row in regular_entries]
    regular_index = {path: index for index, path in enumerate(regular_paths)}
    regular_meta = [meta_index(row) for row in regular_entries]

    explicit_rows: list[list] = []
    previous = ""
    for row in entries:
        rel, kind, *_rest, extra = row
        if kind == "f":
            continue
        prefix = _common_prefix(previous, rel)
        suffix = rel[prefix:]
        code = _KIND_TO_CODE[kind]
        mi = meta_index(row)
        if kind == "d":
            payload = None
        elif kind == "l":
            payload = extra
        else:
            if extra not in regular_index:
                raise RuntimeError("implicit hardlink target is not an authenticated regular owner")
            payload = regular_index[extra]
        explicit_rows.append([prefix, suffix, code, mi, payload])
        previous = rel

    payload = [IMPLICIT_VERSION, metadata, regular_meta, explicit_rows]
    raw = msgpack.packb(payload, use_bin_type=True)
    if len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit r25 filesystem manifest exceeds bounded decode unit")
    return raw


def _unpack(raw: bytes, *, max_path_bytes: int, max_entries: int) -> tuple[list[list], list[int], list[list], list[str]]:
    if not isinstance(raw, bytes) or len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit r25 filesystem manifest exceeds policy")
    try:
        payload = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=max_entries * 6 + 1024,
            max_map_len=16,
            max_str_len=max_path_bytes,
            max_bin_len=MAX_IMPLICIT_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded implicit r25 filesystem manifest") from exc
    if not isinstance(payload, list) or len(payload) != 4 or payload[0] != IMPLICIT_VERSION:
        raise RuntimeError("unsupported implicit r25 filesystem manifest version")
    metadata, regular_meta, explicit_rows = payload[1], payload[2], payload[3]
    if not isinstance(metadata, list) or len(metadata) > max_entries:
        raise RuntimeError("implicit r25 metadata-table declaration")
    if not isinstance(regular_meta, list) or len(regular_meta) > max_entries:
        raise RuntimeError("implicit r25 regular metadata declaration")
    if not isinstance(explicit_rows, list) or len(explicit_rows) > max_entries:
        raise RuntimeError("implicit r25 explicit entry-count declaration")
    if len(regular_meta) + len(explicit_rows) > max_entries:
        raise RuntimeError("implicit r25 total entry-count declaration")
    for meta in metadata:
        _validate_metadata(meta)
    for mi in regular_meta:
        if not isinstance(mi, int) or isinstance(mi, bool) or not 0 <= mi < len(metadata):
            raise RuntimeError("implicit r25 regular metadata-table reference")

    paths: list[str] = []
    previous = ""
    seen: set[str] = set()
    for index, row in enumerate(explicit_rows):
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("malformed implicit r25 filesystem entry")
        prefix, suffix, code, mi, extra = row
        if (
            not isinstance(prefix, int)
            or isinstance(prefix, bool)
            or prefix < 0
            or prefix > len(previous)
            or not isinstance(suffix, str)
        ):
            raise RuntimeError("implicit r25 path-delta declaration")
        if code not in _CODE_TO_KIND:
            raise RuntimeError("implicit r25 entry kind declaration")
        if not isinstance(mi, int) or isinstance(mi, bool) or not 0 <= mi < len(metadata):
            raise RuntimeError("implicit r25 metadata-table reference")
        rel = previous[:prefix] + suffix
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe implicit r25 filesystem path") from exc
        if rel in seen or (paths and rel <= paths[-1]):
            raise RuntimeError("implicit r25 explicit paths are not strictly sorted/unique")
        kind = _CODE_TO_KIND[code]
        if kind == "d":
            if extra is not None:
                raise RuntimeError("implicit directory entry carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("implicit r25 symlink target declaration")
        else:
            if not isinstance(extra, int) or isinstance(extra, bool) or not 0 <= extra < len(regular_meta):
                raise RuntimeError("implicit hardlink target must reference a regular graph entry")
        paths.append(rel)
        seen.add(rel)
        previous = rel
    return metadata, regular_meta, explicit_rows, paths


def identities_from_profile(
    profile: Path,
    raw: bytes,
    *,
    max_path_bytes: int,
    max_entries: int,
    internal_path: str = FS.FILESYSTEM_MANIFEST,
) -> dict[str, tuple[int, bytes]]:
    _metadata, regular_meta, _explicit, explicit_paths = _unpack(
        raw, max_path_bytes=max_path_bytes, max_entries=max_entries
    )
    identities: dict[str, tuple[int, bytes]] = {}
    for path in sorted(p for p in profile.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(profile).as_posix()
        if rel == internal_path:
            continue
        if rel in explicit_paths:
            raise RuntimeError("implicit filesystem path collides with authenticated regular graph path")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                digest.update(block)
        identities[rel] = (size, digest.digest())
    if len(identities) != len(regular_meta):
        raise RuntimeError(
            f"implicit manifest/content-graph regular-count mismatch: manifest={len(regular_meta)} graph={len(identities)}"
        )
    return identities


def decode_to_v1(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> dict:
    metadata, regular_meta, explicit_rows, explicit_paths = _unpack(
        raw, max_path_bytes=max_path_bytes, max_entries=max_entries
    )
    regular_paths = sorted(regular_identities)
    if len(regular_paths) != len(regular_meta):
        raise RuntimeError("implicit regular identity count does not match authenticated metadata vector")
    for rel in regular_paths:
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe authenticated regular graph path") from exc
    if set(regular_paths) & set(explicit_paths):
        raise RuntimeError("implicit regular and explicit filesystem path sets overlap")

    entries: list[list] = []
    regular: dict[str, tuple[int, bytes]] = {}
    for rel, mi in zip(regular_paths, regular_meta, strict=True):
        mode, mtime_ns, uid, gid, xattrs = metadata[mi]
        size, digest = regular_identities[rel]
        if not isinstance(size, int) or size < 0 or not isinstance(digest, bytes) or len(digest) != 32:
            raise RuntimeError("invalid authenticated regular graph identity")
        regular[rel] = (int(size), bytes(digest))
        entries.append([rel, "f", mode, mtime_ns, uid, gid, xattrs, [int(size), bytes(digest)]])

    hardlinks: dict[str, str] = {}
    for row, rel in zip(explicit_rows, explicit_paths, strict=True):
        _prefix, _suffix, code, mi, extra = row
        mode, mtime_ns, uid, gid, xattrs = metadata[mi]
        kind = _CODE_TO_KIND[code]
        if kind == "d":
            semantic_extra = None
        elif kind == "l":
            semantic_extra = extra
        else:
            semantic_extra = regular_paths[int(extra)]
            hardlinks[rel] = semantic_extra
        entries.append([rel, kind, mode, mtime_ns, uid, gid, xattrs, semantic_extra])

    entries.sort(key=lambda row: row[0])
    if len({row[0] for row in entries}) != len(entries):
        raise RuntimeError("implicit expanded filesystem paths are not unique")
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def semantics_equal(v1_raw: bytes, implicit_raw: bytes, *, max_path_bytes: int, max_entries: int) -> bool:
    original = FS.decode_manifest(v1_raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    identities = {path: (size, digest) for path, (size, digest) in original["regular"].items()}
    expanded = decode_to_v1(
        implicit_raw,
        regular_identities=identities,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    return expanded["manifest"] == original["manifest"]
