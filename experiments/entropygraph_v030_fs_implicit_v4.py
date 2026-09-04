from __future__ import annotations

"""C25EG04 filesystem control plane: implicit regular paths + default/delta metadata.

C25EG03 removed duplicate regular paths but exact office evidence still leaves only 173 bytes between the
all-best physical-pack compression bound and the immutable accepted-v0.29 floor.  This candidate attacks control
framing rather than compression effort:

* regular paths and regular byte identities remain owned solely by the authenticated federated content graph;
* one deterministic default filesystem-metadata tuple is stored once;
* each entry stores only a compact bitmask plus numeric deltas / changed xattrs relative to that default;
* explicit paths remain only for directories, symlinks and hardlinks, using the same prefix-delta grammar;
* decoding expands to the exact canonical filesystem-manifest-v1 semantics before publication.

This is bounded research/candidate machinery only.  It changes no shipping grammar or release threshold.
"""

from collections import Counter
import hashlib
from pathlib import Path

import msgpack

from experiments import entropygraph_v030_product_fs as FS

IMPLICIT_V4_VERSION = 4
MAX_IMPLICIT_BYTES = FS.MAX_MANIFEST_BYTES
_KIND_TO_CODE = {"d": 1, "l": 2, "h": 3}
_CODE_TO_KIND = {value: key for key, value in _KIND_TO_CODE.items()}
_MODE = 1 << 0
_MTIME = 1 << 1
_UID = 1 << 2
_GID = 1 << 3
_XATTRS = 1 << 4
_ALL_MASK = _MODE | _MTIME | _UID | _GID | _XATTRS


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
        raise RuntimeError("implicit-v4 metadata tuple declaration")
    mode, mtime_ns, uid, gid, xattrs = meta
    if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
        raise RuntimeError("implicit-v4 mode declaration")
    if (
        not isinstance(mtime_ns, int)
        or isinstance(mtime_ns, bool)
        or not FS.SIGNED_MTIME_MIN <= mtime_ns <= FS.SIGNED_MTIME_MAX
    ):
        raise RuntimeError("implicit-v4 mtime declaration")
    for value, label in ((uid, "uid"), (gid, "gid")):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= FS.UID_GID_MAX:
            raise RuntimeError(f"implicit-v4 {label} declaration")
    if not isinstance(xattrs, list):
        raise RuntimeError("implicit-v4 xattr declaration")
    for item in xattrs:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not isinstance(item[1], bytes)
        ):
            raise RuntimeError("implicit-v4 xattr item")


def _choose_default(entries: list[list]) -> list:
    if not entries:
        return [0, 0, 0, 0, []]
    values = [[row[2], row[3], row[4], row[5], row[6]] for row in entries]
    counts = Counter(_freeze(value) for value in values)
    # Deterministic tie-break: first occurrence in canonical entry order.
    best_count = max(counts.values())
    for value in values:
        if counts[_freeze(value)] == best_count:
            return value
    raise AssertionError("unreachable default metadata selection")


def _override(meta: list, default: list) -> list:
    mask = 0
    values: list = []
    for index, bit in enumerate((_MODE, _MTIME, _UID, _GID)):
        if meta[index] != default[index]:
            mask |= bit
            # Numeric deltas tend to encode substantially smaller than repeated absolute stat values.
            values.append(int(meta[index]) - int(default[index]))
    if meta[4] != default[4]:
        mask |= _XATTRS
        values.append(meta[4])
    return [mask, *values]


def _apply_override(default: list, encoded: list) -> list:
    if not isinstance(encoded, list) or not encoded:
        raise RuntimeError("implicit-v4 metadata override declaration")
    mask = encoded[0]
    if not isinstance(mask, int) or isinstance(mask, bool) or mask < 0 or mask & ~_ALL_MASK:
        raise RuntimeError("implicit-v4 metadata override mask")
    cursor = 1
    out = [default[0], default[1], default[2], default[3], default[4]]
    for index, bit in enumerate((_MODE, _MTIME, _UID, _GID)):
        if mask & bit:
            if cursor >= len(encoded) or not isinstance(encoded[cursor], int) or isinstance(encoded[cursor], bool):
                raise RuntimeError("implicit-v4 numeric metadata delta")
            out[index] = int(default[index]) + int(encoded[cursor])
            cursor += 1
    if mask & _XATTRS:
        if cursor >= len(encoded) or not isinstance(encoded[cursor], list):
            raise RuntimeError("implicit-v4 xattr override")
        out[4] = encoded[cursor]
        cursor += 1
    if cursor != len(encoded):
        raise RuntimeError("implicit-v4 metadata override trailing fields")
    _validate_metadata(out)
    return out


def encode_decoded_v1(decoded: dict) -> bytes:
    """Encode one already-validated filesystem-v1 decode without reparsing its wire bytes.

    The promoted admission seam validates filesystem-v1 before considering a compact control. Reusing that exact
    semantic object removes a full bounded MessagePack decode from creation without gifting away validation or
    changing the implicit-v4 byte grammar. Callers that only have wire bytes should continue to use ``encode_v1``.
    """
    entries = decoded["manifest"]["entries"]
    default = _choose_default(entries)
    _validate_metadata(default)

    regular_entries = [row for row in entries if row[1] == "f"]
    regular_paths = [row[0] for row in regular_entries]
    regular_index = {path: index for index, path in enumerate(regular_paths)}
    regular_meta = [_override([row[2], row[3], row[4], row[5], row[6]], default) for row in regular_entries]

    explicit_rows: list[list] = []
    previous = ""
    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        if kind == "f":
            continue
        prefix = _common_prefix(previous, rel)
        suffix = rel[prefix:]
        code = _KIND_TO_CODE[kind]
        meta = _override([mode, mtime_ns, uid, gid, xattrs], default)
        if kind == "d":
            payload = None
        elif kind == "l":
            payload = extra
        else:
            if extra not in regular_index:
                raise RuntimeError("implicit-v4 hardlink target is not an authenticated regular owner")
            payload = regular_index[extra]
        explicit_rows.append([prefix, suffix, code, meta, payload])
        previous = rel

    payload = [IMPLICIT_V4_VERSION, default, regular_meta, explicit_rows]
    raw = msgpack.packb(payload, use_bin_type=True)
    if len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v4 filesystem manifest exceeds bounded decode unit")
    return raw


def encode_v1(raw_v1: bytes, *, max_path_bytes: int, max_entries: int) -> bytes:
    decoded = FS.decode_manifest(raw_v1, max_path_bytes=max_path_bytes, max_entries=max_entries)
    return encode_decoded_v1(decoded)


def _unpack(raw: bytes, *, max_path_bytes: int, max_entries: int):
    if not isinstance(raw, bytes) or len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v4 filesystem manifest exceeds policy")
    try:
        payload = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=max_entries * 8 + 1024,
            max_map_len=16,
            max_str_len=max_path_bytes,
            max_bin_len=MAX_IMPLICIT_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded implicit-v4 filesystem manifest") from exc
    if not isinstance(payload, list) or len(payload) != 4 or payload[0] != IMPLICIT_V4_VERSION:
        raise RuntimeError("unsupported implicit-v4 filesystem manifest version")
    default, regular_meta, explicit_rows = payload[1], payload[2], payload[3]
    _validate_metadata(default)
    if not isinstance(regular_meta, list) or len(regular_meta) > max_entries:
        raise RuntimeError("implicit-v4 regular metadata declaration")
    if not isinstance(explicit_rows, list) or len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v4 explicit entry-count declaration")
    if len(regular_meta) + len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v4 total entry-count declaration")
    decoded_regular = [_apply_override(default, value) for value in regular_meta]

    paths: list[str] = []
    decoded_explicit: list[tuple[list, list, str]] = []
    previous = ""
    seen: set[str] = set()
    for row in explicit_rows:
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("malformed implicit-v4 filesystem entry")
        prefix, suffix, code, encoded_meta, extra = row
        if (
            not isinstance(prefix, int)
            or isinstance(prefix, bool)
            or prefix < 0
            or prefix > len(previous)
            or not isinstance(suffix, str)
        ):
            raise RuntimeError("implicit-v4 path-delta declaration")
        if code not in _CODE_TO_KIND:
            raise RuntimeError("implicit-v4 entry kind declaration")
        rel = previous[:prefix] + suffix
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe implicit-v4 filesystem path") from exc
        if rel in seen or (paths and rel <= paths[-1]):
            raise RuntimeError("implicit-v4 explicit paths are not strictly sorted/unique")
        kind = _CODE_TO_KIND[code]
        meta = _apply_override(default, encoded_meta)
        if kind == "d":
            if extra is not None:
                raise RuntimeError("implicit-v4 directory carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("implicit-v4 symlink target declaration")
        else:
            if not isinstance(extra, int) or isinstance(extra, bool) or not 0 <= extra < len(regular_meta):
                raise RuntimeError("implicit-v4 hardlink target must reference a regular graph entry")
        paths.append(rel)
        seen.add(rel)
        decoded_explicit.append((row, meta, rel))
        previous = rel
    return default, decoded_regular, decoded_explicit, paths


def identities_from_profile(
    profile: Path,
    raw: bytes,
    *,
    max_path_bytes: int,
    max_entries: int,
    internal_path: str,
) -> dict[str, tuple[int, bytes]]:
    _default, regular_meta, _explicit, explicit_paths = _unpack(
        raw, max_path_bytes=max_path_bytes, max_entries=max_entries
    )
    identities: dict[str, tuple[int, bytes]] = {}
    for path in sorted(p for p in profile.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(profile).as_posix()
        if rel == internal_path:
            continue
        if rel in explicit_paths:
            raise RuntimeError("implicit-v4 explicit path collides with authenticated regular graph path")
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
            f"implicit-v4 manifest/content-graph regular-count mismatch: manifest={len(regular_meta)} graph={len(identities)}"
        )
    return identities


def decode_to_v1(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> dict:
    _default, regular_meta, decoded_explicit, explicit_paths = _unpack(
        raw, max_path_bytes=max_path_bytes, max_entries=max_entries
    )
    regular_paths = sorted(regular_identities)
    if len(regular_paths) != len(regular_meta):
        raise RuntimeError("implicit-v4 regular identity count does not match metadata vector")
    for rel in regular_paths:
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe authenticated implicit-v4 graph path") from exc
    if set(regular_paths) & set(explicit_paths):
        raise RuntimeError("implicit-v4 regular and explicit filesystem path sets overlap")

    entries: list[list] = []
    regular: dict[str, tuple[int, bytes]] = {}
    for rel, meta in zip(regular_paths, regular_meta, strict=True):
        mode, mtime_ns, uid, gid, xattrs = meta
        size, digest = regular_identities[rel]
        if not isinstance(size, int) or size < 0 or not isinstance(digest, bytes) or len(digest) != 32:
            raise RuntimeError("invalid authenticated implicit-v4 regular graph identity")
        regular[rel] = (int(size), bytes(digest))
        entries.append([rel, "f", mode, mtime_ns, uid, gid, xattrs, [int(size), bytes(digest)]])

    hardlinks: dict[str, str] = {}
    for (row, meta, rel) in decoded_explicit:
        _prefix, _suffix, code, _encoded_meta, extra = row
        mode, mtime_ns, uid, gid, xattrs = meta
        kind = _CODE_TO_KIND[code]
        if kind == "d":
            semantic_extra = None
        elif kind == "l":
            semantic_extra = extra
        else:
            owner_index = int(extra)
            semantic_extra = regular_paths[owner_index]
            if meta != regular_meta[owner_index]:
                # A hardlink is another name for the same inode; its inode-owned metadata cannot physically
                # diverge from the regular owner. Fail before expanding a control plane whose claimed filesystem
                # semantics no conforming materializer could preserve exactly.
                raise RuntimeError("implicit-v4 hardlink metadata must match its regular-file owner")
            hardlinks[rel] = semantic_extra
        entries.append([rel, kind, mode, mtime_ns, uid, gid, xattrs, semantic_extra])

    entries.sort(key=lambda item: item[0])
    if len({row[0] for row in entries}) != len(entries):
        raise RuntimeError("implicit-v4 expanded filesystem paths are not unique")
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def semantics_equal_decoded(
    original: dict,
    implicit_raw: bytes,
    *,
    max_path_bytes: int,
    max_entries: int,
) -> bool:
    """Prove implicit-v4 semantics against an already-validated filesystem-v1 decode."""
    identities = {path: (size, digest) for path, (size, digest) in original["regular"].items()}
    expanded = decode_to_v1(
        implicit_raw,
        regular_identities=identities,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    return expanded["manifest"] == original["manifest"]


def semantics_equal(v1_raw: bytes, implicit_raw: bytes, *, max_path_bytes: int, max_entries: int) -> bool:
    original = FS.decode_manifest(v1_raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    return semantics_equal_decoded(
        original,
        implicit_raw,
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
