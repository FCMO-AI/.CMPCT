from __future__ import annotations

"""Production-facing semantic owner for the v0.30 ZIP framing-factor recovery candidate.

This module deliberately stops before selector promotion. It owns the exact CMP25Z4 envelope bytes,
content-agnostic structural admission, fail-closed two-control recovery, canonical strong verification, bounded
random access, and transactional full extraction while reusing the already-audited CMP25Z3 logical grammar.
The release front door must not dispatch here until native/Android parity and exact all-15 selector authority are
green on one fingerprint.

No workload name, path, suffix, source hash, archive hash or frozen-corpus identity participates in admission.
"""

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED

MAGIC = b"CMP25Z4\0"
TAIL_MAGIC = b"ZFRTAIL1"
PROFILE = "zip-framing-factor-recovery-v4"
REVISION = 25
VERSION = 4
MAX_CONTROL = 1024 * 1024
MAX_DECODE = 8 * 1024 * 1024
MAX_AMP = 8.0
DEFAULT_MAX_EXTRACT_BYTES = 64 * 1024 * 1024 * 1024
_FOOTER = struct.Struct("<8sI32s")


class ProfileNotEligible(RuntimeError):
    pass


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _control_len_from_primary(raw: bytes) -> int:
    if len(raw) < len(MAGIC) + V3._HEADER.size or raw[: len(MAGIC)] != MAGIC:
        raise RuntimeError("not a canonical ZIP-factor recovery candidate")
    *_, group_count = V3._HEADER.unpack_from(raw, len(MAGIC))
    if not 1 <= int(group_count) <= V3.MAX_FILES:
        raise RuntimeError("ZIP-factor recovery primary group count exceeds policy")
    size = V3._HEADER.size + int(group_count) * V3._GROUP.size
    if size > MAX_CONTROL or len(MAGIC) + size > len(raw):
        raise RuntimeError("ZIP-factor recovery primary control exceeds policy")
    return size


def _tail_layout(raw: bytes) -> tuple[int, int, bytes]:
    if len(raw) < _FOOTER.size:
        raise RuntimeError("truncated ZIP-factor recovery footer")
    magic, control_len, expected_sha = _FOOTER.unpack_from(raw, len(raw) - _FOOTER.size)
    if magic != TAIL_MAGIC or not 1 <= int(control_len) <= MAX_CONTROL:
        raise RuntimeError("invalid ZIP-factor recovery footer")
    control_start = len(raw) - _FOOTER.size - int(control_len)
    if control_start <= len(MAGIC):
        raise RuntimeError("ZIP-factor recovery tail control overlaps primary")
    return int(control_len), control_start, expected_sha


def _tail_control(raw: bytes) -> tuple[bytes, int]:
    control_len, control_start, expected_sha = _tail_layout(raw)
    control = raw[control_start : control_start + control_len]
    if _sha(control) != expected_sha:
        raise RuntimeError("ZIP-factor recovery tail control authentication")
    return control, control_start


def _v3_candidate(raw: bytes, control: bytes, body_start: int, body_end: int) -> bytes:
    if not 0 <= body_start <= body_end <= len(raw):
        raise RuntimeError("ZIP-factor recovery body bounds")
    return V3.MAGIC + control + raw[body_start:body_end]


def _verify_v3_bytes(candidate: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-product-verify-") as td:
        path = Path(td) / "candidate.cmpct"
        path.write_bytes(candidate)
        result = V3.verify_and_identities(path)
    if not result.get("ok"):
        raise RuntimeError(f"reconstructed ZIP-factor v3 failed verification: {result!r}")
    if float(result["max_member_read_amplification"]) > MAX_AMP:
        raise RuntimeError("ZIP-factor recovery locality ceiling")
    if int(result["max_decode_unit_bytes"]) > MAX_DECODE:
        raise RuntimeError("ZIP-factor recovery decode-unit ceiling")
    return result


def _recover_candidate(raw: bytes) -> tuple[str, bytes, dict]:
    """Recover one exact V3 stream and authenticate its complete logical tree before exposing it."""
    errors: list[str] = []
    try:
        primary_len = _control_len_from_primary(raw)
        tail_len, tail_start, _ = _tail_layout(raw)
        if tail_len != primary_len:
            raise RuntimeError("ZIP-factor recovery control copy length mismatch")
        primary = raw[len(MAGIC) : len(MAGIC) + primary_len]
        candidate = _v3_candidate(raw, primary, len(MAGIC) + primary_len, tail_start)
        return "primary", candidate, _verify_v3_bytes(candidate)
    except Exception as exc:
        errors.append(f"primary={exc!r}")

    try:
        control, tail_start = _tail_control(raw)
        candidate = _v3_candidate(raw, control, len(MAGIC) + len(control), tail_start)
        return "tail", candidate, _verify_v3_bytes(candidate)
    except Exception as exc:
        errors.append(f"tail={exc!r}")
    raise RuntimeError("ZIP-factor recovery failed closed: " + "; ".join(errors))


def build_bytes(root: Path, *, level: int = 3, group_size: int = 7) -> tuple[bytes, dict]:
    """Construct the exact earned CMP25Z4 representation without an intermediate V3 publication."""
    try:
        raw, base_stats = FUSED.build_bytes(Path(root), level=level, group_size=group_size)
    except V3.ProfileNotEligible as exc:
        raise ProfileNotEligible(str(exc)) from exc
    if raw[: len(V3.MAGIC)] != V3.MAGIC:
        raise RuntimeError("unexpected ZIP-factor V3 identity")
    *_, group_count = V3._HEADER.unpack_from(raw, len(V3.MAGIC))
    control_len = V3._HEADER.size + int(group_count) * V3._GROUP.size
    if not 1 <= control_len <= MAX_CONTROL:
        raise RuntimeError("ZIP-factor recovery control exceeds policy")
    control = raw[len(V3.MAGIC) : len(V3.MAGIC) + control_len]
    body = raw[len(V3.MAGIC) + control_len :]
    footer = _FOOTER.pack(TAIL_MAGIC, control_len, _sha(control))
    recovery = MAGIC + control + body + control + footer
    stats = {
        **base_stats,
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "archive_bytes": len(recovery),
        "base_v3_bytes": len(raw),
        "recovery_overhead_bytes": len(recovery) - len(raw),
        "control_bytes": control_len,
        "payload_body_bytes": len(body),
        "payload_body_copies": 1,
        "control_copies": 2,
        "direct_v3_in_memory": True,
        "admission": "supported-zip-structure+shared-framing-signature-v1",
        "path_identity_used_for_admission": False,
    }
    if float(stats["max_member_read_amplification"]) > MAX_AMP:
        raise ProfileNotEligible("ZIP-factor recovery locality ceiling")
    if int(stats["max_decode_unit_bytes"]) > MAX_DECODE:
        raise ProfileNotEligible("ZIP-factor recovery decode-unit ceiling")
    return recovery, stats


def build(root: Path, out: Path, *, level: int = 3, group_size: int = 7) -> dict:
    raw, stats = build_bytes(Path(root), level=level, group_size=group_size)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return stats


def is_archive(path: Path) -> bool:
    try:
        with Path(path).open("rb") as fh:
            return fh.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def verify_and_identities(path: Path) -> dict:
    raw = Path(path).read_bytes()
    recovered_from, _candidate, verified = _recover_candidate(raw)
    return {
        **verified,
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "recovered_from": recovered_from,
        "recovery_semantics_verified": True,
        "payload_body_copies": 1,
        "control_copies": 2,
    }


def strong_verify(path: Path) -> dict:
    try:
        verified = verify_and_identities(Path(path))
        return {
            key: value
            for key, value in verified.items()
            if key not in {"manifest_raw", "manifest", "identities"}
        }
    except Exception as exc:
        return {
            "ok": False,
            "format_revision": REVISION,
            "format_profile": PROFILE,
            "error": repr(exc),
        }


def _entry_rows(verified: dict) -> dict[str, list]:
    # V3 owns FS.decode_manifest(), so `verified["manifest"]` is already the decoded FS wrapper.
    return FS.entry_map(verified["manifest"])


def list_members(path: Path) -> list[dict]:
    verified = verify_and_identities(Path(path))
    rows = _entry_rows(verified)
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    result: list[dict] = []
    entries = verified["manifest"]["manifest"]["entries"]
    regular_sizes = {row[0]: int(row[7][0]) for row in entries if row[1] == "f"}
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
        result.append({"path": rel, "kind": names[kind], "size": size})
    return result


def _open_v3_bytes(candidate: bytes):
    """Use the single audited V3 parser; temporary publication is reader-internal and not selector timing."""
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-product-read-") as td:
        path = Path(td) / "candidate.cmpct"
        path.write_bytes(candidate)
        return V3._open(path)


def _decode_group(template: dict, template_raw: bytes, manifest: dict, group) -> tuple[dict[str, bytes], int]:
    raw_size, expected_group_sha, paths, blob = group
    group_raw = V3._decompress(blob, raw_size, "group")
    if _sha(group_raw) != expected_group_sha:
        raise RuntimeError("ZIP-factor recovery group authentication")
    view = memoryview(group_raw)
    if bytes(view[:4]) != V3.GROUP_MAGIC:
        raise RuntimeError("bad ZIP-factor recovery group magic")
    at = 4
    count, at = V3.BASE._read_uvarint(view, at)
    if count != len(paths):
        raise RuntimeError("ZIP-factor recovery group count mismatch")
    context = len(template_raw) + len(group_raw)
    if context > MAX_DECODE:
        raise RuntimeError("ZIP-factor recovery decode-unit ceiling")
    restored_group: dict[str, bytes] = {}
    for rel in paths:
        dynamics = []
        for _row in template["rows"]:
            if at + 12 > len(view):
                raise RuntimeError("truncated ZIP-factor recovery dynamics")
            crc, csize, usize = struct.unpack_from("<III", view, at)
            at += 12
            if csize > MAX_DECODE or at + csize > len(view):
                raise RuntimeError("truncated ZIP-factor recovery payload")
            payload = bytes(view[at : at + csize])
            at += csize
            dynamics.append((crc, csize, usize, payload))
        restored = V3.BASE._rebuild_zip(template, dynamics)
        expected_size, expected_sha = manifest["regular"][rel]
        if len(restored) != int(expected_size) or _sha(restored) != bytes(expected_sha):
            raise RuntimeError(f"ZIP-factor recovery reconstructed identity mismatch: {rel}")
        amplification = context / max(1, len(restored))
        if amplification > MAX_AMP:
            raise RuntimeError(f"ZIP-factor recovery member locality ceiling: {rel}")
        restored_group[rel] = restored
    if at != len(view):
        raise RuntimeError("ZIP-factor recovery group trailing bytes")
    return restored_group, context


def _read_regular_v3(candidate: bytes, rel: str) -> tuple[bytes, int]:
    _manifest_raw, manifest, template_raw, groups = _open_v3_bytes(candidate)
    if rel not in manifest["regular"]:
        raise KeyError(rel)
    template = V3.BASE._parse_template(template_raw)
    for group in groups:
        if rel not in group[2]:
            continue
        restored, context = _decode_group(template, template_raw, manifest, group)
        return restored[rel], context
    raise RuntimeError("ZIP-factor recovery manifest/group membership mismatch")


def _decode_all_regular_v3(candidate: bytes) -> tuple[dict, dict[str, bytes]]:
    _manifest_raw, manifest, template_raw, groups = _open_v3_bytes(candidate)
    template = V3.BASE._parse_template(template_raw)
    restored: dict[str, bytes] = {}
    for group in groups:
        decoded, _context = _decode_group(template, template_raw, manifest, group)
        overlap = restored.keys() & decoded.keys()
        if overlap:
            raise RuntimeError(f"ZIP-factor recovery duplicate group ownership: {sorted(overlap)!r}")
        restored.update(decoded)
    if set(restored) != set(manifest["regular"]):
        raise RuntimeError("ZIP-factor recovery incomplete regular-file reconstruction")
    return manifest, restored


def read_member_with_stats(path: Path, rel: str) -> tuple[bytes, dict]:
    raw = Path(path).read_bytes()
    recovered_from, candidate, verified = _recover_candidate(raw)
    rows = _entry_rows(verified)
    if rel not in rows:
        raise KeyError(rel)
    row = rows[rel]
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        member = row[7].encode("utf-8")
        context = len(member)
    else:
        owner = row[7] if kind == "h" else rel
        member, context = _read_regular_v3(candidate, owner)
    amplification = int(context) / max(1, len(member))
    if amplification > MAX_AMP or int(context) > MAX_DECODE:
        raise RuntimeError("ZIP-factor recovery public read exceeded locality contract")
    return member, {
        "logical_bytes": len(member),
        "decoded_context_bytes": int(context),
        "decoded_context_amplification": amplification,
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "recovered_from": recovered_from,
    }


def read_member(path: Path, rel: str) -> bytes:
    return read_member_with_stats(Path(path), rel)[0]


def _logical_output_bytes(decoded: dict) -> int:
    regular = decoded["regular"]
    total = 0
    for row in decoded["manifest"]["entries"]:
        kind = row[1]
        if kind == "f":
            total += int(row[7][0])
        elif kind == "h":
            total += int(regular[row[7]][0])
        elif kind == "l":
            total += len(row[7].encode("utf-8"))
    return total


def extract(
    path: Path,
    dst: Path,
    *,
    max_output_bytes: int = DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 0:
        raise ValueError("max_output_bytes must be a non-negative integer")
    dst = Path(dst)
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(dst)

    raw = Path(path).read_bytes()
    _recovered_from, candidate, verified = _recover_candidate(raw)
    decoded = verified["manifest"]
    logical_bytes = _logical_output_bytes(decoded)
    if logical_bytes > max_output_bytes:
        raise RuntimeError("ZIP-factor recovery extraction exceeds caller output budget")

    # Decode and authenticate all regular owners before touching the publication path. The semantic verifier above
    # has already authenticated the complete archive; this second bounded pass materializes exact user bytes only.
    manifest, regular = _decode_all_regular_v3(candidate)
    if manifest["raw"] != decoded["raw"] or manifest["regular"] != decoded["regular"]:
        raise RuntimeError("ZIP-factor recovery extraction semantic-owner drift")

    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-zf-", dir=dst.parent))
    published = False
    try:
        for rel, member in regular.items():
            target = staging.joinpath(*PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(member)
        FS.restore_manifest_tree(staging, decoded, safe_symlinks=safe_symlinks)
        os.replace(staging, dst)
        published = True
    finally:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)


PROMOTION_STATE = "canonical-reader-candidate-only"
SELECTOR_ENABLED = False
PUBLIC_RANDOM_ACCESS_COMPLETE = True
PUBLIC_EXTRACT_COMPLETE = True
RELEASE_CREDIT = False
