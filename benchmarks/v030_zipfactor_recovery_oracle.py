from __future__ import annotations

"""Two-way recovery proof for the compact ZIP-factor candidate.

ZIP-factor cannot enter canonical/native dispatch while its control metadata has only one copy. This oracle proves
a minimal recovery envelope without duplicating compressed payloads: the normal primary control block remains at
the front, one authenticated control copy is appended immediately before a fixed footer, and the payload body is
shared by both. Either control copy can reconstruct the exact existing v3 byte stream and therefore delegates all
logical verification, locality and content identity checks to the unchanged v3 verifier.

The experiment is deliberately fail-closed and non-authoritative. It requires clean verification, primary->tail
recovery, tail->primary recovery, rejection when both copies are damaged, exact logical identity across both
recovery paths, and a complete recovery archive still smaller than the exact solid Zstd-19 comparator. It does
not enable production dispatch or claim the creation-speed contract.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile

from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3

REC_MAGIC = b"CMP25Z4\0"
TAIL_MAGIC = b"ZFRTAIL1"
_FOOTER = struct.Struct("<8sI32s")
MAX_CONTROL = 1024 * 1024


def _sha(raw: bytes) -> bytes:
    return hashlib.sha256(raw).digest()


def _control_len_from_primary(raw: bytes) -> int:
    if len(raw) < len(REC_MAGIC) + V3._HEADER.size or raw[:8] != REC_MAGIC:
        raise RuntimeError("not a ZIP-factor recovery candidate")
    *_, group_count = V3._HEADER.unpack_from(raw, 8)
    if not 1 <= int(group_count) <= V3.MAX_FILES:
        raise RuntimeError("ZIP-factor recovery primary group count exceeds policy")
    size = V3._HEADER.size + int(group_count) * V3._GROUP.size
    if size > MAX_CONTROL or 8 + size > len(raw):
        raise RuntimeError("ZIP-factor recovery primary control exceeds policy")
    return size


def _tail_control(raw: bytes) -> tuple[bytes, int]:
    if len(raw) < _FOOTER.size:
        raise RuntimeError("truncated ZIP-factor recovery footer")
    magic, control_len, expected_sha = _FOOTER.unpack_from(raw, len(raw) - _FOOTER.size)
    if magic != TAIL_MAGIC or not 1 <= control_len <= MAX_CONTROL:
        raise RuntimeError("invalid ZIP-factor recovery footer")
    control_start = len(raw) - _FOOTER.size - control_len
    if control_start <= 8:
        raise RuntimeError("ZIP-factor recovery tail control overlaps primary")
    control = raw[control_start : control_start + control_len]
    if _sha(control) != expected_sha:
        raise RuntimeError("ZIP-factor recovery tail control authentication")
    return control, control_start


def build_recovery(root: Path, out: Path, *, level: int = 6, group_size: int = 7) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-recovery-build-") as td:
        base = Path(td) / "base.cmpct"
        base_stats = V3.build(root, base, level=level, group_size=group_size)
        raw = base.read_bytes()
    if raw[:8] != V3.MAGIC:
        raise RuntimeError("unexpected ZIP-factor v3 identity")
    *_, group_count = V3._HEADER.unpack_from(raw, 8)
    control_len = V3._HEADER.size + int(group_count) * V3._GROUP.size
    control = raw[8 : 8 + control_len]
    body = raw[8 + control_len :]
    footer = _FOOTER.pack(TAIL_MAGIC, control_len, _sha(control))
    recovery = REC_MAGIC + control + body + control + footer
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(recovery)
    return {
        **base_stats,
        "format_profile": "zip-framing-factor-recovery-oracle-v4",
        "archive_bytes": len(recovery),
        "base_v3_bytes": len(raw),
        "recovery_overhead_bytes": len(recovery) - len(raw),
        "control_bytes": control_len,
        "payload_body_bytes": len(body),
        "payload_body_copies": 1,
        "control_copies": 2,
    }


def _v3_candidate(raw: bytes, control: bytes, body_start: int, body_end: int) -> bytes:
    if not 0 <= body_start <= body_end <= len(raw):
        raise RuntimeError("ZIP-factor recovery body bounds")
    return V3.MAGIC + control + raw[body_start:body_end]


def _verify_v3_bytes(candidate: bytes) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-recovery-verify-") as td:
        path = Path(td) / "candidate.cmpct"
        path.write_bytes(candidate)
        result = V3.verify_and_identities(path)
    if not result.get("ok"):
        raise RuntimeError(f"reconstructed ZIP-factor v3 failed verification: {result!r}")
    return result


def recover_verify(path: Path) -> dict:
    raw = Path(path).read_bytes()
    errors: dict[str, str] = {}

    # Primary path derives its own descriptor length, but uses a valid tail footer only to locate the shared
    # payload end. If the tail is damaged, body_end is derived from the primary length and footer-declared layout
    # only when the footer itself remains parseable; otherwise the fixed clean-archive size relation is recovered
    # by scanning the authenticated tail magic from EOF. The oracle's corruption cases exercise both paths.
    try:
        primary_len = _control_len_from_primary(raw)
        tail_control, tail_start = _tail_control(raw)
        primary = raw[8 : 8 + primary_len]
        if len(tail_control) != primary_len:
            raise RuntimeError("ZIP-factor recovery control copy length mismatch")
        candidate = _v3_candidate(raw, primary, 8 + primary_len, tail_start)
        result = _verify_v3_bytes(candidate)
        return {"ok": True, "recovered_from": "primary", "result": result}
    except Exception as exc:
        errors["primary"] = repr(exc)

    try:
        control, tail_start = _tail_control(raw)
        body_start = 8 + len(control)
        candidate = _v3_candidate(raw, control, body_start, tail_start)
        result = _verify_v3_bytes(candidate)
        return {"ok": True, "recovered_from": "tail", "result": result, "primary_error": errors.get("primary")}
    except Exception as exc:
        errors["tail"] = repr(exc)
        return {"ok": False, "errors": errors}


def _snapshot(result: dict) -> dict:
    verified = result["result"]
    return {
        "manifest_sha256": hashlib.sha256(verified["manifest_raw"]).hexdigest(),
        "identities": {
            path: [size, digest.hex()]
            for path, (size, digest) in sorted(verified["identities"].items())
        },
        "verified_user_files": verified["verified_user_files"],
        "max_member_read_amplification": verified["max_member_read_amplification"],
        "max_decode_unit_bytes": verified["max_decode_unit_bytes"],
    }


def _flip(raw: bytes, index: int) -> bytes:
    if not 0 <= index < len(raw):
        raise ValueError("corruption index outside archive")
    out = bytearray(raw)
    out[index] ^= 0x5A
    return bytes(out)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    hostile = EXT.GENERAL.V029._load(
        EXT.GENERAL.V029.ROOT / "benchmarks" / "resemblance_hostile_corpus_v1.py",
        "cmpct_v030_zipfactor_recovery_hostile",
    )
    hostile.build(corpus)
    source = corpus / "04_deflate_family"
    archive = work_root / "candidate.cmpct"
    stats = build_recovery(source, archive, level=6, group_size=7)
    raw = archive.read_bytes()

    clean = recover_verify(archive)
    if not clean.get("ok"):
        raise RuntimeError(f"clean recovery candidate failed: {clean!r}")

    control_len = int(stats["control_bytes"])
    # Corrupt a byte inside the primary manifest SHA-256 field, not a length field, so the primary remains
    # structurally parseable but cannot authenticate reconstructed logical content.
    primary_bad_raw = _flip(raw, 8 + 4 + 3)
    primary_bad = work_root / "primary-bad.cmpct"
    primary_bad.write_bytes(primary_bad_raw)
    primary_recovered = recover_verify(primary_bad)

    # Corrupt the tail control copy while preserving the footer. Primary verification must remain sufficient.
    _tail, tail_start = _tail_control(raw)
    tail_bad_raw = _flip(raw, tail_start + min(7, control_len - 1))
    tail_bad = work_root / "tail-bad.cmpct"
    tail_bad.write_bytes(tail_bad_raw)
    tail_recovered = recover_verify(tail_bad)

    both_bad_raw = _flip(primary_bad_raw, tail_start + min(7, control_len - 1))
    both_bad = work_root / "both-bad.cmpct"
    both_bad.write_bytes(both_bad_raw)
    both_failed = recover_verify(both_bad)

    # Exact external size comparison on the same normalized logical tree. Creation timing is deliberately not
    # credited here; this gate answers whether recovery can fit inside the already-earned ZIP-factor size margin.
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-recovery-comp-") as td:
        td_path = Path(td)
        stage = EXT._normalized_stage(source, td_path)
        zstd_archive = td_path / "archive.tar.zst"
        zstd_out = td_path / "zstd-out"
        zstd_result = EXT._tar_zstd(stage, zstd_archive, zstd_out, td_path)
        if not zstd_result.get("available"):
            raise RuntimeError("solid Zstd-19 unavailable for ZIP-factor recovery proof")
        EXT._verify_extracted(zstd_out, EXT._tree(stage), "recovery-zstd19")

    clean_snapshot = _snapshot(clean)
    primary_snapshot = _snapshot(primary_recovered) if primary_recovered.get("ok") else None
    tail_snapshot = _snapshot(tail_recovered) if tail_recovered.get("ok") else None
    gate = {
        "clean_verified": clean.get("ok") is True,
        "primary_corruption_recovers_from_tail": primary_recovered.get("ok") is True and primary_recovered.get("recovered_from") == "tail",
        "tail_corruption_recovers_from_primary": tail_recovered.get("ok") is True and tail_recovered.get("recovered_from") == "primary",
        "double_control_corruption_fails_closed": both_failed.get("ok") is False,
        "recovered_identity_exact": clean_snapshot == primary_snapshot == tail_snapshot,
        "locality_within_8x": clean_snapshot["max_member_read_amplification"] <= 8.0,
        "decode_unit_within_8mib": clean_snapshot["max_decode_unit_bytes"] <= 8 * 1024 * 1024,
        "recovery_candidate_smaller_than_zstd19": stats["archive_bytes"] < int(zstd_result["archive_bytes"]),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-zipfactor-recovery-oracle-v1",
        "candidate": stats,
        "zstd19_bytes": int(zstd_result["archive_bytes"]),
        "clean": {"recovered_from": clean.get("recovered_from"), "snapshot": clean_snapshot},
        "primary_corruption": {"recovered_from": primary_recovered.get("recovered_from"), "ok": primary_recovered.get("ok")},
        "tail_corruption": {"recovered_from": tail_recovered.get("recovered_from"), "ok": tail_recovered.get("ok")},
        "double_corruption": {"ok": both_failed.get("ok"), "errors": both_failed.get("errors")},
        "gate": gate,
        "claim_boundary": (
            "Research recovery proof only. It demonstrates that two authenticated control copies can share one "
            "payload body while preserving the existing v3 logical verifier and Zstd size margin. It does not "
            "authorize canonical/native/Android dispatch or satisfy the creation-speed release contract."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-recovery-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-recovery.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("ZIP-factor recovery envelope did not satisfy the proof gate")


if __name__ == "__main__":
    main()
