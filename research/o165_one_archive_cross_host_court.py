#!/usr/bin/env python3
"""O165: one authentic Linux-built CMPCT archive, physically transferred to macOS.

O155 strict witness is unchanged. Portable comparison excludes ONLY physical
symlink mode, retaining every original source/receiver strict receipt.
This is a fixed-fixture scientific court, not a general portability or release claim.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
O162 = ROOT / "research/o162_authentic_tree_roundtrip_court.py"
O162_GIT_BLOB = "ed352ad593a41ed541b3cbb6774c8c5f447f3741"
PROJECTION = "cmpct-o165-raw-tree-with-symlink-mode-excluded-v1"


def load_o162():
    spec = importlib.util.spec_from_file_location("o162_authentic_tree_roundtrip", O162)
    if spec is None or spec.loader is None:
        raise RuntimeError("O162 source-exact instrument not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(o162) -> dict:
    inherited = o162.identity_gate()
    blob = subprocess.check_output(
        ["git", "hash-object", str(O162.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()
    if blob != O162_GIT_BLOB:
        raise AssertionError(f"O162 fixture drift: {blob} != {O162_GIT_BLOB}")
    return {**inherited, "o162_blob": blob, "platform": platform.platform()}


def portable_manifest(strict: dict) -> dict:
    """Apply only the preregistered symlink-mode exception; no other coarsening."""
    result = copy.deepcopy(strict)
    if result["schema"] != "cmpct-o155-static-posix-tree-witness-v1":
        raise AssertionError(f"unknown O155 schema: {result['schema']}")
    for entry in result["entries"]:
        if entry["type"] == "symlink":
            del entry["mode"]
    result["schema"] = PROJECTION
    result["scope"] = "O155 exact except physical symlink mode (host-specific)"
    return result


def digest_dict(value: dict) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def physical_deltas(origin: dict, receiver: dict) -> list[dict]:
    """Record all observed entry changes, independently from projection equality."""
    orig = {entry["path_hex"]: entry for entry in origin["entries"]}
    recv = {entry["path_hex"]: entry for entry in receiver["entries"]}
    if set(orig) != set(recv):
        raise AssertionError("entry path set differs across hosts")
    result = []
    for path in sorted(orig):
        a, b = orig[path], recv[path]
        if a == b:
            continue
        fields = sorted({*a, *b} - {k for k in {*a, *b} if a.get(k) == b.get(k)})
        result.append({
            "path_hex": path, "changed_fields": fields,
            "origin_type": a["type"], "receiver_type": b["type"],
            "origin_mode": a.get("mode"), "receiver_mode": b.get("mode"),
        })
    return result


def produce(o162, oracle, args: argparse.Namespace, provenance: dict) -> dict:
    if platform.system() != "Linux":
        raise AssertionError("only the Linux job may produce the archive")
    if args.receipt is None:
        raise ValueError("--receipt is required")
    if args.archive.exists():
        raise AssertionError("archive destination must be new")
    with tempfile.TemporaryDirectory(prefix="cmpct-o165-linux-", dir=os.environ.get("RUNNER_TEMP")) as td:
        scratch = Path(td)
        source = scratch / "source"
        restored = scratch / "local-control"
        old_umask = os.umask(0o022)
        try:
            o162.build_fixture(source)
            source_hash, source_manifest = oracle.strict_digest(source)
            assert len(source_manifest["entries"]) == 10
            assert len(source_manifest["hardlink_classes"]) == 1
            assert sum(e["type"] == "symlink" for e in source_manifest["entries"]) == 3
            create = o162.call_cli(
                ["create", str(source), str(args.archive), "--workers", "1"], scratch
            )
            verify = o162.call_cli(["verify", str(args.archive)], scratch)
            local_extract = o162.call_cli(["extract", str(args.archive), str(restored)], scratch)
            local_hash, local_manifest = oracle.strict_digest(restored)
            if local_manifest != source_manifest:
                raise AssertionError("Ubuntu same-archive strict baseline failed")
            if not os.path.samefile(restored / "a-base.bin", restored / "nested/hardcopy.bin"):
                raise AssertionError("Ubuntu hardlink topology lost")
        finally:
            os.umask(old_umask)
    archive_sha = sha256(args.archive)
    if args.archive.read_bytes()[:8] != b"CMPCT24\\0":
        raise AssertionError("producer did not make a revision-24 archive")
    portable = portable_manifest(source_manifest)
    receipt = {
        "schema": "cmpct-o165-linux-origin-receipt-v1",
        "head": provenance["git_head"],
        "provenance": provenance,
        "archive_sha256": archive_sha,
        "archive_bytes": args.archive.stat().st_size,
        "source_strict_digest": source_hash,
        "source_strict_manifest": source_manifest,
        "source_portable_digest": digest_dict(portable),
        "source_portable_manifest": portable,
        "linux_local_strict_digest": local_hash,
        "linux_local_strict_match": True,
        "installed_create": create,
        "installed_verify": verify,
        "installed_local_extract": local_extract,
        "result": "LINUX_SINGLE_ARCHIVE_ORIGIN_VERIFIED",
    }
    write_json(args.receipt, receipt)
    return {
        "phase": "producer", "head": provenance["git_head"],
        "archive_sha256": archive_sha, "archive_bytes": receipt["archive_bytes"],
        "source_strict_digest": source_hash,
        "source_portable_digest": receipt["source_portable_digest"],
        "source_entries": 10, "symlinks": 3, "hardlink_classes": 1,
        "linux_same_archive_strict_match": True,
        "result": receipt["result"],
    }


def receive(o162, oracle, args: argparse.Namespace, provenance: dict) -> dict:
    if platform.system() != "Darwin":
        raise AssertionError("the independent receiving job must run on macOS")
    if args.receipt is None:
        raise ValueError("--receipt is required")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt["schema"] != "cmpct-o165-linux-origin-receipt-v1":
        raise AssertionError("unexpected producer receipt")
    if receipt["head"] != provenance["git_head"]:
        raise AssertionError("producer/consumer Git source identity differs")
    if receipt["provenance"]["source_blobs"] != provenance["source_blobs"]:
        raise AssertionError("installed engine source blobs differ")
    observed_sha = sha256(args.archive)
    if observed_sha != receipt["archive_sha256"]:
        raise AssertionError("transferred archive bytes differ from Linux producer")
    if args.archive.stat().st_size != receipt["archive_bytes"]:
        raise AssertionError("transferred archive byte count differs")
    if args.archive.read_bytes()[:8] != b"CMPCT24\\0":
        raise AssertionError("transferred bytes are not revision-24 CMPCT")
    source = receipt["source_strict_manifest"]
    expected_portable = portable_manifest(source)
    if expected_portable != receipt["source_portable_manifest"]:
        raise AssertionError("producer portable receipt inconsistent with strict witness")
    if digest_dict(expected_portable) != receipt["source_portable_digest"]:
        raise AssertionError("producer portable checksum inconsistent")

    with tempfile.TemporaryDirectory(prefix="cmpct-o165-mac-", dir=os.environ.get("RUNNER_TEMP")) as td:
        scratch = Path(td)
        restored = scratch / "received"
        verify = o162.call_cli(["verify", str(args.archive)], scratch)
        extract = o162.call_cli(["extract", str(args.archive), str(restored)], scratch)
        actual_strict_digest, actual_strict_manifest = oracle.strict_digest(restored)
        actual_portable = portable_manifest(actual_strict_manifest)
        actual_portable_digest = digest_dict(actual_portable)
        deltas = physical_deltas(source, actual_strict_manifest)
        if any(
            d["origin_type"] != "symlink"
            or d["receiver_type"] != "symlink"
            or d["changed_fields"] != ["mode"]
            for d in deltas
        ):
            raise AssertionError(f"unexpected non-symlink-mode cross-host delta: {deltas}")
        if actual_portable != expected_portable:
            raise AssertionError("cross-host portable O155 structural witness mismatch")
        if actual_portable_digest != receipt["source_portable_digest"]:
            raise AssertionError("cross-host portable digest mismatch")
        hardlink_ok = os.path.samefile(
            restored / "a-base.bin", restored / "nested/hardcopy.bin"
        )
        if not hardlink_ok:
            raise AssertionError("cross-host hardlink relationship lost")
        # Differently rooted hostile negative: same bytes and mode, different inode.
        hardcopy = restored / "nested/hardcopy.bin"
        original_bytes = hardcopy.read_bytes()
        original_mode = stat.S_IMODE(os.lstat(hardcopy).st_mode)
        hardcopy.unlink()
        hardcopy.write_bytes(original_bytes)
        hardcopy.chmod(original_mode)
        no_longer_samefile = not os.path.samefile(restored / "a-base.bin", hardcopy)
        still_same_bytes = hardcopy.read_bytes() == (restored / "a-base.bin").read_bytes()
        mutant_strict_digest, mutant_strict = oracle.strict_digest(restored)
        mutant_portable_digest = digest_dict(portable_manifest(mutant_strict))
        if not no_longer_samefile or not still_same_bytes:
            raise AssertionError("hardlink negative control did not isolate inode topology")
        if mutant_portable_digest == actual_portable_digest:
            raise AssertionError("portable witness ignored hostile hardlink severing")

    if sha256(args.archive) != observed_sha:
        raise AssertionError("macOS verification/extraction changed the source archive")
    return {
        "phase": "consumer", "head": provenance["git_head"],
        "producer_head": receipt["head"],
        "transferred_archive_sha256": observed_sha,
        "transferred_archive_bytes": receipt["archive_bytes"],
        "source_strict_digest": receipt["source_strict_digest"],
        "receiver_strict_digest": actual_strict_digest,
        "strict_manifest_equal": source == actual_strict_manifest,
        "physical_deltas": deltas,
        "portable_projection": PROJECTION,
        "source_portable_digest": receipt["source_portable_digest"],
        "receiver_portable_digest": actual_portable_digest,
        "portable_manifest_equal": True,
        "hardlink_same_inode": hardlink_ok,
        "hostile_hardlink_severed": no_longer_samefile,
        "hostile_bytes_still_equal": still_same_bytes,
        "hostile_portable_digest": mutant_portable_digest,
        "hostile_strict_digest": mutant_strict_digest,
        "hostile_detected": True,
        "receiver_strict_manifest": actual_strict_manifest,
        "installed_verify": verify, "installed_extract": extract,
        "archive_unchanged": True,
        "result": "ONE_AUTHENTIC_ARCHIVE_MACOS_PORTABLE_TREE_FIDELITY_VERIFIED",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", choices=("producer", "receiver"), required=True)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    try:
        o162 = load_o162()
        provenance = identity(o162)
        oracle, _ = o162.load_independent_witnesses()
        if args.role == "producer":
            result = produce(o162, oracle, args, provenance)
        else:
            result = receive(o162, oracle, args, provenance)
        status = 0
    except Exception as exc:
        status = 1
        result = {
            "schema": "cmpct-o165-cross-host-one-archive-v1",
            "role": args.role,
            "result": "FAIL_OR_INFRASTRUCTURE_INCONCLUSIVE",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-6500:],
        }
    write_json(args.output, {"schema": "cmpct-o165-cross-host-one-archive-v1", **result})
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("receiver_strict_manifest", "physical_deltas")},
                     sort_keys=True))
    raise SystemExit(status)


if __name__ == "__main__":
    main()
