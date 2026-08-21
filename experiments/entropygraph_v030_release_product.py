"""CMPCT v0.30 release product front door.

This is the one promoted Python product surface for v0.30. It delegates revision-25 implementation to
``entropygraph_v030_canonical_final`` and the mature revision-24 compatibility path to ``cmpct.reader.CMPCT``.
The distinction matters because release evidence must describe one user tree consistently even when the exact
product selector conservatively falls back to r24.

Research/checkpoint modules remain importable for ablation and historical evidence, but release workflows and
public product operations should import this module.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import stat
import tempfile
import threading
import time

import msgpack

from cmpct.reader import CMPCT
from cmpct import codec as R24_CODEC
from experiments import entropygraph_v030_canonical_final as C
from experiments import entropygraph_v030_verified_restore as VERIFIED_RESTORE

REVISION = C.REVISION
G04_MAGIC = C.G04_MAGIC
G04_TAIL = C.G04_TAIL
PG_MAGIC = C.PG_MAGIC
PG_TAIL = C.PG_TAIL
R24_MAGIC = C.R24_MAGIC
POLICY = C.POLICY
FS = C.FS
ProfileNotEligible = C.ProfileNotEligible
UnsupportedArchiveProfile = C.UnsupportedArchiveProfile
MAX_MANIFEST_ENTRIES = C.MAX_MANIFEST_ENTRIES
MAX_PROFILE_FILES = C.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = C.MAX_PROFILE_LOGICAL_BYTES
R24_RELEASE_PACK_CAP_BYTES = 2 * 1024 * 1024
R24_RELEASE_MICRO_MAX_FILE_BYTES = 32 * 1024
G04_PROCESS_MIN_GRAPH_BYTES = 4 * 1024 * 1024
G04_PROCESS_MIN_RECORDS = 18
G04_AUDITION_MAX_WORKERS = 4
# Canonical r24 fallback must obey the same <=8x selected-member locality law as r25. Virtual ZIP/WHL reads can
# otherwise regenerate a small Deflate stream from a much larger raw member when the historical 64 KiB reuse
# cutoff drops that exact stream. Retain every exact Deflate stream in the release fallback so a selected virtual
# archive read consumes compressed representation bytes rather than needlessly decoding its raw constituents.
# This changes only the r24 encoder policy, not revision-24 grammar or reader semantics; exact product-size and
# runtime gates remain authoritative and can reject the policy if its extra stream metadata costs too much.
R24_RELEASE_DEFLATE_REUSE_MIN_BYTES = 0


def _g04_audition_worker(payload):
    """Spawn-safe delegation to the one canonical G0-G4 audition implementation."""
    record_id, record, member_lengths = payload
    from experiments import entropygraph_v030_release_product as child_product

    shared = child_product.C.SHARED
    return shared.G._audition_record(record_id, record, member_lengths)


def _g04_process_pool_eligible(graph_path: Path, graph_records: list) -> bool:
    """Use processes only where the measured GIL win dominates spawn/serialization overhead.

    The promotion oracle established exact-byte material wins on the frozen office and logs substrates at
    11.5 MiB/35 records and 4.7 MiB/18 records respectively.  The lower bound is deliberately anchored at that
    evidence envelope: smaller graphs keep the existing ordered thread scheduler, so this optimization cannot
    impose process startup on tiny workloads that must also beat ZIP/Zstd creation time.
    """
    return len(graph_records) >= G04_PROCESS_MIN_RECORDS and Path(graph_path).stat().st_size >= G04_PROCESS_MIN_GRAPH_BYTES


def _parallel_deferred_overlay(graph_path: Path, overlay_path: Path) -> dict:
    """Run canonical G0-G4 auditions in parallel but verify only if exact bytes can win.

    The shared portfolio's publication law owns strong verification after complete-artifact pricing. An overlay
    that is already >= the accepted v0.29 floor has no route to publication, so decoding its entire logical tree
    beforehand is pure creation latency. A byte-winning overlay is still strong-verified by ``SHARED.build``
    before it can be selected. Scheduling alone changes here: sufficiently large measured substrates use bounded
    spawned processes to escape the CPython GIL, while small substrates retain the cheaper ordered thread path.
    Candidate order, transform decisions, compression levels, bytes and locality rules are unchanged.

    Footnote: canonical-final originally patched the shared overlay helper before the later deferred-verification
    optimization existed. Keeping this release-product binding explicit prevents that older private override from
    silently reintroducing both eager verification and a stale metadata shape.
    """
    shared = C.SHARED
    source_format, _source, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))

    if graph_records and _g04_process_pool_eligible(graph_path, graph_records):
        worker_count = min(G04_AUDITION_MAX_WORKERS, len(graph_records), max(1, os.cpu_count() or 1))
        payloads = [(record_id, record, users[record_id]) for record_id, record in enumerate(graph_records)]
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=worker_count, mp_context=ctx) as pool:
            outcomes = list(pool.map(_g04_audition_worker, payloads, chunksize=1))
        scheduler = "bounded-ordered-spawn-process-pool-v1"
    elif graph_records:
        worker_count = min(G04_AUDITION_MAX_WORKERS, len(graph_records))

        def audition(item):
            record_id, record = item
            return shared.G._audition_record(record_id, record, users[record_id])

        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-v030-g04") as pool:
            outcomes = list(pool.map(audition, enumerate(graph_records)))
        scheduler = "bounded-ordered-thread-pool-v1"
    else:
        worker_count = 0
        outcomes = []
        scheduler = "empty"

    records = [row[0] for row in outcomes]
    transforms = [row[1] for row in outcomes]
    auditions = [row[2] for row in outcomes]
    annotated_meta = dict(graph_meta)
    annotated_meta["overlay_source_format"] = source_format
    write_stats = shared.G._write_overlay(annotated_meta, records, transforms, overlay_path)
    return {
        "source_format": source_format,
        "records": records,
        "transforms": transforms,
        "auditions": auditions,
        "write_stats": write_stats,
        "verified": None,
        "verification_state": "deferred-until-byte-win",
        "audition_workers": worker_count,
        "audition_scheduler": scheduler,
        "audition_process_min_graph_bytes": G04_PROCESS_MIN_GRAPH_BYTES,
        "audition_process_min_records": G04_PROCESS_MIN_RECORDS,
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


# The canonical module's earlier ordered-parallel helper eagerly verified every overlay. Rebind only its private
# shared clone to the current release law: losers skip logical decode; winners are verified inside SHARED.build.
# Historical/research modules remain untouched and therefore continue to serve as independent byte oracles.
C.SHARED._overlay_retained_graph = _parallel_deferred_overlay


def _largest_regular_user_member_bytes(root: Path) -> int:
    """Return the largest regular source member without following links.

    r24 micro-packs are whole compressed frames. A selected read of any packed file therefore decodes the whole
    owning pack. The frozen v0.30 locality contract selects the largest regular user-visible member and allows at
    most 8x decoded context, so the shipping r24 fallback derives its pack budget from that member. This helper
    computes the bound from source shape only; it never predicts compression or selection.
    """
    largest = 0
    for dirpath, dirnames, filenames in os.walk(Path(root), followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                st = os.lstat(path)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                largest = max(largest, int(st.st_size))
    return largest


def _locality_bounded_r24_build(root: Path, out: Path) -> dict:
    """Build exact canonical r24 bytes while deferring logical verification until selection.

    Revision 24 accepts arbitrary micro-pack sizes; 256 KiB was an encoder heuristic, not grammar. The release
    path spends the selected-member locality budget up to the mature reader's 2 MiB decoded-blob cache ceiling:
    ``min(2 MiB, 8 * largest_regular_member)``. It also retains exact Deflate streams at every size so virtual ZIP
    reconstruction does not turn a tiny selected archive into a large raw-content decode.

    The r24 candidate exists first as a byte floor. Verifying it before the r24/r25 tournament is wasted work when
    r25 wins, and duplicated work when r24 wins because canonical-final strongly verifies the selected publication
    before returning. Therefore this function builds exact r24 bytes only; selected-artifact verification remains
    mandatory and unchanged at the parent publication boundary. Historical v0.29 builders remain untouched.
    """
    started = time.perf_counter()
    root = Path(root)
    out = Path(out)
    builder = C.Builder(root, deflate_reuse_min=R24_RELEASE_DEFLATE_REUSE_MIN_BYTES)
    builder.micro_pack_max_file = R24_RELEASE_MICRO_MAX_FILE_BYTES
    default_target = int(builder.micro_pack_target)
    largest_member = _largest_regular_user_member_bytes(root)
    if largest_member > 0:
        builder.micro_pack_target = min(R24_RELEASE_PACK_CAP_BYTES, 8 * largest_member)
    stats = dict(builder.build(out))
    return {
        **stats,
        "archive_bytes": out.stat().st_size,
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "verified_files": None,
        "verification_state": "deferred-to-selected-artifact",
        "create_s": time.perf_counter() - started,
        "micro_pack_target_default_bytes": default_target,
        "micro_pack_target_release_bytes": int(builder.micro_pack_target),
        "micro_pack_max_file_release_bytes": int(builder.micro_pack_max_file),
        "deflate_reuse_min_release_bytes": R24_RELEASE_DEFLATE_REUSE_MIN_BYTES,
        "locality_selected_member_bytes": largest_member,
        "locality_ceiling": 8.0,
        "locality_pack_policy": "min-2mib-cache-cap-or-8x-largest-regular-member-plus-exact-deflate-retention",
        "release_byte_knobs": "environment-independent-r24-v2",
    }


# Manifest capture is a full content-hash pass that r24 does not depend on. Start r24 before that pass so its
# compression work overlaps manifest hashing instead of waiting behind it. The canonical-final build later asks
# for r24 through the same temp-directory key; that call consumes the exact prebuilt artifact and stats. No bytes,
# format grammar, pricing, or selection rule changes—only when independent work begins.
_ORIGINAL_PREPARE_PROFILE_TREE = C._prepare_profile_tree
_R24_PREBUILD_LOCK = threading.Lock()
_R24_PREBUILDS: dict[str, tuple[ThreadPoolExecutor, object, Path]] = {}


def _prebuild_key(path: Path) -> str:
    return os.fspath(Path(path).parent.absolute())


def _prepare_profile_tree_with_r24_overlap(root: Path, staging_root: Path) -> dict:
    staging_root = Path(staging_root)
    key = _prebuild_key(staging_root)
    prebuilt = staging_root.parent / "prebuilt-canonical-r24.cmpct"
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cmpct-v030-r24-prebuild")
    future = executor.submit(_locality_bounded_r24_build, Path(root), prebuilt)
    with _R24_PREBUILD_LOCK:
        if key in _R24_PREBUILDS:
            executor.shutdown(wait=False, cancel_futures=True)
            raise RuntimeError("duplicate canonical r24 prebuild key")
        _R24_PREBUILDS[key] = (executor, future, prebuilt)
    try:
        return _ORIGINAL_PREPARE_PROFILE_TREE(root, staging_root)
    except ProfileNotEligible:
        # Canonical-final immediately falls back to r24 and will consume the in-flight prebuild.
        raise
    except Exception:
        with _R24_PREBUILD_LOCK:
            _R24_PREBUILDS.pop(key, None)
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        prebuilt.unlink(missing_ok=True)
        raise


def _consume_or_build_locality_bounded_r24(root: Path, out: Path) -> dict:
    out = Path(out)
    key = _prebuild_key(out)
    with _R24_PREBUILD_LOCK:
        pending = _R24_PREBUILDS.pop(key, None)
    if pending is None:
        return _locality_bounded_r24_build(root, out)
    executor, future, prebuilt = pending
    try:
        stats = dict(future.result())
        os.replace(prebuilt, out)
        return {
            **stats,
            "archive_bytes": out.stat().st_size,
            "r24_prebuild_overlap": "filesystem-manifest-capture",
            "r24_prebuild_reused": True,
        }
    finally:
        executor.shutdown(wait=True, cancel_futures=False)
        prebuilt.unlink(missing_ok=True)


# Only the promoted release product gets these r24 policies. Historical v0.29 and research builders remain
# byte-stable evidence oracles. Canonical-final resolves both globals at call time, including profile-ineligible
# fallback and the normal concurrent r24-vs-r25 product tournament.
C._prepare_profile_tree = _prepare_profile_tree_with_r24_overlap
C._r24_build = _consume_or_build_locality_bounded_r24


def _revision_for_archive(archive: Path) -> tuple[int | None, str]:
    """Classify only released r24/r25 profiles; research CMPNX remains non-canonical."""
    return C._profile_for_archive(Path(archive))


def _r24_user_tree_sha(reader: CMPCT) -> str:
    """Project a canonical r24 archive onto the same user-tree identity domain used by r25.

    Footnote: the hash intentionally excludes storage layout and mutable metadata. It covers user-visible path,
    kind, regular-file length/content identity and link relation. Therefore a selector may change representation
    or fall back to r24 without changing what ``tree_sha256`` means to release evidence.
    """
    rows = []
    for row in sorted(reader.files, key=lambda item: item[0]):
        rel, kind, _mode, _mtime, size, _digest, storage = row
        if kind == R24_CODEC.K_FILE:
            semantic = [rel, "f", int(size), bytes(reader.file_sha256(rel))]
        elif kind == R24_CODEC.K_DIR:
            semantic = [rel, "d"]
        elif kind == R24_CODEC.K_SYMLINK:
            target = bytes(reader.read(rel)).decode("utf-8", "surrogateescape")
            semantic = [rel, "l", target]
        elif kind == R24_CODEC.K_HARDLINK:
            if not storage or not isinstance(storage[0], str):
                raise RuntimeError(f"malformed r24 hardlink storage for {rel!r}")
            semantic = [rel, "h", storage[0]]
        else:
            raise RuntimeError(f"unknown r24 user entry kind {kind!r} for {rel!r}")
        rows.append(semantic)
    encoded = msgpack.packb(["cmpct-user-tree-v1", rows], use_bin_type=True)
    return hashlib.sha256(encoded).hexdigest()


def treehash(root: Path) -> str:
    return C.treehash(root)


def build(root: Path, out: Path) -> dict:
    return C.build(root, out)


def strong_verify(archive: Path) -> dict:
    archive = Path(archive)
    revision, profile = _revision_for_archive(archive)
    if revision == REVISION:
        return C.strong_verify(archive)
    if revision == 24:
        try:
            with CMPCT(archive) as reader:
                verified_files = reader.verify()
                user_tree_sha = _r24_user_tree_sha(reader)
            return {
                "ok": True,
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "tree_sha256": user_tree_sha,
                "user_tree_sha256": user_tree_sha,
                "verified_files": verified_files,
                "reader": "cmpct-r24-reference-reader",
                "canonical_release_facade": "cmpct-v030-release-product-v1",
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": repr(exc),
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "reader": "cmpct-r24-reference-reader",
            }
    return {
        "ok": False,
        "error": "research-only CMPNX bytes are not canonical r24/r25" if profile == "research-only" else "unknown CMPCT profile",
        "format_revision": None,
        "format_profile": profile,
        "reader": "cmpct-v030-release-product-v1",
    }


def read_member_with_stats(archive: Path, rel: str) -> tuple[bytes, dict]:
    archive = Path(archive)
    revision, profile = _revision_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            raw = bytes(reader.read(rel))
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": None,
            "decoded_context_amplification": None,
            "format_profile": "canonical-r24",
            "locality_accounting": "instrument-at-operation-or-inherited-r24-evidence",
        }
    if revision == REVISION:
        return C.read_member_with_stats(archive, rel)
    raise UnsupportedArchiveProfile(profile)


def read_member(archive: Path, rel: str) -> bytes:
    return read_member_with_stats(archive, rel)[0]


def list_members(archive: Path) -> list[dict]:
    archive = Path(archive)
    revision, profile = _revision_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            names = {
                R24_CODEC.K_FILE: "file",
                R24_CODEC.K_DIR: "directory",
                R24_CODEC.K_SYMLINK: "symlink",
                R24_CODEC.K_HARDLINK: "hardlink",
            }
            return [
                {"path": row[0], "kind": names.get(row[1], "unknown"), "size": int(row[4])}
                for row in reader.files
            ]
    if revision == REVISION:
        return C.list_members(archive)
    raise UnsupportedArchiveProfile(profile)


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    """Extract the shipping product with one authenticated content pass and one transaction.

    Canonical r25 restoration needs an outer transaction because filesystem metadata/hardlinks/symlinks are
    restored after the authenticated content graph is streamed. Calling ``POLICY.extract`` inside that outer
    transaction used to create a second complete temp directory and rename cycle. The release reader now exposes
    the same verified streamer for caller-owned staging, so r25 pays one transaction while retaining identical
    graph authentication, locality/resource checks, metadata restoration, rollback and final publication.

    The verified streamer has also already authenticated every reconstructed regular-file byte. The generic FS
    restorer intentionally re-hashes arbitrary staging trees, but doing so here was a second full content pass.
    The promoted path therefore uses the verified-staging restorer: type/size are checked again, while digest
    identity remains owned by the immediately preceding authenticated stream.
    """
    archive = Path(archive)
    dst = Path(dst)
    revision, profile = _revision_for_archive(archive)
    if revision == 24:
        return C.extract(archive, dst, max_output_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    decoded = C._validated_manifest(archive)
    if safe_symlinks:
        C._validate_safe_symlinks(decoded)
    user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
    if user_bytes > max_output_bytes:
        raise RuntimeError("r25 extraction exceeds caller output budget")

    dst.parent.mkdir(parents=True, exist_ok=True)
    wrapper = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-product-stage-", dir=dst.parent))
    content_root = wrapper / "tree"
    try:
        internal_budget = min(POLICY.R.MAX_DECLARED_LOGICAL_BYTES, max_output_bytes + FS.MAX_MANIFEST_BYTES)
        with C._revision25_profile_context():
            POLICY.extract_verified_into_staging(archive, content_root, max_output_bytes=internal_budget)
        VERIFIED_RESTORE.restore_verified_manifest_tree(content_root, decoded, safe_symlinks=False)
        C._publish_tree(content_root, dst)
    except Exception:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)
        raise
    else:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    return C.build_ablation(root, out, mode)