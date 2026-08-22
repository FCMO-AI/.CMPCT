from __future__ import annotations

"""Bounded r25-candidate wrapper for the strongest EntropyGraph-v0.25 representation.

This module is intentionally *not* wired into the release selector. It gives the office/analytics
productization campaign its own reader-visible identity and an operation-derived locality audit instead of
crediting research-only ``CMPNX5`` bytes. The underlying representation logic is reused while it is being
factored into a production implementation; native/Android dispatch and release receipts remain forbidden.

The candidate pays canonical filesystem staging, uses a dedicated 8-byte primary/tail identity, caps every
internal Zstd request at level 1, authenticates both metadata copies and every physical pack through the inherited
strong verifier, and verifies the restored canonical user tree after extraction.
"""

from contextlib import contextmanager
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import threading

from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_release_product_base as BASE

MAGIC = b"C25EG01\0"
TAIL_MAGIC = b"C25EG1T\0"
LEVEL_CAP = 1
MAX_PATH_BYTES = 4096
MAX_PROFILE_FILES = BASE.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = BASE.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = BASE.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_MEMBER_AMPLIFICATION = 8.0
_LOCK = threading.RLock()


def _treehash(root: Path) -> str:
    return BASE.treehash(root)


@contextmanager
def _engine(archive: Path, profile: Path | None = None):
    """Isolate the research engine's historical globals behind one process-local lock."""
    with _LOCK:
        old = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)
        original_zc = V25.zc
        V25.OUT = archive
        if profile is not None:
            V25.ROOT = profile
        V25.MAG = MAGIC
        V25.TAIL = TAIL_MAGIC

        def capped(raw: bytes, level: int = 19) -> bytes:
            return original_zc(raw, min(int(level), LEVEL_CAP))

        V25.zc = capped
        try:
            yield
        finally:
            V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc = old


def _restore_profile(profile: Path) -> dict:
    manifest = profile.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    if not manifest.is_file() or manifest.is_symlink():
        raise RuntimeError("candidate omitted authenticated filesystem manifest")
    decoded = FS.decode_manifest(
        manifest.read_bytes(), max_path_bytes=MAX_PATH_BYTES, max_entries=MAX_MANIFEST_ENTRIES
    )
    FS.restore_manifest_tree(profile, decoded)
    return decoded


def build(source: Path, archive: Path) -> dict:
    """Build a dedicated candidate-profile archive and strongly verify it before returning."""
    source = source.resolve()
    archive = archive.resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg01-build-") as td:
        profile = Path(td) / "profile"
        fs = FS.prepare_profile_tree(
            source,
            profile,
            max_path_bytes=MAX_PATH_BYTES,
            max_profile_files=MAX_PROFILE_FILES,
            max_profile_logical_bytes=MAX_PROFILE_LOGICAL_BYTES,
            max_entries=MAX_MANIFEST_ENTRIES,
        )
        with _engine(archive, profile):
            stats = dict(V25.build())
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    return {
        "profile": "federated-eg01",
        "format_revision": 25,
        "archive_bytes": archive.stat().st_size,
        "filesystem_manifest_bytes": int(fs["manifest_bytes"]),
        "filesystem_manifest_entries": int(fs["entries"]),
        "build_stats": stats,
        "verified": verified,
        "locality": locality,
    }


def extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    shutil.rmtree(destination, ignore_errors=True)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg01-extract-") as td:
        profile = Path(td) / "profile"
        with _engine(archive.resolve()):
            V25.extract(profile)
        _restore_profile(profile)
        shutil.copytree(profile, destination, symlinks=True)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    with _engine(archive.resolve()):
        inner = dict(V25.strong_verify())
    with tempfile.TemporaryDirectory(prefix="cmpct-eg01-verify-") as td:
        restored = Path(td) / "restored"
        extract(archive, restored)
        tree = _treehash(restored)
    if expected_tree is not None and tree != expected_tree:
        raise RuntimeError(f"canonical user-tree mismatch: {tree} != {expected_tree}")
    return {"ok": True, "profile": "federated-eg01", "canonical_user_tree_sha256": tree, "inner": inner}


def _refs_packs(refs: list, out: set[int]) -> None:
    for ref in refs:
        if ref[0] not in ("slice", "whole"):
            raise RuntimeError(f"unsupported object reference {ref!r}")
        out.add(int(ref[1]))


def locality_report(archive: Path) -> dict:
    """Derive decoded physical context for every public logical file from authenticated recipes."""
    with _engine(archive.resolve()):
        f, meta, offsets = V25.open_ar()
        try:
            pack_sizes = [int(row[2]) for row in offsets]
            if pack_sizes and max(pack_sizes) > MAX_DECODE_UNIT:
                raise RuntimeError("candidate physical pack exceeds 8 MiB decode ceiling")
            files = {str(path): desc for path, desc in meta.get("files", [])}
            for pi, entries in meta.get("micro", []):
                off = 0
                for path, size in entries:
                    files[str(path)] = ["plain", [["slice", int(pi), off, int(size)]], int(size)]
                    off += int(size)
            stream_packs = [(int(start), int(pi), int(size)) for start, pi, size in meta.get("stream_packs", [])]

            def stream_dependencies(start: int, size: int, out: set[int]) -> None:
                end = start + size
                for slab_start, pi, slab_size in stream_packs:
                    slab_end = slab_start + slab_size
                    if slab_end <= start:
                        continue
                    if slab_start >= end:
                        break
                    out.add(pi)

            visiting: set[str] = set()
            cache: dict[str, tuple[set[int], int]] = {}

            def deps(path: str) -> tuple[set[int], int]:
                if path in cache:
                    packs, length = cache[path]
                    return set(packs), length
                if path in visiting:
                    raise RuntimeError("cycle in candidate reconstruction graph")
                visiting.add(path)
                desc = files[path]
                typ = desc[0]
                packs: set[int] = set()
                if typ == "plain":
                    _refs_packs(desc[1], packs)
                    length = int(desc[2])
                elif typ == "zipstreams":
                    _refs_packs(desc[1], packs)
                    for start, size in desc[3]:
                        stream_dependencies(int(start), int(size), packs)
                    length = int(desc[4])
                elif typ == "inflate_stream":
                    stream_dependencies(int(desc[1]), int(desc[2]), packs)
                    length = int(desc[4])
                elif typ == "decode_file":
                    child, _ = deps(str(desc[1]))
                    packs |= child
                    length = int(desc[3])
                elif typ == "splice":
                    _refs_packs(desc[1], packs)
                    for child_path in desc[3]:
                        child, _ = deps(str(child_path))
                        packs |= child
                    length = int(desc[4])
                else:
                    raise RuntimeError(f"unsupported candidate recipe {typ!r}")
                visiting.remove(path)
                cache[path] = (set(packs), length)
                return packs, length

            rows = []
            max_amp = 0.0
            max_unit = max(pack_sizes, default=0)
            for path in sorted(files):
                # The authenticated filesystem manifest is control-plane state, not a user-addressable member.
                if path == FS.FILESYSTEM_MANIFEST:
                    continue
                packs, logical = deps(path)
                decoded = sum(pack_sizes[i] for i in packs)
                amp = decoded / max(1, logical)
                max_amp = max(max_amp, amp)
                rows.append(
                    {
                        "path": path,
                        "logical_bytes": logical,
                        "decoded_context_bytes": decoded,
                        "amplification": amp,
                        "pack_count": len(packs),
                    }
                )
        finally:
            f.close()
    return {
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_unit,
        "member_count": len(rows),
        "within_release_bounds": max_amp <= MAX_MEMBER_AMPLIFICATION and max_unit <= MAX_DECODE_UNIT,
        "members": rows,
    }
