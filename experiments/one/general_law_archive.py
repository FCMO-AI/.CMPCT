"""ONE-G0.2 automatic general-tree Law + Surprise authenticated archive seed.

This is a research product-boundary candidate, not a Genesis winner claim. It accepts the
same supported arbitrary tree shape as the complete archive envelope, performs bounded
encoder-only discovery, and compiles accepted structure into the existing generic ONE
algebra. Unsupported structure falls back to ordinary Surprise.

The initial discovery policy is intentionally small and auditable: only the immediately
preceding regular file may predict the current file, and only exact reuse, Fill,
ADD8(constant), or XOR(constant) are nominated. Positive nominations are exact-proofed.
The reader performs no discovery and uses the existing authenticated archive reader.
"""
from __future__ import annotations

from dataclasses import dataclass
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
from .authenticated_archive_envelope import AUTH_FIELD, AUTH_LEAF_BYTES, _serialize_tree
from .ir import Limits, Node, OneError, Program, Ref, Root
from .wire import encode_program

SAMPLE_POINTS = 16


@dataclass(frozen=True)
class GeneralLawArchiveStats:
    logical_file_bytes: int
    wire_bytes: int
    surprise_bytes: int
    control_integrity_bytes: int
    authenticated_manifest_bytes: int
    auth_manifest_delta_bytes: int
    raw_auth_index_bytes: int
    source_read_bytes: int
    authentication_source_reread_bytes: int
    discovery_sample_bytes: int
    discovery_exact_proof_bytes: int
    max_predictor_bytes: int
    regular_files: int
    directories: int
    symlinks: int
    nodes: int
    exact_reuse_roots: int
    fill_roots: int
    add8_roots: int
    xor_roots: int
    surprise_roots: int


def _sample_positions(length: int) -> tuple[int, ...]:
    if length <= 0:
        return ()
    if length <= SAMPLE_POINTS:
        return tuple(range(length))
    return tuple(sorted({(i * (length - 1)) // (SAMPLE_POINTS - 1) for i in range(SAMPLE_POINTS)}))


def _all_equal(data: bytes, value: int) -> bool:
    return all(byte == value for byte in data)


def _all_add8(source: bytes, target: bytes, delta: int) -> bool:
    return all(((left + delta) & 0xFF) == right for left, right in zip(source, target, strict=True))


def _all_xor(source: bytes, target: bytes, mask: int) -> bool:
    return all((left ^ mask) == right for left, right in zip(source, target, strict=True))


def _discover_root(
    data: bytes,
    digest: str,
    nodes: list[Node],
    previous: tuple[bytes, str, Ref] | None,
) -> tuple[Ref, str, int, int]:
    """Return (root ref, class, sampled bytes, exact-proof bytes)."""
    sampled = 0
    proof = 0
    positions = _sample_positions(len(data))

    if previous is not None:
        prior_data, prior_digest, prior_ref = previous
        if len(prior_data) == len(data) and prior_digest == digest:
            proof += len(data) * 2
            if data == prior_data:
                return prior_ref, "exact_reuse", sampled, proof

    if data:
        value = data[positions[0]]
        sampled += len(positions)
        if all(data[index] == value for index in positions):
            proof += len(data)
            if _all_equal(data, value):
                node_id = len(nodes)
                nodes.append(Node("fill", count=len(data), value=value, declared_length=len(data)))
                return Ref(node_id), "fill", sampled, proof

    if previous is not None:
        prior_data, _prior_digest, prior_ref = previous
        if len(prior_data) == len(data) and data:
            delta = (data[positions[0]] - prior_data[positions[0]]) & 0xFF
            sampled += len(positions) * 2
            if all(((prior_data[index] + delta) & 0xFF) == data[index] for index in positions):
                proof += len(data) * 2
                if _all_add8(prior_data, data, delta):
                    fill_id = len(nodes)
                    nodes.append(Node("fill", count=len(data), value=delta, declared_length=len(data)))
                    law_id = len(nodes)
                    nodes.append(Node("add8", refs=(prior_ref, Ref(fill_id)), declared_length=len(data)))
                    return Ref(law_id), "add8", sampled, proof

            mask = data[positions[0]] ^ prior_data[positions[0]]
            sampled += len(positions) * 2
            if all((prior_data[index] ^ mask) == data[index] for index in positions):
                proof += len(data) * 2
                if _all_xor(prior_data, data, mask):
                    fill_id = len(nodes)
                    nodes.append(Node("fill", count=len(data), value=mask, declared_length=len(data)))
                    law_id = len(nodes)
                    nodes.append(Node("xor", refs=(prior_ref, Ref(fill_id)), declared_length=len(data)))
                    return Ref(law_id), "xor", sampled, proof

    return _file_nodes(data, nodes), "surprise", sampled, proof


def build_general_law_archive(source: Path) -> tuple[bytes, GeneralLawArchiveStats]:
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
    entries: list[dict[str, Any]] = []
    base_entries: list[dict[str, Any]] = []
    logical_total = 0
    source_read_bytes = 0
    raw_auth_index_bytes = 0
    sampled_bytes = 0
    proof_bytes = 0
    max_predictor_bytes = 0
    regular_index = 0
    counts = {"file": 0, "dir": 0, "symlink": 0}
    classes = {"exact_reuse": 0, "fill": 0, "add8": 0, "xor": 0, "surprise": 0}
    previous: tuple[bytes, str, Ref] | None = None

    for rel, path, info in records:
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            entry = {"kind": "dir", "mode": mode, "path": rel}
            entries.append(entry)
            base_entries.append(dict(entry))
            counts["dir"] += 1
            continue
        if stat.S_ISLNK(info.st_mode):
            target = _validate_symlink_target(rel, os.readlink(path))
            entry = {"kind": "symlink", "mode": mode, "path": rel, "target": target}
            entries.append(entry)
            base_entries.append(dict(entry))
            counts["symlink"] += 1
            continue
        if not stat.S_ISREG(info.st_mode):
            raise OneError(f"unsupported archive entry kind: {rel}")

        data = path.read_bytes()
        source_read_bytes += len(data)
        logical_total += len(data)
        if logical_total > MAX_ARCHIVE_LOGICAL_BYTES:
            raise OneError("archive logical bytes exceed research cap")
        digest = sha256(data).hexdigest()
        ref, relation, sampled, proved = _discover_root(data, digest, nodes, previous)
        sampled_bytes += sampled
        proof_bytes += proved
        classes[relation] += 1

        root_name = f"f{regular_index:06d}"
        regular_index += 1
        roots[root_name] = Root(ref=ref, length=len(data), sha256=digest)
        base_entry = {
            "kind": "file",
            "mode": mode,
            "path": rel,
            "root": root_name,
            "sha256": digest,
            "size": len(data),
        }
        tree = build_auth_tree(data, AUTH_LEAF_BYTES)
        raw_auth_index_bytes += tree.stored_index_bytes
        entry = dict(base_entry)
        entry[AUTH_FIELD] = _serialize_tree(tree)
        entries.append(entry)
        base_entries.append(base_entry)
        counts["file"] += 1

        previous = (data, digest, ref)
        max_predictor_bytes = max(max_predictor_bytes, len(data))

    base_manifest = _canonical_manifest(base_entries)
    manifest = _canonical_manifest(entries)
    manifest_id = len(nodes)
    nodes.append(Node("surprise", surprise=manifest, declared_length=len(manifest)))
    roots[MANIFEST_ROOT] = Root(Ref(manifest_id), len(manifest), sha256(manifest).hexdigest())

    if len(nodes) > MAX_ARCHIVE_NODES:
        raise OneError("archive node count exceeds research cap")

    # Match the existing authenticated Surprise seam's resource-limit accounting exactly.
    # This is important for fallback comparisons because Limits are serialized in ONE0:
    # changing only a policy multiplier would otherwise create wire-byte noise unrelated
    # to Law representation. The base seam builds with the unauthenticated manifest and
    # then charges six work bytes per added auth-manifest byte.
    base_root_bytes = logical_total + len(base_manifest)
    auth_delta = len(manifest) - len(base_manifest)
    base_work_limit = min(
        MAX_ARCHIVE_WORK_BYTES,
        max(1, base_root_bytes * 6 + len(nodes) * 64),
    )
    limits = Limits(
        max_nodes=MAX_ARCHIVE_NODES,
        max_output_bytes=max(1, logical_total + len(manifest)),
        max_work_bytes=base_work_limit + auth_delta * 6,
        max_depth=MAX_ARCHIVE_DEPTH,
    )
    program = Program(nodes=tuple(nodes), roots=roots, limits=limits)
    program.validate_shape()
    wire, wire_stats = encode_program(program)

    return wire, GeneralLawArchiveStats(
        logical_file_bytes=logical_total,
        wire_bytes=len(wire),
        surprise_bytes=wire_stats.surprise_bytes,
        control_integrity_bytes=wire_stats.control_integrity_bytes,
        authenticated_manifest_bytes=len(manifest),
        auth_manifest_delta_bytes=auth_delta,
        raw_auth_index_bytes=raw_auth_index_bytes,
        source_read_bytes=source_read_bytes,
        authentication_source_reread_bytes=0,
        discovery_sample_bytes=sampled_bytes,
        discovery_exact_proof_bytes=proof_bytes,
        max_predictor_bytes=max_predictor_bytes,
        regular_files=counts["file"],
        directories=counts["dir"],
        symlinks=counts["symlink"],
        nodes=len(nodes),
        exact_reuse_roots=classes["exact_reuse"],
        fill_roots=classes["fill"],
        add8_roots=classes["add8"],
        xor_roots=classes["xor"],
        surprise_roots=classes["surprise"],
    )
