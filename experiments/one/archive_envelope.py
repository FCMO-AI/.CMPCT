"""ONE-G0.2 complete Surprise-only archive seam.

Research-only integration layer.  It represents a supported source tree entirely as one
ordinary ONE Program: canonical JSON manifest Surprise plus regular-file roots composed of
Surprise chunks/Concat.  It deliberately performs no Law discovery.  The purpose is to
establish a complete-artifact fallback and path/range lifecycle that later Law compilation
must improve without inventing another reader-visible compression mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any

from .ir import Limits, Node, OneError, Program, Ref, Root
from .range_vm import RangeEvaluationStats, RangeEvaluator
from .validated_program import ValidatedProgram, validate_program_snapshot_compact
from .wire import decode_program, encode_program

MANIFEST_ROOT = "@manifest"
PROFILE = "one-surprise-archive-v1"
CHUNK_BYTES = 1024 * 1024
MAX_ARCHIVE_LOGICAL_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_NODES = 131072
MAX_ARCHIVE_WORK_BYTES = 4 * 1024 * 1024 * 1024
MAX_ARCHIVE_DEPTH = 64


@dataclass(frozen=True)
class ArchiveBuildStats:
    logical_file_bytes: int
    manifest_bytes: int
    wire_bytes: int
    surprise_bytes: int
    control_integrity_bytes: int
    regular_files: int
    directories: int
    symlinks: int
    nodes: int


@dataclass(frozen=True)
class OpenArchive:
    wire: bytes
    validated: ValidatedProgram
    manifest: dict[str, Any]
    entries: dict[str, dict[str, Any]]

    @property
    def program(self) -> Program:
        return self.validated.program

    def list_paths(self) -> tuple[str, ...]:
        return tuple(sorted(self.entries))

    def read_file(self, path: str) -> bytes:
        entry = self._regular(path)
        evaluator = RangeEvaluator.from_validated(self.validated)
        data, _ = evaluator.reconstruct(entry["root"], 0, entry["size"])
        if sha256(data).hexdigest() != entry["sha256"]:
            raise OneError("archive file digest mismatch")
        root = self.program.roots[entry["root"]]
        if root.sha256 != entry["sha256"] or root.length != entry["size"]:
            raise OneError("manifest/file-root identity mismatch")
        return data

    def read_range(self, path: str, start: int, length: int) -> tuple[bytes, RangeEvaluationStats]:
        entry = self._regular(path)
        if type(start) is not int or type(length) is not int or start < 0 or length < 0:
            raise OneError("range start/length must be non-negative integers")
        if start + length > entry["size"]:
            raise OneError("requested archive range exceeds file")
        evaluator = RangeEvaluator.from_validated(self.validated)
        # This base archive seam deliberately does not claim authenticated selective reads;
        # RangeEvaluator exposes authenticated=False.  Authenticated cones remain a separate
        # already-proven execution property until integrated with the complete archive seam.
        return evaluator.reconstruct(entry["root"], start, length)

    def _regular(self, path: str) -> dict[str, Any]:
        canonical = _validate_relative_path(path)
        entry = self.entries.get(canonical)
        if entry is None:
            raise OneError("archive path not found")
        if entry.get("kind") != "file":
            raise OneError("archive path is not a regular file")
        return entry


def _validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise OneError("unsafe archive path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise OneError("unsafe archive path")
    canonical = path.as_posix()
    if canonical != value:
        raise OneError("non-canonical archive path")
    return canonical


def _validate_symlink_target(link_path: str, target: str) -> str:
    if not isinstance(target, str) or not target or "\x00" in target or "\\" in target:
        raise OneError("unsafe symlink target")
    pure = PurePosixPath(target)
    if pure.is_absolute():
        raise OneError("absolute symlink target outside archive scope")
    depth = len(PurePosixPath(link_path).parent.parts)
    for part in pure.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            depth -= 1
            if depth < 0:
                raise OneError("symlink target escapes archive root")
        else:
            depth += 1
    return target


def _canonical_manifest(entries: list[dict[str, Any]]) -> bytes:
    document = {"profile": PROFILE, "entries": entries}
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _file_nodes(data: bytes, nodes: list[Node]) -> Ref:
    if len(data) <= CHUNK_BYTES:
        node_id = len(nodes)
        nodes.append(Node("surprise", surprise=data, declared_length=len(data)))
        return Ref(node_id)
    refs: list[Ref] = []
    for start in range(0, len(data), CHUNK_BYTES):
        chunk = data[start : start + CHUNK_BYTES]
        node_id = len(nodes)
        nodes.append(Node("surprise", surprise=chunk, declared_length=len(chunk)))
        refs.append(Ref(node_id))
    concat_id = len(nodes)
    nodes.append(Node("concat", refs=tuple(refs), declared_length=len(data)))
    return Ref(concat_id)


def build_program(source: Path) -> tuple[Program, dict[str, Any]]:
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
    logical_total = 0
    regular_index = 0
    counts = {"file": 0, "dir": 0, "symlink": 0}

    for rel, path, info in records:
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            entries.append({"kind": "dir", "mode": mode, "path": rel})
            counts["dir"] += 1
            continue
        if stat.S_ISLNK(info.st_mode):
            target = _validate_symlink_target(rel, os.readlink(path))
            entries.append({"kind": "symlink", "mode": mode, "path": rel, "target": target})
            counts["symlink"] += 1
            continue
        if not stat.S_ISREG(info.st_mode):
            raise OneError(f"unsupported archive entry kind: {rel}")

        data = path.read_bytes()
        logical_total += len(data)
        if logical_total > MAX_ARCHIVE_LOGICAL_BYTES:
            raise OneError("archive logical bytes exceed research cap")
        digest = sha256(data).hexdigest()
        ref = _file_nodes(data, nodes)
        root_name = f"f{regular_index:06d}"
        regular_index += 1
        roots[root_name] = Root(ref=ref, length=len(data), sha256=digest)
        entries.append({
            "kind": "file",
            "mode": mode,
            "path": rel,
            "root": root_name,
            "sha256": digest,
            "size": len(data),
        })
        counts["file"] += 1

    manifest_bytes = _canonical_manifest(entries)
    manifest_node = len(nodes)
    nodes.append(Node("surprise", surprise=manifest_bytes, declared_length=len(manifest_bytes)))
    roots[MANIFEST_ROOT] = Root(
        ref=Ref(manifest_node),
        length=len(manifest_bytes),
        sha256=sha256(manifest_bytes).hexdigest(),
    )

    if len(nodes) > MAX_ARCHIVE_NODES:
        raise OneError("archive node count exceeds research cap")
    root_bytes = logical_total + len(manifest_bytes)
    # Reference preflight charges stored node production plus root reads/hashes.  A generous
    # fixed multiple keeps the fallback bounded without pretending to be a tuned cost model.
    limits = Limits(
        max_nodes=MAX_ARCHIVE_NODES,
        max_output_bytes=max(1, root_bytes),
        max_work_bytes=min(MAX_ARCHIVE_WORK_BYTES, max(1, root_bytes * 6 + len(nodes) * 64)),
        max_depth=MAX_ARCHIVE_DEPTH,
    )
    program = Program(nodes=tuple(nodes), roots=roots, limits=limits)
    program.validate_shape()
    return program, {"counts": counts, "logical_file_bytes": logical_total, "manifest_bytes": len(manifest_bytes)}


def build_archive(source: Path) -> tuple[bytes, ArchiveBuildStats]:
    program, build = build_program(source)
    wire, stats = encode_program(program)
    counts = build["counts"]
    return wire, ArchiveBuildStats(
        logical_file_bytes=build["logical_file_bytes"],
        manifest_bytes=build["manifest_bytes"],
        wire_bytes=stats.total_bytes,
        surprise_bytes=stats.surprise_bytes,
        control_integrity_bytes=stats.control_integrity_bytes,
        regular_files=counts["file"],
        directories=counts["dir"],
        symlinks=counts["symlink"],
        nodes=len(program.nodes),
    )


def _parse_manifest(raw: bytes, program: Program) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OneError("invalid archive manifest") from exc
    if not isinstance(document, dict) or document.get("profile") != PROFILE:
        raise OneError("unsupported archive manifest profile")
    raw_entries = document.get("entries")
    if not isinstance(raw_entries, list):
        raise OneError("archive manifest entries missing")
    entries: dict[str, dict[str, Any]] = {}
    previous: str | None = None
    referenced_roots: set[str] = set()
    for value in raw_entries:
        if not isinstance(value, dict):
            raise OneError("invalid archive manifest entry")
        path = _validate_relative_path(value.get("path"))
        if previous is not None and path <= previous:
            raise OneError("archive manifest paths are not canonical/unique")
        previous = path
        kind = value.get("kind")
        if kind not in {"file", "dir", "symlink"}:
            raise OneError("unsupported archive manifest entry kind")
        mode = value.get("mode")
        if type(mode) is not int or mode < 0 or mode > 0o7777:
            raise OneError("invalid archive manifest mode")
        if kind == "file":
            root_name = value.get("root")
            size = value.get("size")
            digest = value.get("sha256")
            if not isinstance(root_name, str) or root_name == MANIFEST_ROOT or root_name not in program.roots:
                raise OneError("archive manifest references missing file root")
            if root_name in referenced_roots:
                raise OneError("archive file root referenced more than once")
            root = program.roots[root_name]
            if type(size) is not int or size < 0 or root.length != size:
                raise OneError("archive manifest file length mismatch")
            if not isinstance(digest, str) or len(digest) != 64 or root.sha256 != digest:
                raise OneError("archive manifest file digest mismatch")
            referenced_roots.add(root_name)
        elif kind == "symlink":
            _validate_symlink_target(path, value.get("target"))
        entries[path] = dict(value)
    file_roots = set(program.roots) - {MANIFEST_ROOT}
    if referenced_roots != file_roots:
        raise OneError("archive manifest/file root set mismatch")
    return document, entries


def open_archive(wire: bytes) -> OpenArchive:
    caps = Limits(
        max_nodes=MAX_ARCHIVE_NODES,
        max_output_bytes=MAX_ARCHIVE_LOGICAL_BYTES,
        max_work_bytes=MAX_ARCHIVE_WORK_BYTES,
        max_depth=MAX_ARCHIVE_DEPTH,
    )
    program = decode_program(wire, caps=caps)
    validated = validate_program_snapshot_compact(program)
    if MANIFEST_ROOT not in validated.program.roots:
        raise OneError("archive manifest root missing")
    manifest_root = validated.program.roots[MANIFEST_ROOT]
    evaluator = RangeEvaluator.from_validated(validated)
    raw, _ = evaluator.reconstruct(MANIFEST_ROOT, 0, manifest_root.length)
    if sha256(raw).hexdigest() != manifest_root.sha256:
        raise OneError("archive manifest root digest mismatch")
    document, entries = _parse_manifest(raw, validated.program)
    return OpenArchive(wire=wire, validated=validated, manifest=document, entries=entries)
