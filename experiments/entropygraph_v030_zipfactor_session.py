"""One-pass verifier/session for the bounded revision-25 ZIP-factor profile.

The profile module owns the archive grammar and exact ZIP reconstruction.  This session owns the release-facing
verification strategy: open once, decompress each bounded group once, rebuild each member once, and return the
identities needed by the canonical filesystem wrapper.  It avoids multiplying group decompression by member count
while preserving exact source SHA-256 and <=8x locality checks.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_profile as ZF


def verify_and_identities(archive: Path) -> dict:
    meta, manifest_raw, template_raw, blobs = ZF._open(Path(archive))
    template = ZF._parse_template(template_raw)
    identities: dict[str, tuple[int, bytes]] = {
        FS.FILESYSTEM_MANIFEST: (len(manifest_raw), hashlib.sha256(manifest_raw).digest())
    }
    max_amp = 1.0
    max_decode = len(manifest_raw)
    verified_user_files = 0

    groups = meta["groups"]
    if len(groups) != len(blobs):
        raise RuntimeError("ZIP-factor group/blob count mismatch")

    for desc, blob in zip(groups, blobs, strict=True):
        raw_size = int(desc[0])
        expected_group_sha = bytes(desc[1])
        paths = desc[2]
        declared_sizes = desc[3]
        if not isinstance(paths, list) or not isinstance(declared_sizes, list) or len(paths) != len(declared_sizes):
            raise RuntimeError("ZIP-factor group path/size declaration")
        group_raw = ZF._decompress(blob, raw_size)
        if hashlib.sha256(group_raw).digest() != expected_group_sha:
            raise RuntimeError("ZIP-factor group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != ZF.GROUP_MAGIC:
            raise RuntimeError("bad ZIP-factor group magic")
        at = 4
        count, at = ZF._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("ZIP-factor group file-count mismatch")
        context = len(template_raw) + len(group_raw)
        if context > ZF.MAX_DECODE:
            raise RuntimeError("ZIP-factor decode-unit ceiling")
        max_decode = max(max_decode, context)

        for index in range(count):
            rel_b, at = ZF._read_blob(view, at)
            rel = rel_b.decode("utf-8")
            expected_size, at = ZF._read_uvarint(view, at)
            if at + 32 > len(view):
                raise RuntimeError("truncated ZIP-factor source digest")
            expected_sha = bytes(view[at:at + 32]); at += 32
            if rel != paths[index] or int(expected_size) != int(declared_sizes[index]):
                raise RuntimeError("ZIP-factor group metadata/content mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated ZIP-factor dynamic fields")
                crc, csize, usize = struct.unpack_from("<III", view, at); at += 12
                if csize > ZF.MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated ZIP-factor compressed payload")
                payload = bytes(view[at:at + csize]); at += csize
                dynamics.append((crc, csize, usize, payload))
            restored = ZF._rebuild_zip(template, dynamics)
            got_sha = hashlib.sha256(restored).digest()
            if len(restored) != expected_size or got_sha != expected_sha:
                raise RuntimeError(f"ZIP-factor reconstructed identity mismatch: {rel}")
            amp = context / max(1, len(restored))
            if amp > ZF.MAX_AMP:
                raise RuntimeError(f"ZIP-factor member locality ceiling: {rel}")
            max_amp = max(max_amp, amp)
            if rel in identities:
                raise RuntimeError("duplicate ZIP-factor logical path")
            identities[rel] = (len(restored), got_sha)
            verified_user_files += 1
        if at != len(view):
            raise RuntimeError("ZIP-factor group trailing bytes")

    return {
        "ok": True,
        "format_revision": ZF.REVISION,
        "format_profile": ZF.PROFILE,
        "verified_user_files": verified_user_files,
        "verified_content_members": len(identities),
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_decode,
        "manifest_raw": manifest_raw,
        "identities": identities,
    }


def strong_verify(archive: Path) -> dict:
    try:
        result = verify_and_identities(archive)
        return {key: value for key, value in result.items() if key not in {"manifest_raw", "identities"}}
    except Exception as exc:
        return {
            "ok": False,
            "format_revision": ZF.REVISION,
            "format_profile": ZF.PROFILE,
            "error": repr(exc),
        }
