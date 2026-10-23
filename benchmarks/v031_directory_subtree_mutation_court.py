#!/usr/bin/env python3
"""Source-bound, evidence-only POSIX directory mutation court for CMPCT revision 24.

Preregistration: benchmarks/history/2026-10-23-v031-directory-subtree-independent-prereg.json
This script *never* edits product code or weakens reader/validator/release policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import traceback
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_delete, append_rename
from cmpct.validation import preflight_archive

EPOCH = 315532800
SCENARIOS = ("rename_nonempty_dir", "delete_nonempty_dir",
             "rename_empty_dir", "delete_empty_dir",
             "rename_regular_file", "delete_regular_file")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(root: Path) -> Path:
    tree = root / "source"
    (tree / "dir" / "sub").mkdir(parents=True)
    (tree / "empty").mkdir()
    (tree / "dir" / "sub" / "nested.bin").write_bytes(
        hashlib.sha256(b"nested").digest() * 131)
    (tree / "dir" / "first.txt").write_bytes(b"directory-child-identity" * 31)
    (tree / "ordinary.txt").write_bytes(b"independent-file" * 23)
    for p in tree.rglob("*"):
        if p.is_file():
            p.chmod(0o640)
            os.utime(p, (EPOCH, EPOCH))
    for p in sorted((p for p in tree.rglob("*") if p.is_dir()), reverse=True):
        p.chmod(0o750)
        os.utime(p, (EPOCH, EPOCH))
    os.utime(tree, (EPOCH, EPOCH))
    return tree


def manifest(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        st = os.lstat(path)
        rel = path.relative_to(root).as_posix()
        row = {"mode": stat.S_IMODE(st.st_mode), "mtime_ns": st.st_mtime_ns}
        if stat.S_ISDIR(st.st_mode):
            row["kind"] = "directory"
        elif stat.S_ISREG(st.st_mode):
            row.update(kind="file", size=st.st_size, sha256=sha_file(path))
        elif stat.S_ISLNK(st.st_mode):
            row.update(kind="symlink", target=os.readlink(path))
        else:
            raise AssertionError("unexpected special file")
        out[rel] = row
    return out


def rows(archive: Path) -> list[dict]:
    with CMPCT(archive) as reader:
        return [{"path": r[0], "kind": r[1],
                 "target": r[6][0] if r[1] == 3 else None}
                for r in reader.index["files"]]


def probe(archive: Path, dest: Path) -> dict:
    outcome = {}
    try:
        preflight_archive(archive)
        outcome["preflight"] = "PASS"
    except Exception as exc:
        outcome["preflight"] = type(exc).__name__ + ": " + str(exc)
    try:
        with CMPCT(archive) as reader:
            reader.verify()
            outcome["reader_verify"] = "PASS"
            outcome["index"] = rows(archive)
            reader.extractall(dest, metadata=True)
        outcome["extract"] = "PASS"
        outcome["restored_manifest"] = manifest(dest)
    except Exception as exc:
        outcome["extract"] = type(exc).__name__ + ": " + str(exc)
        outcome["restored_manifest"] = None
    return outcome


def one(root: Path, scenario: str) -> dict:
    src = source(root)
    expected = root / "posix-reference"
    shutil.copytree(src, expected, copy_function=shutil.copy2)
    archive = root / "source.cmpct"
    t0 = time.perf_counter()
    Builder(src, workers=1, reproducible=False).build(archive)
    build_wall = time.perf_counter() - t0
    before_hash = sha_file(archive)
    before_bytes = archive.stat().st_size
    before_rows = rows(archive)
    operation = None
    posix = None
    if scenario == "rename_nonempty_dir":
        os.rename(expected / "dir", expected / "moved")
        operation = lambda: append_rename(archive, "dir", "moved")
        posix = "POSIX_RENAME_SUCCESS"
    elif scenario == "delete_nonempty_dir":
        try:
            os.rmdir(expected / "dir")
        except OSError as exc:
            posix = "POSIX_NONEMPTY_REFUSAL_" + type(exc).__name__
        else:
            raise AssertionError("POSIX accepted nonempty rmdir")
        operation = lambda: append_delete(archive, "dir")
    elif scenario == "rename_empty_dir":
        os.rename(expected / "empty", expected / "new_empty")
        operation = lambda: append_rename(archive, "empty", "new_empty")
        posix = "POSIX_RENAME_SUCCESS"
    elif scenario == "delete_empty_dir":
        os.rmdir(expected / "empty")
        operation = lambda: append_delete(archive, "empty")
        posix = "POSIX_RMDIR_SUCCESS"
    elif scenario == "rename_regular_file":
        os.rename(expected / "ordinary.txt", expected / "moved.txt")
        operation = lambda: append_rename(archive, "ordinary.txt", "moved.txt")
        posix = "POSIX_RENAME_SUCCESS"
    elif scenario == "delete_regular_file":
        os.unlink(expected / "ordinary.txt")
        operation = lambda: append_delete(archive, "ordinary.txt")
        posix = "POSIX_UNLINK_SUCCESS"
    else:
        raise KeyError(scenario)

    t0 = time.perf_counter()
    try:
        operation()
        mutation = "RETURNED_SUCCESS"
    except Exception as exc:
        mutation = type(exc).__name__ + ": " + str(exc)
    duration = time.perf_counter() - t0

    after_hash = sha_file(archive)
    after_bytes = archive.stat().st_size
    after_rows = rows(archive)
    observed = probe(archive, root / "restored")
    expected_manifest = manifest(expected)
    actual_manifest = observed["restored_manifest"]
    matching = actual_manifest == expected_manifest if actual_manifest is not None else False
    refused = mutation != "RETURNED_SUCCESS"
    unchanged = (after_hash == before_hash and after_bytes == before_bytes)
    if scenario == "delete_nonempty_dir":
        safe = (refused and unchanged and matching)
    else:
        safe = ((not refused) and matching)
    return {"scenario": scenario, "source_sha256": before_hash,
            "initial_archive_bytes": before_bytes,
            "initial_index": before_rows,
            "baseline_create_wall_s": build_wall,
            "posix_control": posix, "operation": mutation,
            "mutation_wall_s": duration,
            "after_archive_sha256": after_hash,
            "after_archive_bytes": after_bytes,
            "archive_unchanged": unchanged,
            "index_after": after_rows,
            "expected_manifest": expected_manifest,
            "extraction": observed,
            "exact_posix_match": matching,
            "strong_semantic_contract_satisfied": safe}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"schema": "cmpct-v031-directory-subtree-custody-court-v1",
              "research_only": True, "product_credit": False, "release_credit": False,
              "cases": []}
    for name in SCENARIOS:
        with tempfile.TemporaryDirectory(prefix="cmpct-dir-court-" + name + "-") as td:
            try:
                result["cases"].append(one(Path(td), name))
            except Exception:
                result["cases"].append({"scenario": name,
                                        "instrument_error": traceback.format_exc()})
    controls = [r for r in result["cases"] if r["scenario"] not in
                ("rename_nonempty_dir", "delete_nonempty_dir")]
    targets = [r for r in result["cases"] if r["scenario"] in
               ("rename_nonempty_dir", "delete_nonempty_dir")]
    result["instrument_errors"] = [r["scenario"] for r in result["cases"]
                                    if "instrument_error" in r]
    result["controls_satisfied"] = all(r.get("strong_semantic_contract_satisfied")
                                        for r in controls)
    result["subtree_hazards"] = [r["scenario"] for r in targets
                                 if r.get("strong_semantic_contract_satisfied") is False]
    result["decision"] = ("INSTRUMENT_INDETERMINATE" if result["instrument_errors"]
                          else "DIR_SUBTREE_SEMANTIC_HAZARD_REPRODUCED"
                          if result["subtree_hazards"] else "SUBTREE_HAZARD_NOT_REPRODUCED")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"],
                      "hazards": result["subtree_hazards"],
                      "controls": result["controls_satisfied"],
                      "errors": result["instrument_errors"],
                      "cases": [{"scenario": r["scenario"],
                                 "operation": r.get("operation"),
                                 "exact": r.get("exact_posix_match"),
                                 "safe": r.get("strong_semantic_contract_satisfied")}
                                for r in result["cases"]]}, sort_keys=True))
    if result["instrument_errors"] or not result["controls_satisfied"]:
        raise SystemExit("evidence court incomplete: inspect retained artifact; no product verdict")


if __name__ == "__main__":
    main()
