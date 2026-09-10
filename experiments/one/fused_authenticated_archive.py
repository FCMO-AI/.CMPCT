"""ONE-G0.2 single-source-pass authenticated archive builder.

Research-only candidate for the fused-authentication preregistration.  It deliberately
produces the exact same authenticated ONE0 artifact as ``build_authenticated_archive``;
the only intended change is dataflow on creation: each regular file is read once and the
same immutable bytes object feeds the root digest, ONE file nodes and generic AuthTree.

This is not a new representation, format revision, integrity mode or reader path.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import stat
from typing import Any

from .archive_envelope import (
    MANIFEST_ROOT,
    MAX_ARCHIVE_DEPTH,
    MAX_ARCHIVE_LOGICAL_BYTES,
    MAX_ARCHIVE_NODES,
    MAX_ARCHIVE_WORK_BYTES,
    _canonical_manifest,
    _file_nodes,
    _validate_relative_path,
    _validate_symlink_target,
)
from .auth_tree import build_auth_tree
from .authenticated_archive_envelope import (
    AUTH_FIELD,
    AUTH_LEAF_BYTES,
    AuthFileMetadataStats,
    AuthenticatedArchiveBuildStats,
    _entry_wire_bytes,
    _serialize_tree,
)
from .ir import Limits, Node, OneError, Program, Ref, Root
from .wire import encode_program


def build_authenticated_archive_fused(source: Path) -> tuple[bytes, AuthenticatedArchiveBuildStats]:
    """Build the authenticated research archive with one payload source read per file.

    The baseline builder first creates the Surprise archive and then rereads every file to
    derive AuthTree state.  This candidate keeps the same canonical node/root ordering and
    limit arithmetic, but derives authentication from the bytes already held for ordinary
    ingest.  ``source_reread_bytes`` is therefore zero by construction; hashing still scans
    the in-memory payload and is deliberately *not* claimed to be free memory traffic.
    """

    source = Path(source)
    if not source.is_dir():
        raise OneError("archive source must be a directory")

    records: list[tuple[str, Path, os.stat_result]] = []
    for path in source.rglob("*"):
        rel = path.relative_to(source).as_posix()
        _validate_relative_path(rel)
        info = path.lstat()
        records.append((rel, path, info))
    records.sort(key=lambda item: item[0])

    nodes: list[Node] = []
    roots: dict[str, Root] = {}
    base_entries: list[dict[str, Any]] = []
    authenticated_entries: list[dict[str, Any]] = []
    logical_total = 0
    regular_index = 0
    counts = {"file": 0, "dir": 0, "symlink": 0}
    raw_index_bytes = 0
    per_file_auth: list[AuthFileMetadataStats] = []

    for rel, path, info in records:
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            entry = {"kind": "dir", "mode": mode, "path": rel}
            base_entries.append(entry)
            authenticated_entries.append(dict(entry))
            counts["dir"] += 1
            continue
        if stat.S_ISLNK(info.st_mode):
            target = _validate_symlink_target(rel, os.readlink(path))
            entry = {"kind": "symlink", "mode": mode, "path": rel, "target": target}
            base_entries.append(entry)
            authenticated_entries.append(dict(entry))
            counts["symlink"] += 1
            continue
        if not stat.S_ISREG(info.st_mode):
            raise OneError(f"unsupported archive entry kind: {rel}")

        # One filesystem/source payload read.  All content-derived state below is computed
        # from this exact immutable snapshot so root identity and AuthTree cannot disagree
        # because of a second read racing a source mutation.
        data = path.read_bytes()
        logical_total += len(data)
        if logical_total > MAX_ARCHIVE_LOGICAL_BYTES:
            raise OneError("archive logical bytes exceed research cap")

        digest = sha256(data).hexdigest()
        ref = _file_nodes(data, nodes)
        root_name = f"f{regular_index:06d}"
        regular_index += 1
        roots[root_name] = Root(ref=ref, length=len(data), sha256=digest)

        base_entry: dict[str, Any] = {
            "kind": "file",
            "mode": mode,
            "path": rel,
            "root": root_name,
            "sha256": digest,
            "size": len(data),
        }
        authenticated_entry = dict(base_entry)
        tree = build_auth_tree(data, AUTH_LEAF_BYTES)
        raw_index_bytes += tree.stored_index_bytes
        base_entry_bytes = _entry_wire_bytes(base_entry)
        authenticated_entry[AUTH_FIELD] = _serialize_tree(tree)
        per_file_auth.append(
            AuthFileMetadataStats(
                path=rel,
                logical_bytes=len(data),
                physical_auth_entry_delta_bytes=_entry_wire_bytes(authenticated_entry) - base_entry_bytes,
                raw_auth_index_bytes=tree.stored_index_bytes,
            )
        )
        base_entries.append(base_entry)
        authenticated_entries.append(authenticated_entry)
        counts["file"] += 1

        # ``data`` is intentionally not retained outside this iteration.  The ONE node(s)
        # own the payload exactly as the existing Surprise seam already does; no separate
        # whole-archive authentication cache is created.

    base_manifest = _canonical_manifest(base_entries)
    authenticated_manifest = _canonical_manifest(authenticated_entries)
    delta = len(authenticated_manifest) - len(base_manifest)
    if delta < 0:
        raise OneError("authenticated manifest unexpectedly shrank")

    manifest_node = len(nodes)
    nodes.append(Node("surprise", surprise=authenticated_manifest, declared_length=len(authenticated_manifest)))
    roots[MANIFEST_ROOT] = Root(
        ref=Ref(manifest_node),
        length=len(authenticated_manifest),
        sha256=sha256(authenticated_manifest).hexdigest(),
    )

    if len(nodes) > MAX_ARCHIVE_NODES:
        raise OneError("archive node count exceeds research cap")

    # Reproduce the baseline's two-stage limit arithmetic exactly.  The baseline first
    # builds a Surprise-only Program using the base manifest, then enlarges its bounds by
    # the authentication-manifest delta.  Matching that arithmetic is required for byte-
    # identical canonical wire rather than merely equivalent decoded semantics.
    root_bytes = logical_total + len(base_manifest)
    base_limits = Limits(
        max_nodes=MAX_ARCHIVE_NODES,
        max_output_bytes=max(1, root_bytes),
        max_work_bytes=min(MAX_ARCHIVE_WORK_BYTES, max(1, root_bytes * 6 + len(nodes) * 64)),
        max_depth=MAX_ARCHIVE_DEPTH,
    )
    limits = replace(
        base_limits,
        max_output_bytes=base_limits.max_output_bytes + delta,
        max_work_bytes=base_limits.max_work_bytes + delta * 6,
    )
    authenticated = Program(nodes=tuple(nodes), roots=roots, limits=limits)
    authenticated.validate_shape()
    wire, _wire_stats = encode_program(authenticated)

    return wire, AuthenticatedArchiveBuildStats(
        logical_file_bytes=logical_total,
        wire_bytes=len(wire),
        base_manifest_bytes=len(base_manifest),
        authenticated_manifest_bytes=len(authenticated_manifest),
        auth_manifest_delta_bytes=delta,
        raw_auth_index_bytes=raw_index_bytes,
        source_reread_bytes=0,
        regular_files=counts["file"],
        per_file_auth=tuple(per_file_auth),
    )
