from __future__ import annotations

"""Fail-closed process bridge to the production Rust logs-inverse reader.

This bridge is research-only until an explicit shipping integration earns the ordinary reader/fuzz,
native/Android and runtime authorities.  It changes no archive bytes or grammar.  The portable CLI
already owns the production ``logs-inverse-r25`` dispatch; this module only gives Python experiments a
bounded, no-shell call surface matching the existing G0-G4 native bridge.

Extraction obtains ``logical_regular_bytes`` through the compact native ``info`` receipt and enforces
the caller's aggregate output budget before transactional native publication.  Native process startup,
archive open and that budget preflight remain visible to any caller timing this bridge.
"""

from pathlib import Path
import os
import subprocess

CANONICAL_LOGS_PROFILE = "logs-inverse-r25"
CANONICAL_LOGS_REVISION = 25
DEFAULT_TIMEOUT_S = 300.0


class NativeLogsReaderError(RuntimeError):
    pass


class NativeRun:
    def __init__(self, stdout: bytes, stderr: bytes):
        self.stdout = stdout
        self.stderr = stderr


def _checked_cli(cli: Path) -> Path:
    cli = Path(cli)
    if not cli.is_file():
        raise NativeLogsReaderError(f"native logs reader CLI not found: {cli}")
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
        raise NativeLogsReaderError(f"native logs reader invocation failed: {exc}") from exc
    if completed.returncode != 0:
        tail = completed.stderr.decode("utf-8", errors="replace")[-2000:]
        raise NativeLogsReaderError(
            f"native logs reader rejected operation rc={completed.returncode}: {tail}"
        )
    return NativeRun(stdout=completed.stdout, stderr=completed.stderr)


def _kv_receipt(stdout: bytes, label: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in stdout.decode("utf-8", errors="strict").splitlines():
        if not raw_line:
            continue
        key, sep, value = raw_line.partition("=")
        if not sep or not key or key in values:
            raise NativeLogsReaderError(f"native logs {label} returned malformed receipt")
        values[key] = value
    if not values:
        raise NativeLogsReaderError(f"native logs {label} returned empty receipt")
    return values


def info_logs(cli: Path, archive: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    archive = Path(archive)
    values = _kv_receipt(_run(cli, "info", os.fspath(archive), timeout_s=timeout_s).stdout, "info")
    try:
        revision = int(values["revision"])
        entries = int(values["entries"])
        logical_regular_bytes = int(values["logical_regular_bytes"])
    except (KeyError, ValueError) as exc:
        raise NativeLogsReaderError("native logs info omitted required integer fields") from exc
    profile = values.get("profile")
    if profile != CANONICAL_LOGS_PROFILE or revision != CANONICAL_LOGS_REVISION:
        raise NativeLogsReaderError(
            f"native logs info selected unexpected profile/revision: {profile!r}/{revision}"
        )
    if entries <= 0 or logical_regular_bytes < 0:
        raise NativeLogsReaderError("native logs info returned invalid public totals")
    return {
        "profile": profile,
        "revision": revision,
        "entries": entries,
        "logical_regular_bytes": logical_regular_bytes,
        "tail_metadata_authenticated": values.get("tail_metadata_authenticated") == "true",
    }


def verify_logs(cli: Path, archive: Path, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    archive = Path(archive)
    receipt = _run(cli, "verify", os.fspath(archive), timeout_s=timeout_s)
    text = receipt.stdout.decode("utf-8", errors="strict").strip()
    expected = f"ok profile={CANONICAL_LOGS_PROFILE}"
    if text != expected:
        raise NativeLogsReaderError(f"native logs verify returned unexpected receipt: {text!r}")
    return {
        "ok": True,
        "backend": "cmpct-portable-process-v1",
        "profile": CANONICAL_LOGS_PROFILE,
        "archive": os.fspath(archive),
    }


def extract_logs(
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
        raise NativeLogsReaderError("negative native logs extraction output budget")
    info = info_logs(cli, archive, timeout_s=timeout_s)
    logical = int(info["logical_regular_bytes"])
    if logical > limit:
        raise NativeLogsReaderError(
            f"native logs extraction declared {logical} regular bytes, exceeding caller budget {limit}"
        )
    _run(cli, "extract", os.fspath(archive), os.fspath(destination), timeout_s=timeout_s)
    return {
        "ok": True,
        "backend": "cmpct-portable-process-v1",
        "profile": CANONICAL_LOGS_PROFILE,
        "entries": int(info["entries"]),
        "declared_regular_bytes": logical,
        "caller_max_output_bytes": limit,
        "destination": os.fspath(destination),
        "transactional_native_extract": True,
        "budget_preflight": "native-info-logical-regular-bytes-v1",
    }
