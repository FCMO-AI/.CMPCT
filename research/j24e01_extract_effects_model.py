"""Research-only metadata effect oracle for CMPCT revision-24 logical extraction.

NOT an archive parser, a hardened product preflight, or a substitute for authenticating
indexes and BHDRs. On any unprovable structure it rejects instead of guessing.
"""
from __future__ import annotations

K_FILE, K_DIR, K_SYMLINK, K_HARDLINK = range(4)
S_BLOB, S_CHUNKS, S_VZIP, S_SPARSE, S_PACK, S_CDC = range(6)


class UnprovedEffect(ValueError):
    """No conservative exact output budget can be certified from these rows."""


def _nat(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise UnprovedEffect(f"{label}: expected nonnegative integer")
    return value


def planned_logical_bytes(index: dict) -> int:
    """Prove and charge every logical member size with linear-time alias resolution.

    Input is a decoded *untrusted* index view. Its actual cryptographic/physical
    authentication, canonical paths, bounded parsing, and namespace isolation
    are separate mandatory production gates. The result is not that proof.
    """
    files, blobs, recipes = index["files"], index["blobs"], index["recipes"]
    if not all(isinstance(x, list) for x in (files, blobs, recipes)):
        raise UnprovedEffect("index arrays required")

    sizes = []
    for n, blob in enumerate(blobs):
        if not isinstance(blob, list) or len(blob) != 5:
            raise UnprovedEffect(f"blob {n}: shape")
        sizes.append(_nat(blob[1], f"blob {n} size"))

    def bsize(ref: object) -> int:
        if type(ref) is not int or ref < 0 or ref >= len(sizes):
            raise UnprovedEffect("invalid physical owner")
        return sizes[ref]

    by_name = {}
    for row in files:
        if not isinstance(row, list) or len(row) != 7:
            raise UnprovedEffect("file row shape")
        name, kind, _, _, size, _, storage = row
        if not isinstance(name, str) or not name or name in by_name:
            raise UnprovedEffect("missing or duplicate logical path")
        if type(kind) is not int or kind not in (K_FILE, K_DIR, K_SYMLINK, K_HARDLINK):
            raise UnprovedEffect(f"{name}: entry kind")
        _nat(size, f"{name} declared size")
        by_name[name] = row

    resolved = {}
    roots = {}
    for name, row in by_name.items():
        kind, size, storage = row[1], row[4], row[6]
        if kind == K_HARDLINK:
            if not isinstance(storage, list) or len(storage) != 1 or not isinstance(storage[0], str):
                raise UnprovedEffect(f"{name}: hardlink target shape")
            continue
        if kind == K_DIR:
            if size or storage is not None:
                raise UnprovedEffect(f"{name}: directory effect")
            resolved[name] = 0
            roots[name] = None
            continue
        if not isinstance(storage, list) or not storage:
            raise UnprovedEffect(f"{name}: storage")
        tag = storage[0]
        if kind == K_SYMLINK:
            if len(storage) != 2 or tag != S_BLOB or size != bsize(storage[1]):
                raise UnprovedEffect(f"{name}: symlink size/owner disagreement")
        elif tag == S_BLOB:
            if len(storage) != 2 or size != bsize(storage[1]):
                raise UnprovedEffect(f"{name}: direct size/owner disagreement")
        elif tag == S_PACK:
            if len(storage) != 4:
                raise UnprovedEffect(f"{name}: pack shape")
            off, length = _nat(storage[2], "pack offset"), _nat(storage[3], "pack length")
            if length != size or off + length > bsize(storage[1]):
                raise UnprovedEffect(f"{name}: pack geometry")
        elif tag == S_CHUNKS:
            if len(storage) != 2 or not isinstance(storage[1], list):
                raise UnprovedEffect(f"{name}: chunks shape")
            if sum(bsize(x) for x in storage[1]) != size:
                raise UnprovedEffect(f"{name}: chunk geometry")
        elif tag == S_CDC:
            if len(storage) != 2 or not isinstance(storage[1], list):
                raise UnprovedEffect(f"{name}: cdc shape")
            total = 0
            for entry in storage[1]:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise UnprovedEffect(f"{name}: cdc entry")
                length = _nat(entry[0], "cdc length")
                if length == 0 or length != bsize(entry[1]):
                    raise UnprovedEffect(f"{name}: cdc geometry")
                total += length
            if total != size:
                raise UnprovedEffect(f"{name}: cdc file length")
        elif tag == S_SPARSE:
            if len(storage) != 2 or not isinstance(storage[1], list):
                raise UnprovedEffect(f"{name}: sparse shape")
            end = 0
            for extent in storage[1]:
                if not isinstance(extent, list) or len(extent) != 3 or not isinstance(extent[2], list):
                    raise UnprovedEffect(f"{name}: sparse extent shape")
                off, length = _nat(extent[0], "extent offset"), _nat(extent[1], "extent length")
                if not length or off < end or off + length > size:
                    raise UnprovedEffect(f"{name}: sparse extent bounds")
                if sum(bsize(x) for x in extent[2]) != length:
                    raise UnprovedEffect(f"{name}: sparse physical write exceeds extent")
                end = off + length
        elif tag == S_VZIP:
            if len(storage) != 2 or type(storage[1]) is not int:
                raise UnprovedEffect(f"{name}: vzip recipe")
            rid = storage[1]
            if rid < 0 or rid >= len(recipes) or not isinstance(recipes[rid], list):
                raise UnprovedEffect(f"{name}: vzip reference")
            if len(recipes[rid]) < 5 or _nat(recipes[rid][4], "vzip length") != size:
                raise UnprovedEffect(f"{name}: vzip size")
        else:
            raise UnprovedEffect(f"{name}: unknown storage mode")
        resolved[name] = size
        roots[name] = name if kind == K_FILE else None

    # Iterative memoized graph walk: forward hardlinks and 50k-deep chains use
    # O(members + links) operations and no Python recursive stack.
    for name in by_name:
        if name in resolved:
            continue
        cursor = name
        chain, visiting = [], set()
        while cursor not in resolved:
            if cursor in visiting:
                raise UnprovedEffect(f"{name}: hardlink cycle")
            visiting.add(cursor)
            row = by_name.get(cursor)
            if row is None or row[1] != K_HARDLINK:
                raise UnprovedEffect(f"{name}: missing/nonfile hardlink owner")
            chain.append(cursor)
            cursor = row[6][0]
        # The memoized cursor can itself be an alias. Proof requires its
        # ultimate regular-file root, never merely the cursor's row kind.
        owner = roots[cursor]
        if owner is None:
            raise UnprovedEffect(f"{name}: hardlink to nonregular")
        physical = resolved[cursor]
        for alias in reversed(chain):
            if by_name[alias][4] != physical:
                raise UnprovedEffect(f"{alias}: alias size != owner")
            resolved[alias] = physical
            roots[alias] = owner

    return sum(resolved.values())
