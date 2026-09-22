from __future__ import annotations

"""Charged source-structure oracle for generic ZIP-family physical ownership.

This does not build or mutate CMPCT archives and earns no product credit. It asks a cheaper question first:
for an arbitrary source tree, which regular files are structurally valid ZIP containers regardless of suffix,
how many exact compressed member streams are physically duplicated across those containers, and which loose
source files are byte-identical to member plaintexts whose compressed streams are already required?

The result is intentionally path/name agnostic for admission. Paths are reported only as evidence. A future
product experiment must still price complete archive metadata, locality, reader/native support and a raw fallback.
"""

import argparse
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _zip_members(path: Path, raw: bytes) -> list[dict] | None:
    if len(raw) < 4 or raw[:4] != b"PK\x03\x04":
        return None
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (OSError, zipfile.BadZipFile):
        return None
    rows: list[dict] = []
    try:
        for info in archive.infolist():
            if info.is_dir():
                continue
            try:
                header = struct.unpack_from("<IHHHHHIIIHH", raw, info.header_offset)
                name_len, extra_len = header[-2], header[-1]
                start = info.header_offset + 30 + name_len + extra_len
                end = start + info.compress_size
                stream = raw[start:end]
                plain = archive.read(info)
            except (IndexError, OSError, RuntimeError, struct.error, zipfile.BadZipFile):
                return None
            if len(stream) != info.compress_size or len(plain) != info.file_size:
                return None
            rows.append({
                "member": info.filename,
                "method": int(info.compress_type),
                "plain_bytes": len(plain),
                "stream_bytes": len(stream),
                "plain_sha256": _sha(plain).hex(),
                "stream_sha256": _sha(stream).hex(),
            })
    finally:
        archive.close()
    return rows


def analyze(root: Path) -> dict:
    root = Path(root)
    regular = sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())
    loose_by_hash: dict[str, list[str]] = defaultdict(list)
    logical_bytes = 0
    for path in regular:
        data = path.read_bytes()
        logical_bytes += len(data)
        loose_by_hash[_sha(data).hex()].append(path.relative_to(root).as_posix())

    containers: list[dict] = []
    stream_owners: dict[str, list[dict]] = defaultdict(list)
    inverse_matches: dict[str, dict] = {}
    for path in regular:
        raw = path.read_bytes()
        members = _zip_members(path, raw)
        if members is None:
            continue
        rel = path.relative_to(root).as_posix()
        container = {
            "path": rel,
            "suffix": path.suffix.lower(),
            "archive_bytes": len(raw),
            "members": len(members),
            "recognized_by_current_r24_suffix_gate": path.suffix.lower() in {".zip", ".whl"},
        }
        containers.append(container)
        for member in members:
            owner = {"container": rel, "member": member["member"], "stream_bytes": member["stream_bytes"]}
            stream_owners[member["stream_sha256"]].append(owner)
            loose = [candidate for candidate in loose_by_hash.get(member["plain_sha256"], []) if candidate != rel]
            if loose:
                previous = inverse_matches.get(member["plain_sha256"])
                candidate = {
                    "loose_paths": loose,
                    "plain_bytes": member["plain_bytes"],
                    "stream_bytes": member["stream_bytes"],
                    "container": rel,
                    "member": member["member"],
                }
                if previous is None or candidate["stream_bytes"] < previous["stream_bytes"]:
                    inverse_matches[member["plain_sha256"]] = candidate

    total_stream_bytes = sum(owner[0]["stream_bytes"] * len(owner) for owner in stream_owners.values())
    unique_stream_bytes = sum(owner[0]["stream_bytes"] for owner in stream_owners.values())
    duplicate_stream_saving = total_stream_bytes - unique_stream_bytes
    inverse_plain_bytes = sum(row["plain_bytes"] for row in inverse_matches.values())
    inverse_stream_bytes = sum(row["stream_bytes"] for row in inverse_matches.values())
    new_containers = [row for row in containers if not row["recognized_by_current_r24_suffix_gate"]]
    return {
        "schema": "cmpct-v030-generic-zip-discovery-oracle-v1",
        "claim_boundary": "source-structure/headroom oracle only; no archive/product credit",
        "root": str(root),
        "files": len(regular),
        "logical_bytes": logical_bytes,
        "valid_zip_containers": len(containers),
        "new_content_discovered_containers": len(new_containers),
        "containers": containers,
        "compressed_member_stream_bytes": total_stream_bytes,
        "unique_compressed_member_stream_bytes": unique_stream_bytes,
        "exact_duplicate_stream_headroom_bytes": duplicate_stream_saving,
        "loose_plaintext_inverse_matches": len(inverse_matches),
        "inverse_match_plain_bytes": inverse_plain_bytes,
        "inverse_match_required_stream_bytes": inverse_stream_bytes,
        "inverse_matches": sorted(inverse_matches.values(), key=lambda row: (-row["plain_bytes"], row["container"])),
        "disproof": (
            "Headroom does not imply product savings. Complete virtual-recipe metadata, retained streams, raw fallback, "
            "locality, integrity, native parity and malformed/resource-limit behavior must be charged before promotion."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
