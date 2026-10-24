#!/usr/bin/env python3
"""Research-only POSIX byte-tree wire/reconstruction oracle, NOT CMPCT r24/r25.

The outer SHA authenticates the detached packet, not a CMPCT archive. Two candidate
name grammars from PR #254 are compared on identical tree bytes. No release credit.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import time
import tracemalloc
import unicodedata
import zlib

import msgpack

from v031_posix_byte_namespace_oracle import (bytes_unwire, bytes_wire,
                                               text_unwire, text_wire)

MAX_ROWS = 128
MAX_RAW = 2 * 1024 * 1024
MAX_COMPRESSED = MAX_RAW
MAX_BLOBS = 128
MAX_PATH = 4095
MAX_BLOB_SIZE = 1024 * 1024
MAX_XATTRS = 32
MAX_XATTR_VALUE = 4096


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def xattrs(path: bytes) -> list[tuple[bytes, bytes]]:
    try:
        names = os.listxattr(path, follow_symlinks=False)
    except (AttributeError, NotImplementedError, OSError):
        return []
    return sorted((os.fsencode(name), os.getxattr(path, name, follow_symlinks=False))
                  for name in names)


def inventory(root: bytes) -> dict:
    """Independent POSIX physical oracle; never uses wire encoder/decoder."""
    seen: dict[tuple[int, int], list[bytes]] = {}
    rows = []

    def visit(relative: bytes) -> None:
        for child in sorted(os.listdir(root + (b"/" + relative if relative else b""))):
            rel = relative + b"/" + child if relative else child
            path = root + b"/" + rel
            st = os.lstat(path)
            mode = stat.S_IMODE(st.st_mode)
            xa = xattrs(path)
            if stat.S_ISDIR(st.st_mode):
                rows.append((rel, "d", mode, None, xa))
                visit(rel)
            elif stat.S_ISLNK(st.st_mode):
                rows.append((rel, "s", mode, os.readlink(path), xa))
            elif stat.S_ISREG(st.st_mode):
                with open(path, "rb") as stream:
                    content = stream.read()
                rows.append((rel, "f", mode, content, xa))
                seen.setdefault((st.st_dev, st.st_ino), []).append(rel)
            else:
                raise ValueError("unsupported source inode type")

    visit(b"")
    groups = sorted(tuple(sorted(paths)) for paths in seen.values() if len(paths) > 1)
    return {"rows": rows, "hardlink_groups": groups}


def source_rows(source: dict):
    """Convert physical oracle into a manifest with stable owner-first hardlinks."""
    allrows = source["rows"]
    groups = source["hardlink_groups"]
    aliases = {alias: group[0] for group in groups for alias in group[1:]}
    content = {}
    output = []
    for rel, kind, mode, payload, xa in allrows:
        if kind == "f" and rel in aliases:
            output.append((rel, "h", mode, aliases[rel], xa))
        elif kind == "f":
            content[digest(payload)] = payload
            output.append((rel, kind, mode, digest(payload), xa))
        else:
            output.append((rel, kind, mode, payload, xa))
    return output, content


def wire_name(name: bytes, grammar: str, kind: str = "segment"):
    return bytes_wire(name, kind) if grammar == "typed" else text_wire(name, kind)


def unwire_name(wire, grammar: str, kind: str = "segment") -> bytes:
    return bytes_unwire(wire, kind) if grammar == "typed" else text_unwire(wire, kind)


def wire_path(rel: bytes, grammar: str):
    return [wire_name(piece, grammar) for piece in rel.split(b"/")]


def decode_path(parts, grammar: str) -> bytes:
    if not isinstance(parts, list) or not parts or len(parts) > MAX_PATH:
        raise ValueError("invalid path components")
    raw = b"/".join(unwire_name(piece, grammar) for piece in parts)
    if len(raw) > MAX_PATH:
        raise ValueError("raw path exceeds budget")
    return raw


def rows_to_wire(source: dict, grammar: str):
    plain, content = source_rows(source)
    rows = []
    for rel, kind, mode, value, xa in plain:
        wire_value = wire_path(value, grammar) if kind == "h" else value
        rows.append([kind, wire_path(rel, grammar), mode, wire_value,
                     [[wire_name(key, grammar, "xattr"), data] for key, data in xa]])
    wire_blobs = [[key, content[key]] for key in sorted(content)]
    return [1, rows, wire_blobs]


def seal(packet) -> tuple[bytes, bytes, int]:
    serialized = msgpack.packb(packet, use_bin_type=True)
    if len(serialized) > MAX_RAW:
        raise ValueError("manifest exceeds raw budget")
    compressed = zlib.compress(serialized, 9)
    if len(compressed) > MAX_COMPRESSED:
        raise ValueError("compressed size limit")
    return compressed, digest(serialized), len(serialized)


def _no_duplicate_dict(pairs):
    result = {}
    for key, value in pairs:
        if type(key) not in (str, bytes, int):
            raise ValueError("unsupported MessagePack map key type")
        if key in result:
            raise ValueError("duplicate MessagePack map key")
        result[key] = value
    return result


def unseal(compressed: bytes, commitment: bytes):
    if type(compressed) is not bytes or type(commitment) is not bytes or len(commitment) != 32:
        raise ValueError("invalid wire or commitment")
    if len(compressed) > MAX_COMPRESSED:
        raise ValueError("compressed budget exceeded")
    dec = zlib.decompressobj()
    raw = dec.decompress(compressed, MAX_RAW + 1)
    if len(raw) > MAX_RAW or not dec.eof or dec.unconsumed_tail or dec.unused_data:
        raise ValueError("invalid or over-budget compressed stream")
    if digest(raw) != commitment:
        raise ValueError("manifest authentication failure")
    try:
        return msgpack.unpackb(raw, raw=False, strict_map_key=True,
                               max_array_len=MAX_ROWS * 8, max_bin_len=MAX_RAW,
                               max_str_len=MAX_RAW, max_map_len=MAX_ROWS * 8,
                               object_pairs_hook=_no_duplicate_dict)
    except (msgpack.ExtraData, msgpack.FormatError, msgpack.StackError, ValueError, TypeError) as exc:
        raise ValueError("invalid MessagePack manifest") from exc


def validate_symlink(rel: bytes, target: bytes) -> None:
    if type(target) is not bytes or not target or b"\0" in target or target.startswith(b"/"):
        raise ValueError("invalid symbolic link target")
    stack = rel.split(b"/")[:-1]
    for part in target.split(b"/"):
        if part in (b"", b"."):
            continue
        if part == b"..":
            if not stack:
                raise ValueError("symlink escapes root")
            stack.pop()
        else:
            stack.append(part)


def validate_target_name(rel: bytes, aliases: set[str]) -> None:
    """Illustrative casefold/Unicode target admission, not a Windows API emulator."""
    keys = []
    for raw in rel.split(b"/"):
        text = raw.decode("utf-8", "strict")
        if text.endswith(".") or text.endswith(" ") or any(c in text for c in '\\:*?"<>|'):
            raise ValueError("nonportable target component")
        if text.upper().split(".")[0] in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT1"):
            raise ValueError("reserved component")
        keys.append(unicodedata.normalize("NFC", text).casefold())
    folded = "/".join(keys)
    if folded in aliases:
        raise ValueError("casefold target collision")
    aliases.add(folded)


def preflight(packet, grammar: str, target: str = "posix"):
    """Authenticated packet already unsealed; validate every row before any FS write."""
    if grammar not in ("typed", "escaped") or target not in ("posix", "casefold"):
        raise ValueError("unknown grammar/target")
    if type(packet) is not list or len(packet) != 3 or type(packet[0]) is not int or packet[0] != 1:
        raise ValueError("unknown manifest version")
    _, rows, blobs = packet
    if type(rows) is not list or len(rows) > MAX_ROWS or type(blobs) is not list or len(blobs) > MAX_BLOBS:
        raise ValueError("invalid record count")
    stored = {}
    for item in blobs:
        if type(item) is not list or len(item) != 2 or type(item[0]) is not bytes or len(item[0]) != 32 or type(item[1]) is not bytes:
            raise ValueError("invalid blob record")
        key, data = item
        if len(data) > MAX_BLOB_SIZE or digest(data) != key or key in stored:
            raise ValueError("blob integrity or duplicate")
        stored[key] = data
    normalized = []
    seen = set()
    dirs = set()
    owners = set()
    aliases = set()
    for row in rows:
        if type(row) is not list or len(row) != 5:
            raise ValueError("malformed entry")
        kind, rawparts, mode, value, xattrrows = row
        if type(kind) is not str or kind not in ("f", "d", "h", "s") or type(mode) is not int or not 0 <= mode <= 0o7777:
            raise ValueError("invalid kind/mode")
        rel = decode_path(rawparts, grammar)
        if rel in seen:
            raise ValueError("duplicate physical byte path")
        parent = rel.rsplit(b"/", 1)[0] if b"/" in rel else b""
        if parent and parent not in dirs:
            raise ValueError("missing parent directory")
        if target == "casefold":
            validate_target_name(rel, aliases)
        seen.add(rel)
        if type(xattrrows) is not list or len(xattrrows) > MAX_XATTRS:
            raise ValueError("invalid xattr array")
        xa = []
        xseen = set()
        for pair in xattrrows:
            if type(pair) is not list or len(pair) != 2 or type(pair[1]) is not bytes or len(pair[1]) > MAX_XATTR_VALUE:
                raise ValueError("invalid xattr pair")
            key = unwire_name(pair[0], grammar, "xattr")
            if key in xseen:
                raise ValueError("duplicate xattr bytes")
            xseen.add(key)
            xa.append((key, pair[1]))
        if kind == "d":
            if value is not None:
                raise ValueError("directory payload")
            dirs.add(rel)
        elif kind == "f":
            if type(value) is not bytes or value not in stored:
                raise ValueError("unresolved content digest")
            owners.add(rel)
        elif kind == "h":
            source = decode_path(value, grammar)
            if source not in owners or rel == source:
                raise ValueError("unresolved/non-earlier hardlink owner")
            value = source
        elif kind == "s":
            validate_symlink(rel, value)
        normalized.append((rel, kind, mode, value, xa))
    if set(stored) != {row[3] for row in normalized if row[1] == "f"}:
        raise ValueError("unreferenced payload")
    return normalized, stored


def materialize(packet, grammar: str, dest: bytes, target: str = "posix"):
    rows, blobs = preflight(packet, grammar, target)
    if os.listdir(dest):
        raise ValueError("destination must be empty")
    for rel, kind, mode, payload, xa in rows:
        path = dest + b"/" + rel
        if kind == "d":
            os.mkdir(path, 0o700)
        elif kind == "f":
            with open(path, "xb") as handle:
                handle.write(blobs[payload])
        elif kind == "h":
            os.link(dest + b"/" + payload, path)
        else:
            os.symlink(payload, path)
        if kind != "s":
            os.chmod(path, mode, follow_symlinks=False)
        for key, val in xa:
            os.setxattr(path, key, val, follow_symlinks=False)
    return len(rows)


def source_fixture(dest: bytes, mode: str = "mixed"):
    if mode not in ("mixed", "utf8", "portable"):
        raise ValueError("bad test fixture")
    os.mkdir(dest + b"/nested", 0o750)
    names = ([b"file-\xff", b"file-\xfe", b"caf\xc3\xa9", b"cafe\xcc\x81",
              b"caf\xe9", b"~Z1__w", b"~z1__w", b"a\\b", b"A", b"a"]
             if mode == "mixed" else
             ([b"file-a", b"file-b", b"caf\xc3\xa9", b"cafe\xcc\x81",
               b"file-c", b"A", b"a"] if mode == "utf8"
              else [b"file-a", b"file-b", b"cafe", b"file-c", b"other"]))
    names += [b"nested/child-\xff" if mode == "mixed" else b"nested/child-d"]
    for i, rel in enumerate(names):
        body = (b"identity:" + rel + b"\0") * (i + 1)
        with open(dest + b"/" + rel, "xb") as handle:
            handle.write(body)
        os.chmod(dest + b"/" + rel, 0o640)
    owner = names[0]
    os.link(dest + b"/" + owner, dest + b"/nested/hardlink")
    os.symlink(b"../" + owner, dest + b"/nested/symlink")
    xa_support = False
    try:
        keys = ([b"user.invalid-\xff", b"user.slash/name", b"user.path/../fragment"]
                if mode == "mixed" else [b"user.text", b"user.more"])
        for name in keys:
            os.setxattr(dest + b"/" + owner, name, name + b"_value")
        xa_support = True
    except OSError:
        pass
    return xa_support


def samples(source, grammar, repeats=5):
    timings = []
    peaks = []
    wirecost = None
    for _ in range(repeats):
        tracemalloc.start()
        t0 = time.perf_counter_ns()
        packet = rows_to_wire(source, grammar)
        sealed, sha, rawsize = seal(packet)
        valid = unseal(sealed, sha)
        preflight(valid, grammar)
        wall = (time.perf_counter_ns() - t0) / 1e6
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        wirecost = (len(sealed) + 32, rawsize, len(sealed))
        timings.append(round(wall, 6))
        peaks.append(peak)
    return timings, peaks, wirecost


def assert_reject(packet, grammar, name, *, target="posix"):
    """Rehash hostile packet and require STRUCTURAL PREFLIGHT reject, before writes."""
    compressed, sha, _ = seal(packet)
    after = unseal(compressed, sha)
    try:
        preflight(after, grammar, target)
    except (ValueError, UnicodeError):
        pass
    else:
        raise AssertionError("preflight admitted hostile packet: " + name)
    with tempfile.TemporaryDirectory() as directory:
        base = os.fsencode(directory)
        dest = base + b"/dst"
        os.mkdir(dest)
        with open(base + b"/sentinel", "wb") as f:
            f.write(b"PRESERVE")
        try:
            materialize(after, grammar, dest, target)
        except (ValueError, UnicodeError):
            pass
        else:
            raise AssertionError("materializer admitted hostile packet: " + name)
        assert not os.listdir(dest), (name, "destination changed")
        assert open(base + b"/sentinel", "rb").read() == b"PRESERVE"
    return name


def hostile_court(packet, grammar, input_mode):
    """Mutate the authenticated manifest, not merely flip an outer digest byte."""
    import copy
    rows = packet[1]
    baseidx = next(i for i, row in enumerate(rows) if row[0] == "f")
    make = lambda: copy.deepcopy(packet)
    outcomes = []
    p = make(); p[1].append(copy.deepcopy(p[1][baseidx]))
    outcomes.append(assert_reject(p, grammar, "duplicate-entry"))
    p = make(); p[1][baseidx][1] = [".."]
    outcomes.append(assert_reject(p, grammar, "dotdot-component"))
    p = make(); p[1][baseidx][1] = ["root/sub"]
    outcomes.append(assert_reject(p, grammar, "embedded-separator"))
    p = make(); p[1][baseidx][1] = ["nul\0name"]
    outcomes.append(assert_reject(p, grammar, "NUL-component"))
    p = make(); p[1][baseidx][2] = True
    outcomes.append(assert_reject(p, grammar, "bool-mode"))
    p = make(); p[1][baseidx][0] = "weird"
    outcomes.append(assert_reject(p, grammar, "unknown-kind"))
    p = make(); p[2][0][1] = b"bad-blob"
    outcomes.append(assert_reject(p, grammar, "blob-authentication"))
    p = make(); p[1][baseidx][3] = b"?"*32
    outcomes.append(assert_reject(p, grammar, "missing-blob"))
    p = make()
    p[1][baseidx][4].append([wire_name(b"user.repeated", grammar, "xattr"), b"same"])
    p[1][baseidx][4].append([wire_name(b"user.repeated", grammar, "xattr"), b"changed"])
    outcomes.append(assert_reject(p, grammar, "duplicate-xattr"))
    p = make(); h = next(i for i,x in enumerate(p[1]) if x[0]=="h")
    p[1][h][3] = wire_path(b"external", grammar)
    outcomes.append(assert_reject(p, grammar, "missing-hardlink-owner"))
    p = make(); s = next(i for i,x in enumerate(p[1]) if x[0]=="s")
    p[1][s][3] = b"../../escape"
    outcomes.append(assert_reject(p, grammar, "symlink-escape"))
    p = make(); p[1][baseidx][1] = ["~Z1_YQ=="] if grammar == "escaped" else [[True, b"\xff"]]
    outcomes.append(assert_reject(p, grammar, "noncanonical-variant"))
    if input_mode in ("mixed", "utf8"):
        outcomes.append(assert_reject(make(), grammar, "nonportable-casefold", target="casefold"))
    return outcomes


def run():
    if os.name != "posix":
        return {"status":"SKIPPED", "reason":"requires POSIX byte names"}
    verdict = {"status":"PASS", "scope":"detached O1 bytes/metadata reconstruction; not CMPCT product",
               "formats":{}, "negative":{},
               "unmeasured":["native reader","revision 24/25 product","Windows real target",
                             "in-place races", "journal/recovery","selective I/O",
                             "full metadata ACL/uid/gid/time"]}
    for mode in ("mixed", "utf8", "portable"):
        with tempfile.TemporaryDirectory() as directory:
            root = os.fsencode(directory) + b"/source"
            os.mkdir(root)
            xa_support = source_fixture(root, mode)
            original = inventory(root)
            table = {}
            saved = {}
            for grammar in ("typed", "escaped"):
                pkt = rows_to_wire(original, grammar)
                packed, commitment, raw = seal(pkt)
                with tempfile.TemporaryDirectory() as target:
                    dst = os.fsencode(target) + b"/fresh"
                    os.mkdir(dst)
                    restored = unseal(packed, commitment)
                    materialize(restored, grammar, dst, "casefold" if mode == "portable" else "posix")
                    actual = inventory(dst)
                    assert actual == original, (mode, grammar, "physical mismatch", actual, original)
                timings, peaks, cost = samples(original, grammar)
                table[grammar] = {"stored_bytes_detached":cost[0], "raw_manifest_bytes":cost[1],
                                  "zlib9_bytes":cost[2], "millis_raw":timings,
                                  "peak_tracemalloc_bytes":peaks,
                                  "manifest_sha256":commitment.hex(),
                                  "physical_reconstruction":"PASS"}
                saved[grammar] = pkt
            verdict["formats"][mode] = {"source_entries":len(original["rows"]),
                                       "hardlink_groups":len(original["hardlink_groups"]),
                                       "xattrs_available":xa_support,"candidates":table}
            if mode != "portable":
                for grammar,pkt in saved.items():
                    verdict["negative"][grammar] = hostile_court(pkt, grammar, mode)
    return verdict


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
