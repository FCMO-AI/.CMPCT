"""Independent J24G47 signed-index referee. Never imports CMPCT or its codecs.

Derive expected fsmeta by logical *name* from the signed parent before replaying
one journal delta. Contrast that result with first-party Reader observation and
the signed compacted full index. This deliberately does not call the product's
ordinal-rekey helper and does not rewrite the J24G46 negative research oracle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

import msgpack
import zstandard

HDR = struct.Struct("<8sHHQQQ32s")
FTR = struct.Struct("<8sBBBBQQQ32s")
MAGIC = b"CMPCT24\x00"
FMAGIC = b"CMPTF24\x00"


def sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def decode(encoded: bytes, codec: int, length: int) -> bytes:
    if length < 0 or length > 8 * 1024 * 1024:
        raise ValueError("independent decoder input bound")
    if codec == 0:
        plain = encoded
    elif codec == 1:
        plain = zstandard.ZstdDecompressor().decompress(
            encoded, max_output_size=max(length, 1))
    else:
        raise ValueError("unknown signed index codec")
    if len(plain) != length:
        raise ValueError("signed index declared length mismatch")
    return plain


def footer(raw: bytes, pos: int):
    if pos < HDR.size or pos + FTR.size > len(raw):
        raise ValueError("invalid footer position")
    magic, kind, codec, flags, reserved, clen, ulen, prev, h = FTR.unpack_from(raw, pos)
    if magic != FMAGIC or kind not in (0, 1) or clen > pos:
        raise ValueError("invalid committed footer")
    plain = decode(raw[pos - clen:pos], codec, ulen)
    if sha(plain) != h:
        raise ValueError("bad signed footer payload")
    return kind, msgpack.unpackb(plain, raw=False), prev


def attrs_by_name(idx: dict) -> dict:
    names = [r[0] for r in idx["files"]]
    result = {}
    for ordinal, records in idx.get("fsmeta", {}).get("xattrs", []):
        if type(ordinal) is not int or not 0 <= ordinal < len(names):
            raise ValueError("invalid physical metadata ordinal")
        name = names[ordinal]
        if name in result:
            raise ValueError("duplicate metadata ordinal")
        result[name] = {
            key: bytes(value).hex() for key, value in records
        }
    return result


def signed_expected_by_name(primary: dict, delta: dict) -> tuple[list[str], dict]:
    """Independent path-keyed oracle: no sorted-ordinal arithmetic until output."""
    names = {r[0]: r for r in primary["files"]}
    attr = attrs_by_name(primary)
    for op in delta.get("ops", []):
        kind = op[0]
        if kind == "put":
            names[op[1][0]] = op[1]
        elif kind == "del":
            names.pop(op[1], None)
            attr.pop(op[1], None)
        elif kind == "ren":
            old, new = op[1], op[2]
            if old not in names or new in names:
                raise ValueError("invalid rename within experiment")
            row = list(names.pop(old))
            row[0] = new
            names[new] = row
            if old in attr:
                attr[new] = attr.pop(old)
        else:
            raise ValueError("unknown journal op")
    sorted_names = sorted(names)
    return sorted_names, {name: attr[name] for name in sorted_names if name in attr}


def load_signed(path: Path):
    raw = path.read_bytes()
    if len(raw) < HDR.size + FTR.size:
        raise ValueError("truncated archive")
    magic, version, flags, clen, ulen, record_bytes, primary_sha = HDR.unpack_from(raw)
    if magic != MAGIC or version != 24:
        raise ValueError("wrong published wire version")
    primary_plain = decode(raw[HDR.size:HDR.size + clen], 1, ulen)
    if sha(primary_plain) != primary_sha:
        raise ValueError("primary index hash mismatch")
    primary = msgpack.unpackb(primary_plain, raw=False)
    kind, tail, prev = footer(raw, len(raw) - FTR.size)
    if kind == 0:
        if prev or tail != primary:
            raise ValueError("full-footer disagreement")
        expected_names = [r[0] for r in primary["files"]]
        expected_attrs = attrs_by_name(primary)
    else:
        if not prev:
            raise ValueError("journal lacks authenticated parent")
        parent_kind, parent, older = footer(raw, prev)
        if parent_kind != 0 or older or parent != primary:
            raise ValueError("journal parent differs from signed base")
        expected_names, expected_attrs = signed_expected_by_name(primary, tail)
    return expected_names, expected_attrs, (kind == 1)


def main(receipt_path: Path, output_path: Path) -> None:
    r = json.loads(receipt_path.read_text())
    labels = {
        "initial_archive": "base",
        "stable_archive": "stable_update",
        "stable_compact_archive": "stable_compact",
        "shifted_archive": "lexical_insert",
        "shifted_compact_archive": "insert_compact",
    }
    records = {}
    for artifact, snapshot in labels.items():
        entry = r["artifact_manifest"][artifact]
        target = (receipt_path.parent / entry["relative_path"]).resolve()
        if receipt_path.parent.resolve() not in target.parents:
            raise ValueError("artifact path escapes evidence root")
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("artifact SHA mismatch")
        names, attrs, journaled = load_signed(target)
        if names != r[snapshot]["names"]:
            raise ValueError("independent signed filenames differ: " + artifact)
        if attrs != r[snapshot]["xattrs_by_logical_name"]:
            raise ValueError("independent path-bound metadata differs: " + artifact)
        records[artifact] = {"names": names, "xattrs": attrs, "journal": journaled}
    if not records["shifted_archive"]["journal"]:
        raise ValueError("lexical insertion not committed as a journal")
    if records["shifted_compact_archive"]["journal"]:
        raise ValueError("compacted tree still contains journal")
    if r.get("native_os_xattrs_supported"):
        key = "com.fcmo.cmpct.j24g46" if r["platform"] == "darwin" else "user.cmpct_j24g46"
        for artifact in ("initial_archive", "stable_archive", "shifted_archive", "shifted_compact_archive"):
            attrs = records[artifact]["xattrs"]
            if key not in attrs.get("z-owner.bin", {}):
                raise ValueError("original owner lost authenticated xattr: " + artifact)
            if key in attrs.get("a-inserted.bin", {}):
                raise ValueError("new unrelated member stole xattr: " + artifact)
        if r["decision"] != "POSITIONAL_IDENTITY_PRESERVED":
            raise ValueError("native physical outcome not repaired")
    elif r["platform"] != "win32" or r["decision"] != "WINDOWS_CONTENT_ONLY_NO_XATTR_POSITIVE":
        raise ValueError("unsupported platform or false native claim")
    result = {
        "auditor": "J24G47 independent path-name signed-wire oracle",
        "source": str(receipt_path),
        "platform": r["platform"],
        "decision": r["decision"],
        "admitted": True,
        "archives": records,
    }
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"admitted": True, "archives": len(records), "decision": r["decision"]}, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
