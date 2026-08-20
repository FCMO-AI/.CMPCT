"""CMPCT v0.30 release product front door.

This is the one promoted Python product surface for v0.30. It delegates revision-25 implementation to
``entropygraph_v030_canonical_final`` and the mature revision-24 compatibility path to ``cmpct.reader.CMPCT``.
The distinction matters because release evidence must describe one user tree consistently even when the exact
product selector conservatively falls back to r24.

Research/checkpoint modules remain importable for ablation and historical evidence, but release workflows and
public product operations should import this module.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import shutil
import tempfile

import msgpack

from cmpct.reader import CMPCT
from cmpct import codec as R24_CODEC
from experiments import entropygraph_v030_canonical_final as C

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


def _parallel_deferred_overlay(graph_path: Path, overlay_path: Path) -> dict:
    """Run canonical G0-G4 auditions in parallel but verify only if exact bytes can win.

    The shared portfolio's publication law owns strong verification after complete-artifact pricing. An overlay
    that is already >= the accepted v0.29 floor has no route to publication, so decoding its entire logical tree
    beforehand is pure creation latency. A byte-winning overlay is still strong-verified by ``SHARED.build``
    before it can be selected. This preserves the bounded ordered audition schedule and exact transform bytes.

    Footnote: canonical-final originally patched the shared overlay helper before the later deferred-verification
    optimization existed. Keeping this release-product binding explicit prevents that older private override from
    silently reintroducing both eager verification and a stale metadata shape.
    """
    shared = C.SHARED
    source_format, _source, graph_meta, graph_records = shared.strict._read_source_records(graph_path)
    users = shared.O._record_member_lengths(graph_meta, len(graph_records))

    def audition(item):
        record_id, record = item
        return shared.G._audition_record(record_id, record, users[record_id])

    if graph_records:
        worker_count = min(4, len(graph_records))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="cmpct-v030-g04") as pool:
            outcomes = list(pool.map(audition, enumerate(graph_records)))
    else:
        worker_count = 0
        outcomes = []

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
        "audition_scheduler": "bounded-ordered-thread-pool-v1",
        "delimiter_transpose": "bulk-rectangular-prefix-v1",
    }


# The canonical module's earlier ordered-parallel helper eagerly verified every overlay. Rebind only its private
# shared clone to the current release law: losers skip logical decode; winners are verified inside SHARED.build.
# Historical/research modules remain untouched and therefore continue to serve as independent byte oracles.
C.SHARED._overlay_retained_graph = _parallel_deferred_overlay


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
    """Extract the shipping product with one transactional publication boundary.

    Canonical r25 restoration needs an outer transaction because filesystem metadata/hardlinks/symlinks are
    restored after the authenticated content graph is streamed. Calling ``POLICY.extract`` inside that outer
    transaction used to create a second complete temp directory and rename cycle. The release reader now exposes
    the same verified streamer for caller-owned staging, so r25 pays one transaction while retaining identical
    graph authentication, locality/resource checks, metadata restoration, rollback and final publication.
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
        # The graph streamer has already authenticated every reconstructed byte and the decoded manifest was
        # cross-bound to those graph identities above. FS remains the sole owner of metadata/link restoration.
        FS.restore_manifest_tree(content_root, decoded, safe_symlinks=False)
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
