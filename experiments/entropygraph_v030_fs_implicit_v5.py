from __future__ import annotations

"""C25EG06 filesystem control: implicit graph paths + run-length metadata overrides.

C25EG05 leaves office only 50 bytes above the immutable v0.29 floor after all-best physical-pack compression.
Its filesystem control still stores one MessagePack array for every regular-file metadata override, even when long
runs share exactly the same override (the common case for generated office trees).  This research codec keeps the
exact implicit-v4 semantics but run-length encodes consecutive regular metadata overrides.

No filesystem fact is removed: modes, signed mtimes, uid/gid, xattrs, explicit directories/symlinks/hardlinks,
and graph-owned regular identities all expand back to the canonical filesystem-manifest-v1 grammar.
"""

import hashlib
from pathlib import Path

import msgpack

from experiments import entropygraph_v030_fs_implicit_v4 as V4
from experiments import entropygraph_v030_product_fs as FS

IMPLICIT_V5_VERSION = 5
MAX_IMPLICIT_BYTES = FS.MAX_MANIFEST_BYTES


def _rle(values: list[list]) -> list[list]:
    runs: list[list] = []
    for value in values:
        if runs and runs[-1][1] == value:
            runs[-1][0] += 1
        else:
            runs.append([1, value])
    return runs


def _expand_runs(runs: list, *, max_entries: int) -> list[list]:
    if not isinstance(runs, list) or len(runs) > max_entries:
        raise RuntimeError("implicit-v5 regular metadata run declaration")
    out: list[list] = []
    for run in runs:
        if not isinstance(run, list) or len(run) != 2:
            raise RuntimeError("implicit-v5 malformed metadata run")
        count, encoded = run
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= max_entries:
            raise RuntimeError("implicit-v5 metadata run length")
        # Validate the override before multiplying it into the logical vector.
        if not isinstance(encoded, list) or not encoded:
            raise RuntimeError("implicit-v5 metadata run override")
        if len(out) + count > max_entries:
            raise RuntimeError("implicit-v5 expanded metadata count exceeds policy")
        out.extend([encoded] * count)
    return out


def encode_v1(raw_v1: bytes, *, max_path_bytes: int, max_entries: int) -> bytes:
    decoded = FS.decode_manifest(raw_v1, max_path_bytes=max_path_bytes, max_entries=max_entries)
    entries = decoded["manifest"]["entries"]
    default = V4._choose_default(entries)
    V4._validate_metadata(default)

    regular_entries = [row for row in entries if row[1] == "f"]
    regular_paths = [row[0] for row in regular_entries]
    regular_index = {path: index for index, path in enumerate(regular_paths)}
    regular_meta = [V4._override([row[2], row[3], row[4], row[5], row[6]], default) for row in regular_entries]
    regular_runs = _rle(regular_meta)

    explicit_rows: list[list] = []
    previous = ""
    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        if kind == "f":
            continue
        prefix = V4._common_prefix(previous, rel)
        suffix = rel[prefix:]
        code = V4._KIND_TO_CODE[kind]
        meta = V4._override([mode, mtime_ns, uid, gid, xattrs], default)
        if kind == "d":
            payload = None
        elif kind == "l":
            payload = extra
        else:
            if extra not in regular_index:
                raise RuntimeError("implicit-v5 hardlink target is not an authenticated regular owner")
            payload = regular_index[extra]
        explicit_rows.append([prefix, suffix, code, meta, payload])
        previous = rel

    payload = [IMPLICIT_V5_VERSION, default, regular_runs, explicit_rows]
    raw = msgpack.packb(payload, use_bin_type=True)
    if len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v5 filesystem manifest exceeds bounded decode unit")
    return raw


def _unpack(raw: bytes, *, max_path_bytes: int, max_entries: int):
    if not isinstance(raw, bytes) or len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v5 filesystem manifest exceeds policy")
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
        raise RuntimeError("invalid bounded implicit-v5 filesystem manifest") from exc
    if not isinstance(payload, list) or len(payload) != 4 or payload[0] != IMPLICIT_V5_VERSION:
        raise RuntimeError("unsupported implicit-v5 filesystem manifest version")
    default, regular_runs, explicit_rows = payload[1], payload[2], payload[3]
    V4._validate_metadata(default)
    regular_meta = _expand_runs(regular_runs, max_entries=max_entries)
    if not isinstance(explicit_rows, list) or len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v5 explicit entry-count declaration")
    if len(regular_meta) + len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v5 total entry-count declaration")
    decoded_regular = [V4._apply_override(default, value) for value in regular_meta]

    paths: list[str] = []
    decoded_explicit: list[tuple[list, list, str]] = []
    previous = ""
    seen: set[str] = set()
    for row in explicit_rows:
        if not isinstance(row, list) or len(row) != 5:
            raise RuntimeError("malformed implicit-v5 filesystem entry")
        prefix, suffix, code, encoded_meta, extra = row
        if (
            not isinstance(prefix, int)
            or isinstance(prefix, bool)
            or prefix < 0
            or prefix > len(previous)
            or not isinstance(suffix, str)
        ):
            raise RuntimeError("implicit-v5 path-delta declaration")
        if code not in V4._CODE_TO_KIND:
            raise RuntimeError("implicit-v5 entry kind declaration")
        rel = previous[:prefix] + suffix
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe implicit-v5 filesystem path") from exc
        if rel in seen or (paths and rel <= paths[-1]):
            raise RuntimeError("implicit-v5 explicit paths are not strictly sorted/unique")
        kind = V4._CODE_TO_KIND[code]
        meta = V4._apply_override(default, encoded_meta)
        if kind == "d":
            if extra is not None:
                raise RuntimeError("implicit-v5 directory carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("implicit-v5 symlink target declaration")
        else:
            if not isinstance(extra, int) or isinstance(extra, bool) or not 0 <= extra < len(regular_meta):
                raise RuntimeError("implicit-v5 hardlink target must reference a regular graph entry")
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
    _default, regular_meta, _explicit, explicit_paths = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    identities: dict[str, tuple[int, bytes]] = {}
    for path in sorted(p for p in profile.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(profile).as_posix()
        if rel == internal_path:
            continue
        if rel in explicit_paths:
            raise RuntimeError("implicit-v5 explicit path collides with authenticated regular graph path")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(block)
                digest.update(block)
        identities[rel] = (size, digest.digest())
    if len(identities) != len(regular_meta):
        raise RuntimeError(
            f"implicit-v5 manifest/content-graph regular-count mismatch: manifest={len(regular_meta)} graph={len(identities)}"
        )
    return identities


def decode_to_v1(
    raw: bytes,
    *,
    regular_identities: dict[str, tuple[int, bytes]],
    max_path_bytes: int,
    max_entries: int,
) -> dict:
    _default, regular_meta, decoded_explicit, explicit_paths = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    regular_paths = sorted(regular_identities)
    if len(regular_paths) != len(regular_meta):
        raise RuntimeError("implicit-v5 regular identity count does not match metadata vector")
    for rel in regular_paths:
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe authenticated implicit-v5 graph path") from exc
    if set(regular_paths) & set(explicit_paths):
        raise RuntimeError("implicit-v5 regular and explicit filesystem path sets overlap")

    entries: list[list] = []
    regular: dict[str, tuple[int, bytes]] = {}
    for rel, meta in zip(regular_paths, regular_meta, strict=True):
        mode, mtime_ns, uid, gid, xattrs = meta
        size, digest = regular_identities[rel]
        if not isinstance(size, int) or size < 0 or not isinstance(digest, bytes) or len(digest) != 32:
            raise RuntimeError("invalid authenticated implicit-v5 regular graph identity")
        regular[rel] = (int(size), bytes(digest))
        entries.append([rel, "f", mode, mtime_ns, uid, gid, xattrs, [int(size), bytes(digest)]])

    hardlinks: dict[str, str] = {}
    for row, meta, rel in decoded_explicit:
        _prefix, _suffix, code, _encoded_meta, extra = row
        mode, mtime_ns, uid, gid, xattrs = meta
        kind = V4._CODE_TO_KIND[code]
        if kind == "d":
            semantic_extra = None
        elif kind == "l":
            semantic_extra = extra
        else:
            semantic_extra = regular_paths[int(extra)]
            hardlinks[rel] = semantic_extra
        entries.append([rel, kind, mode, mtime_ns, uid, gid, xattrs, semantic_extra])

    entries.sort(key=lambda item: item[0])
    if len({row[0] for row in entries}) != len(entries):
        raise RuntimeError("implicit-v5 expanded filesystem paths are not unique")
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": entries,
    }
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def semantics_equal(v1_raw: bytes, implicit_raw: bytes, *, max_path_bytes: int, max_entries: int) -> bool:
    original = FS.decode_manifest(v1_raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    expanded = decode_to_v1(
        implicit_raw,
        regular_identities={path: value for path, value in original["regular"].items()},
        max_path_bytes=max_path_bytes,
        max_entries=max_entries,
    )
    return expanded["manifest"] == original["manifest"]
