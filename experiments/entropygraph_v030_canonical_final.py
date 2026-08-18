"""Final CMPCT v0.30 canonical product boundary for revision 25.

This module is the release-facing successor to ``entropygraph_v030_canonical``.  The earlier module remains a
useful integration checkpoint, but it deliberately stays non-authoritative because slot-00 found five product
boundary defects after T03 handoff: r25 was not priced against genuine r24 bytes, public tree identity mixed the
internal graph with the user tree, negative mtimes were self-rejected, safe symlink policy was host-dependent,
and canonical profile identities were installed by process-wide import-time mutation.

The release surface here closes those defects without deleting the research implementations or their notes:

* canonical r24 and r25 candidates are built concurrently and exact complete bytes decide publication; ties keep
  r24;
* ``tree_sha256`` is a stable user-visible semantic-tree identity, while ``content_graph_tree_sha256`` and
  ``filesystem_manifest_sha256`` remain explicit independent identities;
* filesystem mtimes accept bounded signed i64 nanoseconds;
* safe symlink admission is checked against both POSIX and Windows lexical rules before materialization;
* revision-25 profile binding is operation-scoped, serialized and restored.  Importing this module never mutates
  research-module magic values.  Direct research modules are not part of the promoted concurrent API.

Footnote: the profile lock is intentionally coarse.  The expensive r24 build still runs concurrently with the
r25 tournament, but two promoted r25 writer/reader operations never observe partially rebound research globals.
This is safer than making import order part of archive semantics, and it preserves the single-sourced transform
implementations until the post-v0.30 cleanup can parameterize their profile descriptors directly.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import tempfile
import threading
import time
import uuid

import msgpack

from cmpct import codec as R24_CODEC
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from experiments import entropygraph_v030_geometry_overlay_g04 as G04_RESEARCH
from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_admission as ADMISSION
from experiments import entropygraph_v030_release_candidate as RC
from experiments import entropygraph_v030_release_reader_policy as POLICY
from experiments import entropygraph_v030_shared_portfolio as SHARED

REVISION = 25
G04_MAGIC = b"CMP25G4\0"
G04_TAIL = b"C25G4TL\0"
PG_MAGIC = b"CMP25PG\0"
PG_TAIL = b"C25PGTL\0"
R24_MAGIC = R24_CODEC.MAGIC
MAX_PROFILE_FILES = min(POLICY.R.MAX_FILES - 1, 65_535)
MAX_PROFILE_LOGICAL_BYTES = POLICY.R.MAX_DECLARED_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = POLICY.R.MAX_FILES
MIN_I64 = -(1 << 63)
MAX_I64 = (1 << 63) - 1

if not all(len(value) == 8 for value in (G04_MAGIC, G04_TAIL, PG_MAGIC, PG_TAIL, R24_MAGIC)):
    raise RuntimeError("canonical CMPCT profile magics must remain exactly eight bytes")


class UnsupportedArchiveProfile(RuntimeError):
    """Input bytes are not a canonical r24/r25 product archive."""


ProfileNotEligible = FS.ProfileNotEligible
_PROFILE_LOCK = threading.RLock()


def _snapshot_profile_globals() -> dict[str, object]:
    return {
        "g04_mag": G04_RESEARCH.MAG,
        "g04_tail": G04_RESEARCH.TAIL,
        "shared_mag": SHARED.MAG,
        "shared_tail": SHARED.TAIL,
        "pg_magic": PG.MAGIC,
        "pg_tail": PG.TAIL,
        "reader_g04_mag": POLICY.R.G04.MAG,
        "reader_g04_tail": POLICY.R.G04.TAIL,
        "reader_pg_magic": POLICY.R.PG.MAGIC,
        "reader_pg_tail": POLICY.R.PG.TAIL,
        "rc_g04": RC.G04,
        "rc_eligibility": RC._prefixgraph_eligibility,
        "rc_locality": RC._prefixgraph_locality,
    }


def _install_profile_globals() -> None:
    G04_RESEARCH.MAG = G04_MAGIC
    G04_RESEARCH.TAIL = G04_TAIL
    SHARED.MAG = G04_MAGIC
    SHARED.TAIL = G04_TAIL
    PG.MAGIC = PG_MAGIC
    PG.TAIL = PG_TAIL
    POLICY.R.G04.MAG = G04_MAGIC
    POLICY.R.G04.TAIL = G04_TAIL
    POLICY.R.PG.MAGIC = PG_MAGIC
    POLICY.R.PG.TAIL = PG_TAIL
    RC.G04 = SHARED
    RC._prefixgraph_eligibility = ADMISSION.prefixgraph_eligibility
    RC._prefixgraph_locality = ADMISSION.prefixgraph_locality


def _restore_profile_globals(state: dict[str, object]) -> None:
    G04_RESEARCH.MAG = state["g04_mag"]
    G04_RESEARCH.TAIL = state["g04_tail"]
    SHARED.MAG = state["shared_mag"]
    SHARED.TAIL = state["shared_tail"]
    PG.MAGIC = state["pg_magic"]
    PG.TAIL = state["pg_tail"]
    POLICY.R.G04.MAG = state["reader_g04_mag"]
    POLICY.R.G04.TAIL = state["reader_g04_tail"]
    POLICY.R.PG.MAGIC = state["reader_pg_magic"]
    POLICY.R.PG.TAIL = state["reader_pg_tail"]
    RC.G04 = state["rc_g04"]
    RC._prefixgraph_eligibility = state["rc_eligibility"]
    RC._prefixgraph_locality = state["rc_locality"]


@contextmanager
def _revision25_profile_context():
    """Bind r25 identities for one promoted operation, then restore every research global.

    Footnote: all promoted r25 operations enter the same re-entrant lock.  Therefore canonical callers cannot
    overlap one operation's temporary profile descriptor with another operation or with its own nested verify.
    Research modules remain callable for experiments, but concurrent direct research calls are explicitly not a
    supported product API and cannot define released semantics.
    """
    with _PROFILE_LOCK:
        state = _snapshot_profile_globals()
        _install_profile_globals()
        try:
            yield
        finally:
            _restore_profile_globals(state)


def _magic(archive: Path) -> bytes:
    with Path(archive).open("rb") as stream:
        return stream.read(8)


def _profile_for_archive(archive: Path) -> tuple[int | None, str]:
    magic = _magic(archive)
    if magic == G04_MAGIC:
        return REVISION, "geometry-g04"
    if magic == PG_MAGIC:
        return REVISION, "prefixgraph-depth1"
    if magic == R24_MAGIC:
        return 24, "canonical-r24"
    if magic.startswith(b"CMPNX"):
        return None, "research-only"
    return None, "unknown"


def _prepare_profile_tree(root: Path, staging_root: Path) -> dict:
    prepared = FS.prepare_profile_tree(
        root,
        staging_root,
        max_path_bytes=POLICY.R.MAX_PATH_BYTES,
        max_profile_files=MAX_PROFILE_FILES,
        max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
    )
    if int(prepared["entries"]) > MAX_MANIFEST_ENTRIES:
        raise ProfileNotEligible("r25 filesystem manifest entry count exceeds reader policy")
    return prepared


def _safe_relpath_manifest(rel: object) -> str:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe r25 filesystem manifest path")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe r25 filesystem manifest path")
    encoded = rel.encode("utf-8", "surrogateescape")
    if len(encoded) > POLICY.R.MAX_PATH_BYTES:
        raise RuntimeError("r25 filesystem manifest path exceeds policy")
    if rel == FS.INTERNAL_ROOT or rel.startswith(FS.INTERNAL_ROOT + "/"):
        raise RuntimeError("r25 user manifest collides with reserved namespace")
    return rel


def _decode_manifest(raw: bytes) -> dict:
    """Decode the authenticated product manifest with signed-time and bounded declarations."""
    if not isinstance(raw, bytes) or len(raw) > FS.MAX_MANIFEST_BYTES:
        raise RuntimeError("r25 filesystem manifest exceeds policy")
    try:
        manifest = msgpack.unpackb(
            raw,
            raw=False,
            strict_map_key=False,
            max_array_len=MAX_MANIFEST_ENTRIES * 8 + 1024,
            max_map_len=32,
            max_str_len=POLICY.R.MAX_PATH_BYTES,
            max_bin_len=FS.MAX_MANIFEST_BYTES,
        )
    except (ValueError, TypeError, msgpack.ExtraData, msgpack.FormatError, msgpack.StackError) as exc:
        raise RuntimeError("invalid bounded r25 filesystem manifest") from exc
    if not isinstance(manifest, dict) or manifest.get("v") != FS.FILESYSTEM_MANIFEST_VERSION:
        raise RuntimeError("unsupported r25 filesystem manifest version")
    if manifest.get("profile") != "cmpct-r25-filesystem-manifest-v1":
        raise RuntimeError("unsupported r25 filesystem manifest profile")
    if manifest.get("internal_path") != FS.FILESYSTEM_MANIFEST:
        raise RuntimeError("r25 filesystem manifest internal-path mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) > MAX_MANIFEST_ENTRIES:
        raise RuntimeError("r25 filesystem manifest entry-count declaration")

    seen: set[str] = set()
    regular: dict[str, tuple[int, bytes]] = {}
    hardlinks: dict[str, str] = {}
    for row in entries:
        if not isinstance(row, list) or len(row) != 8:
            raise RuntimeError("malformed r25 filesystem manifest entry")
        rel, kind, mode, mtime_ns, uid, gid, xattrs, extra = row
        rel = _safe_relpath_manifest(rel)
        if rel in seen:
            raise RuntimeError("duplicate r25 filesystem manifest path")
        if kind not in ("f", "d", "l", "h"):
            raise RuntimeError("unknown r25 filesystem manifest entry kind")
        if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
            raise RuntimeError("r25 filesystem mode declaration")
        if not isinstance(mtime_ns, int) or isinstance(mtime_ns, bool) or not MIN_I64 <= mtime_ns <= MAX_I64:
            # Footnote: POSIX timestamps before 1970 are valid signed values.  The writer already captures
            # ``st_mtime_ns`` as signed; rejecting negatives here would make the writer emit self-unreadable bytes.
            raise RuntimeError("r25 filesystem mtime declaration")
        for value, label in ((uid, "uid"), (gid, "gid")):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise RuntimeError(f"r25 filesystem {label} declaration")
        if not isinstance(xattrs, list):
            raise RuntimeError("r25 filesystem xattr declaration")
        for item in xattrs:
            if (
                not isinstance(item, list)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], bytes)
            ):
                raise RuntimeError("r25 filesystem xattr item")
        if kind == "f":
            if (
                not isinstance(extra, list)
                or len(extra) != 2
                or not isinstance(extra[0], int)
                or isinstance(extra[0], bool)
                or extra[0] < 0
                or not isinstance(extra[1], bytes)
                or len(extra[1]) != 32
            ):
                raise RuntimeError("r25 regular-file identity declaration")
            regular[rel] = (int(extra[0]), bytes(extra[1]))
        elif kind == "d":
            if extra is not None:
                raise RuntimeError("r25 directory carries unexpected payload")
        elif kind == "l":
            if not isinstance(extra, str) or "\x00" in extra:
                raise RuntimeError("r25 symlink target declaration")
        else:
            if not isinstance(extra, str) or extra not in regular:
                raise RuntimeError("r25 hardlink target must be an earlier regular-file owner")
            hardlinks[rel] = extra
        seen.add(rel)
    return {"raw": raw, "manifest": manifest, "regular": regular, "hardlinks": hardlinks}


def _safe_symlink_target(target: str) -> bool:
    """Return true only when target cannot lexically escape under POSIX *or* Windows parsing."""
    if not isinstance(target, str) or not target or "\x00" in target:
        return False
    posix = PurePosixPath(target)
    windows = PureWindowsPath(target)
    if posix.is_absolute() or windows.is_absolute() or windows.drive or windows.root:
        return False
    # Backslash is a separator on Windows and slash is accepted there too.  Normalizing both spellings before
    # component inspection makes safety independent of the host that happens to verify the archive first.
    normalized = target.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    return not any(part in ("..", "") for part in parts)


def _semantic_tree_sha(decoded: dict) -> str:
    """Hash the user-visible path/kind/content relation, independent of internal graph representation."""
    rows = []
    for row in sorted(decoded["manifest"]["entries"], key=lambda item: item[0]):
        rel, kind, _mode, _mtime, _uid, _gid, _xattrs, extra = row
        if kind == "f":
            semantic = [rel, kind, int(extra[0]), bytes(extra[1])]
        elif kind in ("l", "h"):
            semantic = [rel, kind, str(extra)]
        else:
            semantic = [rel, kind]
        rows.append(semantic)
    encoded = msgpack.packb(["cmpct-user-tree-v1", rows], use_bin_type=True)
    return hashlib.sha256(encoded).hexdigest()


def treehash(root: Path) -> str:
    """Return the canonical user-visible semantic-tree identity for an r25-eligible source tree."""
    root = Path(root)
    raw, _regular, _stats = FS.capture_filesystem_manifest(
        root,
        max_path_bytes=POLICY.R.MAX_PATH_BYTES,
        max_profile_files=MAX_PROFILE_FILES,
        max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
        max_entries=MAX_MANIFEST_ENTRIES,
    )
    return _semantic_tree_sha(_decode_manifest(raw))


def _read_g04_member(archive: Path, rel: str) -> tuple[bytes, dict]:
    with _revision25_profile_context():
        session = POLICY.R._G04Session(archive)
        try:
            desc = session.meta["files"].get(rel)
            if desc is None:
                raise KeyError(rel)
            decoded_context = 0
            if desc[0] == "preflate":
                raw = session.record(int(desc[1]))
                decoded_context = len(raw)
            elif desc[0] == "nodes":
                chunks = [session.node(int(node_id)) for node_id in desc[1]]
                raw = b"".join(chunks)
                decoded_context = sum(len(chunk) for chunk in chunks)
            else:
                raise RuntimeError("unknown G0-G4 file descriptor")
            if len(raw) != int(desc[2]) or hashlib.sha256(raw).digest() != bytes(desc[3]):
                raise RuntimeError("G0-G4 member integrity mismatch")
            return raw, {
                "logical_bytes": len(raw),
                "decoded_context_bytes": decoded_context,
                "decoded_context_amplification": decoded_context / max(1, len(raw)),
                "format_profile": "geometry-g04",
            }
        finally:
            session.close()


def _read_pg_member(archive: Path, rel: str) -> tuple[bytes, dict]:
    with _revision25_profile_context():
        session = POLICY.R._PGSession(archive)
        try:
            try:
                index = session.meta["files"].index(rel)
            except ValueError as exc:
                raise KeyError(rel) from exc
            desc = session.records[index]
            raw = session.file(index)
            if desc[0] == "prefix":
                base = int(desc[1])
                decoded_context = len(raw) + int(session.records[base][2])
            else:
                decoded_context = len(raw)
            amp = decoded_context / max(1, len(raw))
            if not math.isfinite(amp) or amp > 8.0:
                raise RuntimeError("PrefixGraph member read exceeds canonical locality ceiling")
            return raw, {
                "logical_bytes": len(raw),
                "decoded_context_bytes": decoded_context,
                "decoded_context_amplification": amp,
                "format_profile": "prefixgraph-depth1",
            }
        finally:
            session.close()


def _read_profile_member(archive: Path, rel: str) -> tuple[bytes, dict]:
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    if profile == "geometry-g04":
        return _read_g04_member(archive, rel)
    if profile == "prefixgraph-depth1":
        return _read_pg_member(archive, rel)
    raise UnsupportedArchiveProfile(profile)


def _profile_content_identities(archive: Path) -> dict[str, tuple[int, bytes]]:
    revision, profile = _profile_for_archive(archive)
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    with _revision25_profile_context():
        if profile == "geometry-g04":
            session = POLICY.R._G04Session(archive)
            try:
                return {rel: (int(desc[2]), bytes(desc[3])) for rel, desc in session.meta["files"].items()}
            finally:
                session.close()
        session = POLICY.R._PGSession(archive)
        try:
            return {
                rel: (int(desc[2]), bytes(desc[5]))
                for rel, desc in zip(session.meta["files"], session.records, strict=True)
            }
        finally:
            session.close()


def _validated_manifest(archive: Path) -> dict:
    raw, _stats = _read_profile_member(archive, FS.FILESYSTEM_MANIFEST)
    decoded = _decode_manifest(raw)
    content = _profile_content_identities(archive)
    expected_paths = set(decoded["regular"]) | {FS.FILESYSTEM_MANIFEST}
    if set(content) != expected_paths:
        raise RuntimeError("r25 content profile and filesystem manifest disagree on logical members")
    if content[FS.FILESYSTEM_MANIFEST] != (len(raw), hashlib.sha256(raw).digest()):
        raise RuntimeError("r25 filesystem manifest graph identity mismatch")
    for rel, identity in decoded["regular"].items():
        if content.get(rel) != identity:
            raise RuntimeError(f"r25 manifest/content identity mismatch: {rel}")
    return decoded


def _r24_build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    stats = dict(Builder(Path(root)).build(Path(out)))
    with CMPCT(out) as reader:
        verified_files = reader.verify()
    return {
        **stats,
        "archive_bytes": Path(out).stat().st_size,
        "format_revision": 24,
        "format_profile": "canonical-r24",
        "verified_files": verified_files,
        "create_s": time.perf_counter() - started,
    }


def _r25_build(staged_root: Path, out: Path) -> dict:
    started = time.perf_counter()
    with _revision25_profile_context():
        stats = dict(RC.build(staged_root, out))
    return {**stats, "create_s": time.perf_counter() - started}


def _publish_atomic(source: Path, out: Path) -> None:
    size = source.stat().st_size
    os.replace(source, out)
    if out.stat().st_size != size:
        raise RuntimeError("canonical publication changed selected archive size")


def build(root: Path, out: Path) -> dict:
    """Build exact canonical r24 and r25 candidates concurrently; publish the smaller complete artifact."""
    started = time.perf_counter()
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-final-", dir=out.parent) as td:
        temp = Path(td)
        r24_path = temp / "canonical-r24.cmpct"
        r25_path = temp / "candidate-r25-or-research.cmpct"
        staged = temp / "profile-tree"
        try:
            prepared = _prepare_profile_tree(root, staged)
            source_tree_sha = _semantic_tree_sha(_decode_manifest(prepared["manifest_raw"]))
        except ProfileNotEligible as exc:
            r24_stats = _r24_build(root, r24_path)
            _publish_atomic(r24_path, out)
            verified = strong_verify(out)
            return {
                "selected": "r24-fallback",
                "archive_bytes": out.stat().st_size,
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "r24_product_bytes": out.stat().st_size,
                "r25_product_bytes": None,
                "r25_attempted": False,
                "r25_reject_reason": str(exc),
                "r24": r24_stats,
                "final_strong_verify": verified,
                "portfolio_create_s": time.perf_counter() - started,
                "release_facade": "cmpct-v030-canonical-final-v1",
            }

        # Product-floor correctness and create-time discipline are compatible: run the genuine r24 floor in
        # parallel with the r25 tournament, then compare exact finished artifacts.  No approximate estimate may
        # authorize r25 publication, and exact ties conservatively retain r24.
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="cmpct-v030-product") as pool:
            r24_future = pool.submit(_r24_build, root, r24_path)
            r25_future = pool.submit(_r25_build, staged, r25_path)
            r24_stats = r24_future.result()
            r25_stats = r25_future.result()

        r24_bytes = r24_path.stat().st_size
        r25_revision, r25_profile = _profile_for_archive(r25_path)
        r25_bytes = r25_path.stat().st_size if r25_revision == REVISION else None
        v029_floor = int(r25_stats.get("v029_bytes", r25_path.stat().st_size))
        r25_eligible = bool(
            r25_revision == REVISION
            and r25_bytes is not None
            and r25_bytes < v029_floor
            and r25_bytes < r24_bytes
        )
        if r25_eligible:
            _publish_atomic(r25_path, out)
            selected = str(r25_stats.get("selected", r25_profile))
        else:
            _publish_atomic(r24_path, out)
            selected = "r24-fallback"

        final_revision, final_profile = _profile_for_archive(out)
        verified = strong_verify(out)
        if not verified.get("ok"):
            raise RuntimeError(f"canonical v0.30 publication failed strong verification: {verified!r}")
        if final_revision == REVISION and verified.get("tree_sha256") != source_tree_sha:
            raise RuntimeError("published r25 user-tree identity differs from the source tree")
        if final_revision not in (24, REVISION):
            raise RuntimeError("canonical v0.30 product published a non-canonical profile")

        return {
            "selected": selected,
            "archive_bytes": out.stat().st_size,
            "format_revision": final_revision,
            "format_profile": final_profile,
            "r24_product_bytes": r24_bytes,
            "r25_product_bytes": r25_bytes,
            "r25_attempted": True,
            "r25_candidate_profile": r25_profile,
            "r25_candidate_is_canonical": r25_revision == REVISION,
            "r25_strictly_smaller_than_r24": bool(r25_bytes is not None and r25_bytes < r24_bytes),
            "r25_strictly_smaller_than_v029_research_floor": bool(
                r25_bytes is not None and r25_bytes < v029_floor
            ),
            "tie_policy": "r24-wins",
            "v029_research_floor_bytes": v029_floor,
            "tree_sha256": source_tree_sha,
            "filesystem_manifest_sha256": prepared["manifest_sha256"],
            "filesystem_manifest_bytes": prepared["manifest_bytes"],
            "filesystem_manifest_entries": prepared["entries"],
            "regular_graph_members": prepared["regular_graph_members"],
            "r24": r24_stats,
            "r25": r25_stats,
            "final_strong_verify": verified,
            "portfolio_create_s": time.perf_counter() - started,
            "release_facade": "cmpct-v030-canonical-final-v1",
            "claim_boundary": (
                "canonical r25 publishes only when exact complete r25 bytes strictly beat both the accepted-v0.29 "
                "research floor and a genuine concurrently built canonical-r24 archive for the same user tree"
            ),
        }


def strong_verify(archive: Path) -> dict:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == REVISION:
        with _revision25_profile_context():
            base = dict(POLICY.strong_verify(archive))
        if not base.get("ok"):
            return {**base, "format_revision": revision, "format_profile": profile}
        try:
            manifest = _validated_manifest(archive)
            # Re-read each regular member through the selected representation.  The manifest identities prove
            # membership, while this pass proves the graph actually reconstructs the declared logical bytes.
            for rel, (size, digest) in manifest["regular"].items():
                raw, stats = _read_profile_member(archive, rel)
                if len(raw) != size or hashlib.sha256(raw).digest() != digest:
                    raise RuntimeError(f"r25 user member verification failed: {rel}")
                if stats["decoded_context_amplification"] > 8.0:
                    raise RuntimeError(f"r25 member locality ceiling exceeded: {rel}")
            user_tree = _semantic_tree_sha(manifest)
        except Exception as exc:
            return {
                "ok": False,
                "error": repr(exc),
                "format_revision": revision,
                "format_profile": profile,
                "reader": "cmpct-v030-canonical-final-v1",
            }
        return {
            **base,
            "content_graph_tree_sha256": base.get("tree_sha256"),
            "tree_sha256": user_tree,
            "user_tree_sha256": user_tree,
            "format_revision": revision,
            "format_profile": profile,
            "filesystem_manifest_sha256": hashlib.sha256(manifest["raw"]).hexdigest(),
            "filesystem_entries": len(manifest["manifest"]["entries"]),
            "filesystem_semantics_verified": True,
            "canonical_release_facade": "cmpct-v030-canonical-final-v1",
        }
    if revision == 24:
        try:
            with CMPCT(archive) as reader:
                files = reader.verify()
            return {
                "ok": True,
                "format_revision": 24,
                "format_profile": "canonical-r24",
                "verified_files": files,
                "reader": "cmpct-r24-reference-reader",
                "canonical_release_facade": "cmpct-v030-canonical-final-v1",
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
        "reader": "cmpct-v030-canonical-final-v1",
    }


def read_member_with_stats(archive: Path, rel: str) -> tuple[bytes, dict]:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            raw = bytes(reader.read(rel))
        # r24 decoded-context observability belongs to the mature native/core accounting path.  Do not invent a
        # precise synthetic 1.0x when the stored representation may decode more context than the requested file.
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": None,
            "decoded_context_amplification": None,
            "format_profile": "canonical-r24",
            "locality_accounting": "inherited-r24-evidence",
        }
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    decoded = _validated_manifest(archive)
    rows = {row[0]: row for row in decoded["manifest"]["entries"]}
    row = rows.get(rel)
    if row is None:
        raise KeyError(rel)
    kind = row[1]
    if kind == "d":
        raise IsADirectoryError(rel)
    if kind == "l":
        raw = row[7].encode("utf-8", "surrogateescape")
        return raw, {
            "logical_bytes": len(raw),
            "decoded_context_bytes": len(raw),
            "decoded_context_amplification": 1.0,
            "format_profile": profile,
            "member_kind": "symlink",
        }
    if kind == "h":
        raw, stats = read_member_with_stats(archive, row[7])
        return raw, {**stats, "member_kind": "hardlink", "hardlink_owner": row[7]}
    raw, stats = _read_profile_member(archive, rel)
    return raw, {**stats, "member_kind": "file"}


def read_member(archive: Path, rel: str) -> bytes:
    return read_member_with_stats(archive, rel)[0]


def list_members(archive: Path) -> list[dict]:
    archive = Path(archive)
    revision, profile = _profile_for_archive(archive)
    if revision == 24:
        with CMPCT(archive) as reader:
            kind_names = {
                R24_CODEC.K_FILE: "file",
                R24_CODEC.K_DIR: "directory",
                R24_CODEC.K_SYMLINK: "symlink",
                R24_CODEC.K_HARDLINK: "hardlink",
            }
            return [
                {"path": row[0], "kind": kind_names.get(row[1], "unknown"), "size": int(row[4])}
                for row in reader.files
            ]
    if revision != REVISION:
        raise UnsupportedArchiveProfile(profile)
    decoded = _validated_manifest(archive)
    names = {"f": "file", "d": "directory", "l": "symlink", "h": "hardlink"}
    result = []
    for row in decoded["manifest"]["entries"]:
        size = int(row[7][0]) if row[1] == "f" else 0
        result.append({"path": row[0], "kind": names[row[1]], "size": size})
    return result


def _validate_safe_symlinks(decoded: dict) -> None:
    for row in decoded["manifest"]["entries"]:
        if row[1] == "l" and not _safe_symlink_target(row[7]):
            raise RuntimeError(f"unsafe r25 symlink target in {row[0]!r}")


def _remove_backup_best_effort(backup: Path) -> None:
    try:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink(missing_ok=True)
    except OSError:
        pass


def _publish_tree(staging: Path, dst: Path) -> None:
    backup = dst.parent / f".{dst.name}.cmpct-v030-backup-{uuid.uuid4().hex}"
    moved_old = False
    installed = False
    try:
        if dst.exists() or dst.is_symlink():
            os.replace(dst, backup)
            moved_old = True
        os.replace(staging, dst)
        installed = True
    except Exception:
        if moved_old and not (dst.exists() or dst.is_symlink()) and (backup.exists() or backup.is_symlink()):
            os.replace(backup, dst)
        raise
    else:
        if moved_old:
            _remove_backup_best_effort(backup)
    finally:
        if not installed and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def extract(
    archive: Path,
    dst: Path,
    *,
    max_output_bytes: int = POLICY.DEFAULT_MAX_EXTRACT_BYTES,
    safe_symlinks: bool = True,
) -> None:
    archive = Path(archive)
    dst = Path(dst)
    revision, profile = _profile_for_archive(archive)
    if revision not in (24, REVISION):
        raise UnsupportedArchiveProfile(profile)
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes < 1:
        raise ValueError("max_output_bytes must be a positive integer")

    dst.parent.mkdir(parents=True, exist_ok=True)
    wrapper = Path(tempfile.mkdtemp(prefix=f".{dst.name}.cmpct-v030-stage-", dir=dst.parent))
    publish_root = wrapper
    try:
        if revision == 24:
            with CMPCT(archive) as reader:
                reader.extractall(wrapper, max_bytes=max_output_bytes, safe_symlinks=safe_symlinks)
        else:
            decoded = _validated_manifest(archive)
            if safe_symlinks:
                _validate_safe_symlinks(decoded)
            content_root = wrapper / "tree"
            internal_budget = min(POLICY.R.MAX_DECLARED_LOGICAL_BYTES, max_output_bytes + FS.MAX_MANIFEST_BYTES)
            with _revision25_profile_context():
                POLICY.extract(archive, content_root, max_output_bytes=internal_budget)
            # We already validated against both platform grammars.  Disable the older host-POSIX-only check so
            # materialization does not disagree with the stronger release policy.
            FS.restore_manifest_tree(content_root, decoded, safe_symlinks=False)
            user_bytes = sum(int(identity[0]) for identity in decoded["regular"].values())
            if user_bytes > max_output_bytes:
                raise RuntimeError("r25 extraction exceeds caller output budget")
            publish_root = content_root
        _publish_tree(publish_root, dst)
    except Exception:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)
        raise
    else:
        if wrapper.exists():
            shutil.rmtree(wrapper, ignore_errors=True)


def build_ablation(root: Path, out: Path, mode: str) -> dict:
    """Retain T03's same-substrate causal hooks without making them product-floor authority."""
    root = Path(root)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-final-ablation-", dir=out.parent) as td:
        staged = Path(td) / "tree"
        prepared = _prepare_profile_tree(root, staged)
        with _revision25_profile_context():
            if mode == "v029":
                stats = dict(G04_RESEARCH.BASE.build(staged, out))
            elif mode == "geometry":
                stats = dict(SHARED.build(staged, out))
            elif mode == "prefixgraph":
                expected = PG.treehash(staged)
                eligible, reason = ADMISSION.prefixgraph_eligibility(staged, expected)
                if not eligible:
                    raise ProfileNotEligible(f"PrefixGraph ablation rejected: {reason}")
                stats = dict(PG.build(staged, out))
                locality = ADMISSION.prefixgraph_locality(out)
                if not locality.get("passed"):
                    raise ProfileNotEligible("PrefixGraph ablation exceeded locality ceiling")
                stats["prefixgraph_locality"] = locality
            elif mode == "combined":
                stats = dict(RC.build(staged, out))
            else:
                raise ValueError(f"unknown v0.30 ablation mode: {mode}")
        return {
            **stats,
            "ablation": mode,
            "filesystem_manifest_sha256": prepared["manifest_sha256"],
            "filesystem_manifest_bytes": prepared["manifest_bytes"],
            "canonical_publication": False,
        }


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 final canonical r25/r24 product surface")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    p = sub.add_parser("list"); p.add_argument("archive", type=Path)
    p = sub.add_parser("read"); p.add_argument("archive", type=Path); p.add_argument("member"); p.add_argument("--output", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path); p.add_argument("--max-output-bytes", type=int, default=POLICY.DEFAULT_MAX_EXTRACT_BYTES); p.add_argument("--unsafe-symlinks", action="store_true")
    p = sub.add_parser("ablate"); p.add_argument("mode", choices=("v029", "geometry", "prefixgraph", "combined")); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "verify":
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))
    elif args.cmd == "list":
        print(json.dumps(list_members(args.archive), indent=2, default=str))
    elif args.cmd == "read":
        raw = read_member(args.archive, args.member)
        if args.output is None:
            os.write(1, raw)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(raw)
    elif args.cmd == "extract":
        extract(args.archive, args.destination, max_output_bytes=args.max_output_bytes, safe_symlinks=not args.unsafe_symlinks)
        print(json.dumps({"ok": True}, indent=2))
    else:
        print(json.dumps(build_ablation(args.source, args.archive, args.mode), indent=2, default=str))


if __name__ == "__main__":
    _main()
