from __future__ import annotations

"""Production-facing semantic owner for the v0.30 ZIP framing-factor recovery candidate.

This module deliberately stops one step before selector promotion. It owns the exact CMP25Z4 envelope bytes,
content-agnostic structural admission, fail-closed two-control recovery and canonical strong verification while
reusing the already-audited CMP25Z3 logical grammar. The release front door must not dispatch here until public
list/read/extract, native/Android parity and exact all-15 selector authority are green on one fingerprint.

No workload name, path, suffix, source hash, archive hash or frozen-corpus identity participates in admission.
"""

import hashlib
from pathlib import Path
import struct
import tempfile

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


def _recover_verified(raw: bytes) -> tuple[str, dict]:
    errors: list[str] = []
    try:
        primary_len = _control_len_from_primary(raw)
        tail_len, tail_start, _ = _tail_layout(raw)
        if tail_len != primary_len:
            raise RuntimeError("ZIP-factor recovery control copy length mismatch")
        primary = raw[len(MAGIC) : len(MAGIC) + primary_len]
        candidate = _v3_candidate(raw, primary, len(MAGIC) + primary_len, tail_start)
        return "primary", _verify_v3_bytes(candidate)
    except Exception as exc:
        errors.append(f"primary={exc!r}")

    try:
        control, tail_start = _tail_control(raw)
        candidate = _v3_candidate(raw, control, len(MAGIC) + len(control), tail_start)
        return "tail", _verify_v3_bytes(candidate)
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
    recovered_from, verified = _recover_verified(raw)
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


PROMOTION_STATE = "canonical-semantics-candidate-only"
SELECTOR_ENABLED = False
PUBLIC_READER_COMPLETE = False
RELEASE_CREDIT = False
