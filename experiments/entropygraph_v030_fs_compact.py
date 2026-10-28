from __future__ import annotations

"""Compact authenticated filesystem-control grammar for the federated r25 campaign.

The existing r25 filesystem bridge deliberately carries a complete regular-file ``size + SHA-256`` identity in
its manifest even when the enclosing federated content graph already authenticates the same logical path and
bytes.  That duplication was a safe first productization boundary, but exact evidence now shows office misses the
accepted-v0.29 floor by only ~1.2 KiB even after giving every physical pack its best measured compression effort.

This module tests a stricter ownership split rather than weakening identity:

* the federated graph remains the sole owner of regular-file bytes and their authenticated physical recipes;
* this compact control plane owns filesystem kind, mode, signed mtime, uid/gid, xattrs and link relationships;
* extraction reconstructs the omitted regular ``size + SHA-256`` values from the already authenticated graph
  outputs, and requires the graph's public regular path set to match the manifest exactly before publication.

The wire form also interns repeated metadata tuples and prefix-compresses sorted logical paths.  Decoding expands
back to the exact v1 semantic manifest consumed by ``entropygraph_v030_product_fs``.  This is candidate/research
machinery only; it does not change the shipping r25 filesystem grammar or any release threshold.
"""

import hashlib
from pathlib import Path, PurePosixPath
from typing import Iterable

import msgpack

from experiments import entropygraph_v030_product_fs as FS

COMPACT_VERSION = 2
MAX_COMPACT_BYTES = FS.MAX_MANIFEST_BYTES
_KIND_TO_CODE = {"f": 0, "d": 1, "l": 2, "h": 3}
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
        raise RuntimeError("compact r25 metadata tuple declaration")
    mode, mtime_ns, uid, gid, xattrs = meta
    if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
        raise RuntimeError("compact r25 mode declaration")
    if (
        not isinstance(mtime_ns, int)
        or isinstance(mtime_ns, bool)
        or not FS.SIGNED_MTIME_MIN <= mtime_ns <= FS.SIGNED_MTIME_MAX
    ):
        raise RuntimeError("compact r25 mtime declaration")
    for value, label in ((uid, "uid"), (gid, "gid")):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= FS.UID_GID_MAX:
            raise RuntimeError(f"compact r25 {label} declaration")
    if not isinstance(xattrs, list):
        raise RuntimeError("compact r25 xattr declaration")
    for item in xattrs:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], bytes)
        ):
            raise RuntimeError("compact r25 xattr item")


def encode_v1(raw_v1: bytes, *, max_path_bytes: int, max_entries: int) -> bytes:
    """Encode an already validated v1 manifest into compact control-plane-only form."""
    decoded = FS.decode_manifest(raw_v1, max_path_bytes=max_path_bytes, max_entries=max_entries)
    entries = decoded["manifest"]["entries"]
    metadata: list[list] = []
    metadata_index: dict[object, int] = {}
    rows: list[list] = []
    path_to_index: dict[str, int] = {}
    previous = ""

    for index, row in enumerate(entries):
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        meta = [mode, mtime_ns, uid, gid, xattrs]
        key = _freeze(meta)
        mi = metadata_index.get(key)
        if mi is None:
            mi = len(metadata)
            metadata_index[key] = mi
            metadata.append(meta)

        prefix = _common_prefix(previous, rel)
        suffix = rel[prefix:]
        code = _KIND_TO_CODE[kind]
        if kind in ("f", "d"):
            compact_extra = None
        elif kind == "l":
            compact_extra = extra
        else:
            if extra not in path_to_index:
                raise RuntimeError("compact hardlink target is not an earlier entry")
            compact_extra = path_to_index[extra]
        rows.append([prefix, suffix, code, mi, compact_extra])
        path_to_index[rel] = index
        previous = rel

    payload = [COMPACT_VERSION, metadata, rows]
    raw = msgpack.packb(payload, use_bin_type=True)
    if len(raw) > MAX_COMPACT_BYTES:
        raise RuntimeError("compact r25 filesystem manifest exceeds bounded decode unit")
    return raw


def _unpack(raw: bytes, *, max_path_bytes: int, max_entries: int) -> tuple[list[list], list[list], list[str], list[int]]:
    if not isinstance(raw, bytes) or len(raw) > MAX_COMPACT_BYTES:
        raise RuntimeError("compact r25 filesystem manifest exceeds policy")
    try:
        payload = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=max_entries * 6 + 1024,
            max_map_len=16,
            max_str_len=max_path_bytes,
            max_bin_len=MAX_COMPACT_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded compact r25 filesystem manifest") from exc
    if not isinstance(payload, list) or len(payload) != 3 or payload[0] != COMPACT_VERSION:
        raise RuntimeError("unsupported compact r25 filesystem manifest version")
    metadata, rows = payload[1], payload[2]
    if not isinstance(metadata, list) or len(metadata) > max_entries:
        raise RuntimeError("compact r25 metadata-table declaration")
    if not isinstance(rows, list) or len(rows) > max_entries:
        raise RuntimeError("compact r25 entry-count declaration")
    for meta in metadata:
        _validate_metadata(meta)

    paths: list[str] = []
    kinds: list[int] = []
    previous = ""
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("malformed compact r25 filesystem entry")
        prefix, suffix, code, mi, extra = row
        if (
            not isinstance(prefix, int)
            or isinstance(prefix, bool)
            or prefix < 0
            or prefix > len(previous)
            or not isinstance(suffix, str)
        ):
            raise RuntimeError("compact r25 path-delta declaration")
        if code not in _CODE_TO_KIND:
            raise RuntimeError("compact r25 entry kind declaration")
        if not isinstance(mi, int) or isinstance(mi, bool) or not 0 <= mi < len(metadata):
            raise RuntimeError("compact r25 metadata-table reference")
        rel = previous[:prefix] + suffix
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe compact r25 filesystem path") from exc
        if rel in seen or (paths and rel <= paths[-1]):
            raise RuntimeError("compact r25 paths are not strictly sorted/unique")
        kind = _CODE_TO_KIND[code]
        if kind in ("f", "d"):
            if extra is not None:
                raise RuntimeError("compact regular/directory entry carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("compact r25 symlink target declaration")
        else:
            if (
                not isinstance(extra, int)
                or isinstance(extra, bool)
                or not 0 <= extra < index
                or kinds[extra] != _KIND_TO_CODE["f"]
            ):
                raise RuntimeError("compact hardlink target must be an earlier regular owner")
        paths.append(rel)
        kinds.append(code)
        seen.add(rel)
        previous = rel
    return metadata, rows, paths, kinds


def regular_paths(raw: bytes, *, max_path_bytes: int, max_entries: int) -> list[str]:
    _, _, paths, kinds = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    return [path for path, code in zip(paths, kinds, strict=True) if code == _KIND_TO_CODE["f"]]


def identities_from_profile(
    profile: Path,
    raw: bytes,
    *,
    max_path_bytes: int,
    max_entries: int,
    internal_path: str = FS.FILESYSTEM_MANIFEST,
) -> dict[str, tuple[int, bytes]]:
    """Recover regular identities only after requiring exact graph-path ownership."""
    expected = set(regular_paths(raw, max_path_bytes=max_path_bytes, max_entries=max_entries))
    actual: set[str] = set()
    for path in sorted(p for p in profile.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(profile).as_posix()
        if rel == internal_path:
            continue
        actual.add(rel)
    if actual != expected:
        missing = sorted(expected - actual)[:8]
        extra = sorted(actual - expected)[:8]
        raise RuntimeError(f"compact manifest/content-graph path mismatch: missing={missing!r} extra={extra!r}")

    identities: dict[str, tuple[int, bytes]] = {}
    for rel in sorted(expected):
        path = profile.joinpath(*PurePosixPath(rel).parts)
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
    return identities


def decode_to_v1(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> dict:
    """Expand compact control metadata into the exact semantic v1 manifest shape."""
    metadata, rows, paths, kinds = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    entries: list[list] = []
    regular: dict[str, tuple[int, bytes]] = {}
    hardlinks: dict[str, str] = {}
    for index, (row, rel, code) in enumerate(zip(rows, paths, kinds, strict=True)):
        _, _, _, mi, compact_extra = row
        mode, mtime_ns, uid, gid, xattrs = metadata[mi]
        kind = _CODE_TO_KIND[code]
        if kind == "f":
            identity = regular_identities.get(rel)
            if (
                identity is None
                or not isinstance(identity[0], int)
                or identity[0] < 0
                or not isinstance(identity[1], bytes)
                or len(identity[1]) != 32
            ):
                raise RuntimeError(f"missing authenticated graph identity for compact regular file: {rel}")
            extra = [int(identity[0]), bytes(identity[1])]
            regular[rel] = (int(identity[0]), bytes(identity[1]))
        elif kind == "d":
            extra = None
        elif kind == "l":
            extra = compact_extra
        else:
            target = paths[int(compact_extra)]
            if target not in regular:
                raise RuntimeError("compact hardlink target is not a reconstructed regular owner")
            extra = target
            hardlinks[rel] = target
        entries.append([rel, kind, mode, mtime_ns, uid, gid, xattrs, extra])

    if set(regular_identities) != set(regular):
        raise RuntimeError("compact regular identity set contains paths outside authenticated filesystem control plane")
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def semantics_equal(v1_raw: bytes, compact_raw: bytes, *, max_path_bytes: int, max_entries: int) -> bool:
    """Compare exact filesystem semantics while sourcing regular identities from the authenticated v1 reference."""
    original = FS.decode_manifest(v1_raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    identities = {path: (size, digest) for path, (size, digest) in original["regular"].items()}
    expanded = decode_to_v1(
        compact_raw,
        regular_identities=identities,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    return expanded["manifest"] == original["manifest"]
