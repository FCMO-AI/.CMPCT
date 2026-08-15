#!/usr/bin/env python3
"""Symmetric fresh-process extraction benchmark for cmpct-native versus unzip.

This harness measures one deliberately narrow question: how long does a fresh native CMPCT process
need to open an archive and emit one complete regular-file member, versus a fresh unzip process doing
the same thing? Archive creation is outside the timed region. Both commands write the same member
bytes to a sink, and correctness is checked before timings are accepted.

It intentionally does not compare CMPCT range reads against ``unzip -p`` because that would give CMPCT
a stronger operation. Random-range parity needs a ZIP tool/API with equivalent selective semantics.
Library-vs-library results belong in the existing ZIP parity harness, not here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

DEFAULT_REPEATS = 7


def run_checked(command: list[str], *, stdout=None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, stdout=stdout, stderr=subprocess.PIPE, check=True)


def tool_version(command: list[str]) -> str:
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    except OSError as exc:
        return f"unavailable: {exc}"
    text = (proc.stdout or "").strip().splitlines()
    return text[0] if text else f"exit={proc.returncode}"


def git_head(repo: Path) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def build_cmpct(repo: Path, source_dir: Path, archive: Path) -> None:
    env = os.environ.copy()
    src = str(repo / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(
        [sys.executable, "-m", "cmpct.cli", "create", str(source_dir), str(archive)],
        cwd=repo,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def build_zip(source_dir: Path, archive: Path, member: str) -> None:
    # ZIP_DEFLATED is the ordinary compatibility baseline already used by CMPCT parity work.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(source_dir / member, member)


def resolve_native(repo: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    candidates = [
        repo / "native" / "cmpct-core" / "target" / "release" / "cmpct-native",
        repo / "native" / "cmpct-core" / "target" / "debug" / "cmpct-native",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(
        "cmpct-native not found; build it with `cargo build --release --bin cmpct-native "
        "--manifest-path native/cmpct-core/Cargo.toml` or pass --cmpct-native"
    )


def native_member_name(native: Path, archive: Path, expected_leaf: str) -> str:
    proc = run_checked([str(native), "list", str(archive)], stdout=subprocess.PIPE)
    entries = json.loads(proc.stdout)
    regular = [row["path"] for row in entries if row.get("kind") == 0]
    exact = [path for path in regular if path == expected_leaf]
    if exact:
        return exact[0]
    suffix = [path for path in regular if path.endswith("/" + expected_leaf)]
    if len(suffix) == 1:
        return suffix[0]
    raise RuntimeError(f"could not resolve source member {expected_leaf!r} in native listing: {regular!r}")


def checked_output(command: list[str]) -> bytes:
    proc = run_checked(command, stdout=subprocess.PIPE)
    return proc.stdout


def time_command(command: list[str], repeats: int) -> list[float]:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        run_checked(command, stdout=subprocess.DEVNULL)
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return samples


def make_payload(kind: str, size: int) -> bytes:
    if kind == "compressible":
        seed = b"cmpct-native-vs-zip process-start parity\n"
        return (seed * ((size + len(seed) - 1) // len(seed)))[:size]
    if kind == "incompressible":
        # Deterministic pseudorandom bytes avoid publishing a result that cannot be reproduced.
        out = bytearray()
        counter = 0
        while len(out) < size:
            out.extend(hashlib.sha256(f"cmpct-parity-{counter}".encode()).digest())
            counter += 1
        return bytes(out[:size])
    raise ValueError(kind)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cmpct-native")
    parser.add_argument("--unzip", default=shutil.which("unzip") or "unzip")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--size-mib", type=int, default=8)
    parser.add_argument("--kind", choices=["compressible", "incompressible"], default="incompressible")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("--repeats must be at least 3")
    if args.size_mib <= 0 or args.size_mib > 64:
        parser.error("--size-mib must be between 1 and 64 (native CLI output limit)")

    repo = args.repo.resolve()
    native = resolve_native(repo, args.cmpct_native)
    unzip = args.unzip
    size = args.size_mib * 1024 * 1024
    member = "payload.bin"
    payload = make_payload(args.kind, size)
    payload_sha = hashlib.sha256(payload).hexdigest()

    with tempfile.TemporaryDirectory(prefix="cmpct-native-zip-parity-") as td:
        root = Path(td)
        source = root / "source"
        source.mkdir()
        (source / member).write_bytes(payload)
        cmpct_archive = root / "sample.cmpct"
        zip_archive = root / "sample.zip"
        build_cmpct(repo, source, cmpct_archive)
        build_zip(source, zip_archive, member)

        cmpct_member = native_member_name(native, cmpct_archive, member)
        cmpct_cmd = [str(native), "range", str(cmpct_archive), cmpct_member, "0", str(size)]
        zip_cmd = [unzip, "-p", str(zip_archive), member]

        # Footnote: timing is rejected unless both fresh-process commands first prove byte-identical
        # output. This prevents a faster error/metadata-only path from being recorded as extraction.
        cmpct_bytes = checked_output(cmpct_cmd)
        zip_bytes = checked_output(zip_cmd)
        if hashlib.sha256(cmpct_bytes).hexdigest() != payload_sha or cmpct_bytes != payload:
            raise RuntimeError("cmpct-native output differs from source payload")
        if hashlib.sha256(zip_bytes).hexdigest() != payload_sha or zip_bytes != payload:
            raise RuntimeError("unzip output differs from source payload")

        cmpct_ms = time_command(cmpct_cmd, args.repeats)
        zip_ms = time_command(zip_cmd, args.repeats)
        result = {
            "schema": "cmpct-native-cli-zip-parity-v1",
            "timing_layer": "fresh-process-cli-open-plus-full-member-output",
            "semantic_equivalence": {
                "operation": "open archive and emit complete regular-file member bytes",
                "archive_creation_timed": False,
                "stdout_destination": "os.devnull during timed repetitions",
                "correctness_gate": "byte-exact SHA-256 and direct byte equality before timing",
                "random_range_comparison": False,
                "note": "CMPCT range API is restricted to the full member here because unzip -p has no equivalent selective-offset operation.",
            },
            "source": {
                "kind": args.kind,
                "bytes": size,
                "sha256": payload_sha,
                "generator": "deterministic benchmark-local generator v1",
            },
            "archives": {
                "cmpct_bytes": cmpct_archive.stat().st_size,
                "zip_bytes": zip_archive.stat().st_size,
                "zip_method": "Python zipfile ZIP_DEFLATED compresslevel=6",
            },
            "commands": {
                "cmpct": ["cmpct-native", "range", "sample.cmpct", cmpct_member, "0", str(size)],
                "zip": [Path(unzip).name, "-p", "sample.zip", member],
            },
            "measurements_ms": {
                "cmpct_raw": cmpct_ms,
                "zip_raw": zip_ms,
                "cmpct_median": statistics.median(cmpct_ms),
                "zip_median": statistics.median(zip_ms),
            },
            "repetitions": args.repeats,
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "cmpct_commit": git_head(repo),
                "cmpct_native": tool_version([str(native), "info", str(cmpct_archive)]),
                "unzip": tool_version([unzip, "-v"]),
            },
        }

    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
