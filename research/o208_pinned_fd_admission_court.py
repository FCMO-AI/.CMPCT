#!/usr/bin/env python3
"""O208: authentic CMPCT preflight/Reader inode identity vs immutable-bytes court.

Research only; see committed preregistration. Linux /proc/self/fd is an
experiment, not a portable or secure product repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import traceback


def sha256_file(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open("rb") as handle:
        for buf in iter(lambda: handle.read(1 << 20), b""):
            dig.update(buf)
    return dig.hexdigest()


def inode(fd: int) -> tuple[int, int]:
    stat = os.fstat(fd)
    return stat.st_dev, stat.st_ino


def inode_path(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino


def require_installed_source(workspace: Path) -> dict:
    import cmpct.reader as reader_mod
    import cmpct.validation as validation_mod
    result = {}
    for name, module in (("reader", reader_mod), ("validation", validation_mod)):
        actual = Path(module.__file__).resolve()
        source = workspace / "src" / "cmpct" / (name + ".py")
        assert actual != source.resolve(), "package is not independently installed"
        normalized_source = source.read_bytes().replace(b"\r\n", b"\n")
        normalized_installed = actual.read_bytes().replace(b"\r\n", b"\n")
        assert normalized_source == normalized_installed, f"{name} source drift"
        result[name + "_normal_sha256"] = hashlib.sha256(normalized_source).hexdigest()
        result[name + "_git_blob"] = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:src/cmpct/{name}.py"],
            cwd=workspace, text=True,
        ).strip()
    return result


def make_builder_archive(folder: Path, label: bytes) -> tuple[Path, bytes]:
    from cmpct.builder import Builder

    assert len(label) == 1
    source = folder / "input"
    source.mkdir(parents=True)
    data = label * 8192 + b"\x00\x01" + label * 257
    (source / "payload.bin").write_bytes(data)
    archive = folder / "built.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    return archive, data


def new_pair(base: Path, suffix: str):
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive

    outer = base / suffix
    outer.mkdir()
    a, payload_a = make_builder_archive(outer / "source_a", b"A")
    b, payload_b = make_builder_archive(outer / "source_b", b"B")
    assert payload_a != payload_b and len(payload_a) == len(payload_b)
    a_sha = sha256_file(a)
    b_sha = sha256_file(b)
    assert a_sha != b_sha
    for archive, payload in ((a, payload_a), (b, payload_b)):
        preflight = preflight_archive(archive)
        assert preflight["version"] == 24 and preflight["files"] == 1
        with CMPCT(archive) as r:
            assert r.verify() == 1
            assert r.read("payload.bin") == payload
            assert r.read_range("payload.bin", 4096, 37) == payload[4096:4133]
    return a, b, payload_a, payload_b, a_sha, b_sha


def unpinned_arm(base: Path) -> dict:
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive

    a, b, payload_a, payload_b, a_sha, b_sha = new_pair(base, "unpinned")
    preflight = preflight_archive(a)
    old_inode = inode_path(a)
    new_inode = inode_path(b)
    assert old_inode != new_inode
    os.replace(b, a)
    assert inode_path(a) == new_inode
    with CMPCT(a) as reader:
        actual_inode = inode(reader.f.fileno())
        result = reader.read("payload.bin")
        assert reader.verify() == 1
    assert actual_inode == new_inode and actual_inode != old_inode
    assert result == payload_b and result != payload_a
    assert sha256_file(a) == b_sha and sha256_file(a) != a_sha
    return {
        "preflight_files": preflight["files"],
        "preflight_source_sha256": a_sha,
        "reader_source_sha256": b_sha,
        "preflight_inode": list(old_inode),
        "reader_inode": list(actual_inode),
        "reader_returns_replacement": True,
    }


def pinned_arm(base: Path) -> dict:
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive, ValidationError

    if not Path("/proc/self/fd").is_dir() or not hasattr(os, "pwrite"):
        raise RuntimeError("Linux /proc/self/fd and pwrite required")
    a, b, payload_a, payload_b, a_sha, b_sha = new_pair(base, "pinned")
    fd = os.open(a, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    writer_fd = os.open(a, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    alias = Path(f"/proc/self/fd/{fd}")
    try:
        initial_inode = inode(fd)
        assert inode(writer_fd) == initial_inode
        assert sha256_file(alias) == a_sha
        preflight = preflight_archive(alias)
        assert preflight["version"] == 24 and preflight["files"] == 1
        os.replace(b, a)
        assert inode_path(a) != initial_inode
        assert sha256_file(alias) == a_sha and sha256_file(a) == b_sha
        with CMPCT(alias) as reader:
            actual_inode = inode(reader.f.fileno())
            assert actual_inode == initial_inode
            assert reader.verify() == 1
            assert reader.read("payload.bin") == payload_a
            assert reader.read_range("payload.bin", 4096, 37) == payload_a[4096:4133]
            assert reader.read("payload.bin") != payload_b

            # A retained name/descriptor identity is NOT a byte-level snapshot.
            # Mutate only the obsolete/unlinked A archive header through a writable
            # descriptor to the same inode, leaving its physical data blobs intact.
            changed = os.pwrite(writer_fd, b"?", 0)
            assert changed == 1
            os.fsync(writer_fd)
            mutated_sha = sha256_file(alias)
            assert mutated_sha != a_sha
            assert inode(fd) == initial_inode and inode(reader.f.fileno()) == initial_inode
            strict_rejection = None
            try:
                preflight_archive(alias)
            except ValidationError as exc:
                strict_rejection = type(exc).__name__ + ": " + str(exc)
            assert strict_rejection is not None, "strict preflight accepted mutated magic"
            assert reader.read("payload.bin") == payload_a
            assert reader.verify() == 1
        assert sha256_file(a) == b_sha
        return {
            "preflight_files": preflight["files"],
            "held_original_sha256": a_sha,
            "replacement_sha256": b_sha,
            "mutated_same_inode_sha256": mutated_sha,
            "held_inode": list(initial_inode),
            "reader_inode": list(actual_inode),
            "external_path_inode": list(inode_path(a)),
            "pinned_returns_original_after_rename": True,
            "same_inode_write_invalidates_strict_preflight": strict_rejection,
            "opened_reader_caches_original_index_after_header_mutation": True,
        }
    finally:
        os.close(writer_fd)
        os.close(fd)


def run() -> dict:
    if sys.platform != "linux":
        raise RuntimeError("This research court is deliberately Linux-only")
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace, text=True).strip()
    assert head == os.environ["EVIDENCE_HEAD"], "not exact-head checkout"
    assert subprocess.run(["git", "diff", "--quiet"], cwd=workspace, check=False).returncode == 0
    provenance = require_installed_source(workspace)
    start = time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix="cmpct-o208-") as td:
        base = Path(td)
        ordinary = unpinned_arm(base)
        pinned = pinned_arm(base)
    return {
        "schema": "cmpct-o208-source-admission-identity-v1",
        "source_head": head,
        "github_event_sha": os.environ.get("GITHUB_SHA"),
        "host": platform.platform(),
        "python": platform.python_version(),
        "provenance": provenance,
        "source_files_modified": False,
        "unpinned": ordinary,
        "pinned": pinned,
        "elapsed_lab_ms": (time.perf_counter_ns() - start) / 1e6,
        "decision": "PINNED_INODE_BINDS_TWO_READS_BUT_NOT_SOURCE_IMMUTABILITY",
        "scope": "genuine Builder r24, installed Python modules, Linux procfd only",
        "no_product_promotion": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    opts = parser.parse_args()
    try:
        result = run()
        print("O208_DECISION=" + result["decision"])
    except Exception as error:
        result = {
            "schema": "cmpct-o208-source-admission-identity-v1",
            "decision": "INCONCLUSIVE_OR_FALSIFIED",
            "error": repr(error),
            "traceback": traceback.format_exc(),
        }
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        raise
    opts.out.parent.mkdir(parents=True, exist_ok=True)
    opts.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
