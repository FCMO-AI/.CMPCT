from __future__ import annotations

"""Fresh-process measurement worker for the CMPCT1 Genesis product adapter.

This is a raw measurement primitive only.  It does not select workloads, compare
contenders, score rows, or generate the Genesis corpus.  Production use is guarded by
executor authorization; `--transfer-fixture` exists only for pre-gate synthetic tests.
"""

import argparse
from dataclasses import asdict
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import sys
import time
from typing import Any


SCHEMA = "cmpct-one-genesis-cmpct1-worker-v1"


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB, Darwin bytes. Hosted Genesis runners are Linux, but retain a
    # correct conversion if the transfer falsifier is run on macOS.
    return int(value if sys.platform == "darwin" else value * 1024)


def _regular_files(root: Path) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if stat.S_ISREG(path.lstat().st_mode):
            rows.append((path.relative_to(root).as_posix(), path))
    return sorted(rows)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _authorize(transfer_fixture: bool) -> dict[str, Any]:
    if transfer_fixture:
        return {"transfer_fixture": True, "production_authorized": False}
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("production worker requires executor authorization")
    source = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    if len(source) != 40 or source != _git_head():
        raise RuntimeError("production worker source SHA is not bound to checkout HEAD")
    return {"transfer_fixture": False, "production_authorized": True, "source_sha": source}


def _timed(call):
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    value = call()
    return value, {
        "measured": True,
        "cpu_s": time.process_time() - cpu0,
        "wall_s": time.perf_counter() - wall0,
        "peak_rss_bytes": _peak_rss_bytes(),
        "process_boundary": "fresh-process",
    }


def _load_surface():
    # Dynamic import keeps product import/runtime initialization inside the fresh worker.
    archive = importlib.import_module("experiments.one.general_law_archive")
    reader = importlib.import_module("experiments.one.authenticated_archive_envelope")
    return archive, reader


def _build(root: Path, archive_path: Path) -> dict[str, Any]:
    def action():
        archive, _reader = _load_surface()
        wire, stats = archive.build_general_law_archive(root)
        archive_path.write_bytes(wire)
        return wire, stats

    (wire, stats), timing = _timed(action)
    return {
        "phase": "creation",
        **timing,
        "stored_bytes": len(wire),
        "wire_sha256": sha256(wire).hexdigest(),
        "build_stats": asdict(stats),
    }


def _whole(root: Path, archive_path: Path) -> dict[str, Any]:
    expected = _regular_files(root)

    def action():
        _archive, reader = _load_surface()
        opened = reader.open_authenticated_archive(archive_path.read_bytes())
        digests: dict[str, str] = {}
        returned = 0
        for rel, _path in expected:
            data = opened.read_file(rel)
            returned += len(data)
            digests[rel] = sha256(data).hexdigest()
        return opened, digests, returned

    (opened, digests, returned), timing = _timed(action)
    for rel, path in expected:
        if digests.get(rel) != sha256(path.read_bytes()).hexdigest():
            raise RuntimeError(f"whole-read reconstruction mismatch: {rel}")
    source_paths = {path.relative_to(root).as_posix() for path in root.rglob("*")}
    if set(opened.list_paths()) != source_paths:
        raise RuntimeError("archive path universe differs from executor-owned source tree")
    return {
        "phase": "whole_read",
        **timing,
        "returned_bytes": returned,
        "regular_files": len(expected),
        "exact": True,
        "integrity_checked_by_reader": True,
    }


def _selective(root: Path, archive_path: Path, member: str) -> dict[str, Any]:
    member_path = root / Path(member)
    if not member_path.is_file() or not stat.S_ISREG(member_path.lstat().st_mode):
        raise RuntimeError("selected member is not a regular source file")
    requested = member_path.stat().st_size

    def action():
        _archive, reader = _load_surface()
        opened = reader.open_authenticated_archive(archive_path.read_bytes())
        data, access = opened.read_range(member, 0, requested)
        return sha256(data).hexdigest(), access

    (digest, access), timing = _timed(action)
    if digest != sha256(member_path.read_bytes()).hexdigest():
        raise RuntimeError("selective member reconstruction mismatch")
    access_row = asdict(access)
    return {
        "phase": "selective_access",
        **timing,
        "member": member,
        "requested_bytes": requested,
        "exact": True,
        "integrity_checked_by_reader": True,
        "access": access_row,
    }


def run(*, mode: str, root: Path, archive: Path, member: str | None, transfer_fixture: bool) -> dict[str, Any]:
    auth = _authorize(transfer_fixture)
    root = root.resolve()
    archive = archive.resolve()
    if not root.is_dir():
        raise RuntimeError("input root is not a directory")
    if mode != "build" and not archive.is_file():
        raise RuntimeError("archive does not exist for read phase")
    if mode == "build":
        phase = _build(root, archive)
    elif mode == "whole":
        phase = _whole(root, archive)
    elif mode == "selective":
        if not member:
            raise RuntimeError("selective mode requires --member")
        phase = _selective(root, archive, member)
    else:
        raise RuntimeError(f"unknown mode: {mode}")
    return {
        "schema": SCHEMA,
        "experimental_version": "ONE-G0.2",
        "authorization": auth,
        "scoring_executed": False,
        "winner_selected": False,
        **phase,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("build", "whole", "selective"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--member")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transfer-fixture", action="store_true")
    args = parser.parse_args()
    result = run(
        mode=args.mode,
        root=args.root,
        archive=args.archive,
        member=args.member,
        transfer_fixture=args.transfer_fixture,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
