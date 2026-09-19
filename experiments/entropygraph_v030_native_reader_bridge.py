from __future__ import annotations

"""Fail-closed process bridge to the existing portable Rust G0-G4 reader.

This module is deliberately narrower than the public release facade. It exists so native-reader
performance can be measured through the same bounded call surface that a later shipping integration
would use. It changes no archive bytes or grammar and does not enable native dispatch by itself.

The bridge never invokes a shell. Verification accepts only the canonical ``g04-r25`` profile.
Extraction obtains a compact native ``info`` receipt and enforces the caller's aggregate regular-file
output budget before asking the native reader to perform its own transactional extraction. A positive
performance oracle may promote this bridge later, but until then it has zero release credit.
"""

from pathlib import Path
import os
import subprocess


CANONICAL_G04_PROFILE = "g04-r25"
CANONICAL_G04_REVISION = 25
DEFAULT_TIMEOUT_S = 300.0


class NativeReaderError(RuntimeError):
    pass


class NativeRun:
    def __init__(self, stdout: bytes, stderr: bytes):
        self.stdout = stdout
        self.stderr = stderr


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


def _kv_receipt(stdout: bytes, label: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in stdout.decode("utf-8", errors="strict").splitlines():
        if not raw_line:
            continue
        key, sep, value = raw_line.partition("=")
        if not sep or not key or key in values:
            raise NativeReaderError(f"native {label} returned malformed receipt")
        values[key] = value
    if not values:
        raise NativeReaderError(f"native {label} returned empty receipt")
    return values


def info_g04(cli: Path, archive: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    archive = Path(archive)
    values = _kv_receipt(_run(cli, "info", os.fspath(archive), timeout_s=timeout_s).stdout, "info")
    try:
        revision = int(values["revision"])
        entries = int(values["entries"])
        logical_regular_bytes = int(values["logical_regular_bytes"])
    except (KeyError, ValueError) as exc:
        raise NativeReaderError("native info omitted required integer fields") from exc
    profile = values.get("profile")
    if profile != CANONICAL_G04_PROFILE or revision != CANONICAL_G04_REVISION:
        raise NativeReaderError(
            f"native info selected unexpected profile/revision: {profile!r}/{revision}"
        )
    if entries <= 0 or logical_regular_bytes < 0:
        raise NativeReaderError("native info returned invalid public totals")
    return {
        "profile": profile,
        "revision": revision,
        "entries": entries,
        "logical_regular_bytes": logical_regular_bytes,
        "tail_metadata_authenticated": values.get("tail_metadata_authenticated") == "true",
    }


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
        "backend": "cmpct-portable-process-v2",
        "profile": profile,
        "archive": os.fspath(archive),
    }


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
    info = info_g04(cli, archive, timeout_s=timeout_s)
    logical = int(info["logical_regular_bytes"])
    if logical > limit:
        raise NativeReaderError(
            f"native extraction declared {logical} regular bytes, exceeding caller budget {limit}"
        )
    _run(cli, "extract", os.fspath(archive), os.fspath(destination), timeout_s=timeout_s)
    return {
        "ok": True,
        "backend": "cmpct-portable-process-v2",
        "profile": CANONICAL_G04_PROFILE,
        "entries": int(info["entries"]),
        "declared_regular_bytes": logical,
        "destination": os.fspath(destination),
        "caller_max_output_bytes": limit,
        "transactional_native_extract": True,
        "budget_preflight": "native-info-logical-regular-bytes-v1",
    }
