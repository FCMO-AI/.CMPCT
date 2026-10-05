from __future__ import annotations

"""Current-main v0.31 coordered bounded-drift complete-semantics court.

Research-only: no canonical grammar/selector/release change. The sibling reorders complete
filesystem-v1 regular rows into exact BDC content order and omits only the duplicate regular
SHA-256 already authenticated by each BDC member entry. Logical size remains explicit.

The court is bound to the current v0.31 preregistration and compares same-run complete bytes
against deterministic solid Tar+Zstd-19 on the exact externally normalized source.
"""

import argparse
import hashlib
import io
import json
import msgpack
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from experiments import entropygraph_v030_bounded_drift_container_v1 as BDC
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments import entropygraph_v030_product_fs as FS

MAGIC = b"CMPNXBC1"
HEADER = struct.Struct("<8sQQQ32s")
TRAILER = struct.Struct("<32s")
DIGEST_BYTES = 32
CONTROL_LEVEL = 12
NORMALIZED_MTIME = 315532800
TARGETS = {
    "01_shifted_versions": {
        "tree_sha256": "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd",
        "historical_zstd19_bytes": 1694674,
    },
    "03_boundary_churn": {
        "tree_sha256": "3238446efaef2a70a5c08d722bdc9dac3ac7c1c99ae3cde8093fae1481ad4b3d",
        "historical_zstd19_bytes": 73097,
    },
}


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _normalize_external_semantics(source: Path) -> None:
    """Match the public external comparator's deterministic filesystem input."""
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        path.chmod(0o644)
        os.utime(path, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    for directory in sorted((p for p in source.rglob("*") if p.is_dir()), reverse=True):
        directory.chmod(0o755)
        os.utime(directory, (NORMALIZED_MTIME, NORMALIZED_MTIME))
    source.chmod(0o755)
    os.utime(source, (NORMALIZED_MTIME, NORMALIZED_MTIME))


def _capture(source: Path) -> tuple[bytes, list[tuple[Path, str]], dict]:
    return FS.capture_filesystem_manifest(
        source,
        max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
        max_profile_files=CANONICAL.MAX_PROFILE_FILES,
        max_profile_logical_bytes=CANONICAL.MAX_PROFILE_LOGICAL_BYTES,
        max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
    )


def _content_order(regular_sources: list[tuple[Path, str]]) -> list[tuple[str, bytes]]:
    paired = [(rel, path.read_bytes()) for path, rel in regular_sources]
    # Python's stable sort preserves deterministic regular_sources order for duplicate content,
    # exactly matching BDC.encode_container's stable content-key canonicalization.
    return sorted(paired, key=lambda item: (_sha(item[1]), item[1]))


def _control_from_manifest(decoded: dict, ordered_paths: list[str]) -> bytes:
    by_path = {row[0]: row for row in decoded["manifest"]["entries"]}
    regular_rows: list[list] = []
    for rel in ordered_paths:
        row = by_path.get(rel)
        if row is None or row[1] != "f":
            raise RuntimeError(f"coordered control missing regular owner: {rel}")
        size, digest = row[7]
        if not isinstance(digest, bytes) or len(digest) != DIGEST_BYTES:
            raise RuntimeError("coordered source regular digest declaration")
        # Preserve path/kind/all filesystem metadata/logical size. Only the duplicate SHA-256
        # ownership fact moves into the already-authenticated BDC member entry.
        regular_rows.append([rel, "f", row[2], row[3], row[4], row[5], row[6], [int(size)]])
    explicit_rows = [row for row in decoded["manifest"]["entries"] if row[1] != "f"]
    manifest = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": [*regular_rows, *explicit_rows],
    }
    raw = msgpack.packb(manifest, use_bin_type=True)
    if len(raw) > FS.MAX_MANIFEST_BYTES:
        raise RuntimeError("coordered filesystem control exceeds bounded decode unit")
    return raw


def _expand_control(control_raw: bytes, bdc_blob: bytes) -> bytes:
    try:
        manifest = msgpack.unpackb(
            control_raw,
            raw=False,
            strict_map_key=False,
            max_array_len=CANONICAL.MAX_MANIFEST_ENTRIES * 8 + 1024,
            max_map_len=32,
            max_str_len=CANONICAL.POLICY.R.MAX_PATH_BYTES,
            max_bin_len=FS.MAX_MANIFEST_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid coordered filesystem control") from exc
    if not isinstance(manifest, dict) or manifest.get("v") != FS.FILESYSTEM_MANIFEST_VERSION:
        raise RuntimeError("unsupported coordered filesystem control")
    if manifest.get("profile") != "cmpct-r25-filesystem-manifest-v1" or manifest.get("internal_path") != FS.FILESYSTEM_MANIFEST:
        raise RuntimeError("coordered filesystem control identity")
    rows = manifest.get("entries")
    if not isinstance(rows, list) or len(rows) > CANONICAL.MAX_MANIFEST_ENTRIES:
        raise RuntimeError("coordered filesystem entry declaration")

    parsed = BDC.parse_container(bdc_blob)
    regular_cursor = 0
    expanded: list[list] = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 8:
            raise RuntimeError("malformed coordered filesystem row")
        if row[1] != "f":
            expanded.append(row)
            continue
        if regular_cursor >= len(parsed.entries):
            raise RuntimeError("coordered regular rows exceed BDC members")
        extra = row[7]
        if not isinstance(extra, list) or len(extra) != 1 or not isinstance(extra[0], int):
            raise RuntimeError("coordered regular size declaration")
        member = parsed.entries[regular_cursor]
        if int(extra[0]) != member.logical_size:
            raise RuntimeError("coordered regular size/BDC identity disagreement")
        expanded.append([*row[:7], [member.logical_size, member.sha256]])
        regular_cursor += 1
    if regular_cursor != len(parsed.entries):
        raise RuntimeError("BDC contains unowned regular members")
    expanded.sort(key=lambda row: row[0])
    canonical = {
        "v": FS.FILESYSTEM_MANIFEST_VERSION,
        "profile": "cmpct-r25-filesystem-manifest-v1",
        "internal_path": FS.FILESYSTEM_MANIFEST,
        "entries": expanded,
    }
    raw = msgpack.packb(canonical, use_bin_type=True)
    FS.decode_manifest(raw, max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES, max_entries=CANONICAL.MAX_MANIFEST_ENTRIES)
    return raw


def _encode_sibling(manifest_raw: bytes, regular_sources: list[tuple[Path, str]]) -> tuple[bytes, dict]:
    decoded = FS.decode_manifest(manifest_raw, max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES, max_entries=CANONICAL.MAX_MANIFEST_ENTRIES)
    ordered = _content_order(regular_sources)
    paths = [rel for rel, _data in ordered]
    members = [data for _rel, data in ordered]
    bdc_blob = BDC.encode_container(members)
    control_raw = _control_from_manifest(decoded, paths)
    control_stored = zstd.ZstdCompressor(level=CONTROL_LEVEL, threads=0, write_checksum=True).compress(control_raw)
    header = HEADER.pack(MAGIC, len(control_raw), len(control_stored), len(bdc_blob), _sha(control_raw))
    body = header + control_stored + bdc_blob
    blob = body + TRAILER.pack(_sha(body))
    return blob, {
        "control_raw_bytes": len(control_raw),
        "control_stored_bytes": len(control_stored),
        "bdc_bytes": len(bdc_blob),
        "header_bytes": HEADER.size,
        "trailer_bytes": TRAILER.size,
        "archive_bytes": len(blob),
        "physical_sha256": hashlib.sha256(blob).hexdigest(),
    }


def _parse_sibling(blob: bytes) -> tuple[bytes, bytes, bytes]:
    if not isinstance(blob, bytes) or len(blob) < HEADER.size + TRAILER.size:
        raise RuntimeError("short coordered bounded-drift sibling")
    body, trailer_raw = blob[:-TRAILER.size], blob[-TRAILER.size:]
    (trailer,) = TRAILER.unpack(trailer_raw)
    if _sha(body) != trailer:
        raise RuntimeError("coordered bounded-drift sibling digest mismatch")
    magic, raw_n, stored_n, bdc_n, raw_digest = HEADER.unpack_from(body, 0)
    if magic != MAGIC or raw_n > FS.MAX_MANIFEST_BYTES or stored_n > FS.MAX_MANIFEST_BYTES or bdc_n > BDC.MAX_CONTAINER_BYTES:
        raise RuntimeError("coordered bounded-drift sibling declaration")
    if HEADER.size + stored_n + bdc_n != len(body):
        raise RuntimeError("coordered bounded-drift sibling lengths")
    control_stored = body[HEADER.size:HEADER.size + stored_n]
    bdc_blob = body[HEADER.size + stored_n:]
    try:
        control_raw = zstd.ZstdDecompressor().decompress(control_stored, max_output_size=FS.MAX_MANIFEST_BYTES)
    except zstd.ZstdError as exc:
        raise RuntimeError("coordered filesystem control invalid") from exc
    if len(control_raw) != raw_n or _sha(control_raw) != raw_digest:
        raise RuntimeError("coordered filesystem control identity mismatch")
    return control_raw, bdc_blob, _expand_control(control_raw, bdc_blob)


def _decoded_regular_map(control_raw: bytes, bdc_blob: bytes) -> dict[str, bytes]:
    manifest = msgpack.unpackb(control_raw, raw=False, strict_map_key=False)
    paths = [row[0] for row in manifest["entries"] if row[1] == "f"]
    members = BDC.decode_all(bdc_blob)
    if len(paths) != len(members):
        raise RuntimeError("coordered path/member count mismatch")
    return dict(zip(paths, members, strict=True))


def _materialize_and_recapture(manifest_raw: bytes, regular: dict[str, bytes], root: Path) -> bytes:
    decoded = FS.decode_manifest(manifest_raw, max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES, max_entries=CANONICAL.MAX_MANIFEST_ENTRIES)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in regular.items():
        target = root.joinpath(*Path(rel).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    FS.restore_manifest_tree(root, decoded)
    recaptured, _regular, _stats = _capture(root)
    return recaptured


def _candidate_locality(control_raw: bytes, bdc_blob: bytes) -> dict:
    parsed = BDC.parse_container(bdc_blob)
    worst = 0.0
    max_unit = len(control_raw)
    for index, entry in enumerate(parsed.entries):
        facts = BDC.member_resource_facts(bdc_blob, index)
        decoded = facts.decoded_context_bytes + len(control_raw)
        worst = max(worst, decoded / max(1, entry.logical_size))
        max_unit = max(max_unit, facts.max_decode_unit_bytes)
    return {"max_member_read_amplification": worst, "max_decode_unit_bytes": max_unit, "passed": worst <= 8.0 and max_unit <= 8 * 1024 * 1024}


def _solid_tar_zstd19(stage: Path, work: Path) -> dict:
    exe = shutil.which("zstd")
    if exe is None:
        raise RuntimeError("zstd CLI is required for the exact external-control court")
    tar_path = work / "solid.tar"
    archive = work / "solid.tar.zst"
    started = time.perf_counter()
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as tf:
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            rel = path.relative_to(stage).as_posix()
            raw = path.read_bytes()
            info = tarfile.TarInfo(rel)
            info.size = len(raw); info.mtime = NORMALIZED_MTIME; info.mode = 0o644
            info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""
            tf.addfile(info, io.BytesIO(raw))
    subprocess.run([exe, "-19", "-f", str(tar_path), "-o", str(archive)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    create_s = time.perf_counter() - started
    decoded_tar = work / "decoded.tar"
    extracted = work / "zstd-out"
    subprocess.run([exe, "-d", "-f", str(archive), "-o", str(decoded_tar)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    extracted.mkdir()
    with tarfile.open(decoded_tar, "r") as tf:
        for member in tf.getmembers():
            target = (extracted / member.name).resolve()
            if extracted.resolve() not in target.parents and target != extracted.resolve():
                raise RuntimeError("generated tar contains unsafe path")
        tf.extractall(extracted)
    return {"archive_bytes": archive.stat().st_size, "create_s": create_s, "tree_sha256": HOSTILE.tree_hash(extracted)}


def _build_source(root: Path, name: str) -> Path:
    corpus = root / "corpus"; corpus.mkdir(parents=True, exist_ok=True)
    if name == "01_shifted_versions": HOSTILE.shifted_versions(corpus)
    elif name == "03_boundary_churn": HOSTILE.boundary_churn(corpus)
    else: raise KeyError(name)
    source = corpus / name
    _normalize_external_semantics(source)
    return source


def _row(work: Path, name: str, expected: dict) -> dict:
    source = _build_source(work, name)
    tree = HOSTILE.tree_hash(source)
    if tree != expected["tree_sha256"]: raise RuntimeError(f"{name} tree identity drift: {tree}")
    manifest_raw, regular_sources, manifest_stats = _capture(source)
    started = time.perf_counter(); sibling, sibling_stats = _encode_sibling(manifest_raw, regular_sources); create_s = time.perf_counter() - started
    control_raw, bdc_blob, recovered_manifest = _parse_sibling(sibling)
    if recovered_manifest != manifest_raw: raise RuntimeError(f"{name} filesystem manifest recapture changed bytes")
    regular = _decoded_regular_map(control_raw, bdc_blob)
    restored_root = work / "candidate-out"
    recaptured = _materialize_and_recapture(recovered_manifest, regular, restored_root)
    if recaptured != manifest_raw: raise RuntimeError(f"{name} physical filesystem semantics changed")
    if HOSTILE.tree_hash(restored_root) != tree: raise RuntimeError(f"{name} restored logical tree drift")
    locality = _candidate_locality(control_raw, bdc_blob)
    if not locality["passed"]: raise RuntimeError(f"{name} locality/resource gate failed")
    corrupted = bytearray(sibling); corrupted[len(corrupted) // 2] ^= 1
    try: _parse_sibling(bytes(corrupted))
    except Exception: pass
    else: raise RuntimeError(f"{name} corruption accepted")
    zstd = _solid_tar_zstd19(source, work)
    if zstd["tree_sha256"] != tree: raise RuntimeError(f"{name} Zstd-19 extracted tree drift")
    return {
        "name": name, "tree_sha256": tree, "filesystem_v1_bytes": len(manifest_raw), "manifest_stats": manifest_stats,
        "candidate": {**sibling_stats, **locality, "create_s": create_s, "physical_filesystem_semantics_exact": True},
        "solid_zstd19": {**zstd, "historical_current_fingerprint_bytes": expected["historical_zstd19_bytes"], "matches_historical_current_fingerprint_bytes": zstd["archive_bytes"] == expected["historical_zstd19_bytes"]},
        "delta_bytes_vs_zstd19": len(sibling) - zstd["archive_bytes"], "strict_size_win": len(sibling) < zstd["archive_bytes"],
    }


def _generic_fs_hostile(work: Path) -> dict:
    source = work / "generic-source"; (source / "d").mkdir(parents=True)
    payload = (b"duplicate-content|" * 257) + b"end"
    (source / "a.bin").write_bytes(payload)
    (source / "b.bin").write_bytes(payload)
    (source / "d" / "c.bin").write_bytes(b"other" * 1024)
    os.link(source / "a.bin", source / "hard-a.bin")
    os.symlink("../b.bin", source / "d" / "link-b")
    for p in (source / "a.bin", source / "b.bin", source / "d" / "c.bin"): p.chmod(0o640)
    manifest_raw, regular_sources, _stats = _capture(source)
    sibling, _s = _encode_sibling(manifest_raw, regular_sources)
    control_raw, bdc_blob, recovered_manifest = _parse_sibling(sibling)
    regular = _decoded_regular_map(control_raw, bdc_blob)
    restored = work / "generic-out"
    recaptured = _materialize_and_recapture(recovered_manifest, regular, restored)
    a = restored / "a.bin"; h = restored / "hard-a.bin"; link = restored / "d" / "link-b"
    return {
        "manifest_recapture_exact": recaptured == manifest_raw,
        "duplicate_content_distinct_inode": a.stat().st_ino != (restored / "b.bin").stat().st_ino,
        "hardlink_relation_preserved": a.stat().st_ino == h.stat().st_ino,
        "symlink_target_preserved": os.readlink(link) == "../b.bin",
        "passed": recaptured == manifest_raw and a.stat().st_ino != (restored / "b.bin").stat().st_ino and a.stat().st_ino == h.stat().st_ino and os.readlink(link) == "../b.bin",
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    rows = []
    for name, expected in TARGETS.items():
        with tempfile.TemporaryDirectory(prefix=f"cmpct-v031-bd-{name}-", dir=work_root) as td:
            rows.append(_row(Path(td), name, expected))
    with tempfile.TemporaryDirectory(prefix="cmpct-v031-bd-fs-hostile-", dir=work_root) as td:
        fs_hostile = _generic_fs_hostile(Path(td))
    passed = all(row["strict_size_win"] for row in rows) and fs_hostile["passed"]
    return {
        "schema": "cmpct-v031-bounded-drift-coordered-court-v1",
        "prereg": "benchmarks/history/2026-10-04-v031-bounded-drift-coordered-court-prereg.json",
        "claim_boundary": "research representation/execution evidence only; noncanonical sibling, no product/release credit",
        "rows": rows, "generic_filesystem_hostile": fs_hostile, "passed": passed,
        "decision": "ADVANCE_ONE_PRODUCTIZATION_RUNG" if passed else "RETIRE_OR_NARROW_COORDERED_OWNERSHIP",
        "product_credit": False, "release_credit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v031-bd-coordered-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v031-bd-coordered.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["passed"]:
        raise SystemExit("v0.31 bounded-drift coordered court did not preserve strict size/semantic gates")


if __name__ == "__main__":
    main()
