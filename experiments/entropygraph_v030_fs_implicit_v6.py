from __future__ import annotations

"""C25EG07 filesystem control: hybrid scalar/RLE metadata framing.

EG06 proved the filesystem-control direction but recovered only 8 bytes, leaving office 42 bytes short of a
strict accepted-v0.29 win at the all-best physical-pack bound.  This codec keeps exactly the same canonical
filesystem semantics while removing MessagePack wrapper overhead:

* default regular metadata is encoded as scalar 0 (one entry) or negative run length (repeated entries);
* non-default singleton overrides are stored directly; repeated overrides prepend a negative run length;
* default explicit metadata is scalar 0;
* directories omit the redundant trailing ``None`` payload field.

No filesystem fact is removed.  Decoding expands to the exact canonical filesystem-manifest-v1 grammar.
"""

import hashlib
from pathlib import Path

import msgpack

from experiments import entropygraph_v030_fs_implicit_v4 as V4
from experiments import entropygraph_v030_product_fs as FS

IMPLICIT_V6_VERSION = 6
MAX_IMPLICIT_BYTES = FS.MAX_MANIFEST_BYTES


def _compact_override(encoded: list) -> int | list:
    return 0 if encoded == [0] else encoded


def _expand_override(value) -> list:
    if value == 0:
        return [0]
    if not isinstance(value, list) or not value:
        raise RuntimeError("implicit-v6 metadata override declaration")
    return value


def _encode_runs(values: list[list]) -> list:
    runs: list = []
    index = 0
    while index < len(values):
        value = values[index]
        count = 1
        while index + count < len(values) and values[index + count] == value:
            count += 1
        if value == [0]:
            runs.append(0 if count == 1 else -count)
        elif count == 1:
            runs.append(value)
        else:
            runs.append([-count, *value])
        index += count
    return runs


def _decode_runs(runs: list, *, max_entries: int) -> list[list]:
    if not isinstance(runs, list) or len(runs) > max_entries:
        raise RuntimeError("implicit-v6 regular metadata run declaration")
    out: list[list] = []
    for token in runs:
        if isinstance(token, int) and not isinstance(token, bool):
            if token == 0:
                count, encoded = 1, [0]
            elif token < 0:
                count, encoded = -token, [0]
            else:
                raise RuntimeError("implicit-v6 positive scalar metadata token")
        elif isinstance(token, list) and token:
            if isinstance(token[0], int) and not isinstance(token[0], bool) and token[0] < 0:
                count, encoded = -token[0], token[1:]
                if not encoded:
                    raise RuntimeError("implicit-v6 repeated metadata override is empty")
            else:
                count, encoded = 1, token
        else:
            raise RuntimeError("implicit-v6 malformed metadata run token")
        if not 1 <= count <= max_entries or len(out) + count > max_entries:
            raise RuntimeError("implicit-v6 expanded metadata count exceeds policy")
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
    regular_runs = _encode_runs(regular_meta)

    explicit_rows: list[list] = []
    previous = ""
    for row in entries:
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        if kind == "f":
            continue
        prefix = V4._common_prefix(previous, rel)
        suffix = rel[prefix:]
        code = V4._KIND_TO_CODE[kind]
        meta = _compact_override(V4._override([mode, mtime_ns, uid, gid, xattrs], default))
        if kind == "d":
            encoded_row = [prefix, suffix, code, meta]
        elif kind == "l":
            encoded_row = [prefix, suffix, code, meta, extra]
        else:
            if extra not in regular_index:
                raise RuntimeError("implicit-v6 hardlink target is not an authenticated regular owner")
            encoded_row = [prefix, suffix, code, meta, regular_index[extra]]
        explicit_rows.append(encoded_row)
        previous = rel

    raw = msgpack.packb([IMPLICIT_V6_VERSION, default, regular_runs, explicit_rows], use_bin_type=True)
    if len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v6 filesystem manifest exceeds bounded decode unit")
    return raw


def _unpack(raw: bytes, *, max_path_bytes: int, max_entries: int):
    if not isinstance(raw, bytes) or len(raw) > MAX_IMPLICIT_BYTES:
        raise RuntimeError("implicit-v6 filesystem manifest exceeds policy")
    try:
        payload = msgpack.unpackb(
            raw, raw=False, strict_map_key=False,
            max_array_len=max_entries * 8 + 1024, max_map_len=16,
            max_str_len=max_path_bytes, max_bin_len=MAX_IMPLICIT_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded implicit-v6 filesystem manifest") from exc
    if not isinstance(payload, list) or len(payload) != 4 or payload[0] != IMPLICIT_V6_VERSION:
        raise RuntimeError("unsupported implicit-v6 filesystem manifest version")
    default, regular_runs, explicit_rows = payload[1], payload[2], payload[3]
    V4._validate_metadata(default)
    regular_encoded = _decode_runs(regular_runs, max_entries=max_entries)
    if not isinstance(explicit_rows, list) or len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v6 explicit entry-count declaration")
    if len(regular_encoded) + len(explicit_rows) > max_entries:
        raise RuntimeError("implicit-v6 total entry-count declaration")
    regular_meta = [V4._apply_override(default, value) for value in regular_encoded]

    paths: list[str] = []
    decoded_explicit: list[tuple[list, list, str, object]] = []
    previous = ""
    seen: set[str] = set()
    for row in explicit_rows:
        if not isinstance(row, list) or len(row) not in (4, 5):
            raise RuntimeError("malformed implicit-v6 filesystem entry")
        prefix, suffix, code, encoded_meta = row[:4]
        if not isinstance(prefix, int) or isinstance(prefix, bool) or prefix < 0 or prefix > len(previous) or not isinstance(suffix, str):
            raise RuntimeError("implicit-v6 path-delta declaration")
        if code not in V4._CODE_TO_KIND:
            raise RuntimeError("implicit-v6 entry kind declaration")
        rel = previous[:prefix] + suffix
        try:
            FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        except FS.ProfileNotEligible as exc:
            raise RuntimeError("unsafe implicit-v6 filesystem path") from exc
        if rel in seen or (paths and rel <= paths[-1]):
            raise RuntimeError("implicit-v6 explicit paths are not strictly sorted/unique")
        kind = V4._CODE_TO_KIND[code]
        meta = V4._apply_override(default, _expand_override(encoded_meta))
        if kind == "d":
            if len(row) != 4:
                raise RuntimeError("implicit-v6 directory carries unexpected payload")
            extra = None
        else:
            if len(row) != 5:
                raise RuntimeError("implicit-v6 non-directory lacks payload")
            extra = row[4]
            if kind == "l":
                if not isinstance(extra, str) or "\x00" in extra:
                    raise RuntimeError("implicit-v6 symlink target declaration")
            elif not isinstance(extra, int) or isinstance(extra, bool) or not 0 <= extra < len(regular_meta):
                raise RuntimeError("implicit-v6 hardlink target must reference a regular graph entry")
        paths.append(rel)
        seen.add(rel)
        decoded_explicit.append((row, meta, rel, extra))
        previous = rel
    return default, regular_meta, decoded_explicit, paths


def identities_from_profile(profile: Path, raw: bytes, *, max_path_bytes: int, max_entries: int, internal_path: str) -> dict[str, tuple[int, bytes]]:
    _default, regular_meta, _explicit, explicit_paths = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    identities: dict[str, tuple[int, bytes]] = {}
    for path in sorted(p for p in profile.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(profile).as_posix()
        if rel == internal_path:
            continue
        if rel in explicit_paths:
            raise RuntimeError("implicit-v6 explicit path collides with authenticated regular graph path")
        data = path.read_bytes()
        identities[rel] = (len(data), hashlib.sha256(data).digest())
    if len(identities) != len(regular_meta):
        raise RuntimeError("implicit-v6 manifest/content-graph regular-count mismatch")
    return identities


def decode_to_v1(raw: bytes, *, regular_identities: dict[str, tuple[int, bytes]], max_path_bytes: int, max_entries: int) -> dict:
    _default, regular_meta, decoded_explicit, explicit_paths = _unpack(raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    regular_paths = sorted(regular_identities)
    if len(regular_paths) != len(regular_meta):
        raise RuntimeError("implicit-v6 regular identity count does not match metadata vector")
    if set(regular_paths) & set(explicit_paths):
        raise RuntimeError("implicit-v6 regular and explicit filesystem path sets overlap")
    entries: list[list] = []
    regular: dict[str, tuple[int, bytes]] = {}
    for rel, meta in zip(regular_paths, regular_meta, strict=True):
        FS.safe_relpath(rel, max_path_bytes=max_path_bytes)
        mode, mtime_ns, uid, gid, xattrs = meta
        size, digest = regular_identities[rel]
        if not isinstance(size, int) or size < 0 or not isinstance(digest, bytes) or len(digest) != 32:
            raise RuntimeError("invalid authenticated implicit-v6 regular graph identity")
        regular[rel] = (int(size), bytes(digest))
        entries.append([rel, "f", mode, mtime_ns, uid, gid, xattrs, [int(size), bytes(digest)]])
    hardlinks: dict[str, str] = {}
    for row, meta, rel, extra in decoded_explicit:
        code = row[2]
        mode, mtime_ns, uid, gid, xattrs = meta
        kind = V4._CODE_TO_KIND[code]
        if kind == "d": semantic_extra = None
        elif kind == "l": semantic_extra = extra
        else:
            semantic_extra = regular_paths[int(extra)]
            hardlinks[rel] = semantic_extra
        entries.append([rel, kind, mode, mtime_ns, uid, gid, xattrs, semantic_extra])
    entries.sort(key=lambda item: item[0])
    manifest = {"v": FS.FILESYSTEM_MANIFEST_VERSION, "profile": "cmpct-r25-filesystem-manifest-v1", "internal_path": FS.FILESYSTEM_MANIFEST, "entries": entries}
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def semantics_equal(v1_raw: bytes, implicit_raw: bytes, *, max_path_bytes: int, max_entries: int) -> bool:
    original = FS.decode_manifest(v1_raw, max_path_bytes=max_path_bytes, max_entries=max_entries)
    expanded = decode_to_v1(implicit_raw, regular_identities=dict(original["regular"]), max_path_bytes=max_path_bytes, max_entries=max_entries)
    return expanded["manifest"] == original["manifest"]
