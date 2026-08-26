from __future__ import annotations

"""Fail-closed process bridge to the existing portable Rust G0-G4 reader.

This module is deliberately narrower than the public release facade.  It exists so native-reader
performance can be measured through the same bounded call surface that a later shipping integration
would use.  It changes no archive bytes or grammar and does not enable native dispatch by itself.

The bridge never invokes a shell.  Verification accepts only the canonical ``g04-r25`` profile.
Extraction first obtains the native public entry table and enforces the caller's aggregate regular-file
output budget before asking the native reader to perform its own transactional extraction.  A positive
performance oracle may promote this bridge later, but until then it has zero release credit.
"""

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess


CANONICAL_G04_PROFILE = "g04-r25"
DEFAULT_TIMEOUT_S = 300.0


class NativeReaderError(RuntimeError):
    pass


@dataclass(frozen=True)
class NativeEntry:
    index: int
    kind: int
    size: int
    path: str


@dataclass(frozen=True)
class NativeRun:
    stdout: bytes
    stderr: bytes


def _checked_cli(cli: Path) -> Path:
    cli = Path(cli)
    if not cli.is_file():
        raise NativeReaderError(f"native reader CLI not found: {cli}")
    return cli


def _run(cli: Path, *args: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> NativeRun:
    cli = _checked_cli(cli)
    try:
        completed = subprocess.run(
            [os.fspath(cli), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=float(timeout_s),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeReaderError(f"native reader invocation failed: {exc}") from exc
    if completed.returncode != 0:
        tail = completed.stderr.decode("utf-8", errors="replace")[-2000:]
        raise NativeReaderError(f"native reader rejected operation rc={completed.returncode}: {tail}")
    return NativeRun(stdout=completed.stdout, stderr=completed.stderr)


def _profile_from_verify(stdout: bytes) -> str:
    text = stdout.decode("utf-8", errors="strict").strip()
    prefix = "ok profile="
    if not text.startswith(prefix):
        raise NativeReaderError("native verify returned an unrecognized success receipt")
    profile = text[len(prefix) :].strip()
    if profile != CANONICAL_G04_PROFILE:
        raise NativeReaderError(f"native verify selected unexpected profile: {profile!r}")
    return profile


def verify_g04(cli: Path, archive: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    archive = Path(archive)
    receipt = _run(cli, "verify", os.fspath(archive), timeout_s=timeout_s)
    profile = _profile_from_verify(receipt.stdout)
    return {
        "ok": True,
        "backend": "cmpct-portable-process-v1",
        "profile": profile,
        "archive": os.fspath(archive),
    }


def list_entries(cli: Path, archive: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> list[NativeEntry]:
    archive = Path(archive)
    receipt = _run(cli, "list", os.fspath(archive), timeout_s=timeout_s)
    entries: list[NativeEntry] = []
    for raw_line in receipt.stdout.decode("utf-8", errors="strict").splitlines():
        if not raw_line:
            continue
        fields = raw_line.split("\t", 3)
        if len(fields) != 4:
            raise NativeReaderError("native list returned malformed entry receipt")
        try:
            index = int(fields[0])
            kind = int(fields[1])
            size = int(fields[2])
        except ValueError as exc:
            raise NativeReaderError("native list returned non-integer entry metadata") from exc
        if index != len(entries) or kind < 0 or size < 0 or not fields[3]:
            raise NativeReaderError("native list returned invalid entry metadata")
        entries.append(NativeEntry(index=index, kind=kind, size=size, path=fields[3]))
    if not entries:
        raise NativeReaderError("native list returned an empty public namespace")
    return entries


def declared_regular_bytes(entries: list[NativeEntry]) -> int:
    total = 0
    for entry in entries:
        if entry.kind == 0:
            total += int(entry.size)
    return total


def extract_g04(
    cli: Path,
    archive: Path,
    destination: Path,
    *,
    max_output_bytes: int,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict:
    archive = Path(archive)
    destination = Path(destination)
    limit = int(max_output_bytes)
    if limit < 0:
        raise NativeReaderError("negative native extraction output budget")
    entries = list_entries(cli, archive, timeout_s=timeout_s)
    logical = declared_regular_bytes(entries)
    if logical > limit:
        raise NativeReaderError(
            f"native extraction declared {logical} regular bytes, exceeding caller budget {limit}"
        )
    _run(cli, "extract", os.fspath(archive), os.fspath(destination), timeout_s=timeout_s)
    return {
        "ok": True,
        "backend": "cmpct-portable-process-v1",
        "profile": CANONICAL_G04_PROFILE,
        "entries": len(entries),
        "declared_regular_bytes": logical,
        "destination": os.fspath(destination),
        "caller_max_output_bytes": limit,
        "transactional_native_extract": True,
    }
