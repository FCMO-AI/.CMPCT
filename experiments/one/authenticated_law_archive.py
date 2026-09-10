"""ONE-G0.2 authenticated archive seam containing an ordinary generic Law root.

Research-only composition candidate frozen by the authenticated-Law-archive preregistration.
It intentionally supplies a known ADD8(+37) relation: discovery/admission economics are
proved elsewhere.  The purpose here is to prove that generic Law, Manifest, persisted
AuthTree metadata and authenticated selective reads coexist in one ordinary ONE0 artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import stat

from .archive_envelope import (
    MANIFEST_ROOT,
    MAX_ARCHIVE_DEPTH,
    MAX_ARCHIVE_LOGICAL_BYTES,
    MAX_ARCHIVE_NODES,
    MAX_ARCHIVE_WORK_BYTES,
    _canonical_manifest,
)
from .auth_tree import build_auth_tree
from .authenticated_archive_envelope import AUTH_LEAF_BYTES, _serialize_tree
from .ir import Limits, Node, Program, Ref, Root
from .wire import encode_program

PREVIOUS_PATH = "00-previous.bin"
CURRENT_PATH = "01-current.bin"
ADD_VALUE = 37


@dataclass(frozen=True)
class AuthenticatedLawArchiveStats:
    logical_file_bytes: int
    wire_bytes: int
    control_integrity_bytes: int
    surprise_bytes: int
    auth_index_bytes: int
    nodes: int


def _entry(path: str, root: str, data: bytes, mode: int, tree) -> dict:
    return {
        "auth_tree_v1": _serialize_tree(tree),
        "kind": "file",
        "mode": mode,
        "path": path,
        "root": root,
        "sha256": sha256(data).hexdigest(),
        "size": len(data),
    }


def build_authenticated_add8_pair_archive(previous: bytes, current: bytes, *, mode: int = 0o644) -> tuple[bytes, AuthenticatedLawArchiveStats]:
    """Build one authenticated ONE archive with current derived from previous by ADD8(+37)."""
    if len(previous) != len(current):
        raise ValueError("relation pair lengths differ")
    expected = bytes(((b + ADD_VALUE) & 255) for b in previous)
    if current != expected:
        raise ValueError("current does not satisfy frozen ADD8(+37) relation")
    if len(previous) * 2 > MAX_ARCHIVE_LOGICAL_BYTES:
        raise ValueError("pair exceeds research archive logical cap")

    n = len(previous)
    nodes: list[Node] = [
        Node("surprise", surprise=previous, declared_length=n),
        Node("fill", count=n, value=ADD_VALUE, declared_length=n),
        Node("add8", refs=(Ref(0), Ref(1)), declared_length=n),
    ]
    roots = {
        "f000000": Root(Ref(0), n, sha256(previous).hexdigest()),
        "f000001": Root(Ref(2), n, sha256(current).hexdigest()),
    }

    previous_tree = build_auth_tree(previous, AUTH_LEAF_BYTES)
    current_tree = build_auth_tree(current, AUTH_LEAF_BYTES)
    entries = [
        _entry(PREVIOUS_PATH, "f000000", previous, stat.S_IMODE(mode), previous_tree),
        _entry(CURRENT_PATH, "f000001", current, stat.S_IMODE(mode), current_tree),
    ]
    manifest = _canonical_manifest(entries)
    manifest_id = len(nodes)
    nodes.append(Node("surprise", surprise=manifest, declared_length=len(manifest)))
    roots[MANIFEST_ROOT] = Root(Ref(manifest_id), len(manifest), sha256(manifest).hexdigest())

    logical_plus_manifest = n * 2 + len(manifest)
    limits = Limits(
        max_nodes=MAX_ARCHIVE_NODES,
        max_output_bytes=max(1, logical_plus_manifest),
        max_work_bytes=min(MAX_ARCHIVE_WORK_BYTES, max(1, logical_plus_manifest * 8 + len(nodes) * 64)),
        max_depth=MAX_ARCHIVE_DEPTH,
    )
    program = Program(tuple(nodes), roots, limits)
    program.validate_shape()
    wire, wstats = encode_program(program)
    return wire, AuthenticatedLawArchiveStats(
        logical_file_bytes=n * 2,
        wire_bytes=len(wire),
        control_integrity_bytes=wstats.control_integrity_bytes,
        surprise_bytes=wstats.surprise_bytes,
        auth_index_bytes=previous_tree.stored_index_bytes + current_tree.stored_index_bytes,
        nodes=len(nodes),
    )


def build_surprise_pair_fixture(directory: Path, previous: bytes, current: bytes) -> None:
    """Write the exact comparator source tree used by the frozen falsifier."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / PREVIOUS_PATH).write_bytes(previous)
    (directory / CURRENT_PATH).write_bytes(current)
