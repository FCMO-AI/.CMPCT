#!/usr/bin/env python3
"""O176: same Linux r24 archive, Win32 baseline negative versus installed O167.
The original O171 scientific court is invoked byte-for-byte, not edited.
Results are bounded to this fixture and two exact Git source snapshots.
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

ROOT = Path(__file__).resolve().parents[1]
DONOR_SHA = "841c32d435494f6e4d83c44cd00a1a2f8f7ab148"
SCHEMA = "cmpct-o176-win32-same-archive-typed-topology-v1"


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout)


def git(repo: Path, *args: str) -> str:
    p = run(["git", "-C", str(repo), *args])
    if p.returncode:
        raise AssertionError(f"git {args}: {p.stderr[-1200:]}")
    return p.stdout.strip()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_bytes(repo: Path, commit: str, relative: str) -> bytes:
    p = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{relative}"],
        capture_output=True, timeout=20
    )
    if p.returncode:
        raise AssertionError(f"missing Git source {commit}:{relative}: {p.stderr[-500:]}")
    return p.stdout


def assert_installed_source(repo: Path, source_sha: str, result: dict) -> None:
    import cmpct.reader
    files = ["src/cmpct/reader.py"]
    if repo != ROOT:
        import cmpct._win32_times
        files.append("src/cmpct/_win32_times.py")
    result["source_sha"] = source_sha
    result["installed_files"] = {}
    for relative in files:
        module = cmpct.reader if relative.endswith("reader.py") else cmpct._win32_times
        installed = Path(module.__file__).resolve()
        if installed.is_relative_to((ROOT / "src").resolve()) or installed.is_relative_to((repo / "src").resolve()):
            raise AssertionError(f"not independently installed: {installed}")
        actual = installed.read_bytes()
        canonical = source_bytes(repo, source_sha, relative)
        # Windows may check out text with CRLF. Record a newline-only
        # normalization rather than accepting arbitrary source differences.
        byte_identical = actual == canonical
        newline_only = (not byte_identical and actual.replace(b"\r\n", b"\n") == canonical)
        if not (byte_identical or newline_only):
            raise AssertionError(f"installed module differs from Git blob: {relative}")
        result["installed_files"][relative] = {
            "git_blob": git(repo, "rev-parse", f"{source_sha}:{relative}"),
            "installed_sha256": hashlib.sha256(actual).hexdigest(),
            "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
            "byte_identical": byte_identical,
            "only_crlf_difference": newline_only,
            "installed_outside_source": True,
        }


def cli(op: str, archive: Path, destination: Path | None, cwd: Path) -> dict:
    argv = [sys.executable, "-m", "cmpct", op, str(archive)]
    if destination is not None:
        argv.append(str(destination))
    t = time.perf_counter()
    p = run(argv, cwd=cwd, timeout=90)
    return {
        "argv_operation": op, "returncode": p.returncode,
        "wall_s": round(time.perf_counter() - t, 6),
        "stdout_tail": p.stdout[-4000:], "stderr_tail": p.stderr[-6000:],
    }


def execute(a: argparse.Namespace, record: dict) -> None:
    if platform.system() != "Windows":
        raise AssertionError("a native Windows OS is mandatory")
    producer_head = git(ROOT, "rev-parse", "HEAD")
    receipt = json.loads(a.receipt.read_text(encoding="utf-8"))
    if receipt.get("schema") != "cmpct-o165-linux-origin-receipt-v1":
        raise AssertionError("invalid immutable O165 producer receipt")
    if receipt.get("head") != producer_head:
        raise AssertionError(f"Linux/Windows evidence checkout mismatch: {receipt.get('head')} != {producer_head}")
    if a.archive.stat().st_size != receipt["archive_bytes"] or digest(a.archive) != receipt["archive_sha256"]:
        raise AssertionError("the transferred binary differs from the Linux producer")
    record["producer_head"] = producer_head
    record["archive_bytes"] = receipt["archive_bytes"]
    record["archive_sha256"] = receipt["archive_sha256"]
    record["phase"] = a.phase

    if a.phase == "baseline":
        assert_installed_source(ROOT, producer_head, record)
        with tempfile.TemporaryDirectory(prefix="o176-win32-baseline-") as td:
            scratch = Path(td)
            verify = cli("verify", a.archive, None, scratch)
            extraction = cli("extract", a.archive, scratch / "tree", scratch)
        record["baseline_verify"] = verify
        record["baseline_extract"] = extraction
        if verify["returncode"]:
            raise AssertionError("historical baseline failed verification, contrast inconclusive")
        if extraction["returncode"] == 0:
            raise AssertionError("historical baseline unexpectedly extracted successfully")
        errors = extraction["stderr_tail"]
        if "NotImplementedError" not in errors or "follow_symlinks" not in errors:
            raise AssertionError("baseline failed for a different mechanism than O171")
        record["result"] = "HISTORICAL_O171_NOTIMPLEMENTED_ERROR_REPRODUCED"
    else:
        if not a.donor_checkout:
            raise AssertionError("pinned O167 donor checkout required")
        donor = a.donor_checkout.resolve()
        donor_head = git(donor, "rev-parse", "HEAD")
        if donor_head != DONOR_SHA:
            raise AssertionError(f"donor must be exact O167 head {DONOR_SHA}, got {donor_head}")
        assert_installed_source(donor, donor_head, record)
        baseline = json.loads(a.baseline_result.read_text(encoding="utf-8"))
        if baseline.get("result") != "HISTORICAL_O171_NOTIMPLEMENTED_ERROR_REPRODUCED":
            raise AssertionError("same-run historical negative missing")
        if baseline.get("archive_sha256") != record["archive_sha256"]:
            raise AssertionError("not the same archive as historical baseline")
        original = ROOT / "research" / "o171_linux_to_windows_same_archive_court.py"
        if not original.is_file():
            raise AssertionError("original O171 physical court missing")
        record["unaltered_original_o171_court_blob"] = git(ROOT, "rev-parse", f"HEAD:research/o171_linux_to_windows_same_archive_court.py")
        if record["unaltered_original_o171_court_blob"] == "8c943128f135607dd36abd083bf1019bc9e4433a":  # frozen original court
            cmd = [
                sys.executable, str(original), "--archive", str(a.archive),
                "--receipt", str(a.receipt), "--output", str(a.o171_result),
            ]
            p = run(cmd, timeout=110)
            record["o171_original_court"] = {
                "returncode": p.returncode, "stdout_tail": p.stdout[-4000:],
                "stderr_tail": p.stderr[-4000:],
            }
            if a.o171_result.exists():
                child = json.loads(a.o171_result.read_text(encoding="utf-8"))
                record["o171_original_result"] = child.get("result")
                record["o171_physical_fidelity_failures"] = child.get("physical_fidelity_failures")
                record["o171_source_identity_note"] = (
                    "O171 binds the original Linux receipt/test checkout; installed O167 Reader "
                    "identity is independently verified in installed_files and source_sha."
                )
            if p.returncode:
                raise AssertionError("installed pinned O167 failed unchanged O171 physical court")
            if record.get("o171_original_result") != "ONE_AUTHENTIC_LINUX_ARCHIVE_WIN32_SCOPED_PHYSICAL_FIDELITY_VERIFIED":
                raise AssertionError("O171 result JSON did not report complete physical fidelity")
        else:
            raise AssertionError("historical O171 physical scientific court has drifted")
        record["result"] = "EXACT_O167_WIN32_CROSSHOST_TOPOLOGY_VERIFIED"

    record["archive_unchanged"] = digest(a.archive) == receipt["archive_sha256"]
    if not record["archive_unchanged"]:
        raise AssertionError("archive was mutated by Windows Reader")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--donor-checkout", type=Path)
    parser.add_argument("--baseline-result", type=Path)
    parser.add_argument("--o171-result", type=Path)
    args = parser.parse_args()
    evidence = {"schema": SCHEMA, "result": "INCOMPLETE",
                "host": platform.platform(), "python": sys.version}
    returncode = 0
    try:
        if args.phase == "candidate" and (not args.baseline_result or not args.o171_result):
            raise AssertionError("candidate requires baseline and original O171 JSON destinations")
        execute(args, evidence)
    except Exception as exc:
        returncode = 1
        evidence["error"] = f"{type(exc).__name__}: {exc}"
        evidence["traceback_tail"] = traceback.format_exc()[-4000:]
        if evidence["result"] == "INCOMPLETE":
            evidence["result"] = "INCONCLUSIVE_OR_REJECTED"
    if args.archive.exists():
        evidence["final_archive_sha256"] = digest(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in evidence.items()
                      if k not in ("traceback_tail",)}, sort_keys=True))
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
