#!/usr/bin/env python3
"""O2: signed r24 symlink rejection across hosts, using one Linux-built corpus.

This is evidence infrastructure, not archive grammar or release policy.
Fixture production and extraction verification deliberately run in *different*
processes and may run on different operating systems. Unsafe rejection must
happen before publishing the unrelated ordinary member.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import tempfile
from pathlib import Path

from cmpct.core import Builder, CMPCT

OWNER = b"CMPCT-O2-SIGNED-SYMLINK-OWNER\x00" * 8
CASES = {
    "parent_escape": "../outside",
    "absolute_escape": "/absolute/outside",
    "win_root_escape": "\\outside",
    "win_drive_escape": "C:outside",
    "safe_relative": "a-first.bin",
}
UNSAFE_COMMON = ("parent_escape", "absolute_escape")
UNSAFE_WINDOWS = ("win_root_escape", "win_drive_escape")
SCHEMA = "cmpct-v031-signed-symlink-crosshost-o2-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build(out: Path, head: str) -> None:
    if os.name == "nt":
        raise RuntimeError("signed fixture production is intentionally Linux-only")
    out.mkdir(parents=True, exist_ok=True)
    objects = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-signed-o2-") as scratch:
        for case, target in CASES.items():
            source = Path(scratch) / case
            source.mkdir()
            (source / "a-first.bin").write_bytes(OWNER)
            os.symlink(target, source / "z-link")
            if os.readlink(source / "z-link") != target:
                raise AssertionError(f"producer symlink identity mismatch: {case}")
            archive = out / f"{case}.cmpct"
            Builder(source, workers=1, reproducible=True).build(archive)
            # Assert actual signed archive semantics BEFORE shipping across hosts.
            with CMPCT(archive) as reader:
                assert reader.read("a-first.bin") == OWNER, case
                assert reader.read("z-link").decode("utf-8", "surrogateescape") == target, case
            objects[case] = {
                "archive": archive.name,
                "target": target,
                "sha256": sha256(archive),
                "bytes": archive.stat().st_size,
            }
    manifest = {"schema": SCHEMA, "source_commit": head, "objects": objects}
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"phase": "build", **manifest}, sort_keys=True))


def verify(out: Path, head: str) -> None:
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or manifest.get("source_commit") != head:
        raise AssertionError("cross-host fixture schema or exact source HEAD mismatch")
    if set(manifest["objects"]) != set(CASES):
        raise AssertionError("missing/extra signed fixture cases")
    is_windows = os.name == "nt"
    required = set(UNSAFE_COMMON) | (set(UNSAFE_WINDOWS) if is_windows else set())
    passed = []
    evidence = []
    with tempfile.TemporaryDirectory(prefix="cmpct-signed-o2-verify-") as scratch:
        for case, target in CASES.items():
            record = manifest["objects"][case]
            archive = out / record["archive"]
            if record["target"] != target:
                raise AssertionError(f"signed target manifest mismatch: {case}")
            if archive.stat().st_size != record["bytes"] or sha256(archive) != record["sha256"]:
                raise AssertionError(f"signed fixture corruption or substitution: {case}")
            with CMPCT(archive) as reader:
                if reader.read("a-first.bin") != OWNER:
                    raise AssertionError(f"ordinary member mismatch: {case}")
                if reader.read("z-link").decode("utf-8", "surrogateescape") != target:
                    raise AssertionError(f"signed target decode mismatch: {case}")
                # Win32-only lexical hazards are not treated as host-global
                # rejects on POSIX; preserve legitimate cross-platform semantics.
                if case not in required:
                    evidence.append({"case": case, "status": "read_identity_only"})
                    continue
                dest = Path(scratch) / case
                caught = None
                try:
                    reader.extractall(dest, safe_symlinks=True, metadata=False)
                except OSError as exc:
                    caught = str(exc)
                if caught is None or "unsafe" not in caught or "symlink target" not in caught:
                    raise AssertionError(f"missing expected unsafe-target rejection: {case}: {caught!r}")
                if (dest / "a-first.bin").exists():
                    raise AssertionError(f"partial ordinary-member publication: {case}")
                passed.append(case)
                evidence.append({"case": case, "status": "rejected_before_regular_write", "error": caught})
    if len(passed) != (4 if is_windows else 2):
        raise AssertionError(f"insufficient real platform negatives: {passed}")
    receipt = {
        "schema": SCHEMA,
        "head": head,
        "host": platform.platform(),
        "os_name": os.name,
        "passed_prewrite_negatives": passed,
        "cases": evidence,
        "fixture_sha256": sha256(out / "manifest.json"),
        "claims": "actual Reader and actual Linux Builder; no bypass, no mocked parser, no test skip",
        "limits": "not atomic extraction, not pre-existing destination-symlink/TOCTOU containment",
    }
    (out / "crosshost-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["build", "verify"])
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    if len(args.head) != 40 or any(c not in "0123456789abcdef" for c in args.head):
        parser.error("--head must be an exact lowercase 40-character Git SHA")
    if args.phase == "build":
        build(args.dir, args.head)
    else:
        verify(args.dir, args.head)


if __name__ == "__main__":
    main()
