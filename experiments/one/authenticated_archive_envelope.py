"""ONE-G0.2 complete archive seam with persisted generic selective authentication.

This composes two existing ONE research surfaces: the complete Surprise archive envelope
and the generic AuthTree/selective-cone reader.  It adds no reader-visible compression
operation.  Authentication trees are Crystallization metadata carried inside the archive's
already-authenticated canonical manifest and are reconstructed entirely from serialized
bytes at open.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
from typing import Any

from .archive_envelope import (
    MANIFEST_ROOT,
    OpenArchive,
    _canonical_manifest,
    build_program,
    open_archive,
)
from .auth_tree import AuthTree, _parent_hash, _root_commit, build_auth_tree
from .authenticated_native_selective_cone import AuthenticatedNativeSelectiveStats, reconstruct_validated_authenticated_native_range
from .ir import Node, OneError, Program, Root
from .wire import encode_program

AUTH_LEAF_BYTES = 4096
AUTH_FIELD = "auth_tree_v1"


@dataclass(frozen=True)
class AuthFileMetadataStats:
    path: str
    logical_bytes: int
    physical_auth_entry_delta_bytes: int
    raw_auth_index_bytes: int


@dataclass(frozen=True)
class AuthenticatedArchiveBuildStats:
    logical_file_bytes: int
    wire_bytes: int
    base_manifest_bytes: int
    authenticated_manifest_bytes: int
    auth_manifest_delta_bytes: int
    raw_auth_index_bytes: int
    source_reread_bytes: int
    regular_files: int
    per_file_auth: tuple[AuthFileMetadataStats, ...]


@dataclass(frozen=True)
class OpenedAuthenticatedArchive:
    base: OpenArchive
    trees: dict[str, AuthTree]

    @property
    def program(self) -> Program:
        return self.base.program

    def list_paths(self) -> tuple[str, ...]:
        return self.base.list_paths()

    def read_file(self, path: str) -> bytes:
        return self.base.read_file(path)

    def read_range(self, path: str, start: int, length: int) -> tuple[bytes, AuthenticatedNativeSelectiveStats]:
        entry = self.base._regular(path)
        tree = self.trees.get(path)
        if tree is None:
            raise OneError("archive file authentication tree missing")
        return reconstruct_validated_authenticated_native_range(
            self.base.validated,
            entry["root"],
            tree,
            tree.root,
            start,
            length,
        )


def _serialize_tree(tree: AuthTree) -> dict[str, Any]:
    return {
        "leaf_bytes": tree.leaf_bytes,
        "root": tree.root.hex(),
        "levels_b64": [base64.b64encode(b"".join(level)).decode("ascii") for level in tree.levels],
    }


def _entry_wire_bytes(entry: dict[str, Any]) -> int:
    return len(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def _level_counts(total_len: int, leaf_bytes: int) -> tuple[int, ...]:
    count = max(1, ceil(total_len / leaf_bytes))
    counts = [count]
    while count > 1:
        count = (count + 1) // 2
        counts.append(count)
    return tuple(counts)


def _deserialize_tree(value: Any, total_len: int) -> AuthTree:
    if not isinstance(value, dict):
        raise OneError("archive authentication metadata missing")
    leaf_bytes = value.get("leaf_bytes")
    root_hex = value.get("root")
    levels_b64 = value.get("levels_b64")
    if type(leaf_bytes) is not int or leaf_bytes != AUTH_LEAF_BYTES:
        raise OneError("archive authentication leaf size invalid")
    if not isinstance(root_hex, str):
        raise OneError("archive authentication root invalid")
    try:
        root = bytes.fromhex(root_hex)
    except ValueError as exc:
        raise OneError("archive authentication root invalid") from exc
    if len(root) != 32:
        raise OneError("archive authentication root invalid")
    if not isinstance(levels_b64, list) or any(not isinstance(item, str) for item in levels_b64):
        raise OneError("archive authentication levels invalid")

    counts = _level_counts(total_len, leaf_bytes)
    if len(levels_b64) != len(counts):
        raise OneError("archive authentication level count invalid")

    levels: list[tuple[bytes, ...]] = []
    for encoded, count in zip(levels_b64, counts, strict=True):
        try:
            blob = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise OneError("archive authentication level encoding invalid") from exc
        if len(blob) != count * 32:
            raise OneError("archive authentication level width invalid")
        levels.append(tuple(blob[i : i + 32] for i in range(0, len(blob), 32)))

    # Validate the stored tree's own internal structure at open without reconstructing
    # file bytes. Requested leaves are still checked against these commitments at read.
    for level_no, current in enumerate(levels[:-1], start=1):
        parent = levels[level_no]
        expected: list[bytes] = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            expected.append(_parent_hash(level_no, left, right))
        if tuple(expected) != parent:
            raise OneError("archive authentication tree inconsistent")

    if not levels or len(levels[-1]) != 1 or _root_commit(total_len, leaf_bytes, levels[-1][0]) != root:
        raise OneError("archive authentication root commitment mismatch")
    return AuthTree(total_len=total_len, leaf_bytes=leaf_bytes, levels=tuple(levels), root=root)


def _manifest_document(program: Program) -> tuple[int, dict[str, Any]]:
    manifest_id = program.roots[MANIFEST_ROOT].ref.node
    raw = program.nodes[manifest_id].surprise
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OneError("invalid archive manifest") from exc
    if not isinstance(document, dict) or not isinstance(document.get("entries"), list):
        raise OneError("invalid archive manifest")
    return manifest_id, document


def build_authenticated_archive(source: Path) -> tuple[bytes, AuthenticatedArchiveBuildStats]:
    source = Path(source)
    program, build = build_program(source)
    manifest_id, document = _manifest_document(program)
    base_manifest = program.nodes[manifest_id].surprise

    entries = [dict(entry) for entry in document["entries"]]
    raw_index_bytes = 0
    reread_bytes = 0
    regular_files = 0
    per_file_auth: list[AuthFileMetadataStats] = []
    for entry in entries:
        if entry.get("kind") != "file":
            continue
        data = (source / entry["path"]).read_bytes()
        reread_bytes += len(data)
        regular_files += 1
        if len(data) != entry["size"] or sha256(data).hexdigest() != entry["sha256"]:
            raise OneError("archive source changed during authentication build")
        tree = build_auth_tree(data, AUTH_LEAF_BYTES)
        raw_index_bytes += tree.stored_index_bytes
        base_entry_bytes = _entry_wire_bytes(entry)
        entry[AUTH_FIELD] = _serialize_tree(tree)
        per_file_auth.append(
            AuthFileMetadataStats(
                path=entry["path"],
                logical_bytes=len(data),
                physical_auth_entry_delta_bytes=_entry_wire_bytes(entry) - base_entry_bytes,
                raw_auth_index_bytes=tree.stored_index_bytes,
            )
        )

    authenticated_manifest = _canonical_manifest(entries)
    delta = len(authenticated_manifest) - len(base_manifest)
    if delta < 0:
        raise OneError("authenticated manifest unexpectedly shrank")

    nodes = list(program.nodes)
    nodes[manifest_id] = Node("surprise", surprise=authenticated_manifest, declared_length=len(authenticated_manifest))
    roots = dict(program.roots)
    roots[MANIFEST_ROOT] = Root(
        ref=roots[MANIFEST_ROOT].ref,
        length=len(authenticated_manifest),
        sha256=sha256(authenticated_manifest).hexdigest(),
    )
    limits = replace(
        program.limits,
        max_output_bytes=program.limits.max_output_bytes + delta,
        max_work_bytes=program.limits.max_work_bytes + delta * 6,
    )
    authenticated = Program(nodes=tuple(nodes), roots=roots, limits=limits)
    authenticated.validate_shape()
    wire, _wire_stats = encode_program(authenticated)
    return wire, AuthenticatedArchiveBuildStats(
        logical_file_bytes=build["logical_file_bytes"],
        wire_bytes=len(wire),
        base_manifest_bytes=len(base_manifest),
        authenticated_manifest_bytes=len(authenticated_manifest),
        auth_manifest_delta_bytes=delta,
        raw_auth_index_bytes=raw_index_bytes,
        source_reread_bytes=reread_bytes,
        regular_files=regular_files,
        per_file_auth=tuple(per_file_auth),
    )


def open_authenticated_archive(wire: bytes) -> OpenedAuthenticatedArchive:
    base = open_archive(wire)
    trees: dict[str, AuthTree] = {}
    for path, entry in base.entries.items():
        if entry.get("kind") != "file":
            continue
        tree = _deserialize_tree(entry.get(AUTH_FIELD), entry["size"])
        trees[path] = tree
    return OpenedAuthenticatedArchive(base=base, trees=trees)
