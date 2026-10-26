#!/usr/bin/env python3
"""O171: assess a SINGLE Linux-created CMPCT r24 archive on installed Win32 Reader.

Research court: no Linux archive rebuild on Windows; no full NTFS fidelity or
release claim. Unrepresentable features remain genuine negatives, never skips.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "cmpct-o171-single-linux-r24-on-windows-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def path_from_raw(root: Path, relative_hex: str) -> Path:
    # The immutable O162 fixture contains only valid UTF-8 names. Never try
    # surrogate/opaque bytes or normalize spelling to rescue an invalid case.
    raw = bytes.fromhex(relative_hex)
    chunks = raw.split(b"/")
    if not chunks or any(c in (b"", b".", b"..") or b"\x00" in c or b"\\" in c or b":" in c for c in chunks):
        raise AssertionError("unsafe raw source member name")
    return root.joinpath(*(c.decode("utf-8", "strict") for c in chunks))


def cli(command: str, archive: Path, target: Path | None, cwd: Path) -> dict:
    argv = [sys.executable, "-m", "cmpct", command, str(archive)]
    if target is not None:
        argv.append(str(target))
    start = time.perf_counter_ns()
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=90)
    return {
        "operation": command, "returncode": proc.returncode,
        "elapsed_ms": round((time.perf_counter_ns() - start) / 1e6, 3),
        "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:],
    }


def host_capability_probe(workspace: Path) -> dict:
    result = {}
    left, hard, link = workspace / "probe-file", workspace / "probe-hard", workspace / "probe-sym"
    left.write_bytes(b"cmpct-o171-probe")
    try:
        os.link(left, hard)
        result["hardlink_created"] = os.path.samefile(left, hard)
    except OSError as error:
        result["hardlink_created"] = False
        result["hardlink_error"] = f"{type(error).__name__}: winerror={getattr(error, 'winerror', None)} errno={error.errno}"
    try:
        os.symlink("probe-file", link)
        result["symlink_created"] = link.is_symlink() and link.read_bytes() == left.read_bytes()
        result["symlink_target"] = os.readlink(link)
    except OSError as error:
        result["symlink_created"] = False
        result["symlink_error"] = f"{type(error).__name__}: winerror={getattr(error, 'winerror', None)} errno={error.errno}"
    # Win32 differentiates symbolic links to files and directories at creation.
    # A file-link positive does not imply the Reader's directory-link call
    # (which omits target_is_directory) will reconstruct the O162 ln-dir entry.
    directory = workspace / "probe-directory"
    directory.mkdir()
    directory_link = workspace / "probe-dir-sym"
    try:
        os.symlink("probe-directory", directory_link, target_is_directory=True)
        result["directory_symlink_created"] = (
            directory_link.is_symlink() and directory_link.is_dir()
        )
        result["directory_symlink_target"] = os.readlink(directory_link)
    except OSError as error:
        result["directory_symlink_created"] = False
        result["directory_symlink_error"] = (
            f"{type(error).__name__}: winerror={getattr(error, 'winerror', None)} errno={error.errno}"
        )
    # A second independent host oracle copies the exact Reader API call:
    # os.symlink(relative_directory, leaf), omitting target_is_directory.
    # This distinguishes an OS privilege restriction from a link-kind bug.
    implicit = workspace / "probe-dir-default-sym"
    try:
        os.symlink("probe-directory", implicit)
        result["default_directory_symlink_is_directory"] = implicit.is_dir()
        result["default_directory_symlink_raw_target"] = os.readlink(implicit)
        result["default_directory_symlink_is_link"] = implicit.is_symlink()
    except OSError as error:
        result["default_directory_symlink_is_directory"] = False
        result["default_directory_symlink_error"] = (
            f"{type(error).__name__}: winerror={getattr(error, 'winerror', None)} errno={error.errno}"
        )
    return result


def execute(args: argparse.Namespace, result: dict) -> None:
    if platform.system() != "Windows":
        raise AssertionError(f"real Windows host required, observed {platform.system()}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result["head"] = head
    required_head = os.environ.get("EVIDENCE_HEAD")
    if required_head and head != required_head:
        raise AssertionError(f"checkout HEAD mismatch: {head} != {required_head}")
    import cmpct
    installed = Path(cmpct.__file__).resolve()
    if installed.is_relative_to((ROOT / "src").resolve()):
        raise AssertionError("installed CMPCT imported from source tree, not a real distribution")
    result["independently_installed"] = True
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("schema") != "cmpct-o165-linux-origin-receipt-v1":
        raise AssertionError("wrong O165 Linux producer receipt")
    if receipt.get("head") != head:
        raise AssertionError(f"producer/receiver code HEAD mismatch {receipt.get('head')} != {head}")
    result["source_blobs"] = {}
    for relative, expected in receipt["provenance"]["source_blobs"].items():
        observed = subprocess.check_output(["git", "hash-object", relative], cwd=ROOT, text=True).strip()
        if observed != expected:
            raise AssertionError(f"installed source file identity mismatch {relative}: {observed} != {expected}")
        result["source_blobs"][relative] = observed
    result["source_identity_ok"] = True
    result["expected_archive_bytes"] = receipt["archive_bytes"]
    result["expected_archive_sha256"] = receipt["archive_sha256"]
    result["receiver_archive_bytes"] = args.archive.stat().st_size
    result["receiver_archive_sha256"] = sha256(args.archive)
    result["original_archive_exact"] = (
        result["receiver_archive_bytes"] == receipt["archive_bytes"]
        and result["receiver_archive_sha256"] == receipt["archive_sha256"]
    )
    if not result["original_archive_exact"]:
        raise AssertionError("archive altered in transport; downstream semantics inconclusive")
    if args.archive.open("rb").read(8) != b"CMPCT24\x00":
        raise AssertionError("not authentic CMPCT24 archive")

    manifest = receipt["source_strict_manifest"]
    rows = manifest["entries"]
    if len(rows) != 10 or len(manifest["hardlink_classes"]) != 1:
        raise AssertionError("O162 source-fixture baseline does not have 10 entries / 1 hardlink group")
    types = {"file": 0, "directory": 0, "symlink": 0}
    for row in rows:
        types[row["type"]] += 1
    if types["symlink"] != 3:
        raise AssertionError("O162 three-symlink source fixture drift")
    result["expected_entry_counts"] = types

    with tempfile.TemporaryDirectory(prefix="cmpct-o171-win-", dir=os.environ.get("RUNNER_TEMP")) as td:
        scratch = Path(td)
        result["host_capabilities"] = host_capability_probe(scratch)
        target = scratch / "extracted"
        verify = cli("verify", args.archive, None, scratch)
        result["installed_verify"] = verify
        if verify["returncode"]:
            result["result"] = "WIN32_VERIFY_REJECTED_AUTHENTIC_LINUX_ARCHIVE"
            raise AssertionError("Windows Reader rejected original r24 archive during verify")
        extract = cli("extract", args.archive, target, scratch)
        result["installed_extract"] = extract
        if extract["returncode"]:
            result["result"] = "WIN32_EXTRACTION_REJECTED_AFTER_VALID_VERIFY"
            raise AssertionError("Windows Reader extraction failed; original stderr retained")
        observations = []
        failures = []
        for row in rows:
            p = path_from_raw(target, row["path_hex"])
            record = {"path_hex": row["path_hex"], "expected_type": row["type"]}
            try:
                info = os.lstat(p)
            except OSError as error:
                record["lstat_error"] = f"{type(error).__name__}: {error.errno}"
                observations.append(record)
                failures.append(f"member missing: {row['path_hex']}")
                continue
            mode = info.st_mode
            actual_kind = ("symlink" if stat.S_ISLNK(mode) else
                           "file" if stat.S_ISREG(mode) else
                           "directory" if stat.S_ISDIR(mode) else "special")
            record["physical_type"] = actual_kind
            record["physical_mode"] = stat.S_IMODE(mode)
            if row["type"] != actual_kind:
                failures.append(f"physical kind differs: {row['path_hex']}: {actual_kind}")
            if row["type"] == "file" and actual_kind == "file":
                record["bytes"] = info.st_size
                record["sha256"] = sha256(p)
                if record["sha256"] != row["sha256"] or record["bytes"] != row["length"]:
                    failures.append(f"byte/hash differs: {row['path_hex']}")
            elif row["type"] == "symlink" and actual_kind == "symlink":
                observed_target = os.readlink(p)
                source_target = bytes.fromhex(row["target_hex"]).decode("utf-8", "strict")
                # Slash spelling can change, but target identity must remain
                # relative with otherwise unchanged components.
                record["physical_target"] = observed_target
                record["expected_target"] = source_target
                if observed_target.replace("\\", "/") != source_target:
                    failures.append(f"symlink target changed: {row['path_hex']}")
            observations.append(record)
        result["physical_observations"] = observations
        link_checks = []
        for paths in manifest["hardlink_classes"]:
            members = [path_from_raw(target, raw) for raw in paths]
            try:
                same = all(os.path.samefile(members[0], p) for p in members[1:])
            except OSError:
                same = False
            link_checks.append({"paths_hex": paths, "same_physical_file": same})
            if not same:
                failures.append("hardlink equivalence class not physically restored")
        result["hardlink_checks"] = link_checks
        result["physical_fidelity_failures"] = failures
        result["archive_unchanged_after_extract"] = sha256(args.archive) == receipt["archive_sha256"]
        if not result["archive_unchanged_after_extract"]:
            raise AssertionError("Reader modified input archive while checking/extracting")
        if failures:
            result["result"] = "WIN32_EXTRACT_SUCCEEDED_BUT_PHYSICAL_PORTABILITY_FALSE"
            raise AssertionError(f"physical fidelity differs in {len(failures)} checks")
    result["result"] = "ONE_AUTHENTIC_LINUX_ARCHIVE_WIN32_SCOPED_PHYSICAL_FIDELITY_VERIFIED"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    output = {
        "schema": SCHEMA, "platform": platform.platform(),
        "result": "INCOMPLETE", "evidence_class": "source-exact installed cross-host product falsifier",
    }
    code = 0
    try:
        execute(args, output)
    except Exception as exc:
        code = 1
        output["error"] = f"{type(exc).__name__}: {exc}"
        output["traceback_tail"] = traceback.format_exc()[-6000:]
        if output["result"] == "INCOMPLETE":
            output["result"] = "INCONCLUSIVE_OR_EARLY_FAILURE"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items()
                      if k not in {"physical_observations", "traceback_tail"}},
                     sort_keys=True))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
