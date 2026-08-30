from __future__ import annotations

"""Locality-honest public reader for the canonical CMP25Z4 recovery candidate.

Strong verification still authenticates the complete archive. Selective reads must not do that work first: doing so
would decompress every group and then pretend only the target group counted toward locality. This reader authenticates
the duplicated binary control from the footer SHA, parses only bounded direct metadata, and decompresses exactly the
one target group. It delegates build/full verification/extraction to the canonical recovery product candidate.
"""

import hashlib
from pathlib import Path
import tempfile

from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_recovery_product_candidate as PRODUCT

MAX_AMP = PRODUCT.MAX_AMP
MAX_DECODE = PRODUCT.MAX_DECODE


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _select_v3_candidate(raw: bytes) -> tuple[str, bytes]:
    """Select an authenticated control copy without decompressing unrelated payload groups."""
    errors: list[str] = []
    try:
        tail_len, tail_start, expected_sha = PRODUCT._tail_layout(raw)
    except Exception as exc:
        raise RuntimeError(f"ZIP-factor recovery footer authentication unavailable: {exc!r}") from exc

    try:
        primary_len = PRODUCT._control_len_from_primary(raw)
        if primary_len != tail_len:
            raise RuntimeError("primary/tail control length mismatch")
        primary = raw[len(PRODUCT.MAGIC):len(PRODUCT.MAGIC) + primary_len]
        if _sha(primary) != expected_sha:
            raise RuntimeError("primary control SHA mismatch")
        return "primary", PRODUCT._v3_candidate(
            raw, primary, len(PRODUCT.MAGIC) + primary_len, tail_start
        )
    except Exception as exc:
        errors.append(f"primary={exc!r}")

    try:
        tail, tail_start = PRODUCT._tail_control(raw)
        return "tail", PRODUCT._v3_candidate(
            raw, tail, len(PRODUCT.MAGIC) + len(tail), tail_start
        )
    except Exception as exc:
        errors.append(f"tail={exc!r}")
    raise RuntimeError("ZIP-factor selective reader failed closed: " + "; ".join(errors))


def _open_v3(candidate: bytes):
    # V3._open authenticates/decompresses only the direct manifest/template here; group blobs remain compressed.
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-selective-") as td:
        path = Path(td) / "candidate.cmpct"
        path.write_bytes(candidate)
        return V3._open(path)


def list_members(path: Path) -> list[dict]:
    raw = Path(path).read_bytes()
    _recovered_from, candidate = _select_v3_candidate(raw)
    _manifest_raw, manifest, _template_raw, _groups = _open_v3(candidate)
    rows = PRODUCT.FS.entry_map(manifest)
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    regular_sizes = {row[0]: int(row[7][0]) for row in manifest["manifest"]["entries"] if row[1] == "f"}
    out = []
    for rel in sorted(rows):
        row = rows[rel]
        kind = row[1]
        if kind == "f":
            size = int(row[7][0])
        elif kind == "h":
            size = regular_sizes[row[7]]
        elif kind == "l":
            size = len(row[7].encode("utf-8"))
        else:
            size = 0
        out.append({"path": rel, "kind": names[kind], "size": size})
    return out


def _decode_target(candidate: bytes, rel: str) -> tuple[bytes, int]:
    manifest_raw, manifest, template_raw, groups = _open_v3(candidate)
    if rel not in manifest["regular"]:
        raise KeyError(rel)
    template = V3.BASE._parse_template(template_raw)
    for raw_size, expected_group_sha, paths, blob in groups:
        if rel not in paths:
            continue
        group_raw = V3._decompress(blob, raw_size, "group")
        if _sha(group_raw) != expected_group_sha:
            raise RuntimeError("ZIP-factor selective group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != V3.GROUP_MAGIC:
            raise RuntimeError("bad ZIP-factor selective group magic")
        at = 4
        count, at = V3.BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("ZIP-factor selective group count mismatch")
        # Count everything actually decompressed for this operation, including direct metadata.
        decoded_context = len(manifest_raw) + len(template_raw) + len(group_raw)
        if decoded_context > MAX_DECODE:
            raise RuntimeError("ZIP-factor selective decode-unit ceiling")
        for member in paths:
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated ZIP-factor selective dynamics")
                crc, csize, usize = V3.struct.unpack_from("<III", view, at)
                at += 12
                if csize > MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated ZIP-factor selective payload")
                payload = bytes(view[at:at + csize])
                at += csize
                dynamics.append((crc, csize, usize, payload))
            if member != rel:
                continue
            restored = V3.BASE._rebuild_zip(template, dynamics)
            expected_size, expected_sha = manifest["regular"][rel]
            if len(restored) != int(expected_size) or _sha(restored) != bytes(expected_sha):
                raise RuntimeError("ZIP-factor selective reconstructed identity mismatch")
            amp = decoded_context / max(1, len(restored))
            if amp > MAX_AMP:
                raise RuntimeError("ZIP-factor selective locality ceiling")
            return restored, decoded_context
        raise RuntimeError("ZIP-factor target disappeared from authenticated group")
    raise RuntimeError("ZIP-factor manifest/group membership mismatch")


def read_member_with_stats(path: Path, rel: str) -> tuple[bytes, dict]:
    raw = Path(path).read_bytes()
    recovered_from, candidate = _select_v3_candidate(raw)
    _manifest_raw, manifest, _template_raw, _groups = _open_v3(candidate)
    rows = PRODUCT.FS.entry_map(manifest)
    if rel not in rows:
        raise KeyError(rel)
    row = rows[rel]
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        value = row[7].encode("utf-8")
        context = len(_manifest_raw)
    else:
        owner = row[7] if kind == "h" else rel
        value, context = _decode_target(candidate, owner)
    amp = context / max(1, len(value))
    if amp > MAX_AMP or context > MAX_DECODE:
        raise RuntimeError("ZIP-factor selective public read exceeded locality contract")
    return value, {
        "logical_bytes": len(value),
        "decoded_context_bytes": context,
        "decoded_context_amplification": amp,
        "recovered_from": recovered_from,
        "full_archive_verify_before_read": False,
        "format_revision": PRODUCT.REVISION,
        "format_profile": PRODUCT.PROFILE,
    }


def read_member(path: Path, rel: str) -> bytes:
    return read_member_with_stats(Path(path), rel)[0]


# Whole-tree operations remain owned by the canonical product candidate.
build = PRODUCT.build
build_bytes = PRODUCT.build_bytes
is_archive = PRODUCT.is_archive
strong_verify = PRODUCT.strong_verify
verify_and_identities = PRODUCT.verify_and_identities
extract = PRODUCT.extract

PROMOTION_STATE = "canonical-selective-reader-candidate-only"
SELECTOR_ENABLED = False
RELEASE_CREDIT = False
