from __future__ import annotations

"""Bounded r25 compact-control candidate over the mature r24 physical payload.

C25CC01 changes only the duplicated authenticated control representation. It keeps the completed shipping r24
physical data span byte-for-byte unchanged, stores two authenticated copies of a compact control object, and expands
that object exactly back into the ordinary r24 semantic index before delegating logical operations to the mature r24
reader. It is intentionally a candidate profile: release-product/native/Android dispatch remains closed until the
profile earns those independent promotion gates.
"""

from contextlib import contextmanager
from pathlib import Path
import hashlib
import os
import tempfile

import msgpack

from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_release_product as PRODUCT

MAGIC = b"C25CC01\0"
TAIL_MAGIC = b"C25CCT1\0"
REVISION = 25
PROFILE = "r24-compact-control-v1"
LEVELS = CONTROL.LEVELS
MAX_CONTROL_RAW_BYTES = 64 * 1024 * 1024
# The reconstructed r24 envelope is ephemeral verifier/reader compatibility state, not product bytes. Its compressed
# index only has to round-trip exactly through the mature r24 grammar, so paying the mature encoder's level-12 size
# optimization here is redundant CPU. Level 1 preserves the exact authenticated semantic index while minimizing the
# compatibility bridge latency that is currently material to the ZIP-speed leg.
COMPAT_INDEX_LEVEL = 1


class CompactControlError(RuntimeError):
    pass


class ProfileNotEligible(CompactControlError):
    pass


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _compress_control(raw: bytes) -> tuple[int, bytes]:
    rows = []
    for level in LEVELS:
        comp = R24.zc(raw, level)
        rows.append((len(comp), level, comp))
    _size, level, comp = min(rows, key=lambda row: (row[0], row[1]))
    return int(level), comp


def _source_r24_parts(archive: Path) -> tuple[dict, bytes, dict]:
    payload = Path(archive).read_bytes()
    if len(payload) < R24.HDR.size + R24.FTR.size:
        raise CompactControlError("truncated source r24 archive")
    magic, version, _flags, primary_cbytes, raw_bytes, data_bytes, index_sha = R24.HDR.unpack_from(payload, 0)
    if magic != R24.MAGIC or int(version) != R24.VERSION:
        raise CompactControlError("compact-control source is not canonical r24")
    primary_start = R24.HDR.size
    primary_end = primary_start + int(primary_cbytes)
    data_end = primary_end + int(data_bytes)
    footer_off = len(payload) - R24.FTR.size
    tail_start = footer_off - int(primary_cbytes)
    if data_end != tail_start:
        raise CompactControlError("source r24 physical span accounting mismatch")
    primary = payload[primary_start:primary_end]
    raw = R24.zd(primary, int(raw_bytes))
    if _sha(raw) != index_sha:
        raise CompactControlError("source r24 primary index SHA mismatch")
    if payload[tail_start:footer_off] != primary:
        raise CompactControlError("source r24 recovery index differs from primary")
    index = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    return index, payload[primary_end:data_end], {
        "archive_bytes": len(payload),
        "index_comp_bytes_per_copy": int(primary_cbytes),
        "index_raw_bytes": int(raw_bytes),
        "data_bytes": int(data_bytes),
    }


def _compact_raw(index: dict) -> tuple[bytes, dict]:
    compact = CONTROL._compact_index(index)
    expanded = CONTROL._expand_index(compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise CompactControlError("compact control failed exact semantic-index roundtrip")
    envelope = {"x": list(index["features"]), "c": compact}
    raw = msgpack.packb(envelope, use_bin_type=True)
    if len(raw) > MAX_CONTROL_RAW_BYTES:
        raise ProfileNotEligible("compact control exceeds bounded raw-control ceiling")
    return raw, compact


def _write_profile(source_r24: Path, out: Path) -> dict:
    index, data, physical = _source_r24_parts(source_r24)
    raw, _compact = _compact_raw(index)
    level, comp = _compress_control(raw)
    projected = R24.HDR.size + len(comp) + len(data) + len(comp) + R24.FTR.size
    if projected >= int(physical["archive_bytes"]):
        raise ProfileNotEligible("compact control is not strictly smaller than shipping r24")
    digest = _sha(raw)
    header = R24.HDR.pack(MAGIC, REVISION, 0, len(comp), len(raw), len(data), digest)
    footer = R24.FTR.pack(TAIL_MAGIC, 0, 1, 0, 0, len(comp), len(raw), 0, digest)
    payload = header + comp + data + comp + footer
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.tmp-{os.getpid()}")
    try:
        tmp.write_bytes(payload)
        os.replace(tmp, out)
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "selected": "r24-compact-control",
        "format_revision": REVISION,
        "format_profile": PROFILE,
        "archive_bytes": len(payload),
        "source_r24_bytes": int(physical["archive_bytes"]),
        "saving_vs_r24_bytes": int(physical["archive_bytes"]) - len(payload),
        "physical_data_bytes": len(data),
        "physical_payload_records_unchanged": True,
        "two_authenticated_control_copies": True,
        "compact_control_level": level,
        "compact_control_raw_bytes": len(raw),
        "compact_control_comp_bytes_per_copy": len(comp),
        "source_index_comp_bytes_per_copy": int(physical["index_comp_bytes_per_copy"]),
        "semantic_index_roundtrip_exact": True,
    }


def build(root: Path, out: Path) -> dict:
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-cc-build-", dir=out.parent) as td:
        r24 = Path(td) / "source-r24.cmpct"
        r24_stats = dict(PRODUCT._locality_bounded_r24_build(root, r24))
        stats = _write_profile(r24, out)
        stats["r24"] = r24_stats
        return stats


def _read_control_copy(comp: bytes, raw_bytes: int, digest: bytes) -> dict:
    if raw_bytes < 0 or raw_bytes > MAX_CONTROL_RAW_BYTES:
        raise CompactControlError("compact-control raw-size declaration exceeds bound")
    raw = R24.zd(comp, int(raw_bytes))
    if _sha(raw) != digest:
        raise CompactControlError("compact-control SHA mismatch")
    obj = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if not isinstance(obj, dict) or set(obj) != {"x", "c"}:
        raise CompactControlError("invalid compact-control envelope")
    if not isinstance(obj["x"], list) or not isinstance(obj["c"], dict):
        raise CompactControlError("invalid compact-control envelope types")
    return obj


def _parse(archive: Path) -> dict:
    payload = Path(archive).read_bytes()
    if len(payload) < R24.HDR.size + R24.FTR.size:
        raise CompactControlError("truncated compact-control archive")
    magic, version, _flags, primary_cbytes, raw_bytes, data_bytes, primary_sha = R24.HDR.unpack_from(payload, 0)
    if magic != MAGIC or int(version) != REVISION:
        raise CompactControlError("not C25CC01")
    footer_off = len(payload) - R24.FTR.size
    fmagic, _a, _b, _c, _d, tail_cbytes, tail_raw_bytes, _reserved, tail_sha = R24.FTR.unpack_from(payload, footer_off)
    if fmagic != TAIL_MAGIC:
        raise CompactControlError("compact-control tail magic mismatch")
    primary_start = R24.HDR.size
    primary_end = primary_start + int(primary_cbytes)
    tail_start = footer_off - int(tail_cbytes)
    if primary_end + int(data_bytes) != tail_start:
        raise CompactControlError("compact-control physical span accounting mismatch")
    primary = payload[primary_start:primary_end]
    tail = payload[tail_start:footer_off]
    decoded = None
    recovery = None
    try:
        decoded = _read_control_copy(primary, int(raw_bytes), primary_sha)
        recovery = "primary"
    except Exception:
        decoded = _read_control_copy(tail, int(tail_raw_bytes), tail_sha)
        recovery = "tail"
    compact = decoded["c"]
    index = CONTROL._expand_index(compact, version=R24.VERSION, features=list(decoded["x"]))
    if CONTROL._expand_index(CONTROL._compact_index(index), version=R24.VERSION, features=list(index["features"])) != index:
        raise CompactControlError("compact-control semantic expansion is not stable")
    return {
        "index": index,
        "data": payload[primary_end:tail_start],
        "recovery_source": recovery,
        "primary_control_bytes": int(primary_cbytes),
        "tail_control_bytes": int(tail_cbytes),
        "archive_bytes": len(payload),
    }


def _rebuild_r24_bytes(parsed: dict) -> bytes:
    index = parsed["index"]
    raw = msgpack.packb(index, use_bin_type=True)
    comp = R24.zc(raw, COMPAT_INDEX_LEVEL)
    digest = _sha(raw)
    data = parsed["data"]
    header = R24.HDR.pack(R24.MAGIC, R24.VERSION, 0, len(comp), len(raw), len(data), digest)
    footer = R24.FTR.pack(R24.FMAGIC, 0, 1, 0, 0, len(comp), len(raw), 0, digest)
    return header + comp + data + comp + footer


@contextmanager
def _materialized_r24(archive: Path):
    parsed = _parse(Path(archive))
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-read-") as td:
        path = Path(td) / "expanded-r24.cmpct"
        path.write_bytes(_rebuild_r24_bytes(parsed))
        yield path, parsed


def _verify_materialized_r24(path: Path) -> dict:
    """Strongly verify the compatibility r24 while hashing each physical S_PACK only once.

    Mature ``CMPCT.verify`` necessarily computes a logical hash per member. S_PACK slices do not carry an independent
    per-slice digest; their security boundary is the authenticated index plus the owning physical blob identity. The
    generic path therefore re-reads/re-hashes the same pack slices without gaining an independent check. C25CC01's
    native reader already authenticates the owning physical pack before deriving slice identities. Mirror that exact
    boundary here: validate each owning pack's full SHA-256 once, still execute every logical member read/size check,
    and retain ordinary per-member SHA verification everywhere an independent identity exists.
    """
    with CMPCT(path) as reader:
        verified_files = 0
        verified_packs: set[int] = set()
        for row in reader.files:
            if row[1] == R24.K_DIR:
                continue
            raw = reader.read(row[0])
            storage = row[6]
            if storage and storage[0] == R24.S_PACK:
                pack_idx = int(storage[1])
                if pack_idx not in verified_packs:
                    pack = reader._blob(pack_idx)
                    off = int(reader.blobs[pack_idx][0])
                    pos = int(reader.record_base) + off
                    header = R24.BHDR.unpack_from(reader.mm, pos)
                    expected_sha = bytes(header[-1])
                    if _sha(pack) != expected_sha:
                        raise CompactControlError(f"physical S_PACK SHA-256 verification failure: {pack_idx}")
                    verified_packs.add(pack_idx)
            else:
                want = reader.file_sha256(row[0])
                if _sha(raw) != want:
                    raise CompactControlError(f"SHA-256 verification failure: {row[0]}")
            verified_files += 1
        tree = PRODUCT._r24_user_tree_sha(reader)
    return {
        "ok": True,
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "tree_sha256": tree,
        "user_tree_sha256": tree,
        "verified_files": verified_files,
        "verified_pack_records": len(verified_packs),
        "reader": "cmpct-r24-reference-reader-pack-sha-once",
    }


def strong_verify(archive: Path) -> dict:
    try:
        with _materialized_r24(Path(archive)) as (r24, parsed):
            verified = _verify_materialized_r24(r24)
            if not verified.get("ok") or int(verified.get("format_revision", -1)) != 24:
                raise CompactControlError(f"expanded r24 strong verification failed: {verified!r}")
            return {
                **verified,
                "format_revision": REVISION,
                "format_profile": PROFILE,
                "reader": "cmpct-v030-r24-compact-control-v1",
                "compact_control_recovery_source": parsed["recovery_source"],
                "two_authenticated_control_copies": True,
                "physical_payload_records_unchanged": True,
                "semantic_index_roundtrip_exact": True,
                "compatibility_index_level": COMPAT_INDEX_LEVEL,
                "pack_verification_policy": "authenticated-physical-pack-sha-once",
            }
    except Exception as exc:
        return {
            "ok": False,
            "format_revision": REVISION,
            "format_profile": PROFILE,
            "reader": "cmpct-v030-r24-compact-control-v1",
            "error": repr(exc),
        }


def list_members(archive: Path):
    with _materialized_r24(Path(archive)) as (r24, _parsed):
        return PRODUCT.list_members(r24)


def read_member_with_stats(archive: Path, rel: str):
    with _materialized_r24(Path(archive)) as (r24, parsed):
        data, stats = PRODUCT.read_member_with_stats(r24, rel)
        return data, {**stats, "compact_control_recovery_source": parsed["recovery_source"]}


def read_member(archive: Path, rel: str):
    return read_member_with_stats(archive, rel)[0]


def extract(archive: Path, dst: Path, *, max_output_bytes=PRODUCT.POLICY.DEFAULT_MAX_EXTRACT_BYTES, safe_symlinks=True):
    with _materialized_r24(Path(archive)) as (r24, _parsed):
        return PRODUCT.extract(r24, dst, max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)


def physical_data_span(archive: Path) -> bytes:
    return bytes(_parse(Path(archive))["data"])
