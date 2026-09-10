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
ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_BOUNDARY_MANIFEST = ROOT / "benchmarks" / "one" / "genesis_one_candidate_boundary_v1.json"
CREATOR_SURFACE = "experiments/one/general_law_archive.py"
READER_SURFACE = "experiments/one/authenticated_archive_envelope.py"
RUNTIME_TREE = "experiments/one"
CERTIFIED_STATUS = "CERTIFIED_FOR_GENESIS"
FORBIDDEN_TRANSFER_MODULE_FRAGMENTS = (
    "one_genesis_gate_readiness",
    "neutral_hostile",
    "resemblance_hostile",
)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _regular_files(root: Path) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if stat.S_ISREG(path.lstat().st_mode):
            rows.append((path.relative_to(root).as_posix(), path))
    return sorted(rows)


def _source_semantic_manifest(root: Path) -> dict[str, dict[str, Any]]:
    """Describe source semantics independently with lstat/readlink."""
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            row: dict[str, Any] = {"kind": "dir", "mode": mode, "path": rel}
        elif stat.S_ISLNK(info.st_mode):
            row = {"kind": "symlink", "mode": mode, "path": rel, "target": os.readlink(path)}
        elif stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            row = {
                "kind": "file",
                "mode": mode,
                "path": rel,
                "size": len(data),
                "sha256": sha256(data).hexdigest(),
            }
        else:
            raise RuntimeError(f"unsupported source entry kind: {rel}")
        rows[rel] = row
    return rows


def _archive_semantic_manifest(opened: Any) -> dict[str, dict[str, Any]]:
    """Project the authenticated archive manifest onto source-tree semantics only."""
    rows: dict[str, dict[str, Any]] = {}
    for rel, value in opened.base.entries.items():
        kind = value.get("kind")
        row: dict[str, Any] = {"kind": kind, "mode": value.get("mode"), "path": rel}
        if kind == "symlink":
            row["target"] = value.get("target")
        elif kind == "file":
            row["size"] = value.get("size")
            row["sha256"] = value.get("sha256")
        rows[rel] = row
    return rows


def _assert_tree_semantics(source: dict[str, dict[str, Any]], archive: dict[str, dict[str, Any]]) -> None:
    if set(source) != set(archive):
        raise RuntimeError("archive path universe differs from executor-owned source tree")
    drift = [rel for rel in sorted(source) if source[rel] != archive[rel]]
    if drift:
        raise RuntimeError(f"archive tree semantics differ from executor-owned source tree: {drift[:8]}")


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _git_object_sha(path: str) -> str:
    """Return the exact Git object identity from the current sealed checkout."""
    value = subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"], text=True).strip()
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise RuntimeError(f"invalid Git object identity for {path}")
    return value


def _assert_candidate_boundary_certified() -> dict[str, Any]:
    """Require explicit path/blob/runtime-tree certification before production ONE import."""
    try:
        payload = json.loads(CANDIDATE_BOUNDARY_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Genesis ONE candidate-boundary authority is unreadable") from exc
    if payload.get("schema") != "cmpct-one-genesis-one-candidate-boundary-v1":
        raise RuntimeError("Genesis ONE candidate-boundary authority has wrong schema")
    if payload.get("status") != CERTIFIED_STATUS:
        raise RuntimeError("Genesis ONE candidate boundary is not certified for production gate execution")
    certified = payload.get("certified_candidate")
    if not isinstance(certified, dict):
        raise RuntimeError("Genesis ONE candidate certification is missing certified_candidate")
    expected = {
        "creator_path": CREATOR_SURFACE,
        "creator_blob_sha": _git_object_sha(CREATOR_SURFACE),
        "reader_path": READER_SURFACE,
        "reader_blob_sha": _git_object_sha(READER_SURFACE),
        "runtime_tree_path": RUNTIME_TREE,
        "runtime_tree_sha": _git_object_sha(RUNTIME_TREE),
    }
    for field, value in expected.items():
        if certified.get(field) != value:
            raise RuntimeError(f"Genesis ONE candidate certification {field} differs from worker runtime")
    return certified


def _authorize(transfer_fixture: bool) -> dict[str, Any]:
    if transfer_fixture:
        return {"transfer_fixture": True, "production_authorized": False}
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("production worker requires executor authorization")
    source = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    if len(source) != 40 or source != _git_head():
        raise RuntimeError("production worker source SHA is not bound to checkout HEAD")
    certified = _assert_candidate_boundary_certified()
    return {
        "transfer_fixture": False,
        "production_authorized": True,
        "source_sha": source,
        "candidate_boundary_certified": True,
        "candidate_boundary": certified,
    }


def _transfer_import_attestation() -> dict[str, Any]:
    loaded = sorted(
        name
        for name in sys.modules
        if any(fragment in name for fragment in FORBIDDEN_TRANSFER_MODULE_FRAGMENTS)
    )
    if loaded:
        raise RuntimeError(f"transfer worker imported Genesis workload authority: {loaded}")
    return {
        "genesis_workload_modules_imported": False,
        "forbidden_module_fragments": list(FORBIDDEN_TRANSFER_MODULE_FRAGMENTS),
    }


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
    source_semantics = _source_semantic_manifest(root)

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
    _assert_tree_semantics(source_semantics, _archive_semantic_manifest(opened))
    return {
        "phase": "whole_read",
        **timing,
        "returned_bytes": returned,
        "regular_files": len(expected),
        "tree_entries": len(source_semantics),
        "tree_semantics_checked": True,
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
    return {
        "phase": "selective_access",
        **timing,
        "member": member,
        "requested_bytes": requested,
        "exact": True,
        "integrity_checked_by_reader": True,
        "access": asdict(access),
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
    transfer_attestation = _transfer_import_attestation() if transfer_fixture else {}
    return {
        "schema": SCHEMA,
        "experimental_version": "ONE-G0.2",
        "authorization": auth,
        **transfer_attestation,
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
