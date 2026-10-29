"""J24G46 independent authenticated r24 MessagePack journal metadata referee.

This tool deliberately imports neither CMPCT nor its codecs. The independent
zstandard and msgpack projects decode the genuine published wire format. It
inspects all five materialized archives and checks the *physical* xattr row
associations against the first-party receipt, including signed footer ancestry.
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

def sha(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def inflate(encoded: bytes, codec: int, usize: int) -> bytes:
    if usize > 8 * 1024 * 1024:
        raise ValueError("test's independent index resource limit exceeded")
    if codec == 0:
        out = encoded
    elif codec == 1:
        out = zstandard.ZstdDecompressor().decompress(encoded, max_output_size=max(1, usize))
    else:
        raise ValueError("unknown frame codec")
    if len(out) != usize:
        raise ValueError("wrong declared decoded index length")
    return out

def frame(raw: bytes, pos: int) -> tuple[int, object, int]:
    if pos < HDR.size or pos + FTR.size > len(raw):
        raise ValueError("footer not fully present")
    magic, kind, codec, flags, reserved, cs, us, prev, authenticated_sha = FTR.unpack_from(raw, pos)
    if magic != FMAGIC or cs > pos or kind not in (0, 1):
        raise ValueError("invalid footer")
    decoded = inflate(raw[pos - cs:pos], codec, us)
    if sha(decoded) != authenticated_sha:
        raise ValueError("SHA-256 mismatch in independent footer decode")
    value = msgpack.unpackb(decoded, raw=False, strict_map_key=False)
    return kind, value, prev

def read_committed_index(raw: bytes) -> tuple[dict, dict]:
    if len(raw) < HDR.size + FTR.size:
        raise ValueError("archive truncated")
    magic, version, flags, cs, us, record_len, ph = HDR.unpack_from(raw)
    if magic != MAGIC or version != 24 or cs > len(raw) - HDR.size - FTR.size:
        raise ValueError("invalid primary index header")
    primary_raw = inflate(raw[HDR.size:HDR.size + cs], 1, us)
    if sha(primary_raw) != ph:
        raise ValueError("primary index SHA mismatch")
    index = msgpack.unpackb(primary_raw, raw=False, strict_map_key=False)
    # The current Builder emits a full checkpoint followed by at most one
    # experiment update. Check the independently authenticated committed tail.
    last_footer = len(raw) - FTR.size
    kind, tail, prev = frame(raw, last_footer)
    if kind == 0:
        if prev:
            raise ValueError("compacted full footer unexpectedly has parent")
        if tail != index:
            raise ValueError("dual indexes differ")
        return index, {"kind": kind, "prev": prev}
    if kind != 1 or not prev or prev >= last_footer:
        raise ValueError("expected bounded one-step journal")
    parent_kind, parent, older = frame(raw, prev)
    if parent_kind != 0 or older != 0 or parent != index:
        raise ValueError("journal initial parent is not exact primary")
    for blob in tail.get("blobs", []):
        index["blobs"].append(blob)
    for op in tail.get("ops", []):
        code = op[0]
        if code == "put":
            row = op[1]
            for i, old in enumerate(index["files"]):
                if old[0] == row[0]:
                    index["files"][i] = row
                    break
            else:
                index["files"].append(row)
        elif code == "del":
            index["files"] = [row for row in index["files"] if row[0] != op[1]]
        elif code == "ren":
            match = [row for row in index["files"] if row[0] == op[1]]
            if len(match) != 1:
                raise ValueError("rename source not unique")
            match[0][0] = op[2]
        else:
            raise ValueError("unknown journal operation")
    index["files"].sort(key=lambda row: row[0])
    return index, {"kind": kind, "prev": prev}

def physical_xattrs(index: dict) -> dict:
    by_name = {}
    files = index["files"]
    for index_no, attrs in index.get("fsmeta", {}).get("xattrs", []):
        if not isinstance(index_no, int) or index_no < 0 or index_no >= len(files):
            raise ValueError("bad metadata row ordinal")
        name = files[index_no][0]
        if name in by_name:
            raise ValueError("duplicate xattr row")
        by_name[name] = {str(key): bytes(val).hex() for key, val in attrs}
    return by_name

def main(result_file: Path, output: Path) -> None:
    receipt = json.loads(result_file.read_text())
    manifest = receipt["artifact_manifest"]
    mapping = (
        ("initial_archive", "base"),
        ("stable_archive", "stable_update"),
        ("stable_compact_archive", "stable_compact"),
        ("shifted_archive", "lexical_insert"),
        ("shifted_compact_archive", "insert_compact"),
    )
    results = {}
    for label, receipt_key in mapping:
        path = result_file.parent / manifest[label]["relative_path"]
        raw = path.read_bytes()
        if sha(raw).hex() != manifest[label]["sha256"]:
            raise ValueError("file digest differs from independent physical receipt")
        index, journal = read_committed_index(raw)
        names = [row[0] for row in index["files"]]
        if names != receipt[receipt_key]["names"]:
            raise ValueError("signed logical file order differs from CMPCT receipt")
        attributes = physical_xattrs(index)
        if attributes != receipt[receipt_key]["xattrs_by_logical_name"]:
            raise ValueError("signed xattr mapping differs from first-party receipt")
        results[label] = {
            "kind": journal["kind"],
            "has_parent": bool(journal["prev"]),
            "names": names,
            "xattrs_by_logical_name": attributes,
            "physical_sha256": sha(raw).hex(),
        }
    if results["shifted_archive"]["has_parent"] is not True:
        raise ValueError("lexical insertion was not an authentic committed journal")
    if results["shifted_compact_archive"]["has_parent"] is not False:
        raise ValueError("compaction did not collapse journal ancestry")
    if results["stable_archive"]["has_parent"] is not True:
        raise ValueError("stable control did not exercise journal")
    report = {
        "independent_zstd_and_msgpack": True,
        "source_authentication": "SHA-256 primary and committed footer verified independently",
        "product_outcome": receipt["decision"],
        "audit": "ADMITTED",
        "archives": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "audit": report["audit"],
        "product_outcome": report["product_outcome"],
        "archive_count": len(results),
        "native_signed_xattr_rebind": (
            results["shifted_archive"]["xattrs_by_logical_name"]
            != results["initial_archive"]["xattrs_by_logical_name"]
        ),
    }, sort_keys=True))

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
